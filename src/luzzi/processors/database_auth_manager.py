import subprocess
import logging
from typing import Tuple, Dict, List
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class DatabaseAuthManager:
    """Clase para manejar la autenticación y generación del archivo .env en SQL Server."""

    def __init__(self, server: str):
        self.server = server

    @staticmethod
    def check_user_exists(server: str, username: str) -> bool:
        """Verifica si un usuario existe en el servidor SQL."""
        try:
            query = (
                f"SELECT COUNT(*) FROM sys.server_principals WHERE name = '{username}'"
            )
            result = subprocess.run(
                f'sqlcmd -S {server} -E -Q "{query}" -h-1',
                shell=True,
                capture_output=True,
                text=True,
                check=True,
            )
            output = result.stdout.strip().splitlines()
            for line in output:
                line = line.strip()
                if line.isdigit():
                    return int(line) > 0
            raise ValueError(f"No se pudo interpretar salida: {result.stdout}")
        except Exception as e:
            log.error(f"Error al verificar existencia del usuario {username}: {e}")
            return False

    @staticmethod
    def get_user_creation_queries(username: str, password: str) -> List[str]:
        """Genera las consultas SQL para crear un usuario."""
        return [
            f"IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{username}') "
            f"CREATE LOGIN [{username}] WITH PASSWORD = '{password}'",
            f"USE master",
            f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{username}') "
            f"CREATE USER [{username}] FOR LOGIN [{username}]",
            f"IF IS_SRVROLEMEMBER('sysadmin', '{username}') = 0 "
            f"EXEC sp_addsrvrolemember '{username}', 'sysadmin'",
            f"GRANT CONNECT SQL TO [{username}]",
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON DATABASE::[master] TO [{username}]",
        ]

    def try_windows_auth(self, username: str, password: str) -> Tuple[bool, str]:
        """Intenta autenticación Windows y crea el usuario si no existe."""
        try:
            if self.check_user_exists(self.server, username):
                return True, f"El usuario {username} ya existe"

            queries = self.get_user_creation_queries(username, password)
            for query in queries:
                result = subprocess.run(
                    f'sqlcmd -S {self.server} -E -Q "{query}"',
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                if any(
                    err in result.stderr
                    for err in [
                        "User does not have permission",
                        "does not exist or you do not have permission",
                        "Grantor does not have GRANT permission",
                    ]
                ):
                    return (
                        False,
                        "No tiene permisos suficientes para crear usuario con Windows Authentication",
                    )

            if self.check_user_exists(self.server, username):
                return (
                    True,
                    f"Usuario {username} creado exitosamente usando autenticación Windows",
                )
            return False, "No se pudo crear el usuario con Windows Authentication"

        except subprocess.CalledProcessError as e:
            log.error(f"Error de subprocess en autenticación Windows: {e}")
            return False, str(e)
        except Exception as e:
            log.critical(f"Fallo crítico en autenticación Windows: {e}", exc_info=True)
            return False, str(e)

    def try_sql_auth(
        self, admin_user: str, admin_password: str, new_username: str, new_password: str
    ) -> Tuple[bool, str]:
        """Intenta autenticación SQL usando credenciales de administrador."""
        try:
            if self.check_user_exists(self.server, new_username):
                return True, f"El usuario {new_username} ya existe"

            queries = self.get_user_creation_queries(new_username, new_password)
            for query in queries:
                cmd = f'sqlcmd -S "{self.server}" -U "{admin_user}" -P "{admin_password}" -Q "{query}"'
                subprocess.run(cmd, shell=True, check=True)
            return (
                True,
                f"Usuario {new_username} creado exitosamente usando credenciales de administrador",
            )
        except Exception as e:
            log.error(f"Error en autenticación SQL: {e}")
            return False, str(e)

    def generate_env_file(self, config: Dict[str, str]) -> None:
        """Genera el archivo .env con la configuración proporcionada."""
        try:
            env_content = "\n".join([f"{k}={v}" for k, v in config.items()])
            with open(".env", "w") as f:
                f.write(env_content)
            log.info("Archivo .env generado exitosamente")
        except Exception as e:
            log.error(f"Error al generar el archivo .env: {e}")
            raise

    def setup_and_generate_env(
        self, credentials: Dict[str, str], username: str, password: str
    ) -> Tuple[bool, str]:
        """Intenta crear el usuario y generar el archivo .env."""
        success, message = self.try_windows_auth(username=username, password=password)

        if (
            not success
            and credentials.get("admin_user")
            and credentials.get("admin_password")
        ):
            success, message = self.try_sql_auth(
                admin_user=credentials["admin_user"],
                admin_password=credentials["admin_password"],
                new_username=username,
                new_password=password,
            )

        if success and "exitosamente" in message:
            env_config = {
                "DB_DRIVER": "SQL Server",
                "DB_SERVER": credentials["server"],
                "DB_USER": username,
                "DB_PASSWORD": password,
                "DB_TRUSTED_CONNECTION": "no",
                "DB_TIMEOUT": "30",
            }
            self.generate_env_file(env_config)

        return success, message


if __name__ == "__main__":
    from src.config.config import Config

    config = Config.get_instance(["config.yaml", "filters.yaml"])
    credentials = config.get_credentials()

    auth_manager = DatabaseAuthManager(credentials["server"])
    success, message = auth_manager.setup_and_generate_env(
        credentials=credentials, username="LUZZII", password="Luzzi2025"
    )
    print(message)
    if success:
        print(".env generado exitosamente")
