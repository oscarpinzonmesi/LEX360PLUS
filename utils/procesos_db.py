import sqlite3

class ProcesosDB:
    def __init__(self, conectar):
        self.conectar = conectar

    def obtener_procesos(self):
        with self.conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.nombre, p.descripcion, p.estado, p.fecha_inicio, p.fecha_cierre,
                       c.nombre AS cliente_nombre
                FROM procesos p
                LEFT JOIN clientes c ON p.cliente_id = c.id
            """)
            return cursor.fetchall()

    def insertar_proceso(self, nombre, descripcion, estado, fecha_inicio, fecha_cierre, cliente_id):
        with self.conectar() as conn:
            conn.execute("""
                INSERT INTO procesos (nombre, descripcion, estado, fecha_inicio, fecha_cierre, cliente_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (nombre, descripcion, estado, fecha_inicio, fecha_cierre, cliente_id))

    def actualizar_proceso(self, id_proceso, nombre, descripcion, estado, fecha_inicio, fecha_cierre, cliente_id):
        with self.conectar() as conn:
            conn.execute("""
                UPDATE procesos
                SET nombre = ?, descripcion = ?, estado = ?, fecha_inicio = ?, fecha_cierre = ?, cliente_id = ?
                WHERE id = ?
            """, (nombre, descripcion, estado, fecha_inicio, fecha_cierre, cliente_id, id_proceso))

    def eliminar_proceso(self, id_proceso):
        with self.conectar() as conn:
            conn.execute("DELETE FROM procesos WHERE id = ?", (id_proceso,))
