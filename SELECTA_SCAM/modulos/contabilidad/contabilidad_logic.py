# SELECTA_SCAM/modulos/contabilidad/contabilidad_logic.py

from datetime import date, datetime
from typing import Optional
from dataclasses import dataclass

from .contabilidad_db import ContabilidadDB
from .contabilidad_model import ContabilidadModel
from ..clientes.clientes_logic import ClientesLogic
from ..procesos.procesos_logic import ProcesosLogic

@dataclass
class TipoContable:
    id: int
    nombre: str

@dataclass
class ContabilidadReportData:
    records: list
    total_ingresos: float
    total_gastos: float
    saldo_neto: float
    filtros: str
    tipos_contables_map: dict

class ContabilidadLogic:
    def __init__(self, contabilidad_db: ContabilidadDB, clientes_logic: ClientesLogic, contabilidad_model: ContabilidadModel, procesos_logic: ProcesosLogic):
        self.contabilidad_db = contabilidad_db
        self.clientes_logic = clientes_logic
        self.procesos_logic = procesos_logic
        self.contabilidad_model = contabilidad_model
        self.tipos_contables = self.get_tipos_contables()
        self.tipos_contables_map = {t.id: t.nombre for t in self.tipos_contables}

    def get_contabilidad_data_for_display(self, cliente_id: Optional[int] = None, proceso_id: Optional[int] = None, search_term: Optional[str] = None, tipo_id: Optional[int] = None):
        records_orm = self.contabilidad_db.get_filtered_contabilidad_records(
            cliente_id=cliente_id, proceso_id=proceso_id, search_term=search_term, tipo_id=tipo_id
        )
        display_records = []
        for rec in records_orm:
            cliente_nombre = rec.cliente.nombre if rec.cliente else "SIN CLIENTE"
            proceso_radicado = rec.proceso.radicado if rec.proceso else "N/A"
            tipo_nombre = rec.tipo.nombre if rec.tipo else "SIN TIPO"
            fecha_str = rec.fecha.strftime("%Y-%m-%d") if isinstance(rec.fecha, (date, datetime)) else str(rec.fecha)
            display_records.append((rec.id, cliente_nombre, proceso_radicado, tipo_nombre, rec.descripcion, rec.monto, fecha_str))
        return display_records

    def update_contabilidad_record(self, record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha):
        self.contabilidad_model.update_contabilidad_record(
            record_id, cliente_id, proceso_id, tipo_id, descripcion, valor, fecha
        )

    def get_contabilidad_record_raw(self, record_id: int):
        record = self.contabilidad_db.get_record_by_id(record_id)
        if not record:
            return None
        cliente_nombre = record.cliente.nombre if record.cliente else "N/A"
        proceso_radicado = record.proceso.radicado if record.proceso else "N/A"
        tipo_nombre = self.tipos_contables_map.get(record.tipo_contable_id, "Desconocido")
        fecha_str = record.fecha.strftime("%Y-%m-%d") if record.fecha else ""
        return (record.id, cliente_nombre, proceso_radicado, tipo_nombre, record.descripcion, record.monto, fecha_str)

    def get_tipos_contables(self):
        return [TipoContable(id=i, nombre=n) for i, n in enumerate([
            "Ingreso por Servicios", "Gasto Operativo", "Ingreso por Honorarios",
            "Gasto Administrativo", "Reembolso", "Impuesto", "Nómina",
            "Amortización", "Depreciación", "Inversión", "Préstamo", "Intereses"
        ], 1)]

    def get_contabilidad_report_data(self, record_ids: Optional[list] = None, cliente_id: Optional[int] = None, proceso_id: Optional[int] = None, tipo_id: Optional[int] = None, search_term: Optional[str] = None):
        if record_ids:
            records = self.contabilidad_db.get_contabilidad_records_by_ids(record_ids)
        else:
            records = self.contabilidad_db.get_filtered_contabilidad_records(
                cliente_id=cliente_id, proceso_id=proceso_id, tipo_id=tipo_id, search_term=search_term
            )
        total_ingresos = sum(r.monto for r in records if r.tipo_contable_id in {1, 3})
        total_gastos = sum(r.monto for r in records if r.tipo_contable_id not in {1, 3})
        return ContabilidadReportData(
            records=records,
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            saldo_neto=(total_ingresos - total_gastos),
            filtros="Filtros Aplicados",
            tipos_contables_map=self.tipos_contables_map
        )
