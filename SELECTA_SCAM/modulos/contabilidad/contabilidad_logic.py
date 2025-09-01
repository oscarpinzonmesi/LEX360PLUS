import logging
from datetime import date
from typing import List, Optional, Tuple, Dict
from datetime import datetime, date
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
    ) -> int:
        """
        Crea un registro de contabilidad y devuelve su ID.
        Devuelve un entero para evitar problemas de Lazy Loading / objetos desconectados.
        """
        # Por si llega datetime/QDate, lo normalizamos a date
        if isinstance(fecha, datetime):
            fecha = fecha.date()
        elif hasattr(fecha, "toPyDate"):
            fecha = fecha.toPyDate()

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
            session.flush()  # asegura PK sin disparar __repr__
            new_id = record.id
            session.commit()
            logger.info("ContabilidadLogic: Registro añadido ID=%s", new_id)
            return new_id

    def mover_a_papelera(self, ids: List[int]) -> int:
        with self.db_manager() as session:
            count = (
                session.query(Contabilidad)
                .filter(Contabilidad.id.in_(ids), Contabilidad.eliminado == False)
                .update({Contabilidad.eliminado: True}, synchronize_session=False)
            )
            session.commit()
            return count

    def restaurar_desde_papelera(self, ids: List[int]) -> int:
        with self.db_manager() as session:
            count = (
                session.query(Contabilidad)
                .filter(Contabilidad.id.in_(ids), Contabilidad.eliminado == True)
                .update({Contabilidad.eliminado: False}, synchronize_session=False)
            )
            session.commit()
            return count

    def eliminar_definitivo(self, ids: List[int]) -> int:
        with self.db_manager() as session:
            rows = session.query(Contabilidad).filter(Contabilidad.id.in_(ids)).all()
            count = len(rows)
            for r in rows:
                session.delete(r)
            session.commit()
            return count

    def get_registros_en_papelera(self):
        with self.db_manager() as session:
            return (
                session.query(Contabilidad).filter(Contabilidad.papelera == True).all()
            )

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

    def update_contabilidad_record(self, record_id: int, **data) -> bool:
        """
        Actualiza un registro de Contabilidad.
        Acepta claves nuevas y alias viejos:
        - tipo_contable_id  (alias: tipo_id)
        - monto             (alias: valor)
        - fecha / fecha_pago como date|datetime|str 'YYYY-MM-DD'
        Solo actualiza campos presentes en **data (permite setear None).
        """

        def to_date(v):
            if v is None:
                return None
            if isinstance(v, date):
                # date o datetime -> date
                return v if not isinstance(v, datetime) else v.date()
            if isinstance(v, str) and v.strip():
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(v.strip(), fmt).date()
                    except ValueError:
                        pass
            return None

        def to_float(v):
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return float(v)
            if isinstance(v, str):
                cleaned = v.replace("$", "").replace(",", "").strip()
                try:
                    return float(cleaned)
                except ValueError:
                    return None
            return None

        with self.db_manager() as session:
            obj = session.get(Contabilidad, record_id)
            if not obj:
                raise ValueError(f"Contabilidad ID {record_id} no existe")

            # Normalización de claves (alias → clave real)
            normalized = {}

            # claves directas si vienen
            for key in (
                "cliente_id",
                "proceso_id",
                "tipo_contable_id",
                "descripcion",
                "monto",
                "fecha",
                "metodo_pago",
                "referencia_pago",
                "esta_pagado",
                "fecha_pago",
                "is_active",
            ):
                if key in data:
                    normalized[key] = data[key]

            # alias compatibles
            if "tipo_contable_id" not in normalized and "tipo_id" in data:
                normalized["tipo_contable_id"] = data["tipo_id"]
            if "monto" not in normalized and "valor" in data:
                normalized["monto"] = data["valor"]

            # conversiones
            if "monto" in normalized:
                normalized["monto"] = to_float(normalized["monto"])
            if "fecha" in normalized:
                normalized["fecha"] = to_date(normalized["fecha"])
            if "fecha_pago" in normalized:
                normalized["fecha_pago"] = to_date(normalized["fecha_pago"])

            # aplicar cambios (inclusive None si la clave fue provista)
            for k, v in normalized.items():
                setattr(obj, k, v)

            session.add(obj)
            session.commit()
            return True

    def get_contabilidad_data_for_display(
        self,
        cliente_id: int = None,
        proceso_id: int = None,
        search_term: str = None,
        tipo_contable_id: int = None,
        mostrando_papelera: bool = False,  # 🔎 nuevo
    ) -> List[Tuple]:
        """
        Retorna datos listos para la tabla.
        - search_term: numérico → Contabilidad.id; texto → Cliente.nombre
        - mostrando_papelera: True => is_active=False, False => is_active=True
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

            # Activos vs Papelera
            if mostrando_papelera:
                query = query.filter(Contabilidad.eliminado == True)
            else:
                query = query.filter(Contabilidad.eliminado == False)

            # Filtros directos (cliente_id se ignora si hay search_term para evitar doble filtro)
            if cliente_id and not search_term:
                query = query.filter(Contabilidad.cliente_id == cliente_id)
            if proceso_id:
                query = query.filter(Contabilidad.proceso_id == proceso_id)
            if tipo_contable_id:
                query = query.filter(Contabilidad.tipo_contable_id == tipo_contable_id)

            # Búsqueda flexible
            if search_term:
                if search_term.isdigit():
                    query = query.filter(
                        Contabilidad.id == int(search_term)
                    )  # ID del registro contable
                else:
                    query = query.filter(Cliente.nombre.ilike(f"%{search_term}%"))

            results = query.all()
            return [
                (
                    r[0],  # ID (contabilidad)
                    r[1],  # Cliente
                    r[2] or "",  # Proceso (radicado)
                    r[3],  # Tipo contable (nombre)
                    r[4],  # Descripción
                    float(r[5]),  # Monto
                    r[6].strftime("%Y-%m-%d"),  # Fecha
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

    def get_contabilidad_record_raw(self, record_id: int):
        """
        Devuelve el registro de contabilidad en el mismo orden 'display' que usa el diálogo:
        [0]=Contabilidad.id
        [1]=Cliente.nombre
        [2]=Proceso.radicado  (puede ser None)
        [3]=TipoContable.nombre
        [4]=Contabilidad.descripcion
        [5]=Contabilidad.monto (float)
        [6]=Fecha como 'YYYY-MM-DD' (str)
        Y añade extras al final para 'fallback' por ID:
        [7]=cliente_id
        [8]=proceso_id
        [9]=tipo_contable_id
        """
        with self.db_manager() as session:
            row = (
                session.query(
                    Contabilidad.id,  # [0]
                    Cliente.nombre.label("cliente_nombre"),  # [1]
                    Proceso.radicado.label("proceso_radicado"),  # [2] (outer)
                    TipoContable.nombre.label("tipo_nombre"),  # [3]
                    Contabilidad.descripcion,  # [4]
                    Contabilidad.monto,  # [5]
                    Contabilidad.fecha,  # [6] (datetime/date)
                    Contabilidad.cliente_id,  # [7]
                    Contabilidad.proceso_id,  # [8]
                    Contabilidad.tipo_contable_id,  # [9]
                )
                .join(Cliente, Contabilidad.cliente_id == Cliente.id)
                .outerjoin(Proceso, Contabilidad.proceso_id == Proceso.id)
                .join(TipoContable, Contabilidad.tipo_contable_id == TipoContable.id)
                .filter(Contabilidad.id == record_id)
                .first()
            )

            if not row:
                return None

            # Normaliza tipos: monto a float y fecha a 'YYYY-MM-DD'
            monto = float(row[5]) if row[5] is not None else 0.0
            fecha_val = row[6]
            if isinstance(fecha_val, (datetime, date)):
                fecha_str = fecha_val.strftime("%Y-%m-%d")
            else:
                # Si ya viene como string, lo dejamos tal cual
                fecha_str = str(fecha_val) if fecha_val is not None else None

            return (
                row[0],  # id
                row[1],  # cliente_nombre
                row[2],  # proceso_radicado (puede ser None)
                row[3],  # tipo_nombre
                row[4],  # descripcion
                monto,  # monto float
                fecha_str,  # fecha 'YYYY-MM-DD'
                row[7],  # cliente_id
                row[8],  # proceso_id
                row[9],  # tipo_contable_id
            )

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
