# SELECTA_SCAM/usuarios/insertar_usuario.py
import sys
import os
import getpass

# Añadir la ruta del proyecto
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
sys.path.insert(0, project_root)

# Importaciones correctas y absolutas
from SELECTA_SCAM.utils.db_manager import get_db_session
from SELECTA_SCAM.db.usuarios_db import UsuariosDB
from SELECTA_SCAM.usuarios.seguridad import hash_password

def insertar_nuevo_usuario():
    print("--- Insertar Nuevo Usuario ---")
    username = input("Ingrese el nombre de usuario: ")
    password = getpass.getpass("Ingrese la contraseña: ")
    es_admin_str = input("¿Es administrador? (s/n): ").lower()
    es_admin = es_admin_str == 's'

    usuarios_db = UsuariosDB()
    session = get_db_session()
    
    try:
        if usuarios_db.usuario_existe(session, username):
            print(f"Error: El usuario '{username}' ya existe.")
            return

        hashed_pwd = hash_password(password)

        if usuarios_db.insertar_usuario(session, username, hashed_pwd, es_admin):
            session.commit() # ¡Guardamos el cambio!
            print(f"Usuario '{username}' creado exitosamente.")
        else:
            session.rollback()
            print(f"Error al crear el usuario '{username}'.")
            
    finally:
        session.close()

if __name__ == '__main__':
    insertar_nuevo_usuario()