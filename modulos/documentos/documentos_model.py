import sqlite3
from config import DATABASE_PATH
import os

def obtener_clientes():
    """
    Obtiene todos los clientes activos.
    """
    conn = sqlite3.connect(DATABASE_PATH)  # Usa DATABASE_PATH aquí
    cur = conn.cursor()
    cur.execute("SELECT id, nombre FROM clientes WHERE eliminado = 0")
    clientes = cur.fetchall()
    conn.close()
    return clientes

def obtener_procesos():
    """
    Obtiene todos los procesos activos.
    """
    conn = sqlite3.connect(DATABASE_PATH)  # Usa DATABASE_PATH aquí
    cur = conn.cursor()
    cur.execute("SELECT id, radicado, cliente_id FROM procesos WHERE eliminado = 0")
    procesos = cur.fetchall()
    conn.close()
    return procesos

def obtener_documentos_por_cliente(cliente_id):
    """
    Obtiene los documentos asociados a un cliente, con o sin proceso.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                d.id,
                d.proceso_id,
                d.nombre,
                d.archivo,
                d.fecha,
                d.ruta_archivo,
                d.eliminado,
                d.cliente_id,
                p.radicado  -- Este puede ser NULL si no hay proceso
            FROM documentos d
            LEFT JOIN procesos p ON d.proceso_id = p.id
            WHERE d.cliente_id = ? AND d.eliminado = 0
            ORDER BY d.fecha DESC
        """, (cliente_id,))
        
        return cur.fetchall()

    except sqlite3.Error as e:
        print(f"[ERROR] al obtener documentos del cliente: {e}")
        return []
    finally:
        cur.close()
        conn.close()
def insertar_documento(nombre_archivo, cliente_id, proceso_id, fecha, ruta_destino, tipo_documento):
    """
    Inserta un nuevo documento asociado a un proceso específico.
    nombre_archivo: solo basename con extensión.
    ruta_destino: ruta completa donde se guardó el archivo.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    # Validar duplicado por nombre de archivo y proceso
    cur.execute("""
        SELECT COUNT(*) FROM documentos 
        WHERE archivo = ? AND proceso_id = ? AND eliminado = 0
    """, (nombre_archivo, proceso_id))
    if cur.fetchone()[0] > 0:
        conn.close()
        raise ValueError("El documento ya existe para este proceso.")

    # Insertar separando nombre y ruta, ahora con tipo_documento
    cur.execute("""
        INSERT INTO documentos (nombre, cliente_id, proceso_id, fecha, archivo, ruta_archivo, tipo_documento, eliminado)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (os.path.splitext(nombre_archivo)[0], cliente_id, proceso_id, fecha, nombre_archivo, ruta_destino, tipo_documento))

    conn.commit()
    conn.close()


def eliminar_documento_por_id(doc_id):
    """
    Marca un documento como eliminado (no elimina físicamente).
    """
    conn = sqlite3.connect(DATABASE_PATH)  # Usa DATABASE_PATH aquí
    cur = conn.cursor()
    cur.execute("UPDATE documentos SET eliminado = 1 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

def restaurar_documento(doc_id):
    """
    Restaura un documento que ha sido marcado como eliminado.
    """
    conn = sqlite3.connect(DATABASE_PATH)  # Usa DATABASE_PATH aquí
    cur = conn.cursor()
    cur.execute("UPDATE documentos SET eliminado = 0 WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()

def buscar_documentos(cliente_id=None, proceso_id=None, fecha=None, tipo=None, nombre=None):
    """
    Busca documentos según criterios opcionales: cliente, proceso, fecha, tipo o nombre.
    """
    conn = sqlite3.connect(DATABASE_PATH)  # Usa DATABASE_PATH aquí
    cur = conn.cursor()

    query = """
        SELECT d.id, d.nombre, c.nombre, p.radicado, p.tipo, d.fecha, d.archivo 
        FROM documentos d 
        JOIN procesos p ON d.proceso_id = p.id 
        JOIN clientes c ON p.cliente_id = c.id 
        WHERE d.eliminado = 0
    """

    params = []

    if cliente_id:
        query += " AND p.cliente_id = ?"
        params.append(cliente_id)
    
    if proceso_id:
        query += " AND d.proceso_id = ?"
        params.append(proceso_id)
    
    if fecha:
        query += " AND d.fecha = ?"
        params.append(fecha)
    
    if tipo:
        query += " AND p.tipo = ?"
        params.append(tipo)
    
    if nombre:
        query += " AND d.nombre LIKE ?"
        params.append(f"%{nombre}%")

    query += " ORDER BY d.fecha DESC"

    cur.execute(query, tuple(params))
    documentos = cur.fetchall()
    conn.close()
    return documentos
def editar_documento(doc_id, nombre=None, cliente_id=None, proceso_id=None, fecha=None, ruta_archivo=None,):
    """
    Actualiza los datos de un documento.
    Solo actualiza los campos que se pasan (no None).
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()

    campos = []
    params = []

    if nombre is not None:
        campos.append("nombre = ?")
        params.append(nombre)
    if cliente_id is not None:
        campos.append("cliente_id = ?")
        params.append(cliente_id)
    if proceso_id is not None:
        campos.append("proceso_id = ?")
        params.append(proceso_id)
    if fecha is not None:
        campos.append("fecha = ?")
        params.append(fecha)
    if ruta_archivo is not None:
        campos.append("archivo = ?")
        params.append(ruta_archivo)

    if not campos:
        # No hay campos para actualizar
        conn.close()
        return

    query = f"UPDATE documentos SET {', '.join(campos)} WHERE id = ?"
    params.append(doc_id)

    cur.execute(query, tuple(params))
    conn.commit()
    conn.close()
def verificar_documento_existente(nombre_archivo, proceso_id):
    """
    Verifica si un documento con el mismo nombre (incluida la extensión)
    ya existe en el mismo proceso para evitar duplicados exactos.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM documentos 
        WHERE archivo = ? AND proceso_id = ? AND eliminado = 0
    """, (nombre_archivo, proceso_id))
    existe = cur.fetchone()[0] > 0
    conn.close()
    return existe

