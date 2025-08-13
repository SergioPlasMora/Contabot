from src.commands.base import Command
from .version import Version

class VersionCommand(Command):
    def add_arguments(self, parser):
        pass

    def execute(self, args):
        version = "Luzzi RPA ContaBot v0.1.0.24"
        print(f"Contabot {version}")

