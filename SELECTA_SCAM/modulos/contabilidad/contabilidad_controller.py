import logging
from PyQt5.QtCore import QObject, pyqtSignal
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
    # Señales
    data_loaded = pyqtSignal()
    data_updated = pyqtSignal(list)  # Emite lista de registros para actualizar la tabla
    error_occurred = pyqtSignal(str)
    procesos_loaded_for_dialog = pyqtSignal(list)
    clientes_loaded = pyqtSignal(list)
    procesos_loaded_for_client = pyqtSignal(list)
    operation_successful = pyqtSignal(str)
    operation_failed = pyqtSignal(str)
    summary_data_loaded = pyqtSignal(dict)
    tipos_contables_loaded = pyqtSignal(list)
    documentos_filtrados_loaded = pyqtSignal(list)  # Reservada para documentos
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

    # -------------------------------
    # CRUD + sincronización con tabla
    # -------------------------------

    def get_contabilidad_records_sync(
        self,
        cliente_id: int = None,
        proceso_id: int = None,
        search_term: str = None,
        tipo_id: int = None,
    ):
        """
        Recupera registros filtrados, actualiza la tabla y emite el resumen de totales.
        """
        try:
            records = self.contabilidad_logic.get_contabilidad_data_for_display(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                search_term=search_term,
                tipo_id=tipo_id,
            )
            self.data_updated.emit(records)
            self.logger.info(
                f"ContabilidadController: Registros emitidos ({len(records)})."
            )

            # Calcular resumen
            total_ingresos, total_gastos = 0.0, 0.0
            for record in records:
                valor = record[5]
                tipo_str = str(record[3]).lower()
                if "ingreso" in tipo_str:
                    total_ingresos += valor
                else:
                    total_gastos += valor

            summary_data = {
                "total_ingresos": total_ingresos,
                "total_gastos": total_gastos,
                "saldo": total_ingresos - total_gastos,
            }
            self.summary_data_loaded.emit(summary_data)
        except Exception as e:
            self.logger.exception("Error al cargar registros/resumen")
            self.operation_failed.emit(f"Error al cargar datos y resumen: {str(e)}")

    def add_record(
        self,
        cliente_id,
        proceso_id,
        tipo_contable_id,
        descripcion,
        monto,
        fecha,
        current_filter_cliente_id: int = None,
        current_filter_proceso_id: int = None,
    ):
        """
        Agrega un registro y refresca la tabla.
        """
        try:
            self.contabilidad_logic.add_contabilidad_record(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_contable_id=tipo_contable_id,
                descripcion=descripcion,
                monto=monto,
                fecha=fecha,
            )

            # Recargar datos actualizados
            self.get_contabilidad_records_sync(
                cliente_id=current_filter_cliente_id,
                proceso_id=current_filter_proceso_id,
            )

            self.operation_successful.emit(
                "¡Registro de contabilidad añadido exitosamente!"
            )

        except Exception as e:
            self.logger.error("Error inesperado al añadir registro", exc_info=True)
            self.operation_failed.emit(f"Error inesperado al añadir registro: {str(e)}")

    def update_record(
        self, record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
    ):
        """
        Actualiza un registro en DB.
        """
        try:
            self.contabilidad_logic.update_contabilidad_record(
                record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
            )
            self.operation_successful.emit(
                f"Registro ID {record_id} actualizado exitosamente."
            )
            return True
        except Exception as e:
            self.logger.exception("Error al actualizar registro")
            self.operation_failed.emit(f"Error inesperado al actualizar registro: {e}")
            return False

    def delete_record(
        self,
        record_id,
        current_filter_cliente_id: int = None,
        current_filter_proceso_id: int = None,
    ):
        """
        Elimina un registro de DB y refresca.
        """
        try:
            self.contabilidad_logic.delete_contabilidad_record(record_id)
            self.get_contabilidad_records_sync(
                cliente_id=current_filter_cliente_id,
                proceso_id=current_filter_proceso_id,
            )
            self.operation_successful.emit(
                f"Registro ID {record_id} eliminado exitosamente."
            )
            return True
        except ValueError as ve:
            self.error_occurred.emit(str(ve))
            self.operation_failed.emit(f"Fallo al eliminar registro: {ve}")
            return False
        except Exception as e:
            self.logger.exception("Error inesperado al eliminar registro")
            self.operation_failed.emit(f"Error inesperado al eliminar registro: {e}")
            return False

    # -------------------------------
    # Datos auxiliares
    # -------------------------------

    def get_summary_data(
        self, cliente_id=None, proceso_id=None, search_term=None, tipo_id=None
    ) -> dict:
        """
        Obtiene datos de resumen delegando en la lógica.
        """
        try:
            summary = self.contabilidad_logic.get_summary_data(
                cliente_id, proceso_id, search_term=search_term, tipo_id=tipo_id
            )
            self.summary_data_loaded.emit(summary)
            return summary
        except Exception as e:
            self.logger.exception("Error al obtener resumen")
            self.operation_failed.emit(f"Error al obtener resumen: {e}")
            return {"total_ingresos": 0.0, "total_gastos": 0.0, "saldo": 0.0}

    def get_all_clientes_sync(self) -> list:
        try:
            clientes_data = self.clientes_logic.get_all_clientes_for_combobox()
            self.clientes_loaded.emit(clientes_data)
            return clientes_data
        except Exception as e:
            self.logger.exception("Error al cargar clientes")
            self.operation_failed.emit(f"Error al cargar clientes: {e}")
            return []

    def get_all_procesos_sync(self):
        try:
            return self.procesos_logic.get_all_active_procesos()
        except Exception as e:
            self.logger.error(f"Error al obtener procesos: {e}")
            return []

    def get_procesos_for_client_sync(self, cliente_id: int = None):
        """
        Carga procesos para un cliente.
        ⚠️ Actualmente placeholder, emite lista vacía.
        """
        self.procesos_loaded_for_client.emit([])

    def get_procesos_by_client_for_dialog(self, cliente_id: int):
        try:
            procesos = self.contabilidad_logic.get_procesos_by_client(cliente_id)
            self.procesos_loaded_for_dialog.emit(procesos)
        except Exception as e:
            self.logger.exception("Error al cargar procesos para diálogo")
            self.error_occurred.emit(f"Error al cargar procesos: {e}")
            self.procesos_loaded_for_dialog.emit([])

    def get_tipos_contables_sync(self) -> list:
        try:
            tipos = self.contabilidad_logic.get_tipos_contables()
            self.tipos_contables_loaded.emit(tipos)
            return tipos
        except Exception as e:
            self.logger.exception("Error al cargar tipos contables")
            self.operation_failed.emit(f"Error al cargar tipos contables: {e}")
            return []

    def get_record_by_id_for_display(self, record_id: int):
        try:
            return self.contabilidad_logic.get_record_by_id_for_display(record_id)
        except Exception as e:
            self.logger.exception("Error al obtener registro por ID")
            self.error_occurred.emit(f"Error al cargar detalles del registro: {e}")
            return None

    # -------------------------------
    # Generación de reportes
    # -------------------------------

    def generar_pdf_con_filtros(self, cliente_id, proceso_id, tipo_id, search_term):
        try:
            records = self.contabilidad_logic.get_contabilidad_data_for_display(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_id=tipo_id,
                search_term=search_term,
            )
            if not records:
                QMessageBox.information(
                    None, "Advertencia", "No hay registros para generar el PDF."
                )
                return
            generar_pdf_resumen_contabilidad("reporte_filtrado.pdf", records)
            self.operation_successful.emit("PDF de resumen generado exitosamente.")
        except Exception as e:
            self.logger.error(f"Error al generar PDF: {e}")
            QMessageBox.critical(
                None, "Error", f"Ocurrió un error inesperado al generar el PDF: {e}"
            )
            self.operation_failed.emit(f"Fallo al generar PDF: {e}")

    def generar_pdf_de_seleccion(self, record_ids: list):
        try:
            if not record_ids:
                QMessageBox.information(
                    None,
                    "Advertencia",
                    "No hay registros seleccionados para generar el PDF.",
                )
                return
            records = self.contabilidad_logic.get_records_by_ids(record_ids)
            generar_pdf_resumen_contabilidad("reporte_seleccion.pdf", records)
            self.operation_successful.emit("PDF de selección generado exitosamente.")
        except Exception as e:
            self.logger.error(f"Error al generar PDF selección: {e}")
            QMessageBox.critical(
                None, "Error", f"Ocurrió un error inesperado al generar el PDF: {e}"
            )
            self.operation_failed.emit(f"Fallo al generar PDF selección: {e}")
