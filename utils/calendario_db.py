import sqlite3

class CalendarioDB:
    def __init__(self, conectar):
        self.conectar = conectar

    def obtener_eventos_por_proceso(self, proceso_id):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, titulo, descripcion, fecha
                FROM calendario
                WHERE proceso_id = ?
                ORDER BY fecha
            """, (proceso_id,))
            return cursor.fetchall()

    def agregar_evento(self, proceso_id, titulo, descripcion, fecha):
        with self.conectar() as conn:
            conn.execute("""
                INSERT INTO calendario (proceso_id, titulo, descripcion, fecha)
                VALUES (?, ?, ?, ?)
            """, (proceso_id, titulo, descripcion, fecha))

    def eliminar_evento(self, evento_id):
        with self.conectar() as conn:
            conn.execute("DELETE FROM calendario WHERE id = ?", (evento_id,))
