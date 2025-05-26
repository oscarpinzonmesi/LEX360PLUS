import sqlite3
import bcrypt
from .db_manager import DBManager

def verificar_usuario(username, password):
    db = DBManager()
    conn = db.conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT contrasena, rol FROM usuarios WHERE usuario = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        if bcrypt.checkpw(password.encode(), row[0].encode()):
            return True, row[1]
    return False, None



# Clase para manejar otras operaciones de usuarios
class UsuariosDB:
    def __init__(self, conectar):
        self.conectar = conectar

    def usuario_existe(self, usuario):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,))
            return cursor.fetchone() is not None

    def insertar_usuario(self, usuario, contrasena, rol):
        hashed = bcrypt.hashpw(contrasena.encode(), bcrypt.gensalt()).decode()
        with self.conectar() as conn:
            conn.execute(
                "INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)",
                (usuario, hashed, rol)
            )

    def update_password(self, usuario, nueva_contra):
        hashed = bcrypt.hashpw(nueva_contra.encode(), bcrypt.gensalt()).decode()
        with self.conectar() as conn:
            conn.execute(
                "UPDATE usuarios SET contrasena = ? WHERE usuario = ?", (hashed, usuario)
            )
