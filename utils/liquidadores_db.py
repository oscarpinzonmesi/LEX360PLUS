import sqlite3

class LiquidadoresDB:
    def __init__(self, conectar):
        self.conectar = conectar

    def obtener_liquidadores(self):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre FROM liquidadores")
            return cursor.fetchall()

    def agregar_liquidador(self, nombre):
        with self.conectar() as conn:
            conn.execute("INSERT INTO liquidadores (nombre) VALUES (?)", (nombre,))

    def eliminar_liquidador(self, liquidador_id):
        with self.conectar() as conn:
            conn.execute("DELETE FROM liquidadores WHERE id = ?", (liquidador_id,))
