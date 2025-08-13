from src.luzzi.contabot import Contabot
from src.data.database import DataAccessLayer, SQLServerConnectionPool
import logging


class RunBot:
    def __init__(self):
        self.connection_pool = SQLServerConnectionPool(pool_size=5)
        self.data_access = DataAccessLayer(self.connection_pool)
        self._setup_database_connection()

    def _setup_database_connection(self):
        try:
            logging.info("Conexión a base de datos establecida correctamente")
        except Exception as e:
            logging.error(f"Error al establecer conexión con la base de datos: {e}")
            raise

    def run(self):
        app_path = r"C:\Program Files (x86)\Compac\Contabilidad\contabilidad_i.exe"
        
        contabot = Contabot(app_path)

        try:
            contabot.ejecutar_robot()
            print("El bot ha sido ejecutado correctamente.")

        except Exception as e:
            logging.error(f"Error en la ejecución del robot: {e}")
        finally:
            self.connection_pool.close()
            print("RunBot finalizado.")
