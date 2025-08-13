from src.commands.base import Command
from .show import ShowDB
from src.data.database import DataAccessLayer, SQLServerConnectionPool

class ShowCommand(Command):
    def add_arguments(self, parser):
        parser.add_argument(
            '--option', 
            type=str,
            choices=['todas', 'usuario'],
            help="Opción para mostrar las bases de datos:'todas' o 'usuario'",
            required=True
        )
        parser.add_argument(
            '--usuario',
            type=str,
            help="Nombre del usuario para mostrar las empresas asociadas. Requerido si la opción es 'usuario'.",
            required=False
        )

    def execute(self, args):
        print("Ejecutando Comando....")
        
        connection_pool = SQLServerConnectionPool(pool_size=5)
        dal = DataAccessLayer(connection_pool)

        show_db = ShowDB(dal=dal, option=args.option, usuario=args.usuario)
        
        if args.option == 'usuario' and not args.usuario:
            print("Error: Debe proporcionar un nombre de usuario cuando la opción es 'usuario'.")
        else:
            show_db.show_db()
        connection_pool.close()
