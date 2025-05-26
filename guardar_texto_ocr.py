from pdf2image import convert_from_path
import pytesseract
import os

# Ruta al archivo PDF que quieres procesar
PDF_PATH = r"C:\Users\oscar\OneDrive\Desktop\Certificación Bancaria.pdf"

# Ruta donde quieres guardar el texto extraído
OUTPUT_TXT_PATH = r"C:\Users\oscar\OneDrive\Desktop\texto_extraido.txt"

# Si usas Tesseract manualmente instalado, asegúrate de decirle dónde está:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extraer_texto_pdf_ocr(pdf_path):
    print(f"Procesando: {pdf_path}")
    texto_final = ""
    imagenes = convert_from_path(pdf_path, poppler_path=r"C:\Users\oscar\OneDrive\Desktop\LEX360PLUS\Cpoppler\Library\bin")
    for i, imagen in enumerate(imagenes):
        print(f"Procesando página {i + 1}")
        texto = pytesseract.image_to_string(imagen, lang='spa')
        texto_final += texto + "\n\n"
    return texto_final

# Ejecutar extracción y guardar resultado
texto_extraido = extraer_texto_pdf_ocr(PDF_PATH)

with open(OUTPUT_TXT_PATH, "w", encoding="utf-8") as f:
    f.write(texto_extraido)

print(f"\nTexto guardado en: {OUTPUT_TXT_PATH}")
