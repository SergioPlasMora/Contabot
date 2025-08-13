import logging
import time
import pywinauto
from pywinauto import findwindows
from src.luzzi.helpers.help_bot import WindowHelper
from src.luzzi.helpers.control_bot import ControlBot

logger = logging.getLogger(__name__)


class DialogHandler:
    def __init__(self, app):
        """
        Inicializa el manejador de diálogos con la instancia de la aplicación.

        Args:
            app: Instancia de la aplicación pywinauto.
        """
        self.app = app
        self.bot = ControlBot()

    def manejar_ventana_advertencia_contabilizador(self):
        """
        Maneja la ventana de advertencia dentro del contabilizador.

        Returns:
            bool: True si se manejó la ventana, False si no se encontró o hubo un error.
        """
        ventana_advertencia = self.app.top_window()

        mensaje_completo = ""
        for child in ventana_advertencia.children():
            if child.class_name() == "Static":
                mensaje_completo += child.window_text() + " "

        mensaje_completo = mensaje_completo.strip()

        if (
            "El número de cuentas de clientes / proveedores que desea crear"
            in mensaje_completo
        ):
            boton_aceptar = ventana_advertencia.child_window(
                title="&Aceptar", class_name="Button"
            )
            if boton_aceptar.exists():
                boton_aceptar.click_input()
                logger.debug("Advertencia manejada: Se hizo clic en 'Aceptar'")
                return True
        else:
            logger.warning("\tAdvertencia no identificada")
            return False

    def close_problem_window(self):
        """
        Maneja la ventana de problemas al fallar el inicio de sesión.

        Returns:
            bool: True si se encontró y cerró la ventana, False si no se encontró o hubo un error.
        """
        try:
            problem_hwnds = findwindows.find_windows(
                title="Problema", class_name="SWT_Window0"
            )
            if problem_hwnds:
                problem_hwnd = problem_hwnds[0]
                problem_window = self.app.connect(handle=problem_hwnd).window(
                    handle=problem_hwnd
                )
                logger.error(
                    "Ventana problema encontrada: puede que el usuario o la contraseña sean incorrectos"
                )
                accept_button = problem_window.child_window(
                    title="&Aceptar", class_name="Button"
                )
                accept_button.click()
                logger.debug("Botón 'Aceptar' clickeado.")
                return True
            else:
                logger.debug("No se encontró la ventana de problema.")
                return False
        except pywinauto.findwindows.ElementNotFoundError:
            logger.debug("No se encontró la ventana de problema.")
            return False
        except Exception as e:
            logger.info(f"Error al conectar con la ventana de problema: {str(e)}")
            return False

    def close_login_window(self):
        """
        Cierra la ventana de login cuando las credenciales son incorrectas.

        Returns:
            bool: True si se encontró y cerró la ventana, False si no se encontró o hubo un error.
        """
        try:
            login_hwnds = findwindows.find_windows(
                title="Ingreso a CONTPAQi® Contabilidad", class_name="SWT_Window0"
            )
            if login_hwnds:
                login_hwnd = login_hwnds[0]
                login_window = self.app.connect(handle=login_hwnd).window(
                    handle=login_hwnd
                )
                logger.error(
                    "Ventana de login encontrada: parece que la contraseña es incorrecta"
                )
                login_window.close()
                logger.debug("Ventana de login cerrada.")
                return True
            else:
                logger.debug("No se encontró la ventana de login.")
                return False
        except pywinauto.findwindows.ElementNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error al conectar con la ventana de login: {str(e)}")
            return False

    def handle_warning(self):
        """
        Maneja la ventana de advertencia si está presente.

        Returns:
            bool: True si se manejó la ventana, False si no se encontró o hubo un error.
        """
        try:
            adv_window = self.app.window(title_re=".*Advertencia.*")
            if adv_window.exists(timeout=3):
                logger.debug("Ventana de advertencia encontrada.")
                boton_aceptar = adv_window.child_window(
                    title="&Aceptar", class_name="Button"
                )
                if self.bot.verify_element_state(boton_aceptar):
                    boton_aceptar.click_input()
                    logger.debug(
                        "Botón 'Aceptar' clicado, ventana de advertencia cerrada."
                    )
                    return True
                logger.debug("No se encontró ventana de advertencia.")
        except Exception as e:
            logger.error(f"Error al manejar ventana de advertencia: {str(e)}")
        return False

    def handle_window(self, title, message):
        """
        Maneja distintas ventanas emergentes según su título y mensaje.

        Args:
            title (str): Título de la ventana.
            message (str): Mensaje de la ventana.

        Returns:
            tuple: (bool, str) indicando éxito/fallo y un mensaje descriptivo.
        """
        if title == "":
            return self._handle_untitled_window(message)
        elif title == "Información":
            return self._handle_information_window(message)
        elif title == "Problema":
            return self._handle_problem_window(message)
        elif title == "Confirmación":
            return self._handle_confirmation_window(message)
        elif title == "Advertencia":
            return self._handle_warning_window(message)
        elif title.startswith("CONTPAQi® Contabilidad"):
            company_name = WindowHelper.get_company_name(self.app)
            logger.debug(f"\tEmpresa abierta: {company_name}")
            return True, company_name
        elif title.startswith("Catálogo de Empresas"):
            return None
        else:
            logger.info(
                f"\tVentana no identificada. Título: {title}, Mensaje: {message}"
            )
            return False, "Ventana no manejada"

    def _handle_untitled_window(self, message):
        """Maneja ventanas sin título basado en el mensaje."""
        if not message:
            return None
        if (
            message.startswith("Abriendo la empresa")
            or message.startswith("Creando ADD")
            or message.startswith("Proceso de actualización de esquemas...")
            or message.startswith("Empresas a las")
        ):
            return None
        else:
            logger.info(f"\tVentana sin título no identificada. Mensaje: {message}")
            return False, "Ventana no manejada"

    def _handle_information_window(self, message):
        """Maneja ventanas de información basado en el mensaje."""
        if message.startswith(
            "Uno de tus certificados ha expirado"
        ) or message.startswith("Se identificó una nueva versión de esquemas del ADD"):
            boton_aceptar = self.app.top_window().child_window(
                title="&Aceptar", class_name="Button"
            )
            boton_aceptar.click_input()
            tiempo_maximo_espera = 1200
            pausa = 1
            for _ in range(tiempo_maximo_espera):
                time.sleep(pausa)
                if (
                    not self.app.top_window()
                    .window_text()
                    .startswith("Proceso de actualización de esquemas")
                ):
                    break
            return None
        else:
            logger.info(f"\tInformación no identificada. Mensaje: {message}")
            return False, "Ventana no manejada"

    def _handle_problem_window(self, message):
        """Maneja ventanas de problema basado en el mensaje."""
        if not message:
            return None

        # Mensaje de error de conexión
        if message.startswith("Error al tratar de conectarse al administrador"):
            boton_aceptar = self.app.top_window().child_window(
                title="&Aceptar", class_name="Button"
            )
            boton_aceptar.click_input()
            return False, "Error al tratar de conectarse al ADD"

        elif message.startswith("Los importes de cargos y abonos no son iguales"):
            logger.debug("Detectada ventana de problema: Cargos y abonos no son iguales.")
            boton_aceptar = self.app.top_window().child_window(
                title="&Aceptar", class_name="Button"
            )
            if boton_aceptar.exists(timeout=5):
                boton_aceptar.click_input()
                logger.info("Botón 'Aceptar' presionado para el problema de cargos y abonos.")
                return True, "CARGOS_Y_ABONOS_NO_IGUALES" 
            else:
                logger.error("No se encontró el botón 'Aceptar' en la ventana de problema.")
                return False, "BOTON_ACEPTAR_NO_ENCONTRADO"

        else:
            logger.info(f"\tProblema no identificado. Mensaje: {message}")
            return False, "Ventana no manejada"

    def _handle_confirmation_window(self, message):
        """Maneja ventanas de confirmación basado en el mensaje."""
        if not message:
            return None
        if message.startswith("La versión de la Base de datos de la empresa"):
            boton_no = self.app.top_window().child_window(
                title="&No", class_name="Button"
            )
            if boton_no.exists(timeout=10):
                logger.info("Botón 'No' encontrado. Haciendo clic...")
                boton_no.click_input()
            else:
                logger.error("Botón 'No' no encontrado.")
            return False, "VERSION_INCOMPATIBLE"
        elif message.startswith(
            "La salud de la base de datos se encuentra en estado crítico"
        ):
            boton_no = self.app.top_window().child_window(
                title="&No", class_name="Button"
            )
            if boton_no.exists(timeout=10):
                logger.info("Botón 'No' encontrado. Haciendo clic...")
                boton_no.click_input()
            else:
                logger.error("Botón 'No' no encontrado.")
            return None, "La salud de la base de datos se encuentra en estado crítico"
        else:
            logger.info(f"\tConfirmación no identificada. Mensaje: {message}")
            return True, None

    def _handle_warning_window(self, message):
        """Maneja ventanas de advertencia basado en el mensaje."""
        if not message:
            return None
        if message.startswith("La salud de la base de datos"):
            boton_no = self.app.top_window().child_window(
                title="&No", class_name="Button"
            )
            boton_no.click_input()
            return False, "La salud de la base de datos se encuentra en estado crítico"
        else:
            logger.warning(f"\tAdvertencia no identificada. Mensaje: {message}")
            return False, "Ventana no manejada"
