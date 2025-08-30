from contextlib import contextmanager
from sqlalchemy.orm import joinedload
from sqlalchemy import func, or_
from ...db.models import Contabilidad, Cliente, Proceso
from ...utils.db_manager import get_db_session

class ContabilidadDB:
    def __init__(self):
        pass

    @contextmanager
    def get_session(self):
        session = get_db_session()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_filtered_contabilidad_records(self, cliente_id=None, proceso_id=None, search_term=None, tipo_id=None):
        with self.get_session() as session:
            session.expire_all()
            query = session.query(Contabilidad).options(
                joinedload(Contabilidad.cliente),
                joinedload(Contabilidad.proceso),
                joinedload(Contabilidad.tipo)
            )
            if cliente_id:
                query = query.filter(Contabilidad.cliente_id == cliente_id)
            if proceso_id:
                query = query.filter(Contabilidad.proceso_id == proceso_id)
            if tipo_id:
                query = query.filter(Contabilidad.tipo_contable_id == tipo_id)
            if search_term:
                search_pattern = f"%{search_term.lower()}%"
                try:
                    record_id_int = int(search_term)
                    query = query.filter(
                        or_(
                            Contabilidad.id == record_id_int,
                            func.lower(Contabilidad.descripcion).like(search_pattern),
                            func.lower(Cliente.nombre).like(search_pattern)
                        )
                    )
                except ValueError:
                    query = query.filter(
                        or_(
                            func.lower(Contabilidad.descripcion).like(search_pattern),
                            func.lower(Cliente.nombre).like(search_pattern)
                        )
                    )
            return query.order_by(Contabilidad.fecha.desc()).all()

    def get_contabilidad_records_by_ids(self, record_ids: list):
        with self.get_session() as session:
            return session.query(Contabilidad).filter(Contabilidad.id.in_(record_ids)).options(
                joinedload(Contabilidad.cliente),
                joinedload(Contabilidad.proceso)
            ).all()

    def get_record_by_id(self, record_id: int):
        with self.get_session() as session:
            return session.query(Contabilidad).options(
                joinedload(Contabilidad.cliente),
                joinedload(Contabilidad.proceso)
            ).filter(Contabilidad.id == record_id).first()

    def delete_record(self, record_id: int) -> bool:
        with self.get_session() as session:
            record = session.get(Contabilidad, record_id)
            if record:
                session.delete(record)
                return True
            return False
