import os
import shutil
import sqlite3
from config import RUTA_CLARO_DRIVE  
from modulos.documentos.documentos_model import (
    obtener_clientes,
    obtener_procesos,
    obtener_documentos_por_cliente,
    insertar_documento,
    eliminar_documento_por_id
)
from config import RUTA_BD, RUTA_CLARO_DRIVE
def cargar_datos_iniciales():
    """
    Carga los datos iniciales: clientes y procesos.

    Retorna:
        tuple: Una tupla con dos listas: clientes y procesos.
    """
    clientes = obtener_clientes()
    procesos = obtener_procesos()
    return clientes, procesos

def filtrar_procesos_por_cliente(procesos, cliente_id):
    """
    Filtra los procesos por ID de cliente.

    Args:
        procesos (list): Lista de procesos.
        cliente_id (int): ID del cliente para filtrar los procesos.

    Retorna:
        list: Lista de procesos correspondientes al cliente_id.
    """
    return [p for p in procesos if p[3] == cliente_id]

def copiar_archivo_a_claro_drive(origen, nombre):
    """
    Copia un archivo desde la ruta de origen a Claro Drive.
    """
    if not os.path.exists(origen):
        raise FileNotFoundError(f"El archivo de origen no existe: {origen}")

    os.makedirs(RUTA_CLARO_DRIVE, exist_ok=True)

    extension = os.path.splitext(origen)[1]
    ruta_destino = os.path.join(RUTA_CLARO_DRIVE, f"{nombre}{extension}")

    if os.path.exists(ruta_destino):
        raise FileExistsError(f"El archivo ya existe en Claro Drive: {ruta_destino}")

    try:
        shutil.copy2(origen, ruta_destino)
    except OSError as e:
        raise OSError(f"Error al copiar el archivo: {e}")

    return ruta_destino
def obtener_documento_por_id(doc_id):
    """
    Obtiene un documento por su ID desde la base de datos.

    Parámetros:
        doc_id (int): ID del documento a buscar.

    Retorna:
        tuple: (id, proceso_id, nombre, fecha, ruta_archivo, cliente_id)
        o None si no se encuentra el documento.
    """
    try:
        with sqlite3.connect(RUTA_BD) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, proceso_id, nombre, fecha, ruta_archivo, cliente_id
                FROM documentos
                WHERE id = ?
            """, (doc_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        print(f"Error al obtener el documento: {e}")
        return None



def actualizar_documento(doc_id, nombre, cliente_id, proceso_id, fecha, ruta_archivo):
    """
    Actualiza un documento en la base de datos.

    Args:
        doc_id (int): ID del documento a actualizar.
        nombre (str): Nuevo nombre del documento.
        cliente_id (int): Nuevo ID del cliente.
        proceso_id (int): Nuevo ID del proceso.
        fecha (str): Nueva fecha del documento.
        ruta_archivo (str): Nueva ruta del archivo.

    Retorna:
        None
    """
    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE documentos
        SET nombre = ?, cliente_id = ?, proceso_id = ?, fecha = ?, ruta_archivo = ?
        WHERE id = ?
    """, (nombre, cliente_id, proceso_id, fecha, ruta_archivo, doc_id))
    conn.commit()
    conn.close()

def eliminar_documento_por_id(doc_id):
    """
    Elimina un documento por su ID desde la base de datos.

    Args:
        doc_id (int): ID del documento a eliminar.

    Retorna:
        None
    """
    try:
        conn = sqlite3.connect(RUTA_BD)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documentos WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error al eliminar documento: {e}")
# Dentro de documentos_controller.py


def editar_documento(doc_id, nombre, cliente_id, proceso_id, fecha, ruta_archivo):
    """
    Actualiza la información de un documento en la base de datos.

    Args:
        doc_id (int): ID del documento a actualizar.
        nombre (str): Nuevo nombre del documento.
        cliente_id (int): ID del cliente asociado al documento.
        proceso_id (int): ID del proceso asociado al documento.
        fecha (str): Nueva fecha del documento.
        ruta_archivo (str): Nueva ruta del archivo.
    """
    try:
        conn = sqlite3.connect(RUTA_BD)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE documentos
            SET nombre = ?, cliente_id = ?, proceso_id = ?, fecha = ?, ruta_archivo = ?
            WHERE id = ?
        """, (nombre, cliente_id, proceso_id, fecha, ruta_archivo, doc_id))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error al actualizar documento: {e}")
# En documentos_controller.py

def restaurar_documento(doc_id):
    """
    Restaura un documento en la base de datos a su estado anterior.

    Args:
        doc_id (int): ID del documento a restaurar.
    """
    try:
        conn = sqlite3.connect(RUTA_BD)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE documentos
            SET estado = 'activo'
            WHERE id = ?
        """, (doc_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error al restaurar documento: {e}")
def buscar_documentos(query=""):
    """
    Busca documentos en la base de datos que coincidan con la consulta.

    Args:
        query (str): El término de búsqueda (por ejemplo, el nombre del documento).
    
    Returns:
        list: Lista de documentos que coinciden con la búsqueda.
    """
    try:
        conn = sqlite3.connect(RUTA_BD)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, cliente_id, nombre, archivo, fecha
            FROM documentos
            WHERE eliminado = 0 AND (nombre LIKE ? OR archivo LIKE ?)
            ORDER BY fecha DESC
        """, ('%' + query + '%', '%' + query + '%'))
        resultados = cursor.fetchall()
        conn.close()
        return resultados
    except sqlite3.Error as e:
        print(f"Error al buscar documentos: {e}")
        return []

def verificar_documento_existente(nombre, proceso_id):
    """
    Verifica si un documento con el mismo nombre ya existe en un proceso dado.

    Args:
        nombre (str): El nombre del documento a verificar.
        proceso_id (int): El ID del proceso al que pertenece el documento.

    Returns:
        bool: True si ya existe, False en caso contrario.
    """
    try:
        conn = sqlite3.connect(RUTA_BD)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM documentos
            WHERE nombre = ? 
              AND proceso_id = ?
              AND eliminado = 0
        """, (nombre, proceso_id))
        resultado = cursor.fetchone()
        conn.close()
        return resultado[0] > 0
    except sqlite3.Error as e:
        print(f"Error al verificar documento existente: {e}")
        return False



def obtener_documentos_por_cliente(cliente_id):
    """
    Obtiene los documentos de un cliente dado su ID, incluyendo el nombre del cliente.
    
    Args:
        cliente_id (int): ID del cliente.

    Retorna:
        list: Lista de tuplas con los documentos y el nombre del cliente.
    """
    conn = sqlite3.connect(RUTA_BD)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, d.proceso_id, d.nombre, d.archivo, d.fecha, d.ruta_archivo, 
               d.eliminado, d.cliente_id, c.nombre as nombre_cliente
        FROM documentos d
        JOIN clientes c ON d.cliente_id = c.id
        WHERE d.cliente_id = ?
    """, (cliente_id,))
    documentos = cursor.fetchall()
    conn.close()
    return documentos


