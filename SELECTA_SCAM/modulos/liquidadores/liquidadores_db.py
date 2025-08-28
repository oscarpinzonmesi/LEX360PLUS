# SELECTA_SCAM/modulos/liquidadores/liquidadores_db.py

import logging
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_

# --- INICIO DE CORRECCIONES ---
# Importaciones del nuevo sistema unificado
from ...db.models import Liquidador
from ...utils.db_manager import get_db_session
# --- FIN DE CORRECCIONES ---

logger = logging.getLogger(__name__)

class LiquidadoresDB:
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
            self.logger.error("Error en transacción de LiquidadoresDB, haciendo rollback: %s", e, exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    def obtener_herramientas_liquidacion(self) -> list[Liquidador]:
        """Obtiene la lista de todas las herramientas de liquidación disponibles."""
        with self.get_session() as session:
            return session.query(Liquidador).all()

    def agregar_herramienta_liquidacion(self, **data) -> bool:
        """Inserta una nueva herramienta de liquidación en la base de datos."""
        with self.get_session() as session:
            nueva_herramienta = Liquidador(**data)
            session.add(nueva_herramienta)
            return True

    def actualizar_herramienta_liquidacion(self, herramienta_id: int, **data) -> bool:
        """Actualiza los datos de una herramienta de liquidación existente por su ID."""
        with self.get_session() as session:
            herramienta = session.query(Liquidador).get(herramienta_id)
            if not herramienta:
                self.logger.warning(f"Herramienta de liquidación con ID {herramienta_id} no encontrada.")
                return False
            
            for key, value in data.items():
                if hasattr(herramienta, key) and value is not None:
                    setattr(herramienta, key, value)
            return True

    def eliminar_herramienta_liquidacion(self, herramienta_id: int) -> bool:
        """Elimina una herramienta de liquidación de la base de datos por su ID."""
        with self.get_session() as session:
            herramienta = session.query(Liquidador).get(herramienta_id)
            if not herramienta:
                self.logger.warning(f"Herramienta de liquidación con ID {herramienta_id} no encontrada.")
                return False
            
            session.delete(herramienta)
            return True

    def obtener_herramienta_por_id(self, herramienta_id: int) -> Liquidador | None:
        """Obtiene una herramienta de liquidación específica por su ID."""
        with self.get_session() as session:
            return session.query(Liquidador).get(herramienta_id)

    def buscar_herramientas_liquidacion(self, nombre_o_descripcion: str = None, area_derecho: str = None) -> list[Liquidador]:
        """Busca herramientas de liquidación que coincidan con los criterios especificados."""
        with self.get_session() as session:
            query = session.query(Liquidador)
            if nombre_o_descripcion:
                search_term = f"%{nombre_o_descripcion}%"
                query = query.filter(
                    (Liquidador.nombre_herramienta.ilike(search_term)) |
                    (Liquidador.descripcion.ilike(search_term))
                )
            if area_derecho:
                query = query.filter(Liquidador.area_derecho.ilike(f"%{area_derecho}%"))
            return query.all()