import base64
import datetime
import os

CLAVE_ENCDEC = "luzzi"

class Licencia:

    @classmethod
    def __desencriptar(cls, texto_encriptado):
        base64_bytes = texto_encriptado.encode('utf-8')
        resultado_bytes = base64.b64decode(base64_bytes)
        resultado = resultado_bytes.decode('utf-8')
        
        texto_original = ""
        for i, char in enumerate(resultado):
            char_code = ord(char)
            clave_code = ord(CLAVE_ENCDEC[i % len(CLAVE_ENCDEC)])
            decrypted_char = chr(char_code ^ clave_code)
            texto_original += decrypted_char
        
        return texto_original
    
    @classmethod
    def __generar_hash(cls, cadena):
        hash_value = 0
        for caracter in cadena:
            hash_value += ord(caracter)
        return hash_value

    @classmethod
    def __obtener_licencia(cls):
        ruta_archivo = 'licencia.dat'

        if not os.path.exists(ruta_archivo):
            raise Exception("El archivo de licencia no se encontró en la ruta esperada.")
        
        try:
            with open(ruta_archivo, 'r') as archivo:
                licencia = archivo.read()
            return licencia
        
        except Exception as e:
            raise Exception(f"Ocurrió un problema al abrir el archivo de licencia: {e}")

    @classmethod
    def __desencriptar_licencia(cls, licencia):
        licencia = cls.__desencriptar(licencia)
        datos = licencia.split('|')
        if len(datos) == 3:
            
            hs = cls.__generar_hash(f"{datos[0]}{datos[1]}")
            if str(hs) != datos[2]:
                raise Exception("La clave de la licencia no es válida")
            
            try:
                fecha_vigencia = datetime.datetime.fromtimestamp(float(datos[0]))
            except Exception as e:
                raise Exception("La clave de la licencia no es válida")

            numero_serie = datos[1]

            return fecha_vigencia, numero_serie
        
        else:
            raise Exception("La clave de la licencia no es válida")

    
    @classmethod
    def validar(cls):
        from src.utils import EntornoInfo

        EntornoInfo.inicializar()

        licencia = cls.__obtener_licencia()
        fecha_vigencia, numero_serie = cls.__desencriptar_licencia(licencia)

        if fecha_vigencia < datetime.datetime.now():
            raise Exception("La licencia de uso ha expirado")
        
        if numero_serie != EntornoInfo.contabilidad_licencia_serie:
            raise Exception("La licencia de uso no es válida para su equipo")
        
        return True

if __name__ == '__main__':
    try:    
        Licencia.validar()
        print("Licencia válida")
    except Exception as e:
        print(f"{e}")
