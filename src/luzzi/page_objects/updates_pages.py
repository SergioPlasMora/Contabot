import logging
import time
import pyautogui
from src.luzzi.helpers import ImageHelper, ResourceHelper
from src.luzzi.page_objects import DialogHandler

logger = logging.getLogger(__name__)


class UpdatePage:
    def __init__(self):
        pass

    def focus_and_click(
        self,
        contabilizador_window,
        image_path,
        edit_title="000-00-000",
        edit_class="Edit",
        edit_index=1,
    ):
        try:
            contabilizador_window.set_focus()
            if not ImageHelper.find_and_click_image(image_path):
                logger.error(f"El botón no se encontró en la imagen {image_path}.")
                raise Exception("Imagen no encontrada")
        except Exception as e:
            logger.critical(
                f"Error al hacer clic en la imagen {image_path}. Intentando la segunda opción...",
                e,
            )
            edit_fields = contabilizador_window.children(
                title=edit_title, class_name=edit_class
            )
            if len(edit_fields) <= edit_index:
                raise Exception(
                    f"No se encontraron suficientes campos {edit_class} que coincidan con los criterios."
                )
            edit_field = edit_fields[edit_index]
            edit_field.set_focus()
            time.sleep(1)
            edit_field.click_input()

    def input_code_or_keys(self, contabilizador_window, input_value):
        contabilizador_window.set_focus()
        time.sleep(1)
        contabilizador_window.type_keys(input_value)
        time.sleep(1)
        pyautogui.press("enter")

    def assign_and_handle_warning(self, contabilizador_window, app):
        asignar_button = contabilizador_window.child_window(
            title="Asignar", class_name="Button"
        )
        asignar_button.wait("visible", timeout=10)
        asignar_button.click_input()
        time.sleep(1)
        window_problem = DialogHandler(app)
        window_problem.manejar_ventana_advertencia_contabilizador()
        time.sleep(1)

    def click_next(self, contabilizador_window):
        siguiente_button = contabilizador_window.child_window(
            title=" Siguiente ", class_name="Button"
        )
        siguiente_button.wait("visible", timeout=10)
        siguiente_button.click_input()

    def process_actualizar_clientes(
        self, button, contabilizador_window, app, data_access_layer, alias_database
    ):
        try:
            codigo_cliente = data_access_layer.get_cuenta_for_empresa(
                alias_database, "cliente"
            )
            if not codigo_cliente or "codigo" not in codigo_cliente[0]:
                logger.error("No se pudo obtener el código de cliente válido.")
                raise Exception("No se encontró un código de cliente válido.")
            codigo_c = codigo_cliente[0]["codigo"]
            logger.info(f"Código de cliente obtenido: {codigo_c}")

            image_path = ResourceHelper.resource_path("img/cuenta.png")
            self.focus_and_click(contabilizador_window, image_path)

            self.input_code_or_keys(contabilizador_window, f"{{F3}}{codigo_c}")

            self.assign_and_handle_warning(contabilizador_window, app)

            button.click_input()

            image_path = ResourceHelper.resource_path("img/actualizarproductos.png")
            if not ImageHelper.find_and_click_image_advanced(
                image_path, double_click=True
            ):
                logger.error("El botón 'Actualizar Productos' no se encontró.")

            button_detected = False
            for button_title in ["Actualizar productos y servicios sat"]:
                button = contabilizador_window.child_window(
                    title=button_title, class_name="Button"
                )
                time.sleep(1)
                if button.exists() and button.is_visible():
                    logger.info(
                        f"Botón '{button_title}' detectado. Realizando actualización..."
                    )
                    if button_title == "Actualizar productos y servicios sat":
                        self.process_actualizar_productos(
                            button, contabilizador_window, app
                        )
                        button_detected = True
                        break

            self.click_next(contabilizador_window)

            logger.info("Proceso de actualización de clientes completado.")
        except Exception as e:
            logger.critical(
                f"Error en el proceso de actualización de clientes: {str(e)}"
            )

    def process_actualizar_proveedores(
        self, button, contabilizador_window, app, data_access_layer, alias_database
    ):
        try:
            codigo_proveedor_list = data_access_layer.get_cuenta_for_empresa(
                alias_database, "proveedor"
            )
            if not codigo_proveedor_list or len(codigo_proveedor_list) == 0:
                raise ValueError(
                    "No se encontró el código del proveedor en la base de datos"
                )
            codigo_proveedor = codigo_proveedor_list[0]["codigo"]
            logger.info(f"Código de proveedor a ingresar: {codigo_proveedor}")

            image_path = ResourceHelper.resource_path("img/cuenta.png")
            self.focus_and_click(contabilizador_window, image_path)

            self.input_code_or_keys(contabilizador_window, f"{{F3}}{codigo_proveedor}")

            self.assign_and_handle_warning(contabilizador_window, app)

            button.click_input()

            self.click_next(contabilizador_window)

            logger.info("Proceso de actualización de Proveedor completado.")
        except Exception as e:
            logger.critical(
                f"Error en el proceso de actualización de Proveedor: {str(e)}"
            )

    def process_actualizar_productos(self, button, contabilizador_window, app):
        try:
            image_path = ResourceHelper.resource_path("img/cuenta.png")
            self.focus_and_click(contabilizador_window, image_path)

            self.input_code_or_keys(contabilizador_window, "{F3}")

            self.assign_and_handle_warning(contabilizador_window, app)

            button.click_input()

            estado_actualizaciones = {
                "Actualizar clientes": False,
                "Actualizar proveedores": False,
            }

            botones = {
                "Actualizar clientes": {
                    "imagen": "img/actualizarCliente.png",
                    "proceso": self.process_actualizar_clientes,
                },
                "Actualizar proveedores": {
                    "imagen": "img/actualizarProveedor.png",
                    "proceso": self.process_actualizar_proveedores,
                },
            }

            for button_title, config in botones.items():
                if estado_actualizaciones[button_title]:
                    continue

                encontrado, posicion = ImageHelper.find_and_click_image_advanced(
                    config["imagen"], confidence=0.90, double_click=True
                )

                if encontrado:
                    logger.info(
                        f"Botón '{button_title}' detectado. Realizando actualización..."
                    )

                    button = contabilizador_window.child_window(
                        title=button_title, class_name="Button"
                    )

                    config["proceso"](button, contabilizador_window, app)

                    estado_actualizaciones[button_title] = True

            if all(estado_actualizaciones.values()):
                logger.info("Todas las actualizaciones completadas.")
            else:
                logger.warning("Algunas actualizaciones no se realizaron.")

            self.click_next(contabilizador_window)

            logger.info("Proceso de actualización de productos completado.")
        except Exception as e:
            logger.critical(
                f"Error en el proceso de actualización de productos: {str(e)}"
            )
