
import argparse
from typing import Dict, Type
from src.commands import Command

class CLIParser:
    """
    Clase para manejar la especificación de la interfaz de línea de comandos
    y el parseo de argumentos, incluyendo subcomandos.
    """

    def __init__(self, commands: Dict[str, Type[Command]]):
        """
        Inicializa el parser de argumentos con subcomandos.

        Args:
            commands (Dict[str, Type[Command]]): Diccionario de subcomandos disponibles.
        """
        self.parser = argparse.ArgumentParser(
            description="[Interfaz de Linea de Comandos Contabot LuzziRPA]"
        )
        self.subparsers = self.parser.add_subparsers(dest="command")
        self.commands = commands

        self._add_global_arguments()
        self._add_subcommands()

    def _add_global_arguments(self):
        """
        Agrega los argumentos globales al parser.
        """
        # Subcomando para ejecutar el robot
        self.parser.add_argument(
            "--run",
            action="store_true",  
            help="Ejecuta el robot. Ejemplo de uso: 'contabot run'"
        )
        
        # Subcomando para revisar la configuración de la empresa
        self.parser.add_argument(
            "--check",
            action="store_true", 
            help="Revisa la configuración de la empresa. Ejemplo de uso: 'contabot check --option analizar --empresa-id 5'"
        )
        
        self.parser.add_argument(
            "--show",
            action="store_true", 
            help="Muestra las empresas a las que Luzzi tiene acceso. Ejemplo de uso:show --option 'todas' o 'show --option 'usuario' --usuario 'LUZZI'"
        )
        
        self.parser.add_argument(
            "--check_regestry",
            action="store_true", 
            help="Revisa y genera la licencia desde el Registro de Windows. Ejemplo de uso: 'contabot check_regestry --numero_serie 52459E228DB222F6 --fecha_vigencia 2024-12-31 --guardar'"
        )
        
        self.parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help="Muestra la versión de la aplicación"
        )
        
        self.parser.add_argument(
            "--debug",
            action="store_true",
            help="Habilita el modo de depuración para obtener más detalles en los logs"
        )
        self.parser.add_argument(
            "--create_user_db",
            action="store_true", 
        help="Crea el Usuario para el SSMS. Ejemplo de uso: create_user_db --server 'local\sql2022'"
        )

    def _add_subcommands(self):
        """ Agrega los subcomandos al parser. """
        for cmd_name, cmd_class in self.commands.items():
            subparser = self.subparsers.add_parser(cmd_name)
            cmd_class().add_arguments(subparser)

    def parse_arguments(self):
        """
        Parsea los argumentos de la línea de comandos.

        Returns:
            argparse.Namespace: Objeto con los argumentos parseados.
        """
        return self.parser.parse_args()

    def print_help(self):
        
        """
        Imprime el mensaje de ayuda del parser.
        """
        self.parser.print_help()