import logging
from src.luzzi.page_objects.application_manager_page import ApplicationManager
from src.luzzi.page_objects.dialog_handler_page import DialogHandler
from src.luzzi.helpers.control_bot import ControlBot


logger = logging.getLogger(__name__)


class LoginPage:
    def __init__(self, app, app_path):
        self.app = app
        self.login_window = None
        self.app_path = app_path
        self.app_manager = ApplicationManager(app_path)
        self.dialog_handler = DialogHandler(app)
        self.bot = ControlBot()

    def procesar_ventana_emergente(self, title, message):
        resultado = self.dialog_handler.handle_window(title, message)
        if resultado:
            print(f"Ventana manejada: {title}")
        else:
            print(f"No se pudo manejar la ventana: {title}")
        return resultado

    def find_login_window(self):
        """Busca la ventana de inicio de sesión."""
        try:
            self.login_window = self.app.window(
                title_re=".*Ingreso a CONTPAQi® Contabilidad.*"
            )
            return self.bot.wait_for_element(self.login_window, timeout=80)
        except Exception as e:
            logger.critical(f"Error al buscar la ventana de login: {str(e)}")
            return False

    def enter_username(self, user):
        """Ingresa el nombre de usuario en el campo correspondiente."""
        if self.login_window:
            self.login_window.Edit1.type_keys(user, with_spaces=True)

    def enter_password(self, password):
        """Ingresa la contraseña en el campo correspondiente."""
        if self.login_window:
            self.login_window.Edit2.type_keys(password, with_spaces=True)

    def click_accept(self):
        """Hace clic en el botón 'Aceptar'."""
        if self.login_window:
            self.login_window.Aceptar.click()

    def login(self, user, password):
        """
        Ejecuta el proceso de inicio de sesión.

        Args:
            user: Nombre del usuario.
            password: Contraseña del usuario.
        Returns:
            bool: True si el inicio de sesión es exitoso, False si falla.
        """
        try:
            if self.find_login_window():
                self.enter_username(user)
                self.enter_password(password)
                self.click_accept()

                # Usar DialogHandler para manejar ventanas emergentes
                if self.dialog_handler.close_problem_window():
                    logger.error("Credenciales incorrectas. Cerrando ventana de login.")
                    self.dialog_handler.close_login_window()
                    return False

                # Usar la instancia existente de ApplicationManager
                if self.app_manager.is_active_desktop():
                    main_window = self.app.window(title_re=".*CONTPAQi® Contabilidad.*")
                    self.bot.wait_for_element(main_window, timeout=15)
                    if not main_window.is_maximized():
                        main_window.maximize()
                    main_window.set_focus()
                    logger.debug("Ventana principal maximizada y enfocada.")
                else:
                    logger.error(
                        "No hay escritorio activo. No se puede maximizar la ventana principal."
                    )
                return True
            else:
                logger.info(
                    "Ventana de login no encontrada, posiblemente ya autenticado."
                )
                if self.app_manager.is_active_desktop():
                    main_window = self.app.window(title_re=".*CONTPAQi® Contabilidad.*")
                    if main_window.exists(timeout=5):
                        if not main_window.is_maximized():
                            main_window.maximize()
                        main_window.set_focus()
                        logger.debug("Ventana principal maximizada y enfocada.")
                else:
                    logger.error(
                        "No hay escritorio activo. No se puede maximizar la ventana principal."
                    )
                return True
        except Exception as e:
            logger.critical(f"Error al intentar iniciar sesión: {str(e)}")
            return False
