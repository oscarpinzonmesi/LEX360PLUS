# SELECTA_SCAM/modulos/procesos/procesos_db.py

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import date
from sqlalchemy import or_

# --- INICIO DE CORRECCIONES ---
# Importaciones del nuevo sistema unificado
from ...db.models import Proceso, Cliente
from ...utils.db_manager import get_db_session
# --- FIN DE CORRECCIONES ---

logger = logging.getLogger(__name__)

class ProcesosDB:
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
            self.logger.error("Error en transacción de ProcesosDB, haciendo rollback: %s", e, exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_procesos(self) -> list[Proceso]:
        """Obtiene todos los procesos activos."""
        with self.get_session() as session:
            return session.query(Proceso).filter(Proceso.eliminado == False).order_by(Proceso.fecha_inicio.desc()).all()

    def get_proceso_by_id(self, proceso_id: int) -> Proceso | None:
        """Obtiene un proceso por su ID."""
        with self.get_session() as session:
            return session.query(Proceso).filter(Proceso.id == proceso_id, Proceso.eliminado == False).first()

    def add_proceso(self, **data) -> Proceso | None:
        """Añade un nuevo proceso a la base de datos."""
        with self.get_session() as session:
            # Verificar si el cliente existe
            cliente_id = data.get("cliente_id")
            if not session.query(Cliente).filter(Cliente.id == cliente_id, Cliente.eliminado == False).first():
                self.logger.warning(f"No se puede agregar proceso. Cliente con ID {cliente_id} no encontrado.")
                return None
            
            # Verificar si el radicado ya existe
            radicado = data.get("radicado")
            if session.query(Proceso).filter(Proceso.radicado == radicado).first():
                self.logger.warning(f"Ya existe un proceso con el radicado '{radicado}'.")
                return None

            new_proceso = Proceso(**data, fecha_creacion=date.today(), eliminado=False)
            session.add(new_proceso)
            session.flush()
            return new_proceso

    def update_proceso(self, proceso_id: int, **data) -> Proceso | None:
        """Actualiza un proceso existente."""
        with self.get_session() as session:
            proceso = session.query(Proceso).filter(Proceso.id == proceso_id, Proceso.eliminado == False).first()
            if proceso:
                for key, value in data.items():
                    setattr(proceso, key, value)
                return proceso
            return None

    def delete_proceso(self, proceso_id: int) -> bool:
        """Marca un proceso como eliminado lógicamente."""
        with self.get_session() as session:
            proceso = session.query(Proceso).filter(Proceso.id == proceso_id).first()
            if proceso:
                proceso.eliminado = True
                return True
            return False
            
    def restaurar_proceso(self, proceso_id: int) -> bool:
        """Restaura un proceso marcado como eliminado."""
        with self.get_session() as session:
            proceso = session.query(Proceso).filter(Proceso.id == proceso_id).first()
            if proceso:
                proceso.eliminado = False
                return True
            return False

    def eliminar_proceso_definitivo(self, proceso_id: int) -> bool:
        """Elimina un proceso de forma permanente."""
        with self.get_session() as session:
            proceso = session.query(Proceso).filter(Proceso.id == proceso_id).first()
            if proceso:
                session.delete(proceso)
                return True
            return False

    def buscar_procesos(self, query: str) -> list[Proceso]:
        """Busca procesos por diferentes criterios."""
        if not query:
            return self.get_all_procesos()

        with self.get_session() as session:
            search_pattern = f"%{query}%"
            try:
                query_id = int(query)
            except ValueError:
                query_id = -1

            return session.query(Proceso).join(Cliente).filter(
                or_(
                    Proceso.radicado.ilike(search_pattern),
                    Proceso.tipo.ilike(search_pattern),
                    Proceso.estado.ilike(search_pattern),
                    Proceso.juzgado.ilike(search_pattern),
                    Cliente.nombre.ilike(search_pattern),
                    Proceso.id == query_id
                )
            ).all()
            
    def get_procesos_by_cliente_id(self, cliente_id: int) -> list[Proceso]:
        """Obtiene todos los procesos activos de un cliente específico."""
        with self.get_session() as session:
            return session.query(Proceso).filter(
                Proceso.cliente_id == cliente_id,
                Proceso.eliminado == False
            ).all()