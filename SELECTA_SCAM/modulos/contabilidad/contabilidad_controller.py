import logging
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from datetime import datetime, date
from typing import Optional
from SELECTA_SCAM.modulos.contabilidad.contabilidad_logic import ContabilidadLogic
from SELECTA_SCAM.modulos.clientes.clientes_logic import ClientesLogic
from SELECTA_SCAM.modulos.procesos.procesos_logic import ProcesosLogic
from SELECTA_SCAM.modulos.contabilidad.contabilidad_model import ContabilidadModel

from SELECTA_SCAM.modulos.contabilidad.contabilidad_pdf import (
    generar_pdf_resumen_contabilidad,
)
from PyQt5.QtWidgets import QMessageBox


logger = logging.getLogger(__name__)


class ContabilidadController(QObject):
    # Señales:
    data_loaded = (
        pyqtSignal()
    )  # Esta señal parece no usarse activamente, pero se mantiene si es parte de otra lógica.
    data_updated = pyqtSignal(
        list
    )  # <--- ¡CAMBIO IMPORTANTE! Ahora emite una LISTA de datos
    error_occurred = pyqtSignal(str)
    procesos_loaded_for_dialog = pyqtSignal(list)
    clientes_loaded = pyqtSignal(list)
    procesos_loaded_for_client = pyqtSignal(list)
    operation_successful = pyqtSignal(str)
    operation_failed = pyqtSignal(str)
    summary_data_loaded = pyqtSignal(dict)
    tipos_contables_loaded = pyqtSignal(list)
    documentos_filtrados_loaded = pyqtSignal(
        list
    )  # Esta señal parece pertenecer a un módulo de documentos.
    record_updated = pyqtSignal(int)

    def __init__(
        self,
        model: ContabilidadModel,
        contabilidad_logic: ContabilidadLogic,
        clientes_logic: ClientesLogic,
        procesos_logic: ProcesosLogic,
        parent=None,
    ):
        super().__init__(parent)
        self.model = model
        self.contabilidad_logic = contabilidad_logic
        self.clientes_logic = clientes_logic
        self.procesos_logic = procesos_logic
        self.logger = logger
        self.logger.info("ContabilidadController: Inicializado.")

    def get_filtered_documents(
        self, cliente_id: int = None, search_term: str = None, tipo_doc_id: int = None
    ):
        try:
            self.operation_failed.emit(
                "Funcionalidad no implementada",
                "La búsqueda de documentos desde Contabilidad no está activa.",
            )
            pass  # Placeholder si documentos_logic no está inicializado
        except Exception as e:
            logger.exception(
                "ContabilidadController (Doc): Error al obtener documentos filtrados."
            )
            self.operation_failed.emit(
                f"Error de Carga de Documentos",
                f"No se pudieron cargar los documentos filtrados: {e}",
            )

        # En: contabilidad_controller.py

    # Reemplaza el método completo con este:

    def get_contabilidad_records_sync(
        self,
        cliente_id: int = None,
        proceso_id: int = None,
        search_term: str = None,
        tipo_id: int = None,
    ):
        """
        Recupera los registros, los emite para actualizar la tabla,
        Y ADEMÁS, calcula y emite el resumen de totales.
        """
        try:
            # 1. Obtenemos los datos formateados para la tabla desde la lógica (esto ya lo tenías)
            records = self.contabilidad_logic.get_contabilidad_data_for_display(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                search_term=search_term,
                tipo_id=tipo_id,
            )
            self.data_updated.emit(records)
            self.logger.info(
                f"ContabilidadController: Registros de contabilidad emitidos ({len(records)})."
            )

            # --- INICIO DE LA NUEVA LÓGICA ---
            # 2. Calculamos los totales a partir de los MISMOS datos que se muestran en la tabla
            total_ingresos = 0.0
            total_gastos = 0.0

            for record in records:
                # En la tupla que preparamos, el valor está en la 6ª posición (índice 5)
                # y el tipo está en la 4ª posición (índice 3).
                valor = record[5]
                tipo_str = record[3].lower()

                if "ingreso" in tipo_str:
                    total_ingresos += valor
                else:  # Asumimos que si no es ingreso, es gasto
                    total_gastos += valor

            saldo = total_ingresos - total_gastos

            # 3. Preparamos el diccionario de resumen
            summary_data = {
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "saldo": saldo,
            }

            # 4. Emitimos la señal para que el widget actualice las cajas de texto
            self.summary_data_loaded.emit(summary_data)
            self.logger.info(f"ContabilidadController: Resumen de totales emitido.")
            # --- FIN DE LA NUEVA LÓGICA ---

        except Exception as e:
            self.logger.exception(
                "ContabilidadController: Error al cargar registros y calcular resumen."
            )
            self.operation_failed.emit(f"Error al cargar datos y resumen: {str(e)}")

    def get_contabilidad_data_for_table(self, cliente_id=None, proceso_id=None):
        """
        Obtiene los datos de contabilidad filtrados para la tabla.
        """
        return self.contabilidad_logic.get_contabilidad_data(cliente_id, proceso_id)

    def add_record(
        self,
        cliente_id,
        proceso_id,
        tipo_id,
        descripcion,
        valor,
        fecha,
        current_filter_cliente_id: int = None,
        current_filter_proceso_id: int = None,
    ):
        try:
            # Ahora se pasa directamente el 'tipo_id' en lugar del nombre
            self.contabilidad_logic.add_contabilidad_record(
                cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
            )
            self.get_contabilidad_records_sync(
                cliente_id=current_filter_cliente_id,
                proceso_id=current_filter_proceso_id,
            )
            self.operation_successful.emit(
                "¡Registro de contabilidad añadido exitosamente!"
            )
            return True
        except ValueError as ve:
            self.error_occurred.emit(str(ve))
            self.operation_failed.emit(f"Fallo al añadir registro: {ve}")
            return False
        except Exception as e:
            self.error_occurred.emit(f"Error al añadir registro: {e}")
            self.operation_failed.emit(f"Error inesperado al añadir registro: {e}")
            return False

    # En: contabilidad_controller.py

    def update_record(
        self, record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
    ):
        """
        Actualiza el registro y luego pide al widget que se refresque.
        """
        try:
            # Llama a la lógica para que actualice la base de datos
            self.contabilidad_logic.update_contabilidad_record(
                record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
            )
            # Emite la señal de éxito
            self.operation_successful.emit(
                f"Registro ID {record_id} actualizado exitosamente."
            )
            return True
        except Exception as e:
            self.logger.exception(
                f"Error al orquestar la actualización del registro: {e}"
            )
            self.operation_failed.emit(f"Error inesperado al actualizar registro: {e}")
            return False

    def add_record(
        self, cliente_id, proceso_id, tipo_contable_id, descripcion, monto, fecha
    ):
        try:
            self.contabilidad_logic.add_contabilidad_record(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_contable_id=tipo_contable_id,
                descripcion=descripcion,
                monto=monto,
                fecha=fecha,
            )
            self.load_records()  # recargar tabla/resumen
        except Exception as e:
            logger.error("Error inesperado al añadir registro", exc_info=True)
            QMessageBox.critical(
                None, "Error", f"Error inesperado al añadir registro: {e}"
            )

    def get_summary_data(
        self,
        cliente_id: int = None,
        proceso_id: int = None,
        search_term: str = None,
        tipo_id: int = None,
    ) -> dict:
        """
        Obtiene los datos de resumen (ingresos, gastos, saldo) aplicando filtros
        y un término de búsqueda, delegando la tarea a la capa de lógica.
        """
        # logger.info(f"ContabilidadController: Solicitando datos de resumen (cliente_id={cliente_id}, proceso_id={proceso_id}, search_term='{search_term}').")
        try:
            summary = self.contabilidad_logic.get_summary_data(
                cliente_id, proceso_id, search_term=search_term, tipo_id=tipo_id
            )  # Nuevo parámetro
            self.summary_data_loaded.emit(summary)
            # logger.info("ContabilidadController: Datos de resumen cargados. Señal summary_data_loaded emitida.")
            return summary
        except Exception as e:
            logger.exception(
                "ContabilidadController: Error al obtener datos de resumen."
            )
            self.error_occurred.emit(f"Error al obtener resumen: {e}")
            self.operation_failed.emit(f"Error al obtener resumen: {e}")
            return {"total_ingresos": 0.0, "total_gastos": 0.0, "saldo": 0.0}

    def get_all_clientes_sync(self) -> list:
        """
        Método síncrono para obtener todos los clientes. Usado por los diálogos y para inicializar el combo del widget.
        Retorna una lista de diccionarios con 'id' y 'nombre'.
        """
        ##logger.info("ContabilidadController: Obteniendo todos los clientes de forma síncrona.")
        try:
            clientes_data = (
                self.clientes_logic.get_all_clientes_for_combobox()
            )  # <-- ¡CAMBIO AQUÍ! Usar clientes_logic
            ##logger.info(f"ContabilidadController: Emitiendo clientes_loaded con data: {clientes_data}")
            self.clientes_loaded.emit(clientes_data)
            return clientes_data
        except Exception as e:
            logger.exception(
                "ContabilidadController: Error al obtener todos los clientes de forma síncrona."
            )
            self.operation_failed.emit(f"Error al cargar clientes: {e}")
            return []

    def get_procesos_by_client_for_dialog(self, cliente_id: int):
        """
        Obtiene procesos para un cliente específico y emite la señal
        procesos_loaded_for_dialog.
        """
        ##logger.info(f"ContabilidadController: Obteniendo procesos para diálogo por cliente ID {cliente_id}.")
        try:
            procesos = self.contabilidad_logic.get_procesos_by_client(
                cliente_id
            )  # Asume que contabilidad_logic tiene este método
            self.procesos_loaded_for_dialog.emit(procesos)
            # logger.info(f"ContabilidadController: Procesos para diálogo cargados para cliente {cliente_id}. Señal emitida.")
        except Exception as e:
            logger.exception(
                f"ContabilidadController: Error al cargar procesos para diálogo para cliente ID {cliente_id}."
            )
            self.error_occurred.emit(f"Error al cargar procesos: {e}")
            self.procesos_loaded_for_dialog.emit(
                []
            )  # Emitir lista vacía en caso de error

    def get_tipos_contables_sync(self) -> list:
        """
        Método síncrono para obtener los tipos contables. Usado por los diálogos y el widget.
        """
        ##logger.info("ContabilidadController: Obteniendo tipos contables de forma síncrona.")
        try:
            tipos = self.contabilidad_logic.get_tipos_contables()
            self.tipos_contables_loaded.emit(tipos)
            # logger.info("ContabilidadController: Tipos contables cargados. Señal tipos_contables_loaded emitida.")
            return tipos
        except Exception as e:
            logger.exception(
                "ContabilidadController: Error al obtener tipos contables de forma síncrona."
            )
            self.error_occurred.emit(f"Error al cargar tipos contables: {e}")
            self.operation_failed.emit(f"Error al cargar tipos contables: {e}")
            return []

    def get_record_by_id_for_display(self, record_id: int) -> tuple:
        """
        Obtiene un registro por ID y lo formatea para mostrarlo en el diálogo de edición.
        Retorna la tupla formateada por logic, o una tupla vacía/None si no se encuentra.
        """
        ##logger.info(f"ContabilidadController: Obteniendo registro ID {record_id} para display.")
        try:
            # Una mejor aproximación es que contabilidad_logic tenga un get_record_by_id_for_display
            record = self.contabilidad_logic.get_record_by_id_for_display(record_id)
            if record:
                ##logger.info(f"ContabilidadController: Registro ID {record_id} encontrado y formateado para display.")
                return record
            logger.warning(
                f"ContabilidadController: No se encontró el registro ID {record_id}."
            )
            return None
        except Exception as e:
            logger.exception(
                f"ContabilidadController: Error al obtener y formatear registro ID {record_id}."
            )
            self.error_occurred.emit(f"Error al cargar detalles del registro: {e}")
            return None

    def get_all_procesos_sync(self):
        """
        Obtiene todos los procesos activos de forma síncrona para usarlos en un diálogo.
        """
        try:
            # Llama al método correcto en la lógica de procesos
            return self.procesos_logic.get_all_active_procesos()
        except Exception as e:
            self.logger.error(
                f"Error al obtener todos los procesos de forma síncrona: {e}"
            )
            return []

    def get_procesos_for_client_sync(self, cliente_id: int = None):
        # self.##logger.info(f"ContabilidadController: Cargando procesos para filtro de cliente ID {cliente_id}.")
        # No se va a tocar la lógica de procesos por ahora, por lo que emitimos una lista vacía
        self.procesos_loaded_for_client.emit([])
        # self.#logger.info("ContabilidadController: Módulo de procesos ignorado. Lista de procesos vacía emitida.")

    def generar_pdf_con_filtros(self, cliente_id, proceso_id, tipo_id, search_term):
        """
        Genera un PDF con los registros de contabilidad filtrados.
        """
        try:
            # 1. Obtener los datos filtrados desde la lógica
            records = self.contabilidad_logic.get_contabilidad_data_for_display(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_id=tipo_id,
                search_term=search_term,
            )

            if not records:
                QMessageBox.information(
                    None,
                    "Advertencia",
                    "No hay registros para generar el PDF con los filtros seleccionados.",
                )
                return

            # 2. Llamar a la clase generadora de PDF para crear el documento
            self.pdf_generator.generate_summary_pdf(records)
            self.operation_successful.emit("PDF de resumen generado exitosamente.")

        except Exception as e:
            self.logger.error(f"Error al generar el PDF: {e}")
            QMessageBox.critical(
                None, "Error", f"Ocurrió un error inesperado al generar el PDF: {e}"
            )
            self.operation_failed.emit(f"Fallo al generar PDF: {e}")

    def generar_pdf_de_seleccion(self, record_ids: list):
        """
        Genera un PDF solo para una lista específica de registros seleccionados.
        """
        try:
            if not record_ids:
                QMessageBox.information(
                    None,
                    "Advertencia",
                    "No hay registros seleccionados para generar el PDF.",
                )
                return

            # Obtener los datos específicos de los registros seleccionados
            records = self.contabilidad_logic.get_records_by_ids(record_ids)

            # Llamar al generador de PDF con la lista de registros
            self.pdf_generator.generate_summary_pdf(records)
            self.operation_successful.emit(
                "PDF de registros seleccionados generado exitosamente."
            )

        except Exception as e:
            self.logger.error(f"Error al generar el PDF de la selección: {e}")
            QMessageBox.critical(
                None, "Error", f"Ocurrió un error inesperado al generar el PDF: {e}"
            )
            self.operation_failed.emit(f"Fallo al generar PDF de selección: {e}")
