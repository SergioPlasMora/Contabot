import sys
import os

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from src.application import Application
from src.commands import (
    RunCommand,
    CheckCommand,
    ShowCommand,
    CreateUserDB,
    VersionCommand,
    CheckRegistryCommand,
)

def main_function():
    commands = {
        "run": RunCommand,
        "check": CheckCommand,
        "show": ShowCommand,
        "create_user_db" : CreateUserDB,
        "version": VersionCommand,
        "check_regestry": CheckRegistryCommand
    }
    
    app = Application(commands)
    app.run()

if __name__ == "__main__":
    main_function()
