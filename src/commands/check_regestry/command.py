import datetime
import winreg
from src.commands.base import Command
from src.utils.encdec import encriptar, obtener_hash  

RUTA_REGISTRO = r"SOFTWARE\WOW6432Node\Computación en Acción, SA CV\AppKey\Contpaq_i\Temp"
RUTA_ARCHIVO_LICENCIA = 'licencia.dat'

class CheckRegistryCommand(Command):
    def add_arguments(self, parser):
        """Añade argumentos específicos para el comando check_registry"""
        parser.add_argument(
            '--numero_serie',
            type=str,
            help="Número de serie para la licencia",
            required=True
        )
        parser.add_argument(
            '--fecha_vigencia', 
            type=str,
            help="Fecha de vigencia en formato YYYY-MM-DD HH:MM:SS",
            required=True
        )
        parser.add_argument(
            '--guardar',
            action="store_true",
            help="Guarda la licencia en un archivo"
        )

    def execute(self, args):
        """Ejecuta la lógica del comando de registro"""
  
        try:
            ts = datetime.datetime.strptime(args.fecha_vigencia, '%Y-%m-%d %H:%M:%S').timestamp()
            token = f"{str(ts)}{args.numero_serie}"
            hs = obtener_hash(token)
            token = f"{str(ts)}|{args.numero_serie}|{hs}"
            licencia = encriptar(token)
            print(f"Licencia generada: {licencia}\n")

            self._escribir_en_registro(args.numero_serie)
            
            if args.guardar:
                self._guardar_licencia_en_archivo(licencia)
            
            print("Proceso de registro completado exitosamente.\n")
        
        except Exception as e:
            print(f"Error al procesar el registro: {e}")

    def _escribir_en_registro(self, numero_serie):
        """Método interno para escribir en el registro de Windows"""
        try:
            registry_key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, RUTA_REGISTRO)
            
            index = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(registry_key, index)
                    if value_data == numero_serie:
                        print(f"El número de serie '{numero_serie}' ya existe en el registro.\n")
                        return
                    index += 1
                except OSError:
                    break
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            serial_key = f"Serial-{timestamp}"
            winreg.SetValueEx(registry_key, serial_key, 0, winreg.REG_SZ, numero_serie)
            print(f"Valor de registro '{serial_key}' creado con el número de serie. \n")
            
            winreg.CloseKey(registry_key)
        except Exception as e:
            print(f"Error al escribir en el Registro: {e}")

    def _guardar_licencia_en_archivo(self, licencia):
        try:
            with open(RUTA_ARCHIVO_LICENCIA, "w") as archivo:
                archivo.write(licencia)
            print("Archivo de licencia generado correctamente. \n")
        except Exception as e:
            print(f"Error al generar el archivo de licencia: {e}")
