import pyodbc
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, TypeVar, Generic
from queue import Queue
import logging
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, date
from dataclasses import dataclass
from abc import abstractmethod

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def get_env_path():
    """
    Finds .env file in multiple potential locations
    Priority:
    1. Same directory as executable/script
    2. Parent directory
    3. Default .env in current working directory
    """
    # Possible paths to search for .env
    possible_paths = [
        # Path of the current script/executable
        os.path.join(get_application_path(), ".env"),
        # Parent directory of the script/executable
        os.path.join(get_application_path(), "..", ".env"),
        # Current working directory
        os.path.join(os.getcwd(), ".env"),
    ]

    # Default drivers to try if not specified
    default_drivers = ["ODBC Driver 17 for SQL Server", "SQL Server"]

    # Try to find existing .env file
    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def get_application_path():
    """Obtiene la ruta correcta sea en desarrollo o en el ejecutable"""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
        return base_path
    else:
        return os.path.dirname(os.path.abspath(__file__))


@dataclass
class ConnectionConfig:
    """Clase para manejar la configuración de conexión con flexibilidad de drivers"""

    driver: str = None
    server: str = None
    username: str = None
    password: str = None
    trusted_connection: bool = False
    timeout: int = 30

    def __post_init__(self):
        """
        Load configuration with fallback mechanisms
        1. Try loading from .env file
        2. Use default drivers if not specified
        """
        env_path = get_env_path()
        if env_path:
            load_dotenv(env_path)

        self.driver = self.driver or os.getenv("DB_DRIVER")
        self.server = self.server or os.getenv("DB_SERVER")
        self.username = self.username or os.getenv("DB_USER")
        self.password = self.password or os.getenv("DB_PASSWORD")

        default_drivers = ["ODBC Driver 17 for SQL Server", "SQL Server"]

        if not self.driver:
            for test_driver in default_drivers:
                try:
                    self._test_driver(test_driver)
                    self.driver = test_driver
                    break
                except Exception as e:
                    print(f"Error al probar el driver {test_driver}: {e}")
            else:
                raise ValueError("No valid SQL driver found")

        required_vars = {
            "Driver": self.driver,
            "Server": self.server,
            "Username": self.username,
            "Password": self.password,
        }

        missing = [var for var, value in required_vars.items() if not value]
        if missing:
            raise ValueError(f"Faltan variables requeridas: {', '.join(missing)}")

    def _test_driver(self, driver_name):
        """
        Test if a specific driver is available
        Implement basic driver validation logic
        """
        try:
            import pyodbc

            # Attempt to list drivers
            drivers = pyodbc.drivers()
            return driver_name in drivers
        except Exception:
            return False

    def get_connection_string(self, database: str) -> str:
        """Generate connection string with flexible configuration"""
        if self.trusted_connection:
            return (
                f"Driver={{{self.driver}}};"
                f"Server={self.server};"
                f"Trusted_Connection=Yes;"
                f"Connection Timeout={self.timeout};"
                f"Database={database};"
                f"TrustServerCertificate=yes;"
            )
        else:
            return (
                f"Driver={{{self.driver}}};"
                f"Server={self.server};"
                f"UID={self.username};"
                f"PWD={self.password};"
                f"Connection Timeout={self.timeout};"
                f"Database={database};"
                f"TrustServerCertificate=yes;"
            )


class DatabaseError(Exception):
    pass


T = TypeVar("T")


class ConnectionPool(Generic[T]):
    """Clase base abstracta para pools de conexiones"""

    @abstractmethod
    def get_connection(self, database: str) -> T:
        pass

    @abstractmethod
    def return_connection(self, database: str, connection: T) -> None:
        pass


class SQLServerConnectionPool(ConnectionPool[pyodbc.Connection]):
    def __init__(self, pool_size: int = 5, config: Optional[ConnectionConfig] = None):
        self.config = config or ConnectionConfig()
        self.pools: Dict[str, Queue[pyodbc.Connection]] = {}
        self.size = pool_size

    def _create_connection(self, database: str) -> pyodbc.Connection:
        """Crea la conexión a la base de datos."""
        try:
            connection_string = self.config.get_connection_string(database)
            return pyodbc.connect(connection_string)
        except pyodbc.Error as e:
            logger.error(f"Error creating connection to database {database}: {e}")
            raise DatabaseError(f"Could not create connection: {e}")

    def get_connection(self, database: str) -> pyodbc.Connection:
        if database not in self.pools:
            self.pools[database] = Queue(maxsize=self.size)
            for _ in range(self.size):
                self.pools[database].put(self._create_connection(database))
            logger.debug(f"Created new connection pool for database {database}")

        try:
            return self.pools[database].get(timeout=5)
        except Exception as e:
            logger.error(
                f"Error getting connection from pool for database {database}: {e}"
            )
            raise DatabaseError(f"Could not get connection from pool: {e}")

    def return_connection(self, database: str, connection: pyodbc.Connection) -> None:
        try:
            self.pools[database].put(connection, timeout=5)
        except Exception as e:
            logger.warning(
                f"Could not return connection to pool for database {database}: {e}"
            )
            connection.close()

    def close(self) -> None:
        """Cierra todas las conexiones en el pool"""
        for database, pool in self.pools.items():
            while not pool.empty():
                conn = pool.get()
                conn.close()

    @contextmanager
    def connection(self, database: str):
        conn = None
        try:
            conn = self.get_connection(database)
            yield conn
        except Exception as e:
            logger.error(f"Error during connection usage: {e}")
            raise
        finally:
            if conn:
                self.return_connection(database, conn)


class QueryRepository:
    """Repositorio de queries con validación de existencia"""

    QUERIES = {
        "get_estruct_cta": "SELECT EstructCta FROM [dbo].[Parametros] WHERE Id = ?",
        "get_Par_Func": "SELECT ParFunc FROM [dbo].[Parametros] WHERE Id = ?",
        "get_empresa_info": "SELECT * FROM [dbo].[ListaEmpresas] WHERE Id = ?",
        "get_all_empresas": """
            SELECT Id, Nombre, AliasBDD 
            FROM [GeneralesSQL].[dbo].[ListaEmpresas]
        """,
        "get_empresas_por_usuario": """
            SELECT le.Id, le.Nombre, le.AliasBDD 
            FROM [GeneralesSQL].[dbo].[EmpresasUsuario] eu
            INNER JOIN [GeneralesSQL].[dbo].[ListaEmpresas] le ON eu.IdEmpresa = le.Id
            INNER JOIN [GeneralesSQL].[dbo].[Usuarios] u ON eu.IdUsuario = u.Id
            WHERE u.Nombre = ?
        """,
        "check_empresa": """
            SELECT Id, AliasBDD FROM [dbo].[ListaEmpresas] WHERE Id = ?
        """,
        "check_tabla_parametros": """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME = 'Parametros'
        """,
        "get_estructura_cta": """
            SELECT EstructCta FROM [dbo].[Parametros] WHERE Id = 1
        """,
        "get_parametros_funcionamiento": """
            SELECT ParFunc FROM [dbo].[Parametros] WHERE Id = 1
        """,
    }

    @classmethod
    def get_query(cls, query_name: str) -> str:
        if query_name not in cls.QUERIES:
            raise ValueError(f"Query '{query_name}' not found in repository")
        return cls.QUERIES[query_name]


class DataAccessLayer:
    def __init__(self, connection_pool: SQLServerConnectionPool):
        self.connection_pool = connection_pool
        self.logger = logging.getLogger(__name__)

    def get_connection(self):
        return self.connection_pool.get_connection()

    def execute_query(
        self, database: str, query: str, params: tuple = ()
    ) -> List[Dict[str, Any]]:
        try:
            with self.connection_pool.connection(database) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    columns = [column[0] for column in cursor.description]
                    return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            self.logger.error(f"Error executing query in {database}: {e}")
            raise DatabaseError(f"Query execution failed: {e}")

    def execute_scalar(
        self, database: str, query: str, params: tuple = ()
    ) -> Optional[Any]:
        try:
            with self.connection_pool.connection(database) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    result = cursor.fetchone()
                    return result[0] if result else None
        except Exception as e:
            self.logger.error(f"Error executing scalar query in {database}: {e}")
            raise DatabaseError(f"Scalar query execution failed: {e}")

    def get_estruct_cta(self, database: str, param_id: int) -> Optional[str]:
        """Obtiene la estructura de la cuenta a partir de un ID específico"""
        query = QueryRepository.get_query("get_estruct_cta")
        return self.execute_scalar(database, query, (param_id,))

    def get_Par_Func(self, database: str, param_id: int) -> Optional[str]:
        """Obtiene los parámetros de funcionamiento a partir de un ID específico"""
        query = QueryRepository.get_query("get_Par_Func")
        return self.execute_scalar(database, query, (param_id,))

    def get_database_alias(self, empresa_id: int) -> Optional[str]:
        """Obtiene el alias de la base de datos a partir del Id de la empresa."""
        query = "SELECT AliasBDD FROM [dbo].[ListaEmpresas] WHERE Id = ?"
        result = self.execute_scalar("GeneralesSQL", query, (empresa_id,))
        return result

    def get_empresa_info(self, empresa_id: int):
        """Obtiene la información de la empresa a partir del Id."""
        query = "SELECT * FROM [dbo].[ListaEmpresas] WHERE Id = ?"
        connection = self.connection_pool.get_connection()

        try:
            with connection.cursor() as cursor:
                cursor.execute(query, (empresa_id,))
                row = cursor.fetchone()

                if row:
                    columns = [column[0] for column in cursor.description]
                    empresa_info = dict(zip(columns, row))
                    return empresa_info
                else:
                    return None
        finally:
            self.connection_pool.release_connection(connection)

    def get_all_empresas(self) -> List[Dict[str, Any]]:
        """Obtiene todas las empresas"""
        query = QueryRepository.get_query("get_all_empresas")
        return self.execute_query("GeneralesSQL", query)

    def get_empresas_por_usuario(self, username: str) -> List[Dict[str, Any]]:
        """Obtiene las empresas asociadas a un usuario"""
        query = QueryRepository.get_query("get_empresas_por_usuario")
        return self.execute_query("GeneralesSQL", query, (username,))

    def get_empresas(self, user_codigo: str) -> List[Dict[str, Any]]:
        """Obtiene las empresas a las que tiene acceso el usuario"""
        query = """
        SELECT eu.IdEmpresa, e.Nombre, e.AliasBDD
        FROM GeneralesSQL.dbo.EmpresasUsuario eu
        LEFT JOIN GeneralesSQL.dbo.Usuarios u ON eu.IdUsuario = u.id
        LEFT JOIN GeneralesSQL.dbo.ListaEmpresas e ON eu.IdEmpresa = e.id
        WHERE u.Codigo = ?
        """
        return self.execute_query("GeneralesSQL", query, (user_codigo,))

    def get_asientos(self, database: str) -> List[Dict[str, Any]]:
        """Obtiene los asientos que contienen el token 'LUZZI' y el TipoXML."""
        query = f"""        
        SELECT *
        FROM (
            SELECT 
                a.Codigo,
                a.Nombre,
                a.TipoXML,
                CASE 
                    WHEN COUNT(
                        CASE 
                            WHEN m.FormulaCuenta IS NULL 
                                OR m.FormulaCuenta IN ('Banco_Deudor', 'Por captar','Gastos_Proveedor')
                            THEN 1 
                        END
                    ) > 0 THEN 'Inválido'
                    ELSE 'Válido'
                END AS ValFormulaCuenta
            FROM {database}.dbo.Asientos a 
            LEFT JOIN {database}.dbo.MovimientosAsiento m 
                ON a.Id = m.IdAsiento
            WHERE a.TipoXML IN (1, 4)
            GROUP BY 
                a.Codigo, 
                a.Nombre, 
                a.TipoXML
        ) AS t
        WHERE t.ValFormulaCuenta = 'Válido'
        AND t.Nombre NOT LIKE '%Cobro%'
        AND t.Nombre NOT LIKE '%Pago%'
        ORDER BY t.Codigo;
        """
        return self.execute_query(database, query)

    def get_cuenta_for_empresa(self, alias_database: str, tipo_cuenta: str) -> list:
        """
        Obtiene y valida la cuenta contable según el tipo y la empresa.

        Args:
            alias_database (str): Nombre de la base de datos de la empresa
            tipo_cuenta (str): Tipo de cuenta ('cliente' o 'proveedor')

        Returns:
            list: Lista con diccionario conteniendo el código y estado de la cuenta
        """
        codigos_agrupador = {"cliente": "105.01", "proveedor": "201.01"}

        if tipo_cuenta not in codigos_agrupador:
            return [
                {
                    "codigo": None,
                    "estado": "Inválido",
                    "mensaje": f"Tipo de cuenta no válido: {tipo_cuenta}",
                }
            ]

        query = f"""
            SELECT TOP 1
                c.Codigo,
                p.EstructCta,
                calc.ultimoSegmento,
                CASE 
                    WHEN calc.ultimoSegmento <= 0 THEN 'Inválido'
                    WHEN RIGHT(c.Codigo, calc.ultimoSegmento) = REPLICATE('0', calc.ultimoSegmento) 
                    THEN 'Válido'
                    ELSE 'Inválido'
                END AS Estatus
            FROM {alias_database}.dbo.Cuentas c
            LEFT JOIN AgrupadoresSAT a 
                ON c.IdAgrupadorSAT = a.Id 
            INNER JOIN {alias_database}.dbo.Parametros p 
                ON p.IdEmpresa = p.IdEmpresa  
            CROSS APPLY (
                SELECT 
                    CASE 
                        WHEN CHARINDEX('-', REVERSE('-' + p.EstructCta)) > 1 
                            THEN CAST(
                                REVERSE(
                                    SUBSTRING(
                                        REVERSE('-' + p.EstructCta), 
                                        1, 
                                        (CHARINDEX('-', REVERSE('-' + p.EstructCta)) - 1) -- Paréntesis explícitos
                                    )
                                ) AS INT 
                            )
                        ELSE 0 
                    END AS ultimoSegmento 
            ) AS calc
            WHERE 
                a.Codigo = ?
                AND c.Afectable = 0 
                AND c.EsBaja = 0
            ORDER BY c.Codigo;
        """

        try:
            result = self.execute_query(
                alias_database, query, (codigos_agrupador[tipo_cuenta],)
            )

            if not result:
                return [
                    {
                        "codigo": None,
                        "estado": "Inválido",
                        "mensaje": f"No se encontró cuenta para {tipo_cuenta}",
                    }
                ]

            cuenta = result[0]

            return [
                {
                    "codigo": cuenta["Codigo"],
                    "estado": cuenta["Estatus"],
                    "mensaje": f"La cuenta {cuenta['Codigo']} {'tiene' if cuenta['Estatus'] == 'Válido' else 'no tiene'} el formato correcto en su último segmento",
                }
            ]

        except Exception as e:
            return [{"codigo": None, "estado": "Inválido", "mensaje": str(e)}]

    def validar_parametros(self, alias_database: str) -> List[Dict[str, Any]]:
        """
        Valida los parámetros de funcionamiento para una base de datos específica.

        Args:
            alias_database (str): Alias de la base de datos a validar

        Returns:
            List[Dict[str, Any]]: Lista de resultados de validación
        """
        query = f"""
        SELECT 
            Id,
            ParFunc,
            CASE 
                WHEN LEN(REPLACE(ParFunc, ' ', '')) >= 43
                AND SUBSTRING(REPLACE(ParFunc, ' ', ''), 7, 1) = 'N' 
                AND (SUBSTRING(REPLACE(ParFunc, ' ', ''), 8, 1) = 'S'
                OR SUBSTRING(REPLACE(ParFunc, ' ', ''), 8, 1) = 'M')
                AND SUBSTRING(REPLACE(ParFunc, ' ', ''), 43, 1) = 'S'  
                THEN 'Válido'
                ELSE 'Inválido'
            END AS estado
        FROM {alias_database}.[dbo].[Parametros];
        """

        try:
            # Execute the query and return the results
            return self.execute_query(alias_database, query)
        except Exception as e:
            self.logger.error(f"Error validando parámetros en {alias_database}: {e}")
            raise DatabaseError(f"Validation failed: {e}")

    def get_fechas_for_empresa(self, alias_database: str) -> tuple:
        query = """
        SELECT 
            CONVERT(VARCHAR, DATEFROMPARTS(e.Ejercicio, p.PerActual, 1), 23) AS FechaInicial,
            CONVERT(VARCHAR, EOMONTH(DATEFROMPARTS(e.Ejercicio, p.PerActual, 1)), 23) AS FechaFinal
        FROM 
            {alias_database}.dbo.Parametros AS p
        LEFT JOIN 
            {alias_database}.dbo.Ejercicios AS e 
            ON p.EjerActual = e.Id
        """
        try:
            result = self.execute_query(
                alias_database, query.format(alias_database=alias_database)
            )
            if not result or len(result) == 0:
                raise ValueError("No se encontraron fechas para la empresa")

            fecha_inicial, fecha_final = (
                result[0]["FechaInicial"],
                result[0]["FechaFinal"],
            )

            # Función auxiliar para manejar cualquier tipo de fecha
            def format_date(date_value):
                if isinstance(date_value, str):
                    try:
                        return datetime.strptime(date_value, "%Y-%m-%d").strftime(
                            "%d/%m/%Y"
                        )
                    except ValueError:
                        return datetime.strptime(date_value, "%d/%m/%Y").strftime(
                            "%d/%m/%Y"
                        )
                elif isinstance(date_value, (date, datetime)):
                    return date_value.strftime("%d/%m/%Y")
                else:
                    raise ValueError(f"Tipo de fecha no soportado: {type(date_value)}")

            try:
                fecha_inicial_str = format_date(fecha_inicial)
                fecha_final_str = format_date(fecha_final)
                return fecha_inicial_str, fecha_final_str
            except Exception as e:
                logger.error(f"Error al formatear fechas: {e}")
                raise

        except Exception as e:
            logger.error(f"Error al obtener las fechas para la empresa: {e}")
            raise

    def cleanup(self) -> None:
        """Método para limpiar el pool de conexiones"""
        self.connection_pool.close()
        logger.info("Cleaned up resources")


if __name__ == "__main__":
    connection_pool = SQLServerConnectionPool()
    data_access_layer = DataAccessLayer(connection_pool)
    dal = DataAccessLayer(connection_pool)
    username = "LUZZI"
    # empresas = dal.get_empresas_por_usuario(username)
    # print(f"USER LUZZI {empresas}")

    # fecha = data_access_layer.get_fechas_for_empresa("ctGREXTI_2024")
    # print(fecha)

    try:
        codigo = data_access_layer.get_cuenta_for_empresa(
        "ctEmpresa17", "cliente")
        print(f"Código obtenido: {codigo}")
        codigo = data_access_layer.get_cuenta_for_empresa(
        "ctEmpresa18", "cliente")
        print(f"Código obtenido: {codigo}")
        codigo = data_access_layer.get_cuenta_for_empresa("ctEmpresa17", "proveedor")
        codigo = data_access_layer.get_cuenta_for_empresa("ctEmpresa18", "proveedor")
        print(f"Código obtenido: {codigo}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

        # 201-01-01-1000
        # 201-01-01-0000

        # 10102011000
