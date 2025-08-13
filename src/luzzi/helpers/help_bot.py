import time
import logging
import os
import sys
import cv2
import numpy as np
import pyautogui
from PIL import ImageGrab
from pywinauto import findwindows, timings

logger = logging.getLogger(__name__)


class WindowHelper:
    """Clase para manejar operaciones relacionadas con ventanas de la aplicación."""

    @staticmethod
    def is_top_window_with_title(app, title_pattern):
        """
        Verifica si la ventana superior coincide con un patrón de título.

        Args:
            app: Instancia de la aplicación pywinauto.
            title_pattern: Patrón del título a buscar.

        Returns:
            bool: True si coincide, False en caso contrario.
        """
        try:
            return app.top_window().window_text().startswith(title_pattern)
        except Exception as e:
            logger.error(f"Error al verificar título de ventana: {e}")
            return False

    @staticmethod
    def get_control_text(window, control_class="Static", index=0):
        """
        Obtiene el texto de un control específico en la ventana.

        Args:
            window: Ventana donde buscar el control.
            control_class: Clase del control (default: "Static").
            index: Índice del control si hay múltiples (default: 0).

        Returns:
            str: Texto del control o None si no se encuentra.
        """
        try:
            controls = window.children(class_name=control_class)
            if index < len(controls):
                return controls[index].window_text()
            return None
        except Exception as e:
            logger.error(f"Error al obtener texto del control: {e}")
            return None

    @staticmethod
    def find_static_control(window, text, offset=0):
        """
        Busca un control estático por texto y retorna el control en el offset especificado.

        Args:
            window: Ventana donde buscar.
            text: Texto a buscar en el control.
            offset: Desplazamiento desde el control encontrado.

        Returns:
            Control encontrado o None si no se encuentra.
        """
        try:
            static_controls = window.children(class_name="Static")
            for i, control in enumerate(static_controls):
                if control.window_text() == text:
                    if i + offset < len(static_controls):
                        return static_controls[i + offset]
            return None
        except Exception as e:
            logger.error(f"Error al buscar control estático: {e}")
            return None

    @staticmethod
    def get_company_name(app):
        """
        Extrae el nombre de la empresa desde el título de la ventana principal.

        Args:
            app: Instancia de la aplicación pywinauto.

        Returns:
            str: Nombre de la empresa o None si no se encuentra.
        """
        if WindowHelper.is_top_window_with_title(app, "CONTPAQi® Contabilidad"):
            title = app.top_window().window_text().strip()
            parts = title.split(" - ")
            if len(parts) >= 3:
                return parts[1].strip()
        return None

    @staticmethod
    def handle_message_window(app):
        """
        Maneja y cierra ventanas de mensaje si están presentes.

        Args:
            app: Instancia de la aplicación pywinauto.

        Returns:
            bool: True si se manejó la ventana, False en caso contrario.
        """
        try:
            message_window = app.window(title_re=".*Mensaje.*")
            if message_window.exists(timeout=1):
                logger.debug("Ventana de mensaje encontrada.")
                message_window.set_focus()
                message_window.close()
                logger.debug("Ventana de mensaje cerrada.")
                return True
            logger.debug("No se encontró la ventana de mensaje.")
            return False
        except Exception as e:
            logger.error(f"Error al manejar la ventana de mensaje: {e}")
            return False
        
    @staticmethod
    def check_policy_created(contabilizador_window):
            try:
                listview = contabilizador_window.child_window(
                    class_name="SysListView32"
                )
                for i in range(listview.item_count()):
                    for j in range(listview.column_count()):
                        if "Póliza creada" in listview.item(i, j).text():
                            return True
                        elif "No se puede guardar el movimiento de la  póliza por que la" in listview.item(i, j).text():
                            return False
            except Exception as e:
                logger.error(f"Error al verificar 'Póliza creada': {e}")
                return False

    @staticmethod
    def wait_for_policy_created(contabilizador_window, timeout=30):
        """
        Espera a que aparezca un resultado (éxito o fallo) en la lista.
        """
        try:
            def check_condition():
                return WindowHelper.check_policy_created(contabilizador_window) is not None
            
            timings.wait_until(timeout, 1, check_condition)
            
            # Verificamos el resultado final
            final_status = WindowHelper.check_policy_created(contabilizador_window)
            if final_status is True:
                logger.info("Póliza creada encontrada exitosamente.")
                return True
            else:
                logger.error("La espera terminó, pero se encontró un error en la lista o un resultado inesperado.")
                return False
        except timings.TimeoutError:
            logger.critical(f"Timeout ({timeout}s) esperando resultado de la póliza.")
            return False

    @staticmethod
    def detect_window_by_content(
        app, content_patterns, timeout=5, ignore_patterns=None
    ):
        """
        Detecta una ventana sin título que contenga ciertos patrones de texto, ignorando ventanas con patrones no deseados.

        Args:
            app: Instancia de la aplicación pywinauto.
            content_patterns: Lista de patrones a buscar en el contenido.
            timeout: Tiempo máximo de espera en segundos.
            ignore_patterns: Lista de patrones a ignorar (opcional).

        Returns:
            HwndWrapper: Ventana encontrada o None.
        """
        ignore_patterns = ignore_patterns or []
        start_time = time.time()
        while time.time() - start_time < timeout:
            ventanas_sin_titulo = findwindows.find_windows(title="")
            for hwnd in ventanas_sin_titulo:
                try:
                    ventana = app.window(handle=hwnd)
                    contenido = WindowHelper.get_control_text(ventana)
                    if contenido:
                        # Ignorar ventanas con patrones no deseados
                        if any(
                            ignore.lower() in contenido.lower()
                            for ignore in ignore_patterns
                        ):
                            continue
                        # Verificar si contiene alguno de los patrones deseados
                        if any(
                            p.lower() in contenido.lower() for p in content_patterns
                        ):
                            logger.info(f"Ventana detectada con contenido: {contenido}")
                            return ventana
                except Exception as e:
                    logger.warning(f"Error al procesar ventana: {e}")
                time.sleep(0.1)
        logger.warning(
            f"No se detectó la ventana con contenido esperado después de {timeout} segundos"
        )
        return None

    @staticmethod
    def wait_for_window_disappearance(window, timeout=5):
        """
        Espera a que una ventana desaparezca.

        Args:
            window: Ventana a verificar.
            timeout: Tiempo máximo de espera en segundos.

        Returns:
            bool: True si la ventana desapareció, False en caso contrario.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if not window.exists():
                return True
            time.sleep(0.05)
        return False

    @staticmethod
    def get_control_by_class_name(window, class_name, index=0):
        """
        Obtiene un control por su clase y índice.

        Args:
            window: Ventana donde buscar.
            class_name: Nombre de la clase del control.
            index: Índice del control (default: 0).

        Returns:
            Control encontrado o None.
        """
        try:
            return window.child_window(class_name=class_name, found_index=index)
        except findwindows.ElementNotFoundError:
            return None


class ImageHelper:
    """Clase para manejar búsqueda y clics en imágenes de la pantalla."""

    @staticmethod
    def find_and_click_image(
        template_path,
        confidence=0.8,
        double_click=False,
        scale_range=(0.8, 1.2),
        steps=10,
    ):
        """
        Busca una imagen en pantalla y hace clic o doble clic si se encuentra, con soporte para diferentes escalas.

        Args:
            template_path: Ruta de la imagen de plantilla.
            confidence: Umbral de confianza.
            double_click: Indica si se debe hacer doble clic.
            scale_range: Rango de escalado.
            steps: Cantidad de escalas para probar.

        Returns:
            bool: True si se encontró y se hizo clic, False en caso contrario.
        """
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(
                f"No se pudo cargar la plantilla desde: {template_path}"
            )

        scales = np.linspace(scale_range[0], scale_range[1], steps)
        for scale in scales:
            resized_template = cv2.resize(template, None, fx=scale, fy=scale)
            result = cv2.matchTemplate(
                screenshot_gray, resized_template, cv2.TM_CCOEFF_NORMED
            )
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= confidence:
                button_x, button_y = max_loc
                button_center_x = button_x + resized_template.shape[1] // 2
                button_center_y = button_y + resized_template.shape[0] // 2

                if double_click:
                    pyautogui.doubleClick(button_center_x, button_center_y)
                else:
                    pyautogui.click(button_center_x, button_center_y)
                logger.info(
                    f"Imagen encontrada y clic realizada con confianza {max_val:.2f}"
                )
                return True

        logger.warning("No se encontró la imagen en ninguna escala.")
        return False

    @staticmethod
    def find_and_click_image_advanced(
        template_path, confidence=0.90, double_click=False
    ):
        """
        Búsqueda avanzada de imágenes con pre-procesamiento y múltiples métodos.

        Args:
            template_path: Ruta de la imagen de plantilla.
            confidence: Umbral de confianza.
            double_click: Indica si se debe hacer doble clic.

        Returns:
            tuple: (bool, tuple) - Éxito/fracaso y coordenadas.
        """
        try:
            template_path = ResourceHelper.resource_path(template_path)
            logger.debug(f"Buscando imagen en: {template_path}")

            screenshot = pyautogui.screenshot()
            screenshot = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_RGB2GRAY)

            template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
            if template is None:
                raise FileNotFoundError(
                    f"No se pudo cargar la plantilla desde: {template_path}"
                )

            scales = [0.8, 0.9, 1.0, 1.1, 1.2]
            preprocessing_methods = [
                lambda img: img,
                lambda img: cv2.equalizeHist(img),
                lambda img: cv2.GaussianBlur(img, (3, 3), 0),
                lambda img: cv2.Canny(img, 100, 200),
            ]

            best_confidence = 0
            best_location = None

            for preprocess in preprocessing_methods:
                processed_screenshot = preprocess(screenshot_gray.copy())
                processed_template = preprocess(template.copy())

                for scale in scales:
                    width = int(processed_template.shape[1] * scale)
                    height = int(processed_template.shape[0] * scale)
                    resized_template = cv2.resize(processed_template, (width, height))

                    result = cv2.matchTemplate(
                        processed_screenshot, resized_template, cv2.TM_CCOEFF_NORMED
                    )
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                    if max_val > best_confidence:
                        best_confidence = max_val
                        best_location = (max_loc, resized_template.shape)

            if best_confidence >= confidence and best_location:
                loc, template_shape = best_location
                button_center_x = loc[0] + template_shape[1] // 2
                button_center_y = loc[1] + template_shape[0] // 2

                if double_click:
                    pyautogui.doubleClick(button_center_x, button_center_y)
                else:
                    pyautogui.click(button_center_x, button_center_y)
                logger.info(f"Imagen encontrada con confianza {best_confidence:.2f}")
                return True, (button_center_x, button_center_y)
            logger.warning(
                f"No se encontró la imagen. Mejor confianza: {best_confidence:.2f}"
            )
            return False, None
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada de imagen: {e}")
            return False, None


class ColorHelper:
    """Clase para manejar la detección de colores en áreas específicas de la pantalla."""

    @staticmethod
    def detect_colors_in_area(colors, area, tolerance=5):
        """
        Detecta si alguno de los colores objetivo está presente en el área especificada.

        Args:
            colors: Lista de colores objetivo (tuplas RGB).
            area: Coordenadas del área a capturar (x1, y1, x2, y2).
            tolerance: Tolerancia para coincidencia de color.

        Returns:
            bool: True si se detecta algún color, False en caso contrario.
        """
        captura = ImageGrab.grab(bbox=area)
        imagen = np.array(captura)

        for color_objetivo in colors:
            diff = np.abs(imagen - color_objetivo)
            mask = np.all(diff <= tolerance, axis=2)
            if np.any(mask):
                logger.debug(f"Color detectado cerca de {color_objetivo}")
                return True
        return False

    @staticmethod
    def wait_for_colors(colors, area, max_attempts=20, interval=0.5):
        """
        Espera a que aparezca alguno de los colores en el área especificada.

        Args:
            colors: Lista de colores objetivo.
            area: Coordenadas del área a verificar.
            max_attempts: Número máximo de intentos.
            interval: Intervalo entre intentos en segundos.

        Returns:
            bool: True si se detecta el color, False si se agota el tiempo.
        """
        for _ in range(max_attempts):
            if ColorHelper.detect_colors_in_area(colors, area, tolerance=5):
                logger.debug("Color objetivo detectado en la tabla de facturas.")
                return True
            logger.debug("Esperando que se asocien los XML...")
            time.sleep(interval)
        logger.error("Tiempo de espera agotado. No se detectó ningún color objetivo.")
        return False


class ResourceHelper:
    """Clase para manejar rutas de recursos, especialmente en entornos congelados con PyInstaller."""

    @staticmethod
    def resource_path(relative_path):
        """
        Obtiene la ruta absoluta de un recurso, considerando PyInstaller.

        Args:
            relative_path: Ruta relativa al recurso.

        Returns:
            str: Ruta absoluta al recurso.
        """
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        full_path = os.path.join(base_path, relative_path)
        if not os.path.exists(full_path):
            logger.warning(f"Archivo no encontrado: {full_path}")
            alt_dirs = [
                os.path.abspath("img"),
                os.path.join(os.path.dirname(os.path.abspath(".")), "img"),
                os.path.join(base_path, "luzzi", "img"),
            ]
            for alt_dir in alt_dirs:
                alt_path = os.path.join(alt_dir, os.path.basename(relative_path))
                if os.path.exists(alt_path):
                    logger.info(f"Archivo encontrado en ruta alternativa: {alt_path}")
                    return alt_path
        return full_path
