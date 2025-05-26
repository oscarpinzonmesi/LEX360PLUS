import sqlite3
import os
import shutil
from datetime import datetime
from tkinter import messagebox

# Ruta de la base de datos
DATABASE_PATH = r"data\base_datos.db"

# Carpeta de Claro Drive donde se guardarán los documentos
RUTA_CLARO_DRIVE = r"C:\Users\oscar\Claro drive2\LEX360"
RUTA_BD = DATABASE_PATH  # Para compatibilidad con otros módulos que usen RUTA_BD

# Verificar si la carpeta de Claro Drive existe, si no, crearla
if not os.path.exists(RUTA_CLARO_DRIVE):
    os.makedirs(RUTA_CLARO_DRIVE)

def ver_procesos():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()

        # Mostrar nombres de columnas
        cur.execute("PRAGMA table_info(procesos)")
        columnas = cur.fetchall()
        print("Columnas de la tabla 'procesos':")
        for col in columnas:
            print(f"- {col[1]} ({col[2]})")

        # Mostrar datos de ejemplo (hasta 10)
        print("\nRegistros de la tabla 'procesos':")
        cur.execute("SELECT * FROM procesos LIMIT 10")
        registros = cur.fetchall()
        for fila in registros:
            print(fila)

        conn.close()
    except Exception as e:
        print(f"Error leyendo la tabla procesos: {e}")


# Asegúrate de que esta constante esté definida correctamente

def copiar_archivo_a_destino(ruta_origen, nombre_destino):
    """
    Copia el archivo desde la ruta de origen a la carpeta de destino (RUTA_CLARO_DRIVE) con el nuevo nombre.
    """
    try:
        # Asegúrate de que el nombre del archivo tenga la extensión .pdf
        nombre_destino_completo = f"{nombre_destino}.pdf"
        
        # Define la ruta de destino
        ruta_destino = os.path.join(RUTA_CLARO_DRIVE, nombre_destino_completo)

        # Mostrar la ruta de destino para depuración
        print(f"Ruta destino: {ruta_destino}")

        # Verifica si el archivo ya existe en la carpeta de destino
        if os.path.exists(ruta_destino):
            raise FileExistsError(f"El archivo {ruta_destino} ya existe.")

        # Copia el archivo
        shutil.copy(ruta_origen, ruta_destino)

        # Devuelve la ruta de destino
        return ruta_destino
    except Exception as e:
        print(f"Error al copiar archivo: {e}")
        raise


def guardar(self):
    try:
        print(f"Nombre del documento: {self.nombre}")
        print(f"Cliente ID: {self.cliente_id}, Proceso ID: {self.proceso_id}")
        print(f"Ruta archivo: {self.ruta_archivo}")

        # Copiar archivo y obtener la ruta final
        ruta_destino = copiar_archivo_a_destino(self.ruta_archivo, self.nombre)

        print(f"Copiado exitosamente a: {ruta_destino}")

        # Guardar en base de datos
        guardar_documento_en_db(self.nombre, self.cliente_id, self.proceso_id, ruta_destino)

        messagebox.showinfo("Éxito", "Documento guardado correctamente.")

    except Exception as e:
        print(f"Error al guardar documento: {e}")
        messagebox.showerror("Error", f"Ocurrió un error al guardar el documento: {e}")

# Función para guardar en la base de datos
def guardar_documento_en_db(nombre, cliente_id, proceso_id, ruta_archivo):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO documentos (nombre, cliente_id, proceso_id, archivo, fecha)
            VALUES (?, ?, ?, ?, ?)
        """, (
            nombre,
            cliente_id,
            proceso_id,
            ruta_archivo,
            datetime.now().strftime("%Y-%m-%d")
        ))
        conn.commit()
        conn.close()
        print("Documento guardado en la base de datos correctamente.")
    except Exception as e:
        print(f"Error al guardar en la base de datos: {e}")
        raise
