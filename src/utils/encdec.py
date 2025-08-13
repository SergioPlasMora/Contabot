import base64

CLAVE_ENCDEC = "luzzi"


def encriptar(texto):
    # Paso 1: Encriptar usando XOR
    resultado = ""
    for i, char in enumerate(texto):
        char_code = ord(char)
        clave_code = ord(CLAVE_ENCDEC[i % len(CLAVE_ENCDEC)])
        encrypted_char = chr(char_code ^ clave_code)
        resultado += encrypted_char

    # Paso 2: Convertir a Base64
    resultado_bytes = resultado.encode("utf-8")
    base64_bytes = base64.b64encode(resultado_bytes)
    return base64_bytes.decode("utf-8")


def desencriptar(texto_encriptado):
    # Paso 1: Decodificar de Base64
    base64_bytes = texto_encriptado.encode("utf-8")
    resultado_bytes = base64.b64decode(base64_bytes)
    resultado = resultado_bytes.decode("utf-8")

    # Paso 2: Desencriptar usando XOR
    texto_original = ""
    for i, char in enumerate(resultado):
        char_code = ord(char)
        clave_code = ord(CLAVE_ENCDEC[i % len(CLAVE_ENCDEC)])
        decrypted_char = chr(char_code ^ clave_code)
        texto_original += decrypted_char

    return texto_original


def obtener_hash(cadena):
    hash_value = 0
    for caracter in cadena:
        hash_value += ord(caracter)
    return hash_value
