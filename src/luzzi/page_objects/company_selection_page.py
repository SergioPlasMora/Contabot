import logging
import time
from src.luzzi.helpers.help_bot import WindowHelper
from src.luzzi.helpers.control_bot import ControlBot
from src.luzzi.page_objects.dialog_handler_page import DialogHandler


logger = logging.getLogger(__name__)


class CompanySelectionPage:
    def __init__(self, app):
        self.app = app
        self.catalog_window = None
        self.dialog_handler = DialogHandler(app)
        self.bot = ControlBot()

    def procesar_ventana_emergente(self, titulo_ventana, mensaje_ventana):
        resultado = self.dialog_handler.handle_window(titulo_ventana, mensaje_ventana)
        if resultado:
            print(f"Ventana manejada: {titulo_ventana}")
        else:
            print(f"No se pudo manejar la ventana: {titulo_ventana}")
        return resultado

    def open_catalog(self):
        """
        Abre el catálogo de empresas mediante la barra de navegación de la aplicación.

        Returns:
            bool: True si el catálogo se abrió correctamente, False en caso contrario.
        """
        try:
            window = self.app["CONTPAQi® Contabilidad -  - LUZZI"]
            window.wait("visible", timeout=30)

            retries = 3
            while retries > 0:
                try:
                    window.maximize()
                    window.set_focus()
                    if window.is_maximized():
                        logger.debug("Ventana principal maximizada y enfocada.")
                        break
                except Exception as e:
                    logger.error(f"Error al maximizar la ventana principal: {str(e)}")
                retries -= 1

            toolbars = window.children(class_name="ToolbarWindow32")
            if toolbars:
                toolbar = toolbars[0]
                max_attempts = 20
                attempts = 0
                while attempts < max_attempts:
                    try:
                        toolbar.click()
                        buttons = toolbar.children()
                        if buttons:
                            buttons[0].click()
                            logger.debug(
                                "Primer botón de la barra de herramientas clickeado."
                            )

                        time.sleep(2)
                        if WindowHelper.is_top_window_with_title(
                            self.app, title_pattern="Catálogo de Empresas"
                        ):
                            logger.debug("Catálogo de Empresas abierto correctamente.")
                            return True
                        else:
                            logger.warning(
                                "Catálogo de Empresas no abierto aún, reintentando..."
                            )
                            attempts += 1
                            time.sleep(3)
                    except Exception as e:
                        logger.error(
                            f"Error al intentar abrir el Catálogo de Empresas: {str(e)}"
                        )
                        attempts += 1
                        time.sleep(2)
                logger.critical(
                    f"No se pudo abrir el Catálogo de Empresas después de {max_attempts} intentos."
                )
                return False
        except Exception as e:
            logger.critical(
                f"Error al interactuar con la barra de herramientas: {str(e)}"
            )
            return False

    def get_companies(self):
        """
        Extrae todas las empresas después de abrir el catálogo de empresas.

        Returns:
            list: Lista de diccionarios con la información de las empresas o None si falla.
        """
        empresas = []
        if not WindowHelper.is_top_window_with_title(
            self.app, title_pattern="Catálogo de Empresas"
        ):
            logger.critical("La ventana del catálogo de empresas no está activa.")
            return None

        try:
            self.catalog_window = self.app.top_window()
            self.bot.wait_for_element(self.catalog_window, timeout=30)
            list_control = self.catalog_window.child_window(class_name="SysListView32")
            if not self.bot.verify_element_state(list_control, timeout=10):
                logger.critical("El control de la lista no está disponible.")
                return None

            for i in range(list_control.item_count()):
                try:

                    def obtener_empresa():
                        return {
                            "id": list_control.item(i, 1).text(),
                            "nombre": list_control.item(i, 0).text(),
                            "bdd": list_control.item(i, 2).text(),
                            "ruta": WindowHelper.find_static_control(
                                self.catalog_window, "Ubicación:", 1
                            ).window_text(),
                        }

                    empresa = self.bot.retry_action(obtener_empresa, max_retries=3)
                    empresas.append(empresa)
                    logger.debug(
                        f"{i}: {empresa['id']}, {empresa['nombre']}, {empresa['bdd']}, {empresa['ruta']}"
                    )
                except Exception as e:
                    logger.error(f"Error al procesar empresa {i}: {str(e)}")
                    continue
            return empresas
        except Exception as e:
            logger.critical(f"Error al obtener la lista de empresas: {str(e)}")
            return None

    def open_company(self, company_name):
        """
        Abre una empresa específica después de obtenerla del catálogo de empresas.

        Args:
            company_name (str): Nombre de la empresa a abrir.

        Returns:
            tuple: (bool, str) indicando éxito/fallo y un mensaje descriptivo.
        """
        if not WindowHelper.is_top_window_with_title(self.app, "Catálogo de Empresas"):
            return False, "No se encuentra en la ventana de Catálogo de Empresas"

        try:
            self.catalog_window = self.app.top_window()
            self.bot.wait_for_element(self.catalog_window, timeout=30)
            lista_empresas = self.catalog_window.child_window(
                class_name="SysListView32"
            )
            if not self.bot.verify_element_state(lista_empresas, timeout=10):
                return False, "No se puede acceder a la lista de empresas."

            empresa_index = None
            for i in range(lista_empresas.item_count()):
                if lista_empresas.item(i, 0).text() == company_name:
                    empresa_index = i
                    break

            if empresa_index is None:
                return False, "Empresa no encontrada en el catálogo"

            def abrir_empresa():
                lista_empresas.item(empresa_index).click_input(double=True)

            self.bot.retry_action(abrir_empresa, max_retries=3)

            pausa = 0.5
            tiempo_maximo_espera = 600
            iteraciones = int(tiempo_maximo_espera / pausa)
            ventanas_manejadas = set()

            for _ in range(iteraciones):
                time.sleep(pausa)
                if not self.app.top_window():
                    continue

                titulo_ventana = self.app.top_window().window_text().strip()
                mensaje_ventana = WindowHelper.get_control_text(
                    self.app.top_window()
                ).strip()

                if (titulo_ventana, mensaje_ventana) in ventanas_manejadas:
                    continue

                logger.debug(f"\tVentana activa: {titulo_ventana}")
                logger.debug(f"\tMensaje: {mensaje_ventana}")

                resultado = self.dialog_handler.handle_window(
                    titulo_ventana, mensaje_ventana
                )
                if resultado:
                    return resultado

                ventanas_manejadas.add((titulo_ventana, mensaje_ventana))

            return False, "Timeout"
        except Exception as e:
            return False, f"Error al intentar abrir la empresa: {str(e)}"

    def closeCompany(self):
        """
        Metodo encargado de cerrar una empresa al final el proceso.

        Args:
            app: Se utiliza para hacer referencia a una ventana.
        """
        try:
            main_window = self.app.top_window()
            main_window.menu_select("Empresa->Cerrar empresa")
            time.sleep(1)
            logger.debug("Empresa cerrada mediante menú.")

            company_window = self.app.window(title_re=".*CONTPAQi® Contabilidad.*")
            if company_window.exists(timeout=10):
                company_window.wait_not("exists", timeout=10)
                logger.debug("Ventana de empresa cerrada")
            else:
                logger.debug(
                    "No se encontró la ventana de la empresa o ya estaba cerrada."
                )

        except Exception as e:
            logger.error(f"Error al cerrar la empresa: {str(e)}")
