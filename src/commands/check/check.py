from  src.data.database import DataAccessLayer, QueryRepository


class Check:
    """Clase que verifica que la estructura de la base de datos (empresa) sea correcta"""
    
    def __init__(self, dal: DataAccessLayer, option=None):
        self.option = option
        self.dal = dal
    
    def check(self, empresa_id: int):
        if self.option == "analizar":
            print("Ejecutando el análisis de datos.....\n")

            try:
                empresa_info = self.dal.execute_query(
                    'GeneralesSQL',
                    QueryRepository.get_query("check_empresa"),
                    (empresa_id,)
                )
                
                if not empresa_info:
                    print(f"No se encontró la empresa con Id {empresa_id} en GeneralesSQL.")
                    return

                database = empresa_info[0]['AliasBDD']

                table_exists = self.dal.execute_scalar(
                    database,
                    QueryRepository.get_query("check_tabla_parametros"),
                )

                if not table_exists:
                    print(f"La tabla Parametros no existe en la base de datos {database}")
                    return

                estructura_cta = self.dal.execute_scalar(
                    database,
                    QueryRepository.get_query("get_estructura_cta")
                )
                
                parametros_funcionamiento = self.dal.execute_scalar(
                    database,
                    QueryRepository.get_query("get_parametros_funcionamiento")
                )

                if estructura_cta:
                    print(f"Estructura de la empresa: {estructura_cta}\n")
                    
                    if not self.verificar_estructura(estructura_cta):
                        print("Error: La estructura de la empresa es incorrecta. Debe ser '3-2-3'.")
                        return
                else:
                    print(f"No se encontró la estructura en la tabla Parametros para la empresa {empresa_id}.")
                    return
                
                if parametros_funcionamiento:
                    if not self.verificar_parametros_funcionamiento(parametros_funcionamiento):
                        print("Error: Los parámetros de funcionamiento son incorrectos.\nLa Estructura de la cuenta debe ser Alfanumerica.\nEl nivel de catalogo debe ser cada segmento debe ser apartir de la cuenta de mayor los segmetos si son un nivel.\nLa Empresa debe manejar devolución de IVA.\n")
                        print(f"Para corregir este problema entre a la empresa que genero el problema Confuguracion->Redefinir Empresa-> 3.Cuenta y Estructura")
                        return
                else:
                    print(f"No se encontraron los parámetros de funcionamiento en la tabla Parametros para la empresa {empresa_id}.")
                    return
                
                print("La estructura y los parámetros de la empresa son correctos ya puedes iniciar el Contabot ¡Buena Suerte!...\n")
                
            except Exception as e:
                print(f"Error durante la verificación: {str(e)}")
                return
            
        elif self.option == "reporte":
            print("Generando un reporte...")
        else:
            print(f"Opción desconocida: {self.option}")
    
    def verificar_estructura(self, estructura_cta: str) -> bool:
        """Verifica si la estructura de la cuenta es correcta"""
        return estructura_cta == '3-2-3'
    
    def verificar_parametros_funcionamiento(self, parametros_funcionamiento: str) -> bool:
        """Verifica si los parámetros de funcionamiento son correctos"""

        parametros_funcionamiento = parametros_funcionamiento.replace(" ", "")

        if len(parametros_funcionamiento) < 43:
            print(f"Cadena demasiado corta: {len(parametros_funcionamiento)} caracteres")
            return False

        return (
            parametros_funcionamiento[6] == 'N' and
            parametros_funcionamiento[7] == 'M' and
            parametros_funcionamiento[42] == 'S'
        )
