from src.data.database import DataAccessLayer

class ShowDB:
    """Esta clase tiene la responsabilidad de Mostrar las Bases de Datos"""

    def __init__(self, dal: DataAccessLayer, option=None, usuario=None):
        self.dal = dal
        self.option = option
        self.usuario = usuario

    def show_db(self):
        if self.option == "una empresa":
            print("Mostrando información de una sola empresa...")
            empresa_id = input("Ingrese el ID de la empresa: ")
            self.show_single_empresa(int(empresa_id))
        elif self.option == "todas":
            print("Mostrando todas las empresas...")
            self.show_all_empresas()
        elif self.option == "usuario" and self.usuario:
            print(f"Mostrando empresas para el usuario: {self.usuario}")
            self.show_empresas_por_usuario(self.usuario)
        else:
            print(f"Opción desconocida: {self.option}")

    def show_single_empresa(self, empresa_id: int):
        empresa_info = self.dal.get_empresa_info(empresa_id)
        if empresa_info:
            print(f"Información de la empresa:")
            print(f"ID: {empresa_info.get('Id', 'No disponible')}")
            print(f"Nombre: {empresa_info.get('Nombre', 'No disponible')}")
        else:
            print(f"No se encontró información para la empresa con ID {empresa_id}")

    def show_all_empresas(self):
        empresas = self.dal.get_all_empresas()
        if empresas:
            print("Lista de todas las empresas:")
            for empresa in empresas:
                print(f"ID: {empresa['Id']}, Nombre: {empresa['Nombre']}")
        else:
            print("No se encontraron empresas")

    def show_empresas_por_usuario(self, nombre_usuario: str):
        empresas = self.dal.get_empresas_por_usuario(nombre_usuario)
        if empresas:
            print(f"Lista de empresas asociadas al usuario {nombre_usuario}:")
            for empresa in empresas:
                print(f"ID: {empresa['Id']}, Nombre: {empresa['Nombre']}")
        else:
            print(f"No se encontraron empresas para el usuario {nombre_usuario}")
