import argparse
import subprocess
from typing import Dict, Tuple
from src.commands.base import Command

class CreateUserDB(Command):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Agrega argumentos específicos para este comando."""
        parser.add_argument('--server', required=True, help='Nombre del servidor SQL')
        # Argumentos opcionales para credenciales de admin
        parser.add_argument('admin_user', nargs='?', help='Usuario administrador con permisos')
        parser.add_argument('admin_password', nargs='?', help='Contraseña del usuario administrador')
        parser.add_argument('--driver', default='SQL Server', help='Driver SQL')

    def execute(self, args: argparse.Namespace) -> None:
        """Ejecuta el comando usando los argumentos proporcionados."""
        success = False
        new_username = "LUZZII"
        new_password = "Luzzi2025"

        try:
            # Primer intento: usando autenticación Windows
            if not args.admin_user or not args.admin_password:
                success = self.try_windows_auth(args.server, new_username, new_password)
            
            # Segundo intento: usando credenciales de admin si se proporcionaron o si falló Windows auth
            if not success and args.admin_user and args.admin_password:
                success = self.try_sql_auth(
                    args.server, 
                    args.admin_user, 
                    args.admin_password,
                    new_username,
                    new_password
                )
            
            if not success:
                print("No se pudo crear el usuario. Por favor, proporcione credenciales de administrador:")
                print("Ejemplo: create_user_db --server SERVIDOR admin_user admin_password")
                return

            # Configurar archivo .env
            config = {
                'DB_DRIVER': args.driver,
                'DB_SERVER': args.server,
                'DB_USER': new_username,
                'DB_PASSWORD': new_password,
                'DB_TRUSTED_CONNECTION': 'no',
                'DB_TIMEOUT': '30'
            }
            self.generate_env_file(config)
            print("Archivo .env generado exitosamente")

        except Exception as e:
            print(f"Error: {str(e)}")

    def try_windows_auth(self, server: str, username: str, password: str) -> bool:
        """Intenta crear usuario usando autenticación Windows."""
        try:
            queries = self.get_user_creation_queries(username, password)
            for query in queries:
                cmd = f'sqlcmd -S {server} -E -Q "{query}"'
                subprocess.run(cmd, shell=True, check=True)
            print(f"Usuario {username} creado exitosamente usando autenticación Windows")
            return True
        except subprocess.CalledProcessError:
            return False

    def try_sql_auth(self, server: str, admin_user: str, admin_password: str, 
                new_username: str, new_password: str) -> bool:
        """Intenta crear usuario usando autenticación SQL."""
        try:
            queries = self.get_user_creation_queries(new_username, new_password)
            for query in queries:
                # Enclose password in quotes to handle special characters
                cmd = f'sqlcmd -S "{server}" -U "{admin_user}" -P "{admin_password}" -Q "{query}"'
                subprocess.run(cmd, shell=True, check=True)
            print(f"Usuario {new_username} creado exitosamente usando credenciales de administrador")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error al crear usuario con credenciales de administrador: {str(e)}")
            return False

    @staticmethod
    def get_user_creation_queries(username: str, password: str) -> list:
        """Retorna las queries necesarias para crear el usuario."""
        return [
            f"IF NOT EXISTS (SELECT * FROM sys.server_principals WHERE name = '{username}') "
            f"CREATE LOGIN [{username}] WITH PASSWORD = '{password}'",
            f"USE master",
            f"IF NOT EXISTS (SELECT * FROM sys.database_principals WHERE name = '{username}') "
            f"CREATE USER [{username}] FOR LOGIN [{username}]",
            f"IF IS_SRVROLEMEMBER('sysadmin', '{username}') = 0 "
            f"EXEC sp_addsrvrolemember '{username}', 'sysadmin'",
            f"GRANT CONNECT SQL TO [{username}]",
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON DATABASE::[master] TO [{username}]"
        ]

    @staticmethod
    def generate_env_file(config: Dict[str, str]) -> None:
        """Genera archivo .env con configuración."""
        env_content = "\n".join([f"{k}={v}" for k, v in config.items()])
        with open('.env', 'w') as f:
            f.write(env_content)