""" """

from abc import ABC, abstractmethod


class Command(ABC):
    """
    Interfaz abstracta para los subcomandos de la aplicación.
    """

    @abstractmethod
    def add_arguments(self, parser):
        """
        Añade los argumentos específicos del comando al parser.

        Args:
            parser (argparse.ArgumentParser): El parser al que se añadirán los argumentos.
        """
        pass

    @abstractmethod
    def execute(self, args):
        """
        Ejecuta la lógica del comando.

        Args:
            args (argparse.Namespace): Los argumentos parseados.
        """
        pass
