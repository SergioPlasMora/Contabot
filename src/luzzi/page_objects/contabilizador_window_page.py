import logging
import time
import traceback
import win32gui
from src.luzzi.helpers.help_bot import ResourceHelper, ImageHelper
from src.luzzi.helpers.control_bot import ControlBot
from src.config.config import Config

logger = logging.getLogger(__name__)


class ContabilizadorWindowPage:
    def __init__(self, app):
        """
        Inicializa la clase con la instancia de la aplicación pywinauto.

        Args:
            app: Instancia de la aplicación pywinauto.
        """
        self.app = app
        self.contabilizador_window = None
        self.xml_window = None
        self.bot = ControlBot()

    def open_contabilizador(self):
        """
        Abre la ventana del contabilizador haciendo clic en el botón correspondiente.

        Returns:
            pywinauto.WindowSpecification: La ventana del contabilizador si se abre correctamente, None en caso contrario.
        """
        try:
            main_window = self.app.window(title_re=".*CONTPAQi® Contabilidad.*")
            self.bot.wait_for_element(main_window, timeout=30)

            def abrir_contabilizador_ventana():
                image_path = ResourceHelper.resource_path("img/contabilizador.png")
                if not ImageHelper.find_and_click_image(image_path):
                    logger.error("El botón 'Contabilizador' no se encontró.")
                    raise Exception(
                        "El botón 'Contabilizador' no se encontró en la interfaz."
                    )
                logger.debug(
                    "Botón 'Contabilizador' clicado, esperando ventana del contabilizador."
                )
                time.sleep(1)  # Reducido a 1 segundo

            self.bot.retry_action(abrir_contabilizador_ventana, max_retries=3)

            # Tiempo máximo de espera reducido a 10 segundos
            start_time = time.time()
            while time.time() - start_time < 10:
                try:
                    # Usar directamente win32gui para buscar la ventana
                    def callback(hwnd, windows):
                        if win32gui.IsWindowVisible(hwnd):
                            title = win32gui.GetWindowText(hwnd)
                            if "Contabilizar CFDI" in title:
                                windows.append(hwnd)

                    windows = []
                    win32gui.EnumWindows(callback, windows)

                    if windows:
                        logger.debug(
                            f"Ventana encontrada usando win32gui: handle {windows[0]}"
                        )
                        self.contabilizador_window = self.app.window(handle=windows[0])
                        self.bot.wait_for_element(
                            self.contabilizador_window, timeout=30
                        )
                        self.contabilizador_window.maximize()
                        return self.contabilizador_window

                except Exception as e:
                    logger.debug(f"Error en búsqueda: {str(e)}")

                time.sleep(0.2)  # Reducido el tiempo entre intentos

            logger.critical(
                "No se encontró una ventana válida del contabilizador dentro del tiempo límite."
            )
            return None

        except Exception as e:
            logger.critical(f"Ocurrió un error inesperado: {str(e)}")
            return None

    def get_xml_window(self):
        """
        Obtiene la ventana XML donde se procesan las pólizas.

        Returns:
            pywinauto.WindowSpecification: La ventana XML si se encuentra, None en caso contrario.
        """
        try:
            self.xml_window = self.app.window(title_re=".*XML*")
            self.xml_window.wait("visible", timeout=10)
            return self.xml_window
        except Exception as e:
            logger.critical(f"No se pudo encontrar la ventana XML: {str(e)}")
            return None

    def apply_dynamic_filters(self, fecha_inicio, fecha_final, filters, tipo_xml):
        """
        Aplica filtros dinámicos en la ventana XML.

        Args:
            fecha_inicio (str): Fecha inicial para la contabilidad.
            fecha_final (str): Fecha final para la contabilidad.
            filters (dict): Filtros a aplicar.
            tipo_xml (str): Tipo de XML para determinar posiciones de filtros.
        """
        try:
            config = Config.get_instance()

            # Asegurarse de que la ventana XML esté activa
            if not self.xml_window:
                self.xml_window = self.get_xml_window()
                if not self.xml_window:
                    raise Exception(
                        "No se pudo obtener la ventana XML para aplicar filtros."
                    )

            time.sleep(0.5)
            self.xml_window.type_keys("^a")
            self.xml_window.type_keys("{BACKSPACE}")
            time.sleep(0.5)
            self.xml_window.type_keys(f"{fecha_inicio}{{TAB}}")
            time.sleep(0.5)
            self.xml_window.type_keys("^a")
            self.xml_window.type_keys("{BACKSPACE}")
            time.sleep(0.5)
            self.xml_window.type_keys(f"{fecha_final}{{ENTER}}")
            time.sleep(0.5)

            filter_positions = config.get_filter_positions().get(tipo_xml, {})

            self.xml_window.type_keys("{TAB}" * 3)
            current_position = 3

            logger.info(f"Aplicando filtros para {tipo_xml}")
            for filter_name, filter_value in filters.items():
                if filter_name in filter_positions:
                    position = filter_positions[filter_name]
                    tabs_needed = position - current_position
                    logger.debug(
                        f"Moviendo a {filter_name} en la posición {position}. Tabulaciones necesarias: {tabs_needed}"
                    )
                    self.xml_window.type_keys("{TAB}" * tabs_needed)
                    current_position = position

                    if isinstance(filter_value, list):
                        for value in filter_value:
                            if value:
                                logger.debug(f"Aplicando valor de lista: {value}")
                                self.xml_window.type_keys(value)
                                self.xml_window.type_keys("{TAB}{TAB}")
                    elif filter_value:
                        logger.debug(f"Aplicando valor único: {filter_value}")
                        if filter_name == "rfc":
                            self.xml_window.send_chars(filter_value)
                        else:
                            self.xml_window.type_keys(filter_value)
                        self.xml_window.type_keys("{TAB}")
                    else:
                        logger.debug(f"Saltando filtro vacío: {filter_name}")
                        self.xml_window.type_keys("{TAB}")

                    current_position += 1

            self.xml_window.type_keys("{ENTER}")
            time.sleep(5)

            self.xml_window.click_input(coords=(500, 500))
            self.xml_window.type_keys("^a")

            logger.debug(f"Filtros aplicados para {tipo_xml}: {filters}")
        except Exception as e:
            logger.error(f"Error al aplicar filtros para {tipo_xml}: {str(e)}")
            print(traceback.format_exc())
