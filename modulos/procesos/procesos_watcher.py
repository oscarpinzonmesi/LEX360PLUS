# procesos_watcher.py

import os
import re
import time
import shutil
import pytesseract
import sqlite3
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pdf2image import convert_from_path
from PyPDF2 import PdfReader

# Configuración
CARPETA_DESCARGAS = os.path.expanduser("~/Downloads")
RUTA_DB = os.path.join(os.path.dirname(__file__), "data", "base_datos.db")
DESTINO_DOCUMENTOS = "documentos"  # Carpeta base para mover archivos
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extraer_texto_pdf_ocr(ruta_pdf):
    texto_total = ""
    try:
        imagenes = convert_from_path(ruta_pdf)
        for img in imagenes:
            texto = pytesseract.image_to_string(img, lang='spa')
            texto_total += texto + "\n"
    except Exception as e:
        print(f"[ERROR] OCR: {e}")
    return texto_total


def extraer_texto_pdf(ruta_pdf):
    try:
        reader = PdfReader(ruta_pdf)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() or ""
        return texto
    except Exception as e:
        print(f"[ERROR] Extracción directa: {e}")
        return ""


def extraer_info(archivo, texto):
    patrones_radicado = [r'\b\d{20}\b', r'\b\d{23}\b']
    patrones_nombre = [r'Nombre: ([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+ [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)',
                       r'Parte: ([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+ [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)']

    radicado = next((re.search(p, texto) or re.search(p, archivo)) for p in patrones_radicado if re.search(p, texto) or re.search(p, archivo))
    nombre = next((re.search(p, texto) for p in patrones_nombre if re.search(p, texto)), None)

    return (
        radicado.group(0) if radicado else None,
        nombre.group(1) if nombre else None
    )


def buscar_carpeta_proceso(archivo):
    texto = extraer_texto_pdf(archivo)
    if not texto.strip():
        print("[INFO] PDF vacío o escaneado. Intentando OCR...")
        texto = extraer_texto_pdf_ocr(archivo)

    radicado, nombre = extraer_info(archivo, texto)
    print(f"[INFO] Extraído: radicado={radicado}, cliente={nombre}")

    try:
        conn = sqlite3.connect(RUTA_DB)
        cursor = conn.cursor()

        if radicado:
            cursor.execute("SELECT id FROM procesos WHERE radicado = ?", (radicado,))
            result = cursor.fetchone()
            if result:
                return os.path.join(DESTINO_DOCUMENTOS, f"proceso_{result[0]}")

        if nombre:
            cursor.execute("""SELECT p.id FROM procesos p
                              JOIN clientes c ON p.cliente_id = c.id
                              WHERE c.nombre LIKE ?""", (f"%{nombre}%",))
            result = cursor.fetchone()
            if result:
                return os.path.join(DESTINO_DOCUMENTOS, f"proceso_{result[0]}")

    except Exception as e:
        print(f"[ERROR] Consulta en DB: {e}")
    finally:
        conn.close()

    return None


class DescargasWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory or not event.src_path.lower().endswith(".pdf"):
            return

        archivo = event.src_path
        print(f"[INFO] Archivo detectado: {archivo}")
        time.sleep(2)  # Espera a que termine de descargarse

        destino = buscar_carpeta_proceso(archivo)
        if destino:
            os.makedirs(destino, exist_ok=True)
            shutil.move(archivo, os.path.join(destino, os.path.basename(archivo)))
            print(f"[✅] Archivo movido a: {destino}")
        else:
            print("[⚠️] No se identificó proceso para este archivo.")


def iniciar_watcher():
    observer = Observer()
    event_handler = DescargasWatcher()
    observer.schedule(event_handler, path=CARPETA_DESCARGAS, recursive=False)
    observer.start()
    print(f"[👁️] Observando: {CARPETA_DESCARGAS}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    iniciar_watcher()
