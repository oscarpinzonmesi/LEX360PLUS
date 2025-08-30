import logging
from datetime import date
from typing import List, Optional, Tuple, Dict

from SELECTA_SCAM.utils.db_manager import get_db_session
from SELECTA_SCAM.db.models import Contabilidad, Cliente, Proceso, TipoContable

logger = logging.getLogger(__name__)


class ContabilidadLogic:
    def __init__(self, db_manager=None):
        """
        Constructor de la lógica de Contabilidad.
        Si no se especifica un db_manager, usa el gestor centralizado.
        """
        self.db_manager = db_manager or get_db_session

    # -------------------------------
    # CRUD
    # -------------------------------

    def add_contabilidad_record(
        self,
        cliente_id: int,
        proceso_id: Optional[int],
        tipo_contable_id: int,
        descripcion: str,
        monto: float,
        fecha: date,
    ) -> Contabilidad:
        with self.db_manager() as session:
            record = Contabilidad(
                cliente_id=cliente_id,
                proceso_id=proceso_id,
                tipo_contable_id=tipo_contable_id,
                descripcion=descripcion,
                monto=monto,
                fecha=fecha,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            logger.info(f"ContabilidadLogic: Registro añadido ID={record.id}")
            return record

    def update_contabilidad_record(
        self,
        record_id: int,
        cliente_id: int,
        proceso_id: Optional[int],
        tipo_id: int,
        descripcion: str,
        valor: float,
        fecha: date,
    ) -> bool:
        with self.db_manager() as session:
            record = session.get(Contabilidad, record_id)
            if not record:
                raise ValueError(f"Registro ID {record_id} no encontrado.")
            record.cliente_id = cliente_id
            record.proceso_id = proceso_id
            record.tipo_id = tipo_id
            record.descripcion = descripcion
            record.monto = valor
            record.fecha = fecha
            session.commit()
            logger.info(f"ContabilidadLogic: Registro actualizado ID={record_id}")
            return True

    def delete_contabilidad_record(self, record_id: int) -> bool:
        with self.db_manager() as session:
            record = session.get(Contabilidad, record_id)
            if not record:
                raise ValueError(f"Registro ID {record_id} no encontrado.")
            session.delete(record)
            session.commit()
            logger.info(f"ContabilidadLogic: Registro eliminado ID={record_id}")
            return True

    # -------------------------------
    # Consultas principales
    # -------------------------------

    def get_contabilidad_data(
        self, cliente_id: int = None, proceso_id: int = None
    ) -> List[Tuple]:
        """
        Retorna datos crudos para tabla:
        [(id, cliente, proceso, tipo, desc, valor, fecha), ...]
        """
        with self.db_manager() as session:
            query = (
                session.query(
                    Contabilidad.id,
                    Cliente.nombre,
                    Proceso.radicado,
                    TipoContable.nombre,
                    Contabilidad.descripcion,
                    Contabilidad.monto,
                    Contabilidad.fecha,
                )
                .join(Cliente, Contabilidad.cliente_id == Cliente.id)
                .outerjoin(Proceso, Contabilidad.proceso_id == Proceso.id)
                .join(TipoContable, Contabilidad.tipo_contable_id == TipoContable.id)
            )

            if cliente_id:
                query = query.filter(Contabilidad.cliente_id == cliente_id)
            if proceso_id:
                query = query.filter(Contabilidad.proceso_id == proceso_id)

            results = query.all()
            return [
                (r[0], r[1], r[2] or "", r[3], r[4], r[5], r[6].strftime("%Y-%m-%d"))
                for r in results
            ]

    def get_contabilidad_data_for_display(
        self,
        cliente_id: int = None,
        proceso_id: int = None,
        search_term: str = None,
        tipo_contable_id: int = None,
    ) -> List[Tuple]:
        """
        Retorna datos para mostrar en la UI, con filtros extra.
        Permite buscar por cliente_id exacto o por nombre de cliente.
        """
        with self.db_manager() as session:
            query = (
                session.query(
                    Contabilidad.id,
                    Cliente.nombre,
                    Proceso.radicado,
                    TipoContable.nombre,
                    Contabilidad.descripcion,
                    Contabilidad.monto,
                    Contabilidad.fecha,
                )
                .join(Cliente, Contabilidad.cliente_id == Cliente.id)
                .outerjoin(Proceso, Contabilidad.proceso_id == Proceso.id)
                .join(TipoContable, Contabilidad.tipo_contable_id == TipoContable.id)
            )

            # 📌 Filtros directos
            if cliente_id:
                query = query.filter(Contabilidad.cliente_id == cliente_id)
            if proceso_id:
                query = query.filter(Contabilidad.proceso_id == proceso_id)
            if tipo_contable_id:
                query = query.filter(Contabilidad.tipo_contable_id == tipo_contable_id)

            # 📌 Nuevo: búsqueda flexible de cliente
            if search_term:
                if search_term.isdigit():
                    # 🔎 Buscar por ID exacto del cliente
                    query = query.filter(Cliente.id == int(search_term))
                else:
                    # 🔎 Buscar por nombre de cliente
                    query = query.filter(Cliente.nombre.ilike(f"%{search_term}%"))

            results = query.all()

            # 📌 Preparar resultados para la tabla
            return [
                (
                    r[0],  # ID
                    r[1],  # Cliente.nombre
                    r[2] or "",  # Proceso.radicado (puede ser None)
                    r[3],  # TipoContable.nombre
                    r[4],  # Descripción
                    float(r[5]),  # Monto (float)
                    r[6].strftime("%Y-%m-%d"),  # Fecha formateada
                )
                for r in results
            ]

    def get_summary_data(
        self, cliente_id=None, proceso_id=None, search_term=None, tipo_id=None
    ) -> Dict[str, float]:
        """
        Calcula totales de ingresos y gastos con filtros.
        """
        records = self.get_contabilidad_data_for_display(
            cliente_id, proceso_id, search_term, tipo_id
        )
        total_ingresos, total_gastos = 0.0, 0.0
        for rec in records:
            valor = rec[5]
            tipo_str = str(rec[3]).lower()
            if "ingreso" in tipo_str:
                total_ingresos += valor
            else:
                total_gastos += valor
        return {
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "saldo": total_ingresos - total_gastos,
        }

    # -------------------------------
    # Utilidades
    # -------------------------------

    def get_record_by_id_for_display(self, record_id: int) -> Optional[Tuple]:
        """
        Obtiene un solo registro formateado para edición.
        """
        with self.db_manager() as session:
            query = (
                session.query(
                    Contabilidad.id,
                    Cliente.nombre,
                    Proceso.radicado,
                    TipoContable.nombre,
                    Contabilidad.descripcion,
                    Contabilidad.monto,
                    Contabilidad.fecha,
                )
                .join(Cliente, Contabilidad.cliente_id == Cliente.id)
                .outerjoin(Proceso, Contabilidad.proceso_id == Proceso.id)
                .join(TipoContable, Contabilidad.tipo_contable_id == TipoContable.id)
            )

            if not rec:
                return None
            return (
                rec[0],
                rec[1],
                rec[2] or "",
                rec[3],
                rec[4],
                float(rec[5]),
                rec[6].strftime("%Y-%m-%d"),
            )

    def get_records_by_ids(self, record_ids: List[int]) -> List[Tuple]:
        """
        Obtiene varios registros por IDs.
        """
        with self.db_manager() as session:
            query = (
                session.query(
                    Contabilidad.id,
                    Cliente.nombre,
                    Proceso.radicado,
                    TipoContable.nombre,
                    Contabilidad.descripcion,
                    Contabilidad.monto,
                    Contabilidad.fecha,
                )
                .join(Cliente, Contabilidad.cliente_id == Cliente.id)
                .outerjoin(Proceso, Contabilidad.proceso_id == Proceso.id)
                .join(TipoContable, Contabilidad.tipo_contable_id == TipoContable.id)
            )

            return [
                (
                    r[0],
                    r[1],
                    r[2] or "",
                    r[3],
                    r[4],
                    float(r[5]),
                    r[6].strftime("%Y-%m-%d"),
                )
                for r in results
            ]

    def get_tipos_contables(self) -> List[TipoContable]:
        """
        Retorna la lista completa de tipos contables.
        """
        with self.db_manager() as session:
            return session.query(TipoContable).all()

    def get_procesos_by_client(self, cliente_id: int) -> List[Tuple[int, str]]:
        """
        Retorna procesos asociados a un cliente.
        """
        with self.db_manager() as session:
            procesos = (
                session.query(Proceso).filter(Proceso.cliente_id == cliente_id).all()
            )
            return [(p.id, p.radicado) for p in procesos]
