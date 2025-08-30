# SELECTA_SCAM/modulos/contabilidad/contabilidad_db.py

from sqlalchemy.exc import SQLAlchemyError
from SELECTA_SCAM.utils.db_manager import get_session
from SELECTA_SCAM.db.base import Base
from SELECTA_SCAM.db.models import AsientoContable, CuentaContable  # ajusta según tus modelos


class ContabilidadDB:
    """
    Clase encargada de la lógica de acceso a datos para el módulo de contabilidad.
    Ahora centralizada con db_manager (sin duplicar engine ni Session).
    """

    def __init__(self):
        pass  # no necesitamos engine ni session aquí, todo pasa por get_session()

    # -------------------------------
    # 📌 Métodos CRUD de CuentaContable
    # -------------------------------
    def add_cuenta(self, cuenta_data: dict):
        try:
            with get_session() as session:
                nueva_cuenta = CuentaContable(**cuenta_data)
                session.add(nueva_cuenta)
                session.commit()
                session.refresh(nueva_cuenta)
                return nueva_cuenta
        except SQLAlchemyError as e:
            raise Exception(f"Error al agregar cuenta: {e}")

    def get_cuenta(self, cuenta_id: int):
        try:
            with get_session() as session:
                return session.get(CuentaContable, cuenta_id)
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener cuenta: {e}")

    def list_cuentas(self):
        try:
            with get_session() as session:
                return session.query(CuentaContable).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al listar cuentas: {e}")

    def delete_cuenta(self, cuenta_id: int):
        try:
            with get_session() as session:
                cuenta = session.get(CuentaContable, cuenta_id)
                if cuenta:
                    session.delete(cuenta)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            raise Exception(f"Error al eliminar cuenta: {e}")

    # -------------------------------
    # 📌 Métodos CRUD de AsientoContable
    # -------------------------------
    def add_asiento(self, asiento_data: dict):
        try:
            with get_session() as session:
                nuevo_asiento = AsientoContable(**asiento_data)
                session.add(nuevo_asiento)
                session.commit()
                session.refresh(nuevo_asiento)
                return nuevo_asiento
        except SQLAlchemyError as e:
            raise Exception(f"Error al agregar asiento: {e}")

    def get_asiento(self, asiento_id: int):
        try:
            with get_session() as session:
                return session.get(AsientoContable, asiento_id)
        except SQLAlchemyError as e:
            raise Exception(f"Error al obtener asiento: {e}")

    def list_asientos(self):
        try:
            with get_session() as session:
                return session.query(AsientoContable).all()
        except SQLAlchemyError as e:
            raise Exception(f"Error al listar asientos: {e}")

    def delete_asiento(self, asiento_id: int):
        try:
            with get_session() as session:
                asiento = session.get(AsientoContable, asiento_id)
                if asiento:
                    session.delete(asiento)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            raise Exception(f"Error al eliminar asiento: {e}")
