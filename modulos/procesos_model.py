class ProcesosModel:
    def __init__(self, db):
        self.db = db

    def obtener_todos(self):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tipo, descripcion, cliente_id, estado, fecha_inicio, fecha_fin FROM procesos")
        return cursor.fetchall()

    def obtener_por_id(self, proceso_id):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procesos WHERE id = ?", (proceso_id,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado

    def insertar(self, cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin=None):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO procesos (cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id



    def actualizar(self, proceso_id, cliente_id, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE procesos
            SET cliente_id = ?, tipo = ?, descripcion = ?, juzgado = ?, estado = ?, fecha_inicio = ?, fecha_fin = ?
            WHERE id = ?
        ''', (cliente_id, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin, proceso_id))
        conn.commit()
        conn.close()




    def eliminar(self, proceso_id):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM procesos WHERE id = ?", (proceso_id,))
        conn.commit()
        conn.close()

    def obtener_radicado_por_id(self, proceso_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT descripcion FROM procesos WHERE id = ?", (proceso_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else ""
