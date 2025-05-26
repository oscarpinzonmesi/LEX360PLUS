import sqlite3

DATABASE_PATH = "data/base_datos.db"

def insertar_usuario():
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    # Usuario de prueba
    usuario = "admin"
    contrasena = "admin123"  # O la que tú quieras
    rol = "administrador"

    cur.execute("INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)",
                (usuario, contrasena, rol))

    conn.commit()
    conn.close()
    print("✅ Usuario de prueba agregado correctamente.")

if __name__ == "__main__":
    insertar_usuario()
