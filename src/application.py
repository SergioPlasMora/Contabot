import logging
from typing import Dict, Type
from src.cli_parser import CLIParser
from commands import Command

class Application:
    """
    Clase principal que maneja la ejecución de la aplicación.
    """
    def __init__(self, commands: Dict[str, Type[Command]]):
        """
        Args:
            commands (Dict[str, Type[Command]]): Diccionario de subcomandos disponibles.
        """
        self.commands = commands
        self.cli_parser = CLIParser(commands)
        self.args = self.cli_parser.parse_arguments()
        self.logger = self._setup_logger()

    def _setup_logger(self):
        """
        Configura y retorna el logger de la aplicación.

        Returns:
            logging.Logger: Logger configurado.
        """
        level = logging.DEBUG if self.args.debug else logging.INFO
        logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")
        return logging.getLogger(__name__)

    def run(self):
        """
        Método principal que ejecuta la lógica de la aplicación con el manejo de subcomandos.
        """
        if self.args.version:
            self._show_version()
            return
        print("Iniciando la aplicación...")
        try:
            self._startup() 
            self._execute_command()  
        except Exception as e:
            self.logger.error(f"Error durante la ejecución: {e}")
        finally:
            self._shutdown()
    
    def _show_version(self):
        """
        Muestra la versión de la aplicación.
        """
        version = "Luzzi RPA ContaBot v0.1.0.24" 
        print(f"Contabot versión {version}")

    def _startup(self):
        """
        Realiza las tareas de inicio de la aplicación.
        """
        self.logger.debug("Iniciando Ejecucion...\n")

    def _execute_command(self):
        """
        Ejecuta el subcomando especificado por el usuario.
        """
        self.logger.debug("Application._execute_command()")
        if self.args.command:
            command_class = self.commands[self.args.command]
            command = command_class() 
            command.execute(self.args)  
        else:
            self.logger.error("No se especificó ningún subcomando.")
            self.cli_parser.print_help()

    def print_help(self):
        print("Subcomandos disponibles:")
        for cmd in self.commands:
            print(f"  - {cmd}")

    def _shutdown(self):
        """
        Realiza las tareas de cierre de la aplicación.
        """
        print("Ejecucion Finalizada...")
