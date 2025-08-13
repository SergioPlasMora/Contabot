import os
from pathlib import Path
import yaml

class Config:
    _instance = None

    @classmethod
    def get_instance(cls, archivos_config=None):
        if cls._instance is None:
            cls._instance = cls(cls.cargar(archivos_config))
        return cls._instance

    @classmethod
    def cargar(cls, archivos_config=None):
        if archivos_config is None:
            archivos_config = ['config.yaml', 'filters.yaml']

        config = {}

        base_dir = os.getcwd()

        for nombre_archivo in archivos_config:
            ruta_archivo = Path(base_dir) / nombre_archivo

            if not ruta_archivo.exists():
                raise ValueError(f"El archivo de configuración '{ruta_archivo}' no fue encontrado en el directorio actual.")

            try:
                with ruta_archivo.open('r') as file:
                    data = yaml.safe_load(file)
                    if data:
                        config.update(data)
            except Exception as e:
                raise ValueError(f"Ocurrió un problema al cargar el archivo de configuración '{nombre_archivo}': {e}")

        return config

    def __init__(self, config_dict):
        self._config = config_dict
        self.validar_configuracion()

    def validar_configuracion(self):
        required_keys = ['companies', 'filterPositions', 'user', 'password','server','admin_user','admin_password']
        for key in required_keys:
            if key not in self._config:
                raise ValueError(f"Falta la clave de configuración: {key}")

    def get_companies(self):
        return self._config.get('companies', {})

    def get_templates(self):
        templates = {}
        companies = self.get_companies()

        for company, config in companies.items():
            company_templates = config.get('templates', {})
            templates.update(company_templates)

        return templates

    def get_filter_positions(self):
        return self._config.get('filterPositions', {})

    def get_credentials(self):
        return {
            'user': self._config.get('user'),
            'password': self._config.get('password'),
            'server' : self._config.get('server'),
            'admin_user' : self._config.get('admin_user'),
            'admin_password' : self._config.get('admin_password'),

        }
    
if __name__ == "__main__":
    archivos_config = ['config.yaml', 'filters.yaml']

    try:
        config = Config.get_instance(archivos_config)

        companies = config.get_companies()
        print("\nCompanies:")
        print(yaml.dump(companies, allow_unicode=True))

        filter_positions = config.get_filter_positions()
        print("\nPosiciones de filtros:")
        print(yaml.dump(filter_positions, allow_unicode=True))

        credentials = config.get_credentials()
        print("\nCredenciales:")
        print(f"Usuario: {credentials['user']}")
        print(f"Contraseña: {credentials['password']}")
        print(f"Server: {credentials['server']}")
        print(f"Admin Server: {credentials['admin_user']}")
        print(f"Password Server: {credentials['admin_password']}")


    except Exception as e:
        print(f"Error: {e}")
