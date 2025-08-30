from datetime import datetime, date
from typing import Optional
from SELECTA_SCAM.modulos.contabilidad.contabilidad_db import ContabilidadDB
from SELECTA_SCAM.db.models import Contabilidad, TipoContable


class ContabilidadModel:
    def __init__(self, contabilidad_db: ContabilidadDB):
        self.contabilidad_db = contabilidad_db

    def get_all_contabilidad_records(
        self, cliente_id: int = None, proceso_id: int = None, search_term: str = None
    ) -> list[Contabilidad]:
        return self.contabilidad_db.get_filtered_contabilidad_records(
            cliente_id, proceso_id, search_term
        )

    def update_contabilidad_record(
        self,
        record_id: int,
        cliente_id: int,
        proceso_id: int,
        tipo_id: int,
        descripcion: str,
        valor: float,
        fecha,
    ):
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        with self.contabilidad_db.get_session() as session:
            record = (
                session.query(Contabilidad).filter(Contabilidad.id == record_id).first()
            )
            if record:
                record.cliente_id = cliente_id
                record.proceso_id = proceso_id
                record.tipo_contable_id = tipo_id
                record.descripcion = descripcion
                record.monto = valor
                record.fecha = fecha

    def delete_contabilidad_record(self, record_id: int):
        return self.contabilidad_db.delete_record(record_id)

    def get_contabilidad_record_by_id(self, record_id: int):
        return self.contabilidad_db.get_record_by_id(record_id)

    def get_filtered_contabilidad_records(
        self,
        cliente_id: Optional[int] = None,
        proceso_id: Optional[int] = None,
        search_term: Optional[str] = None,
    ) -> list:
        return self.contabilidad_db.get_filtered_contabilidad_records(
            cliente_id=cliente_id, proceso_id=proceso_id, search_term=search_term
        )

    def add_contabilidad_record(
        self,
        cliente_id: int,
        proceso_id: Optional[int],
        tipo_id: int,
        descripcion: str,
        valor: float,
        fecha: str,
    ):
        if isinstance(fecha, str):
            fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
        elif not isinstance(fecha, (date, datetime)):
            raise TypeError(
                "La fecha debe ser un string YYYY-MM-DD o un objeto date/datetime."
            )
        with self.contabilidad_db.get_session() as session:
            nuevo = Contabilidad(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_contable_id=tipo_id,
                descripcion=descripcion,
                monto=valor,
                fecha=fecha,
            )
            session.add(nuevo)

    def get_ingreso_types(self):
        with self.contabilidad_db.get_session() as session:
            return [
                t.nombre
                for t in session.query(TipoContable)
                .filter(TipoContable.es_ingreso == True)
                .all()
            ]

    def get_gasto_types(self):
        with self.contabilidad_db.get_session() as session:
            return [
                t.nombre
                for t in session.query(TipoContable)
                .filter(TipoContable.es_ingreso == False)
                .all()
            ]
