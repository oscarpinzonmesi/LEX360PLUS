import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

def generar_pdf_contabilidad(ruta_guardar, datos):
    """
    Genera un PDF de reporte de contabilidad usando una plantilla de fondo.

    Parámetros:
        ruta_guardar (str): Ruta donde se guardará el PDF generado.
        datos (dict): Diccionario con las claves:
            - cliente
            - radicado
            - clase
            - concepto
            - monto_total
            - abonado
            - restante
            - fecha
    """
    fondo_path = os.path.join("assets", "formato_reporte_contabilidad.png")  # debe ser imagen, no PDF
    firma_path = os.path.join("assets", "firma_abogado.png")

    c = canvas.Canvas(ruta_guardar, pagesize=letter)

    # Dibujar fondo si existe
    if os.path.exists(fondo_path):
        c.drawImage(ImageReader(fondo_path), 0, 0, width=612, height=792)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 700, "REPORTE DE CONTABILIDAD")

    c.setFont("Helvetica", 12)
    c.drawString(100, 660, f"Cliente: {datos['cliente']}")
    c.drawString(100, 640, f"Radicado: {datos['radicado']}")
    c.drawString(100, 620, f"Clase: {datos['clase']}")
    c.drawString(100, 600, f"Concepto: {datos['concepto']}")
    c.drawString(100, 580, f"Monto Total: ${datos['monto_total']}")
    c.drawString(100, 560, f"Abonado: ${datos['abonado']}")
    c.drawString(100, 540, f"Restante: ${datos['restante']}")
    c.drawString(100, 520, f"Fecha: {datos['fecha']}")

    # Agregar firma si existe
    if os.path.exists(firma_path):
        c.drawImage(ImageReader(firma_path), 400, 100, width=150, height=50)

    c.save()