import logging
import time
from src.luzzi.page_objects import (
    CompanySelectionPage,
    ContabilizadorWindowPage
    )
from src.luzzi.processors.entry_processor import EntryProcessor
from src.config.config import Config


logger = logging.getLogger(__name__)


class CompanyProcessor:
    def __init__(self, app, data_access_layer):
        self.app = app
        self.data_access_layer = data_access_layer
        self.config = Config.get_instance()
        self.company_selection_page = CompanySelectionPage(app)
        self.contabilizador_page = ContabilizadorWindowPage(app)
        self.entry_processor = EntryProcessor(app)

    def process_companies(self):
        try:
            companies = self.data_access_layer.get_empresas("LUZZI")
            if not companies:
                logger.critical("No se pudieron obtener las empresas.")
                return

            config_companies = self.config.get_companies()
            logger.info(f"Total de empresas encontradas: {len(companies)}")

            for company in companies:
                company_name = company["Nombre"]
                alias_database = company["AliasBDD"]

                if company_name not in config_companies:
                    logger.info(
                        f"La empresa {company_name} no está configurada en el archivo YAML."
                    )
                    continue

                if not self._validate_company_parameters(alias_database):
                    continue

                if not self._validate_company_accounts(alias_database, company_name):
                    continue

                logger.info(f"Procesando empresa: {company_name}")
                time.sleep(1)

                success, result = self.company_selection_page.open_company(company_name)
                if not success:
                    if result == "VERSION_INCOMPATIBLE":
                        logger.critical("Versión de base de datos incompatible.")
                    else:
                        logger.warning(f"No se pudo abrir la empresa: {result}")
                    continue

                ventana_contabilizador = self.contabilizador_page.open_contabilizador()
                if not ventana_contabilizador:
                    logger.critical("No se pudo abrir la ventana del contabilizador.")
                    continue

                self.entry_processor.set_contabilizador_window(ventana_contabilizador)

                asientos = self.data_access_layer.get_asientos(alias_database)
                if not asientos:
                    logger.info(
                        f"No hay asientos configurados para la empresa {company_name}."
                    )
                    continue

                for asiento in asientos:
                    try:
                        self.entry_processor.process_entry(
                            asiento,
                            config_companies[company_name],
                            self.data_access_layer,
                            alias_database,
                            company["AliasBDD"],
                        )
                        logger.info(
                            f"Asiento contable {asiento['Codigo']} procesado exitosamente."
                        )
                    except Exception as e:
                        logger.error(
                            f"Error al procesar el asiento contable {asiento['Codigo']}: {str(e)}"
                        )

                ventana_contabilizador.close()
                ventana_contabilizador.wait_not("exists", timeout=3)
                logger.debug(f"Cerrando empresa: {company_name}")
                self.company_selection_page.closeCompany()
                self.company_selection_page.open_catalog()

            logger.info("Proceso de todas las empresas completado.")
        except Exception as e:
            logger.error(f"Error general en el procesamiento: {str(e)}")
            raise

    def _validate_company_parameters(self, alias_database):
        parametros = self.data_access_layer.validar_parametros(alias_database)
        if not parametros or parametros[0]["estado"] == "Inválido":
            logger.warning(
                f"Parámetros inválidos para la empresa con alias {alias_database}."
            )
            return False
        return True

    def _validate_company_accounts(self, alias_database, company_name):
        cuenta_cliente = self.data_access_layer.get_cuenta_for_empresa(
            alias_database, "cliente"
        )
        cuenta_proveedor = self.data_access_layer.get_cuenta_for_empresa(
            alias_database, "proveedor"
        )
        cuentas_invalidas = []

        if cuenta_cliente and cuenta_cliente[0]["estado"] == "Inválido":
            cuentas_invalidas.append(f"Cliente: {cuenta_cliente[0]['mensaje']}")
        if cuenta_proveedor and cuenta_proveedor[0]["estado"] == "Inválido":
            cuentas_invalidas.append(f"Proveedor: {cuenta_proveedor[0]['mensaje']}")

        if cuentas_invalidas:
            for mensaje in cuentas_invalidas:
                logger.warning(f"Empresa {company_name}: {mensaje}")
            logger.warning(
                f"No se procesará la empresa {company_name} debido a cuentas con formato inválido."
            )
            return False
        return True
