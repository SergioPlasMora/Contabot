import winreg

def obtener_valores(ruta):
    try:
        partes = ruta.split("\\", 1)
        if len(partes) != 2:
            return None
        
        clave_raiz_str, subclave = partes
        
        claves_raiz = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG
        }
        
        clave_raiz = claves_raiz.get(clave_raiz_str.upper())
        if clave_raiz is None:
            return None
        
        clave = winreg.OpenKey(clave_raiz, subclave)
        
        resultados = {}
        index = 0
        while True:
            try:
                nombre, valor, tipo = winreg.EnumValue(clave, index)
                resultados[nombre] = valor
                index += 1
            except WindowsError:
                break
        
        winreg.CloseKey(clave)
        
        return resultados if resultados else None
    
    except WindowsError:
        return None


if __name__ == "__main__":
    ruta = r"HKEY_LOCAL_MACHINE\HARDWARE\DESCRIPTION\System\CentralProcessor\0"
    
    valores = obtener_valores(ruta)
    
    if valores is not None:
        print("Valores encontrados:")
        for nombre, valor in valores.items():
            print(f"{nombre}: {valor}")
    else:
        print("No se encontraron valores o la ruta no existe.")
