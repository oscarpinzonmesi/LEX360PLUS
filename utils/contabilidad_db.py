# utils/contabilidad_db.py

import sqlite3

class ContabilidadDB:
    def __init__(self, conectar):
        """
        La clase ContabilidadDB administra todas las operaciones de la base de datos
        relacionadas con el módulo de contabilidad, procesos y clientes.
        
        Parámetros:
            conectar (callable): función que retorna una conexión SQLite (por ejemplo, DBManager.conectar).
        """
        self.conectar = conectar

    # ---------------------------------------------------------
    # FUNCIONES PARA MÓDULO DE CLIENTES (usadas por ContabilidadWidget)
    # ---------------------------------------------------------
    def get_clientes(self):
        """
        Recupera todos los clientes activos (id, nombre).
        
        Retorna:
            lista de tuplas: [(id_cliente, nombre_cliente), ...]
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")
        clientes = cursor.fetchall()
        conn.close()
        return clientes

    # ---------------------------------------------------------
    # FUNCIONES PARA MÓDULO DE PROCESOS (usadas por ContabilidadWidget)
    # ---------------------------------------------------------
    def get_procesos_por_cliente(self, cliente_id):
        """
        Recupera todos los procesos (radicados) asociados a un cliente específico.
        
        Parámetros:
            cliente_id (int): ID del cliente.
        
        Retorna:
            lista de tuplas: [(id_proceso, cliente_id, clase, radicado), ...]
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, cliente_id, clase, radicado
            FROM procesos
            WHERE cliente_id = ?
        """, (cliente_id,))
        procesos = cursor.fetchall()
        conn.close()
        return procesos

    # ---------------------------------------------------------
    # FUNCIONES PARA MÓDULO DE CONTABILIDAD (ContabilidadWidget)
    # ---------------------------------------------------------
    def get_contabilidad_detallada(self):
        """
        Recupera todos los registros de contabilidad en detalle, 
        usando solo las columnas que efectivamente existen:
            id_contabilidad,
            nombre_cliente,
            tipo,
            descripcion,
            valor,
            fecha
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.id,
                cl.nombre,
                c.tipo,
                c.descripcion,
                c.valor,
                c.fecha
            FROM contabilidad AS c
            JOIN clientes AS cl ON c.cliente_id = cl.id
            ORDER BY c.fecha DESC, c.id DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return rows

    def add_contabilidad(self, cliente_id, tipo, descripcion, valor, fecha):
        """
        Inserta un nuevo registro en la tabla 'contabilidad'.
        
        Parámetros:
            cliente_id (int): ID del cliente asociado.
            tipo (str): Tipo de registro.
            descripcion (str): Descripción o concepto.
            valor (float): Valor monetario.
            fecha (str): Fecha en formato 'YYYY-MM-DD'.
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contabilidad (
                cliente_id, tipo, descripcion, valor, fecha
            ) VALUES (?, ?, ?, ?, ?)
        """, (cliente_id, tipo, descripcion, valor, fecha))
        conn.commit()
        conn.close()

    def update_contabilidad(self, contabilidad_id, cliente_id, tipo, descripcion, valor, fecha):
        """
        Actualiza un registro existente en la tabla 'contabilidad'.
        
        Parámetros:
            contabilidad_id (int): ID del registro contable a actualizar.
            cliente_id (int): ID del cliente.
            tipo (str): Tipo de registro.
            descripcion (str): Descripción o concepto.
            valor (float): Valor monetario.
            fecha (str): Fecha en 'YYYY-MM-DD'.
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE contabilidad
            SET cliente_id = ?,
                tipo = ?,
                descripcion = ?,
                valor = ?,
                fecha = ?
            WHERE id = ?
        """, (cliente_id, tipo, descripcion, valor, fecha, contabilidad_id))
        conn.commit()
        conn.close()

    def delete_contabilidad(self, contabilidad_id):
        """
        Elimina un registro de la tabla 'contabilidad' por su ID.
        
        Parámetros:
            contabilidad_id (int): ID del registro a eliminar.
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contabilidad WHERE id = ?", (contabilidad_id,))
        conn.commit()
        conn.close()

    # ---------------------------------------------------------
    # MÉTODOS ADICIONALES PARA USOS ESPECÍFICOS (opcionales)
    # ---------------------------------------------------------
    def obtener_contabilidad_por_proceso(self, proceso_id):
        """
        Recupera registros contables asociados a un proceso específico, ordenados por fecha descendente.
        
        Parámetros:
            proceso_id (int): ID del proceso (radicado).
        
        Retorna:
            lista de tuplas: [(id, descripcion, valor, fecha, tipo), ...]
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                id,
                descripcion,
                valor,
                fecha,
                tipo
            FROM contabilidad
            WHERE proceso_id = ?
            ORDER BY fecha DESC
        """, (proceso_id,))
        resultado = cursor.fetchall()
        conn.close()
        return resultado

    def agregar_registro_contable(self, proceso_id, descripcion, monto, fecha, tipo):
        """
        Inserta un registro contable sencillo (solo para propósitos internos de procesos).
        
        Parámetros:
            proceso_id (int): ID del proceso.
            descripcion (str): Descripción o concepto.
            monto (float): Monto.
            fecha (str): Fecha en 'YYYY-MM-DD'.
            tipo (str): Tipo o referencia (puede ser documento).
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contabilidad (proceso_id, descripcion, valor, fecha, tipo, cliente_id)
            VALUES (?, ?, ?, ?, ?,
                (SELECT cliente_id FROM procesos WHERE id = ?)
            )
        """, (proceso_id, descripcion, monto, fecha, tipo, proceso_id))
        conn.commit()
        conn.close()

    def eliminar_registro_contable(self, contabilidad_id):
        """
        Elimina un registro contable por su ID (uso interno de procesos).
        
        Parámetros:
            contabilidad_id (int): ID del registro en contabilidad.
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contabilidad WHERE id = ?", (contabilidad_id,))
        conn.commit()
        conn.close()
