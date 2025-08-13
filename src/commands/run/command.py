from src.commands.base import Command
from src.luzzi.contabot import Contabot
import logging
import psutil


class RunCommand(Command):
    def add_arguments(self, parser):
        parser.add_argument(
            "--info",
            action="store_true",
            help="Muestra información sobre el comando 'run'.",
        )

    def execute(self, args):
        if args.info:
            print("### Comando 'run' ###")
            print(
                "Este comando inicia el bot para procesar los asientos de contabilidad."
            )
            print("\nUso:")
            print("    python contabot.py run")
            print("\nOpciones:")
            print("    --info      Muestra esta ayuda.")
            print("\nDescripción:")
            print(
                "    Al ejecutar este comando, el bot realizará las acciones necesarias"
            )
            print("    para procesar los asientos de la empresa configurada.")
            print("    No se requieren argumentos adicionales.")
            return

        print("Ejecutando RunCommand.execute()")
        main_exe = "contabilidad_i.exe"
        app_path = r"C:\Program Files (x86)\Compac\Contabilidad\contabilidad_i.exe"
        contabot = Contabot(app_path)

        try:
            contabot.ejecutar_robot()

            print("El bot ha sido ejecutado correctamente.")

        except Exception as e:
            logging.error(f"Error en la ejecución del comando: {e}")
        finally:
            for proc in psutil.process_iter(["name", "pid"]):
                if proc.info["name"].lower() == main_exe.lower():
                    Contabot.terminar_ejecucion(proc.info["pid"])
