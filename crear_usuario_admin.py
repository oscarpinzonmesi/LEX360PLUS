# crear_usuario_admin.py (actualizado)
import sys, os
from datetime import date
from SELECTA_SCAM.utils.db_manager import get_db_session
from SELECTA_SCAM.db.models import Usuario
from SELECTA_SCAM.utils.hashing import hash_password  # ya lo tienes en utils


def crear_usuario_admin():
    session = get_db_session()
    try:
        if session.query(Usuario).filter_by(username="admin").first():
            print("⚠️ El usuario 'admin' ya existe.")
            return

        user = Usuario(
            username="admin",
            password_hash=hash_password("admin123"),
            email="admin@example.com",
            activo=True,
            es_admin=True,
            fecha_creacion=date.today(),
            eliminado=False,
        )
        session.add(user)
        session.commit()
        print("✅ Usuario 'admin' creado con éxito.")
    except Exception as e:
        print("❌ Error al crear admin:", e)
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    crear_usuario_admin()
