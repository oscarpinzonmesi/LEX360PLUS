# SELECTA_SCAM/modulos/calendario/calendario_db.py

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, date

# --- INICIO DE CORRECCIONES ---
# Importaciones del nuevo sistema unificado
from ...db.models import Evento
from ...utils.db_manager import get_db_session
# --- FIN DE CORRECCIONES ---

logger = logging.getLogger(__name__)

class CalendarioDB:
    def __init__(self):
        """El constructor ya no necesita argumentos."""
        self.logger = logger

    @contextmanager
    def get_session(self):
        """
        Usa la sesión global del db_manager para garantizar una única conexión.
        """
        session = get_db_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            self.logger.error("Error en transacción de CalendarioDB, haciendo rollback: %s", e, exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    def add_evento(self, proceso_id: int, titulo: str, descripcion: str, fecha_evento: datetime) -> int | None:
        """Añade un nuevo evento a la base de datos."""
        with self.get_session() as session:
            nuevo_evento = Evento(
                proceso_id=proceso_id,
                titulo=titulo,
                descripcion=descripcion,
                fecha_evento=fecha_evento
            )
            session.add(nuevo_evento)
            session.flush()
            return nuevo_evento.id

    def get_eventos_by_date(self, fecha: date) -> list[Evento]:
        """Obtiene todos los eventos para una fecha específica."""
        with self.get_session() as session:
            start_of_day = datetime.combine(fecha, datetime.min.time())
            end_of_day = datetime.combine(fecha, datetime.max.time())
            return session.query(Evento).filter(
                Evento.fecha_evento >= start_of_day,
                Evento.fecha_evento <= end_of_day
            ).all()

    def update_evento(self, evento_id: int, **data) -> bool:
        """Actualiza un evento existente."""
        with self.get_session() as session:
            evento = session.query(Evento).get(evento_id)
            if evento:
                for key, value in data.items():
                    if value is not None:
                        setattr(evento, key, value)
                return True
            return False

    def delete_evento(self, evento_id: int) -> bool:
        """Elimina un evento por su ID."""
        with self.get_session() as session:
            evento = session.query(Evento).get(evento_id)
            if evento:
                session.delete(evento)
                return True
            return False

    def get_all_eventos(self) -> list[Evento]:
        """Obtiene todos los eventos, ordenados por fecha."""
        with self.get_session() as session:
            return session.query(Evento).order_by(Evento.fecha_evento.asc()).all()

    def get_eventos_between_dates(self, start_date: date, end_date: date) -> list[Evento]:
        """Obtiene todos los eventos dentro de un rango de fechas."""
        with self.get_session() as session:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())
            return session.query(Evento).filter(
                and_(Evento.fecha_evento >= start_dt, Evento.fecha_evento <= end_dt)
            ).order_by(Evento.fecha_evento.asc()).all()