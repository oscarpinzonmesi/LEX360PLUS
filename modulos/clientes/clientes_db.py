import sqlite3

class ClientesDB:
    def __init__(self, conectar):
        self.conectar = conectar


    def get_clientes(self, incluir_eliminados=False):
        """
        Obtiene la lista de clientes activos o todos, según el parámetro.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            if incluir_eliminados:
                cursor.execute("""
                    SELECT id, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado
                    FROM clientes
                """)
            else:
                cursor.execute("""
                    SELECT id, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado
                    FROM clientes
                    WHERE eliminado = 0
                """)
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except sqlite3.Error as e:
            print(f"Error en la base de datos: {e}")
            return []


    def agregar_cliente(self, nombre, tipo_id, identificacion, correo, telefono, direccion):
            """
            Inserta un nuevo cliente como activo (eliminado = 0).
            """
            try:
                conn = self.conectar()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO clientes (nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado)
                    VALUES (?, ?, ?, ?, ?, ?, 0)
                """, (nombre, tipo_id, identificacion, correo, telefono, direccion))
                conn.commit()
                conn.close()
            except sqlite3.Error as e:
                print(f"Error al agregar el cliente: {e}")

    def marcar_como_eliminado(self, cliente_id):
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET eliminado = 1 WHERE id = ?", (cliente_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al eliminar el cliente: {e}")


    def restaurar_cliente(self, cliente_id):
        """
        Restaura un cliente marcado como eliminado.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("UPDATE clientes SET eliminado = 0 WHERE id = ?", (cliente_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al restaurar el cliente: {e}")

    def update_cliente(self, cliente_id, nombre, tipo_id, identificacion, correo, telefono, direccion):
        """
        Actualiza los datos de un cliente existente.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clientes
                SET nombre = ?, tipo_id = ?, identificacion = ?, correo = ?, telefono = ?, direccion = ?
                WHERE id = ?
            """, (nombre, tipo_id, identificacion, correo, telefono, direccion, cliente_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al actualizar el cliente: {e}")

    def obtener_id_por_identificacion(self, identificacion):
        """
        Obtiene el ID de un cliente activo según su identificación.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM clientes
                WHERE identificacion = ? AND eliminado = 0
            """, (identificacion,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None
        except sqlite3.Error as e:
            print(f"Error al buscar cliente por identificación: {e}")
            return None


    def buscar_por_identificacion(self, identificacion):
        """
        Busca un cliente por su número de identificación.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clientes WHERE identificacion = ? AND eliminado = 0", (identificacion,))
            result = cursor.fetchone()
            conn.close()
            return result
        except sqlite3.Error as e:
            print(f"Error al buscar cliente por identificación: {e}")
            return None

    def actualizar_cliente(self, id_, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado=0):
        """
        Actualiza un cliente específico.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE clientes SET 
                    nombre = ?, tipo_id = ?, identificacion = ?, correo = ?, telefono = ?, direccion = ?, eliminado = ?
                WHERE id = ?
            """, (nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado, id_))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al actualizar el cliente: {e}")
    def debug_imprimir_clientes_eliminados(self):
        """
        Imprime los clientes eliminados para fines de depuración.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, tipo_id, identificacion, eliminado FROM clientes WHERE eliminado = 1")
            resultados = cursor.fetchall()
            conn.close()
            for cliente in resultados:
                pass  # Línea necesaria para evitar error de indentación
            return resultados
        except sqlite3.Error as e:
            print(f"Error al imprimir clientes eliminados: {e}")
            return []

    def marcar_como_recuperado(self, cliente_id):
        """
        Marca un cliente como no eliminado (eliminado = 0).
        """
        conn = self.conectar()
        cur = conn.cursor()
        cur.execute("UPDATE clientes SET eliminado = 0 WHERE id = ?", (cliente_id,))
        conn.commit()
        conn.close()
    def buscar_eliminados(self, texto):
        """
        Busca clientes eliminados que coincidan parcialmente con el texto dado.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado
                FROM clientes
                WHERE eliminado = 1 AND (
                    nombre LIKE ? OR
                    identificacion LIKE ? OR
                    correo LIKE ? OR
                    telefono LIKE ?
                )
            """, (f'%{texto}%', f'%{texto}%', f'%{texto}%', f'%{texto}%'))
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except sqlite3.Error as e:
            print(f"Error al buscar clientes eliminados: {e}")
            return []
    
    def buscar_por_id_o_nombre(self, texto):
        """
        Busca clientes activos cuyo nombre o ID coincida parcialmente con el texto dado,
        ignorando mayúsculas.
        """
        try:
            texto_normalizado = texto.lower()
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado
                FROM clientes
                WHERE eliminado = 0 AND (
                    LOWER(nombre) LIKE ? OR
                    CAST(id AS TEXT) LIKE ?
                )
            """, (f'%{texto_normalizado}%', f'%{texto_normalizado}%'))
            resultados = cursor.fetchall()
            conn.close()
            return resultados
        except sqlite3.Error as e:
            print(f"Error al buscar clientes por ID o nombre: {e}")
            return []


    def eliminar_cliente_definitivo(self, cliente_id):
        """
        Elimina permanentemente un cliente de la base de datos.
        """
        try:
            conn = self.conectar()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Error al eliminar permanentemente el cliente: {e}")

    def editar_cliente(self, cliente_id, nombre, tipo_id, identificacion, correo, telefono, direccion):
        """
        Actualiza los datos de un cliente en la base de datos.
        """
        try:
            conexion = self.conectar()
            cursor = conexion.cursor()  # Usar 'conexion' para el cursor

            query = """
            UPDATE clientes 
            SET nombre = ?, tipo_id = ?, identificacion = ?, correo = ?, telefono = ?, direccion = ?
            WHERE id = ?
            """
            cursor.execute(query, (nombre, tipo_id, identificacion, correo, telefono, direccion, cliente_id))
            conexion.commit()
            conexion.close()
        except Exception as e:
            print(f"Error al actualizar cliente: {e}")
            raise
