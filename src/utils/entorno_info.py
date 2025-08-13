from src.luzzi.helpers import registry

RUTA_APPKEY_CONTPAQI = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Computación en Acción, SA CV\AppKey\Contpaq_i\Temp"
RUTA_CONTPAQI = (
    r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Computación en Acción, SA CV\CONTPAQ i"
)
RUTA_SACI = r"HKEY_LOCAL_MACHINE\SOFTWARE\WOW6432Node\Computación en Acción, SA CV\CONTPAQ I Servidor de Aplicaciones"


class EntornoInfo:
    contabilidad_version = None
    contabilidad_tipo_instalacion = None
    contabilidad_directorio_base = None
    contabilidad_directorio_datos = None
    contabilidad_licencia_serie = None
    contabilidad_licencia_sitio = None
    componentes_version = None

    @classmethod
    def inicializar(cls):

        llaves = registry.obtener_valores(RUTA_CONTPAQI)
        if llaves is not None:
            for nombre, valor in llaves.items():
                if nombre.startswith("DIRECTORIOBASE"):
                    cls.contabilidad_directorio_base = valor
                elif nombre.startswith("TIPOINSTALACION"):
                    cls.contabilidad_tipo_instalacion = valor
                elif nombre.startswith("VERSION"):
                    cls.contabilidad_version = valor

        llaves = registry.obtener_valores(RUTA_APPKEY_CONTPAQI)
        if llaves is not None:
            for nombre, valor in llaves.items():
                if nombre.startswith("Serial-"):
                    cls.contabilidad_licencia_serie = valor
                elif nombre.startswith("SiteCode-"):
                    cls.contabilidad_licencia_sitio = valor

        llaves = registry.obtener_valores(RUTA_SACI)
        if llaves is not None:
            for nombre, valor in llaves.items():
                if nombre.startswith("VERSION"):
                    cls.componentes_version = valor
                elif nombre.startswith("DIRECTORIODATOS"):
                    cls.ruta_empresas = valor


if __name__ == "__main__":
    EntornoInfo.inicializar()

    print(EntornoInfo.contabilidad_version)
    print(EntornoInfo.componentes_version)
    print(EntornoInfo.contabilidad_licencia_serie)
