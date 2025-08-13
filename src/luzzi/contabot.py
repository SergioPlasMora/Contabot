import sys
import psutil
import time
import msvcrt
import logging
from src.utils import setup_logging
from src.data.database import DataAccessLayer, SQLServerConnectionPool
from src.luzzi.helpers import Licencia
from src.config.config import Config
from src.luzzi.page_objects import (
    ApplicationManager,
    DialogHandler,
    LoginPage,
    CompanySelectionPage,
    ContabilizadorWindowPage,
)
from src.luzzi.processors import DatabaseAuthManager, CompanyProcessor

app_path = r"C:\Program Files (x86)\Compac\Contabilidad\contabilidad_i.exe"
NOMBRE_ROBOT = "contabot"

setup_logging()
logger = logging.getLogger(__name__)

class Contabot:
    """Clase principal que controla el flujo del proceso de Contabot."""

    def __init__(self, app_path):
        """
        Inicializa la clase Contabot.

        Args:
            app_path (str): Ruta del ejecutable de la aplicación.
        """
        self.app_manager = ApplicationManager(app_path)
        self.dialog_handler = DialogHandler(None)
        self.app_path = app_path = r"C:\Program Files (x86)\Compac\Contabilidad\contabilidad_i.exe"
        

    def principal(self):
        """Método principal que ejecuta el flujo completo del robot."""
        try:
            if len(sys.argv) > 1:
                return self.ejecutar_comando()

            config = Config.get_instance(["config.yaml", "filters.yaml"])
            credentials = config.get_credentials()

            auth_manager = DatabaseAuthManager(credentials["server"])
            success, message = auth_manager.setup_and_generate_env(
                credentials=credentials, username="LUZZII", password="Luzzi2025"
            )
            print(message)
            if success:
                print(".env generado exitosamente")

            self.validar_licencia()
            self.mostrar_version()
            self.cargar_configuracion()
            self.ejecutar_robot()

        except Exception as e:
            print(f"Error: {e}")
        finally:
            print("\nPresione cualquier tecla para terminar")
            sys.exit(0)

    def ejecutar_robot(self):
        """Ejecuta el robot y realiza la automatización."""
        main_exe = "contabilidad_i.exe"

        try:
            archivos_config = ["config.yaml", "filters.yaml"]
            config = Config.cargar(archivos_config)
            username = config["user"]
            password = config["password"]
        except Exception as e:
            logger.critical(f"Error al cargar la configuración: {e}")
            return

        app = self.app_manager.restart_application(main_exe)
        if app:
            logger.info("Aplicación reiniciada y lista para la automatización.")
            self.dialog_handler = DialogHandler(app)  # Actualizar con app
            login_page = LoginPage(app, app_path)
            if login_page.login(username, password):
                logger.debug(
                    "Inicio de sesión exitoso. Continúa con la automatización."
                )
                company_selection_page = CompanySelectionPage(app)
                if company_selection_page.open_catalog():
                    time.sleep(0.5)
                    connection_pool = SQLServerConnectionPool(pool_size=5)
                    data_access_layer = DataAccessLayer(connection_pool)
                    processor = CompanyProcessor(app, data_access_layer)
                    processor.process_companies()
                    for proc in psutil.process_iter(["name", "pid"]):
                        if proc.info["name"].lower() == main_exe.lower():
                            self.terminar_ejecucion(proc.info["pid"])
                else:
                    logger.critical(
                        "Error al intentar acceder al Catálogo de Empresas."
                    )
            else:
                logger.critical(
                    "Error en el inicio de sesión. Abortando automatización."
                )
        else:
            logger.critical("No se pudo reiniciar la aplicación.")

    def ejecutar_comando(self):
        """Ejecuta comandos adicionales si se pasan argumentos."""
        from src.main import main_function

        try:
            main_function()
            return 0
        except Exception as e:
            logger.error(f"Error inesperado: {str(e)}")
            return 1

    def mensaje(self, mensaje, tiempo_espera=10):
        """Muestra un mensaje y espera interacción o tiempo límite."""
        logger.info(mensaje)
        if tiempo_espera > 0:
            start_time = time.time()
            while True:
                if msvcrt.kbhit():
                    msvcrt.getch()
                    break
                elif time.time() - start_time >= tiempo_espera:
                    break

    def validar_nombre_ejecutable(self, nombre_ejecutable):
        """Valida que el nombre del ejecutable sea correcto."""
        nombre_instancia = sys.argv[0].lower()
        nombres_validos = [nombre_ejecutable, f"{nombre_ejecutable}.exe"]
        if nombre_instancia not in nombres_validos:
            raise ValueError(
                f"El nombre del proceso en ejecución [{nombre_instancia}] no es válido"
            )
        return True

    def validar_instancias(self, nombre_ejecutable):
        """Valida que no haya múltiples instancias ejecutándose."""
        contador = 0
        for proc in psutil.process_iter():
            try:
                if proc.name().lower() == nombre_ejecutable.lower():
                    contador += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if contador > 1:
            raise ValueError(
                f"La aplicación se está ejecutando en este momento por el usuario [{proc.username}]. Espere que termine su ejecución."
            )

    def mostrar_version(self):
        """Muestra la versión de la aplicación."""
        from src.utils import AppInfo
        AppInfo.print_version()

    def validar_licencia(self):
        """Valida que la licencia sea correcta y no esté expirada."""
        Licencia.validar()

    def cargar_configuracion(self):
        """Carga la configuración desde los archivos YAML."""
        return Config.cargar()

    def terminar_ejecucion(self, pid):
        """Termina la ejecución de un proceso dado su PID."""
        try:
            proc = psutil.Process(pid)
            if proc.is_running():
                logger.debug(f"Cerrando proceso (PID: {pid})")
                proc.terminate()
                proc.wait(timeout=10)
            else:
                logger.debug(f"El proceso con PID {pid} no está en ejecución.")
        except psutil.NoSuchProcess:
            logger.debug(f"No se encontró el proceso con PID {pid}.")
        except psutil.AccessDenied:
            logger.debug(
                f"Acceso denegado al intentar cerrar el proceso con PID {pid}."
            )
        except psutil.TimeoutExpired:
            logger.warning(
                f"Forzando cierre del proceso con PID {pid} debido a tiempo de espera agotado."
            )
            proc.kill()
        except Exception as e:
            logger.error(f"Error al intentar cerrar el proceso con PID {pid}: {str(e)}")


if __name__ == "__main__":
    contabot = Contabot(app_path)
    contabot.principal()
