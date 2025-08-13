""" """


class AppInfo:
    # CompanyName: Nombre de la empresa
    company_name = "Grex Tecnologías"
    # FileDescription: Descripción corta de la aplicación.
    file_description = "Luzzi RPA ContaBot"
    # FileVersion: Número de versión de archivo.
    file_version = "0.1.0.24"
    # InternalName: Nombre interno de la aplicación.
    internal_name = ""
    # LegalCopyright: Información de copyright.
    legal_copyright = "Todos los derechos reservados.©2024 Grex Tecnologías"
    # OriginalFilename: Nombre original del archivo.
    original_filename = "contabot"
    # ProductName: Nombre del producto.
    product_name = "Luzzi RPA ContaBot"

    @classmethod
    def print_version(cls):
        pass


if __name__ == "__main__":
    AppInfo.print_version()
