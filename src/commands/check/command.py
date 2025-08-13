from src.commands.base import Command
from .check import Check
from src.data.database import DataAccessLayer, SQLServerConnectionPool

class CheckCommand(Command):
    def add_arguments(self, parser):         
        parser.add_argument(
            '--option', 
            type=str,
            help="Opción para revisar el bot (analizar)",
            required=True  
        )
        parser.add_argument(
            '--empresa-id',
            type=int,
            help="ID de la empresa para verificar la estructura",
            required=True 
        )
       
    def execute(self, args):             
        connection_pool = SQLServerConnectionPool(pool_size=5)  
        dal = DataAccessLayer(connection_pool)  
        
        bot = Check(dal=dal, option=args.option)
        

        if args.empresa_id is None:
            print("ID de empresa no proporcionado.\n")
            return
        
        print(f"Verificando la empresa con ID: {args.empresa_id} \n")
        bot.check(empresa_id=args.empresa_id)
        
        connection_pool.close()