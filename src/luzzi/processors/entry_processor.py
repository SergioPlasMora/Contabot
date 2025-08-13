import logging
import time
from src.luzzi.page_objects.updates_pages import UpdatePage
from src.luzzi.helpers.help_bot import WindowHelper, ImageHelper, ResourceHelper, ColorHelper
from src.config.config import Config
from src.data.database import SQLServerConnectionPool, DataAccessLayer
from src.luzzi.page_objects.dialog_handler_page import DialogHandler
logger = logging.getLogger(__name__)


class EntryProcessor:
    def __init__(self, app, contabilizador_window_page=None):
        self.app = app
        self.contabilizador_window = None
        self.update_page = UpdatePage()

        if contabilizador_window_page:
            self.contabilizador_window = contabilizador_window_page.open_contabilizador()
        else:
            try:
                window = self.app.window(title_re=".*Contabilizador.*")
                if window.exists() and window.is_visible():
                    self.contabilizador_window = window
            except Exception as e:
                logging.warning(f"No se pudo detectar automáticamente la ventana del Contabilizador: {e}")

    def set_contabilizador_window(self, contabilizador_window):
        self.contabilizador_window = contabilizador_window

    def process_generate_policies(self, intentar_generar_poliza):
        """
        Procesa el botón 'Generar pólizas' y gestiona las ventanas emergentes relacionadas.

        Args:
            intentar_generar_poliza: Función para intentar crear una póliza.

        Returns:
            bool: True si se creó la póliza exitosamente, False de lo contrario.
        """
        if not self.contabilizador_window:
            logger.error("La ventana del contabilizador no está abierta.")
            return False

        max_intentos = 200
        tiempo_espera = 0.05
        max_intentos_rapidos = 20
        tiempo_espera_rapido = 0.02

        for intento in range(max_intentos):
            try:
                generar_polizas = self.contabilizador_window.child_window(
                    title="&Generar pólizas", class_name="Button"
                )

                if generar_polizas.is_visible() and generar_polizas.is_enabled():
                    ventana_generando = WindowHelper.detect_window_by_content(
                        self.app,
                        content_patterns=["Generando asientos contables, espere..."], ignore_patterns=["Buscar"]
                    )

                    if ventana_generando:
                        logger.debug(
                            "Ventana 'Generando asientos contables, espere...' detectada. Esperando..."
                        )
                        if WindowHelper.wait_for_window_disappearance(ventana_generando):
                            logger.debug(
                                "La ventana 'Generando asientos contables, espere...' ha desaparecido."
                            )
                            for intento_rapido in range(max_intentos_rapidos):
                                logger.debug(
                                    f"Intento rápido {intento_rapido + 1} de hacer clic en 'Generar pólizas'..."
                                )
                                if intentar_generar_poliza(generar_polizas):
                                    logger.debug("Póliza creada exitosamente.")
                                    return True
                                time.sleep(tiempo_espera_rapido)
                            logger.error(
                                "No se pudo crear la póliza después de los intentos rápidos."
                            )
                    else:
                        logger.debug("Haciendo clic en 'Generar pólizas'...")
                        if intentar_generar_poliza(generar_polizas):
                            logger.debug("Póliza creada exitosamente.")
                            return True
                        logger.debug("No se encontró 'Póliza creada'. Reintentando...")
                else:
                    logger.debug(
                        f"El botón 'Generar pólizas' no está visible o habilitado. "
                        f"Visible: {generar_polizas.is_visible()}, Habilitado: {generar_polizas.is_enabled()}"
                    )
            except Exception as e:
                logger.debug(f"Error durante el intento {intento + 1}: {e}")
            time.sleep(tiempo_espera)

        logger.error(
            f"Error: No se pudieron crear las pólizas después de {max_intentos} intentos."
        )
        return False

    def process_entry(
        self, asiento, company_config, data_access_layer, alias_database, company
    ):
        """
        Procesa un asiento contable completo.

        Args:
            asiento: Datos del asiento contable.
            company_config: Configuración de la empresa.
            data_access_layer: Capa de acceso a datos.
            alias_database: Alias de la base de datos.
            company: Datos de la empresa.

        Returns:
            bool: True si se procesó exitosamente, False en caso contrario.
        """
        from src.luzzi.page_objects.contabilizador_window_page import (
            ContabilizadorWindowPage,
        )
        import time
        from PIL import ImageGrab

        try:
            if not self.contabilizador_window:
                raise RuntimeError("Ventana del Contabilizador no configurada.")

            config = Config.get_instance()
            codigo = str(asiento["Codigo"])
            logger.info(f"Procesando código: {codigo}")

            templates = company_config["templates"]
            if codigo not in templates:
                logger.warning(
                    f"No se encontró configuración de template para el asiento {codigo}"
                )
                return False

            template_config = templates[codigo]

            asiento_control = WindowHelper.get_control_by_class_name(
                self.contabilizador_window, "Edit", 0
            )
            if asiento_control:
                asiento_control.set_focus()
                asiento_control.type_keys(codigo, with_spaces=True)
                logger.debug(f"Se escribió el asiento contable {codigo}")
                time.sleep(0.2)
            else:
                logger.warning("No se encontró el control [Asiento].")
                return False

            self.contabilizador_window.set_focus()
            image_path = ResourceHelper.resource_path("img/seleccionar_CFDI.png")
            if not ImageHelper.find_and_click_image(image_path):
                logger.error("El botón 'seleccionar_CFDI' no se encontró.")
                return False

            contabilizadorwindowpage = ContabilizadorWindowPage(self.app)
            ventana_xml = contabilizadorwindowpage.get_xml_window()
            if ventana_xml is None:
                logger.critical("No se pudo encontrar la ventana XML")
                return False

            filters = template_config.get("filters", {})
            if not filters:
                logger.error(
                    f"Error: No se encontraron filtros en la configuración del template {codigo}"
                )
                return False

            fecha_inicio = filters.get("firstDate", "").strip()
            fecha_final = filters.get("lastDate", "").strip()

            if not (fecha_inicio and fecha_final):
                connection_pool = SQLServerConnectionPool()
                data_access_layer_instance = DataAccessLayer(connection_pool)
                fecha_inicio, fecha_final = (
                    data_access_layer_instance.get_fechas_for_empresa(alias_database)
                )

            logger.debug(
                f"Fechas finales: Inicio: {fecha_inicio}, Final: {fecha_final}"
            )
            filtros = contabilizadorwindowpage.apply_dynamic_filters(
                fecha_inicio, fecha_final, filters, template_config["tipoXML"]
            )
            time.sleep(0.5)

            image_path = ResourceHelper.resource_path("img/asociar.png")
            if not ImageHelper.find_and_click_image(image_path):
                logger.error("El botón 'Asociar' no se encontró.")
            else:
                logger.info("Botón 'Asociar' clickeado.")

            image_path = ResourceHelper.resource_path("img/si.png")
            if not ImageHelper.find_and_click_image(image_path):
                logger.error("El botón 'Sí' no se encontró.")
            else:
                logger.info("Botón 'Sí' clickeado.")

            if WindowHelper.handle_message_window(self.app):
                logger.info(f"No hay pólizas para generar en el asiento {codigo}.")
                image_path = ResourceHelper.resource_path("img/cerrar.png")
                if not ImageHelper.find_and_click_image(image_path):
                    logger.error("El botón 'Cerrar' no se encontró.")
                return True

            colores_objetivo = [(69, 179, 157)]
            area_a_verificar = (500, 300, 502, 302)

            if ColorHelper.wait_for_colors(colores_objetivo, area_a_verificar, max_attempts=60, interval=0.5):
                logger.debug("Color verde detectado, procediendo a cerrar...")
                image_path = ResourceHelper.resource_path("img/cerrar.png")
                if not ImageHelper.find_and_click_image(image_path):
                    logger.error("El botón 'Cerrar' no se encontró.")
                else:
                    image_path = ResourceHelper.resource_path("img/cerrar.png")
                    logger.info("Botón 'Cerrar' clickeado exitosamente.")
            else:
                logger.error("No se detectó el color a tiempo, abortando.")

            ventana_leyendo = WindowHelper.detect_window_by_content(
                self.app, content_patterns=["Leyendo documentos "], ignore_patterns=["Buscar"]
            )
            if ventana_leyendo:
                logger.debug(
                    "Ventana 'Leyendo documentos...' detectada. Esperando su desaparición..."
                )
                if not WindowHelper.wait_for_window_disappearance(
                    ventana_leyendo
                ):
                    logger.debug(
                        "La ventana 'Leyendo documentos...' no desapareció en el tiempo esperado."
                    )

            max_intentos_totales = 200
            max_intentos_actualizacion = 3
            tiempo_espera = 0.2

            actualizaciones_completadas = {
                "Actualizar clientes": False,
                "Actualizar proveedores": False,
                "Actualizar productos y servicios sat": False,
            }

            intentos_totales = 0
            while intentos_totales < max_intentos_totales:
                intentos_totales += 1
                logger.info(f"Ciclo de procesamiento {intentos_totales}")

                if self._llegamos_a_generar_polizas():
                    logger.info("Llegamos a la pantalla de 'Generar pólizas'")
                    break

                boton_encontrado = False
                for button_title in actualizaciones_completadas.keys():
                    if actualizaciones_completadas[button_title]:
                        continue

                    button = self.contabilizador_window.child_window(
                        title=button_title, class_name="Button"
                    )
                    if button.exists() and button.is_visible():
                        logger.info(
                            f"Botón '{button_title}' detectado. Realizando actualización..."
                        )
                        boton_encontrado = True

                        if button_title == "Actualizar clientes":
                            self.update_page.process_actualizar_clientes(
                                button,
                                self.contabilizador_window,
                                self.app,
                                data_access_layer,
                                alias_database,
                            )
                        elif button_title == "Actualizar proveedores":
                            self.update_page.process_actualizar_proveedores(
                                button,
                                self.contabilizador_window,
                                self.app,
                                data_access_layer,
                                alias_database,
                            )
                        elif button_title == "Actualizar productos y servicios sat":
                            self.update_page.process_actualizar_productos(
                                button, self.contabilizador_window, self.app
                            )
                        actualizaciones_completadas[button_title] = True
                        break

                if not boton_encontrado:
                    siguiente_button = self.contabilizador_window.child_window(
                        title="&Siguiente", class_name="Button", found_index=0
                    )
                    if siguiente_button.exists() and siguiente_button.is_visible():
                        logger.info(
                            "No se encontró botón de actualización, pero hay 'Siguiente'. Avanzando..."
                        )
                        siguiente_button.click_input()
                        time.sleep(tiempo_espera)
                    elif all(actualizaciones_completadas.values()):
                        logger.info(
                            "Todas las actualizaciones completadas. Forzando avance..."
                        )
                        if siguiente_button.exists() and siguiente_button.is_visible():
                            siguiente_button.click_input()
                            time.sleep(tiempo_espera)

            if not self._llegamos_a_generar_polizas():
                logger.critical("No se pudo llegar a 'Generar pólizas'.")
                return False

            resultado = self.process_generate_policies(self._try_generate_policy)
        
            if resultado == "ERROR_HANDLED":
                logger.info(f"Error de cargos y abonos manejado para el asiento {codigo}. Continuando con el siguiente.")
                return True
            elif resultado is True:
                logger.info(f"Póliza generada exitosamente para el asiento {codigo}.")
                time.sleep(0.5)
                nuevo_button_path = ResourceHelper.resource_path("img/nuevo.png")
                if not ImageHelper.find_and_click_image(nuevo_button_path, confidence=0.8):
                    logger.warning("No se pudo hacer clic en 'Nuevo' después del éxito.")
                return True
            else:
                logger.warning(f"Fallo en la generación de póliza para el asiento {codigo}.")
                ImageHelper.find_and_click_image(ResourceHelper.resource_path("img/nuevo.png"), confidence=0.8)
                return False

        except Exception as e:
            logger.critical(f"Error al procesar el asiento contable {codigo}: {str(e)}")
            return False
        
    def _try_generate_policy(self, generar_polizas):
        """
        Intenta generar una póliza siguiendo un flujo secuencial:
        1. Hace clic en 'Generar pólizas'.
        2. Detecta si aparece el error de cargos y abonos (durante 8 segundos).
        3. Si no hay error, espera a que termine el procesamiento.
        4. Verifica el resultado final ('Póliza creada' en SysListView32).
        
        Args:
            generar_polizas: Botón de 'Generar pólizas' en la interfaz.
        
        Returns:
            str o bool: "ERROR_HANDLED" si se manejó un error, True si la póliza se creó, False si falló.
        """
        try:
            logger.debug("Haciendo clic en 'Generar pólizas'...")
            generar_polizas.click_input()
            time.sleep(0.5)

            logger.debug("Verificando si aparece error de cargos y abonos...")
            if self._handle_error_window():
                logger.info("Error de cargos y abonos detectado y manejado.")
                return "ERROR_HANDLED"

            logger.debug("No se detectó error de cargos y abonos, continuando con el proceso normal...")

            logger.debug("Procesamiento terminado, verificando resultado final...")
            result = WindowHelper.wait_for_policy_created(self.contabilizador_window, timeout=30)

            if result is True:
                logger.info("Póliza creada exitosamente.")
                return True
            else:
                logger.error("La póliza no se creó correctamente o se encontró un error.")
                return False

        except Exception as e:
            logger.critical(f"Excepción crítica al intentar generar póliza: {str(e)}")
            return False


    def _handle_error_window(self):
        """
        Maneja la ventana 'Problema' si aparece, específicamente el error de cargos y abonos.
        
        Returns:
            bool: True si se detectó y manejó el error, False si no apareció.
        """
        max_wait_for_error = 3  # Tiempo máximo para esperar el error
        start_time = time.time()

        logger.debug("Iniciando monitoreo de error de cargos y abonos...")

        while time.time() - start_time < max_wait_for_error:
            try:
                problema_window = self.app.window(title="Problema", class_name="SWT_Window1")
                if problema_window.exists() and problema_window.is_visible():
                    logger.warning("Ventana 'Problema' detectada.")
                    
                    static_control = problema_window.child_window(
                        title="Los importes de cargos y abonos no son iguales", 
                        class_name="Static"
                    )
                    
                    if static_control.exists():
                        logger.warning("Confirmado: Error de cargos y abonos detectado.")
                        accept_button = problema_window.child_window(
                            title="&Aceptar", class_name="Button"
                        )
                        
                        if accept_button.exists() and accept_button.is_visible():
                            logger.info("Haciendo clic en 'Aceptar' para cerrar la ventana de error.")
                            accept_button.click_input()
                            time.sleep(1)
                            
                            logger.info("Haciendo clic en 'Nuevo' para continuar con el siguiente asiento.")
                            nuevo_button_path = ResourceHelper.resource_path("img/nuevo.png")
                            if ImageHelper.find_and_click_image(nuevo_button_path, confidence=0.8):
                                logger.info("Botón 'Nuevo' clickeado exitosamente.")
                            else:
                                logger.warning("No se pudo hacer clic en 'Nuevo', pero continuando...")
                            
                            return True
                        else:
                            logger.error("No se pudo encontrar el botón 'Aceptar'.")
                            return True
                    else:
                        logger.warning("Ventana 'Problema' sin mensaje de cargos y abonos.")
                        try:
                            accept_button = problema_window.child_window(
                                title="&Aceptar", class_name="Button"
                            )
                            if accept_button.exists():
                                accept_button.click_input()
                                time.sleep(1)
                        except Exception as e:
                            logger.debug(f"Error al cerrar ventana de problema: {e}")
                        return True
            except Exception as e:
                logger.debug(f"Excepción durante búsqueda de error: {e}")
            
            time.sleep(0.5)  # Pausa antes del siguiente intento

        logger.debug("No se detectó error de cargos y abonos en el tiempo establecido.")
        return False
            
    def _llegamos_a_generar_polizas(self):
        """ 
        Verifica si se llegó a la pantalla de 'Generar pólizas'.

        Returns:
            bool: True si el botón está visible, False en caso contrario.
        """
        generar_polizas_button = self.contabilizador_window.child_window(
            title="&Generar pólizas", class_name="Button"
        )
        return generar_polizas_button.exists() and generar_polizas_button.is_visible()
