# SELECTA_SCAM/utils/db_manager.py
import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..db.base import Base # Importa la Base de los modelos

# --- CONFIGURACIÓN CENTRALIZADA DE LA RUTA DE LA BASE DE DATOS ---
# Esto asegura que la base de datos siempre se cree en el lugar correcto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DATABASE_PATH = os.path.join(project_root, 'SELECTA_SCAM', 'data', 'base_oficial.db')
db_dir = os.path.dirname(DATABASE_PATH)
os.makedirs(db_dir, exist_ok=True)
# --- FIN DE LA CONFIGURACIÓN ---

engine = create_engine(f"sqlite:///{DATABASE_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_all_tables():
    """
    Función global para crear todas las tablas definidas en los modelos.
    """
    logger.info("Creando todas las tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas exitosamente.")

def get_db_session():
    """
    Función global para obtener una nueva sesión de base de datos.
    """
    return SessionLocal()