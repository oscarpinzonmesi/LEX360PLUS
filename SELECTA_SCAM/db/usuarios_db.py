# SELECTA_SCAM/db/usuarios_db.py

import logging
from .models import Usuario
from sqlalchemy.exc import SQLAlchemyError

# Correcto (ruta completa desde la raíz del paquete)
from SELECTA_SCAM.usuarios.seguridad import check_password, hash_password
logger = logging.getLogger(__name__)

class UsuariosDB:
    def __init__(self):
        self.logger = logger

    def verificar_usuario(self, session, username, password):
        """Verifica las credenciales del usuario usando la sesión proporcionada."""
        try:
            usuario = session.query(Usuario).filter(Usuario.username == username).first()
            if usuario and check_password(usuario.password_hash, password) and usuario.activo:
                role = 'admin' if usuario.es_admin else 'user'
                return True, role
            return False, None
        except Exception as e:
            self.logger.error(f"Error al verificar usuario: {e}")
            return False, None

    def usuario_existe(self, session, username: str) -> bool:
        """Verifica si un nombre de usuario ya existe en la DB usando la sesión proporcionada."""
        try:
            return session.query(Usuario).filter(Usuario.username == username).count() > 0
        except Exception as e:
            self.logger.error(f"Error al verificar si el usuario '{username}' existe: {e}")
            return False

    def insertar_usuario(self, session, username, password_hash, es_admin):
        """Inserta un nuevo usuario en la DB usando la sesión proporcionada."""
        try:
            nuevo_usuario = Usuario(
                username=username,
                password_hash=password_hash,
                es_admin=es_admin,
                activo=True
            )
            session.add(nuevo_usuario)
            return True
        except Exception as e:
            self.logger.error(f"Error al insertar el usuario '{username}': {e}")
            return False

    def actualizar_contrasena(self, session, username: str, new_plain_password: str):
        """Actualiza la contraseña de un usuario usando la sesión proporcionada."""
        try:
            user = session.query(Usuario).filter_by(username=username).first()
            if user:
                hashed_new_password = hash_password(new_plain_password)
                user.password_hash = hashed_new_password
                return True
            return False
        except SQLAlchemyError as e:
            self.logger.error(f"Error al actualizar contraseña: {e}")
            return False

    def get_all_users(self, session):
        """Obtiene todos los usuarios usando la sesión proporcionada."""
        try:
            return session.query(Usuario.id, Usuario.username, Usuario.es_admin, Usuario.activo).all()
        except SQLAlchemyError as e:
            self.logger.error(f"Error en UsuariosDB.get_all_users: {e}")
            return []

    def get_user_by_id(self, session, user_id: int):
        """Obtiene un usuario por ID usando la sesión proporcionada."""
        try:
            return session.query(Usuario).get(user_id)
        except SQLAlchemyError as e:
            self.logger.error(f"Error en UsuariosDB.get_user_by_id (ID: {user_id}): {e}")
            return None

    def delete_user(self, session, user_id: int):
        """Realiza una eliminación lógica de un usuario usando la sesión proporcionada."""
        try:
            user = session.query(Usuario).get(user_id)
            if user:
                user.activo = False
                self.logger.info(f"Usuario ID {user_id} marcado como inactivo.")
                return True
            return False
        except SQLAlchemyError as e:
            self.logger.error(f"Error al eliminar lógicamente al usuario: {e}")
            return False

    def update_user_role(self, session, user_id: int, new_role: str):
        """Actualiza el rol de un usuario usando la sesión proporcionada."""
        try:
            user = session.query(Usuario).get(user_id)
            if user:
                if new_role.lower() == 'admin':
                    user.es_admin = True
                elif new_role.lower() == 'user':
                    user.es_admin = False
                else:
                    self.logger.warning(f"Rol '{new_role}' no válido.")
                    return False
                return True
            return False
        except SQLAlchemyError as e:
            self.logger.error(f"Error al actualizar rol de usuario: {e}")
            return False