import sqlite3
from config import RUTA_BD

class DocumentosDB:
    def __init__(self):
        self.db_path = RUTA_BD

    def _conectar(self):
        """ Método auxiliar para conectar con la base de datos. """
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except sqlite3.Error as e:
            print(f"Error de conexión a la base de datos: {e}")
            return None

    def obtener_documentos_por_proceso(self, proceso_id):
        conn = self._conectar()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("""
            SELECT d.id, d.nombre, c.nombre, p.radicado, p.tipo, d.fecha, d.archivo
            FROM documentos d
            JOIN procesos p ON d.proceso_id = p.id
            JOIN clientes c ON p.cliente_id = c.id
            WHERE d.proceso_id = ? AND d.eliminado = 0
            ORDER BY d.fecha DESC
        """, (proceso_id,))
        resultados = cur.fetchall()
        conn.close()
        return resultados

    def agregar_documento(self, proceso_id, nombre, ruta_archivo, fecha, eliminado=0):
        conn = self._conectar()
        if conn is None:
            return
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documentos (proceso_id, nombre, archivo, fecha, eliminado)
            VALUES (?, ?, ?, ?, ?)
        """, (proceso_id, nombre, ruta_archivo, fecha, eliminado))
        conn.commit()
        conn.close()

    def eliminar_documento(self, documento_id):
        """ Marca un documento como eliminado en lugar de eliminarlo físicamente. """
        conn = self._conectar()
        if conn is None:
            return
        cur = conn.cursor()
        cur.execute("""
            UPDATE documentos 
            SET eliminado = 1 
            WHERE id = ?
        """, (documento_id,))
        conn.commit()
        conn.close()

    def obtener_documentos_por_cliente(self, cliente_id):
        conn = self._conectar()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("""
            SELECT d.id, d.nombre, c.nombre, p.radicado, p.tipo, d.fecha, d.archivo, d.eliminado
            FROM documentos d
            JOIN procesos p ON d.proceso_id = p.id
            JOIN clientes c ON p.cliente_id = c.id
            WHERE c.id = ? AND d.eliminado = 0
            ORDER BY d.fecha DESC
        """, (cliente_id,))
        documentos = cur.fetchall()
        conn.close()
        return documentos

    def insertar_documento(self, nombre, cliente_id, proceso_id, fecha, ruta_archivo):
        conn = self._conectar()
        if conn is None:
            return
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO documentos (
                nombre, cliente_id, proceso_id, fecha, archivo, eliminado
            ) VALUES (?, ?, ?, ?, ?, 0)
        ''', (nombre, cliente_id, proceso_id, fecha, ruta_archivo))
        conn.commit()
        conn.close()


    def obtener_documentos_por_radicado(self, radicado_id):
        conn = self._conectar()
        if conn is None:
            return []
        cur = conn.cursor()
        cur.execute("""
            SELECT d.id, d.nombre, c.nombre, p.radicado, p.tipo, d.fecha, d.archivo
            FROM documentos d
            JOIN procesos p ON d.proceso_id = p.id
            JOIN clientes c ON p.cliente_id = c.id
            WHERE p.radicado = ? AND d.eliminado = 0
            ORDER BY d.fecha DESC
        """, (radicado_id,))
        resultados = cur.fetchall()
        conn.close()
        return resultados


    def obtener_todos_los_radicados(self):
        """
        Consulta todos los radicados existentes en la base de datos.
        Retorna una lista de diccionarios con `id` y `radicado`.
        """
        conn = self._conectar()
        if conn is None:
            return []
        query = """
            SELECT DISTINCT p.id, p.radicado 
            FROM procesos p
            ORDER BY p.radicado ASC
        """
        try:
            cur = conn.cursor()
            cur.execute(query)
            resultados = cur.fetchall()
            conn.close()
            # Convertimos los resultados a una lista de diccionarios
            return [{"id": row[0], "radicado": row[1]} for row in resultados]
        except Exception as e:
            print(f"Error al obtener todos los radicados: {e}")
            return []
    def obtener_radicados_por_cliente(self, cliente_id):
        """
        Obtiene todos los radicados asociados a un cliente específico.
        Retorna una lista de diccionarios con `id` y `radicado`.
        """
        conn = self._conectar()
        if conn is None:
            return []
            
        query = """
            SELECT DISTINCT p.id, p.radicado 
            FROM procesos p
            WHERE p.cliente_id = ? AND p.radicado IS NOT NULL
            ORDER BY p.radicado ASC
        """
        try:
            cur = conn.cursor()
            cur.execute(query, (cliente_id,))
            resultados = cur.fetchall()
            conn.close()
            return [{"id": row[0], "radicado": row[1]} for row in resultados]
        except Exception as e:
            print(f"Error al obtener radicados por cliente: {e}")
            return []

