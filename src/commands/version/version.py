"""
Este modulo muestra la version del Contabot
"""

class Version:
    def __init__(self, option=None):
        self.option = option

    def version(self):
        print(f"Se ejecutó el comando Version : {self.option}")
        