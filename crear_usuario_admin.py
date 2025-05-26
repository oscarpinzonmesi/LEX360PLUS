import sqlite3
import bcrypt

DATABASE_PATH = "data/base_datos.db"  # Ajusta si usas otro nombre o ruta

def crear_usuario_admin():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    username = "admin"
    password = "admin123"
    role = "administrador"

    # Encriptar la contraseña correctamente
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        conn.commit()
        print("✅ Usuario 'admin' creado con éxito.")
    except sqlite3.IntegrityError:
        print("⚠️ El usuario 'admin' ya existe.")

    conn.close()

if __name__ == "__main__":
    crear_usuario_admin()
