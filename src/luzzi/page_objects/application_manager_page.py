import logging
import time
import subprocess
import psutil
import pywinauto
from pywinauto import Desktop

logger = logging.getLogger(__name__)


class ApplicationManager:
    def __init__(self, app_path):
        """
        Inicializa el administrador de la aplicación con la ruta del ejecutable.

        Args:
            app_path (str): Ruta del archivo ejecutable de la aplicación.
        """
        self.app_path = app_path

    def is_active_desktop(self):
        """
        Verifica si el escritorio tiene ventanas activas.

        Returns:
            bool: True si hay ventanas abiertas, False en caso de error o si no hay ventanas.
        """
        try:
            desktop = Desktop(backend="win32")
            windows = desktop.windows()
            return len(windows) > 0
        except Exception:
            return False

    def is_app_running(self, app_name, user):
        """
        Verifica si la aplicación está activa para el usuario especificado.

        Args:
            app_name (str): Nombre de la aplicación.
            user (str): Nombre del usuario.

        Returns:
            bool: True si la aplicación está corriendo para el usuario, False en caso contrario.
        """
        return any(
            p.info["name"].lower() == app_name.lower() and p.info["username"] == user
            for p in psutil.process_iter(["name", "username"])
        )

    def close_main_process(self, main_exe_name, current_user):
        """
        Cierra el proceso principal de la aplicación para el usuario especificado.

        Args:
            main_exe_name (str): Nombre del ejecutable principal.
            current_user (str): Nombre del usuario del sistema.
        """
        for proc in psutil.process_iter(["name", "username"]):
            try:
                if (
                    proc.info["name"].lower() == main_exe_name.lower()
                    and proc.info["username"] == current_user
                ):
                    proc.terminate()
                    proc.wait(timeout=10)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                pass

    def verify_process_running(self, main_exe_name, current_user):
        """
        Verifica si el proceso de la aplicación está activo para el usuario especificado.

        Args:
            main_exe_name (str): Nombre del ejecutable principal.
            current_user (str): Nombre del usuario del sistema.

        Returns:
            bool: True si el proceso está corriendo, False en caso contrario.
        """
        return any(
            p.info["name"].lower() == main_exe_name.lower()
            and p.info["username"] == current_user
            for p in psutil.process_iter(["name", "username"])
        )

    def restart_application(self, main_exe_name, wait_time=15, max_retries=3):
        """
        Reinicia la aplicación especificada.

        Args:
            main_exe_name (str): Nombre del ejecutable principal.
            wait_time (int): Tiempo de espera entre intentos (segundos).
            max_retries (int): Número máximo de intentos.

        Returns:
            pywinauto.Application: Instancia de la aplicación conectada o None si falla.
        """
        logger.debug(f"Iniciando proceso de reinicio para {main_exe_name}")
        current_user = psutil.Process().username()
        logger.debug("Luzzi RPA Contabilizador v0.2.0 beta")
        logger.debug(
            "Automatiza la contabilización de CFDIs en CONTPAQi(R) Contabilidad"
        )
        logger.debug("(compatible con CONTPAQi(R) Contabilidad 16.4.1+)")
        logger.debug(f"Usuario actual: {current_user}")

        for attempt in range(max_retries):
            if self.is_app_running(main_exe_name, current_user):
                logger.debug(
                    f"La aplicación {main_exe_name} ya está en ejecución para el usuario {current_user}."
                )
                try:
                    app = pywinauto.Application(backend="win32").connect(
                        path=main_exe_name
                    )
                    return app
                except Exception as e:
                    logger.critical(f"Error al conectar con {main_exe_name}: {str(e)}")

            self.close_main_process(main_exe_name, current_user)
            time.sleep(2)
            logger.debug(
                f"Iniciando {main_exe_name} (intento {attempt + 1}/{max_retries})"
            )
            try:
                subprocess.Popen(self.app_path)
            except Exception as e:
                logger.critical(f"Error al iniciar {main_exe_name}: {str(e)}")
                continue

            if not self.verify_process_running(main_exe_name, current_user):
                logger.critical(
                    f"El proceso {main_exe_name} no se inició correctamente"
                )
                continue

            try:
                app = pywinauto.Application(backend="win32").connect(path=main_exe_name)
                logger.debug(f"Conexión exitosa con {main_exe_name}")
                return app
            except Exception as e:
                logger.critical(f"Error al conectar con {main_exe_name}: {str(e)}")

        logger.critical(
            f"No se pudo iniciar {main_exe_name} después de {max_retries} intentos."
        )
        return None
