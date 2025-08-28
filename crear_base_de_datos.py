# crear_base_de_datos.py
import sys
import os
import logging

# Añade la ruta del proyecto para que las importaciones funcionen
sys.path.insert(0, os.getcwd())

from SELECTA_SCAM.utils.db_manager import create_all_tables, get_db_session
from SELECTA_SCAM.db.models import TipoContable

logging.basicConfig(level=logging.INFO, format='%(message)s')

def inicializar_datos():
    """
    Crea todas las tablas e inserta los datos iniciales necesarios.
    """
    create_all_tables()
    
    session = get_db_session()
    try:
        if session.query(TipoContable).count() == 0:
            print("Inicializando datos en la tabla tipos_contables...")
            tipos = [
                TipoContable(nombre="Ingreso por Servicios", es_ingreso=True),
                TipoContable(nombre="Ingreso por Honorarios", es_ingreso=True),
                # ... (añade todos los demás tipos que necesites) ...
                TipoContable(nombre="Gasto Operativo", es_ingreso=False),
            ]
            session.bulk_save_objects(tipos)
            session.commit()
            print("Datos iniciales de tipos_contables creados.")
        else:
            print("La tabla tipos_contables ya contiene datos.")
            
    except Exception as e:
        print(f"Ocurrió un error al inicializar los datos: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    db_file = os.path.join('SELECTA_SCAM', 'data', 'base_oficial.db')
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Base de datos antigua '{db_file}' eliminada.")
        
    inicializar_datos()
    print("\n¡Base de datos lista! Ahora puedes crear tu usuario.")