# SELECTA_SCAM/config/settings.py
import os

# La ruta base del proyecto ahora es la carpeta SELECTA_SCAM
# __file__ es SELECTA_SCAM/config/settings.py
# os.path.abspath(__file__) -> .../SELECTA_SCAM/config/settings.py
# os.path.dirname(...) -> .../SELECTA_SCAM/config/
# os.path.dirname(os.path.dirname(...)) -> .../SELECTA_SCAM/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Subcarpetas relativas a BASE_DIR (SELECTA_SCAM)
DATA_DIR = os.path.join(BASE_DIR, 'data')
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# --- ¡IMPORTANTE: CREAR EL DIRECTORIO 'data' SI NO EXISTE! ---
# Esto creará SELECTA_SCAM/data si no existe.
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
# -----------------------------------------------------------

# Bases de datos
# Usa 'base_oficial.db' si ese es el nombre de tu archivo principal de DB.
# Si tu DB principal se llama 'base_datos.db', 'lex360plus.db', etc., cámbialo aquí.
DEFAULT_DB_FILENAME = 'base_oficial.db'
DATABASE_PATH = os.path.join(DATA_DIR, DEFAULT_DB_FILENAME)

# Archivos estáticos importantes
LOGO_PATH = os.path.join(ASSETS_DIR, 'logoapp.jpeg')
FIRMA_ABOGADO_PATH = os.path.join(ASSETS_DIR, 'firma_abogado.jpg')
FORMATO_REPORTE_CONTABILIDAD = os.path.join(ASSETS_DIR, 'formato_reporte_contabilidad.pdf.pdf')

# **¡VARIABLE AÑADIDA!** Define la ruta para Claro Drive.
# **IMPORTANTE:** Cambia esta ruta a la ubicación REAL de tu carpeta "Claro Drive" en tu equipo.
# Ejemplo: RUTA_CLARO_DRIVE = "C:/Users/oscar/Claro Drive"
RUTA_CLARO_DRIVE = os.path.join(os.path.expanduser("~"), "Claro Drive")
# Si la línea de arriba no funciona, descomenta la siguiente y pon tu ruta exacta:
# RUTA_CLARO_DRIVE = "C:/Users/oscar/Tu_Carpeta_De_Claro_Drive"


# Configuración general
APP_NAME = "SELECTA SCAM"
APP_VERSION = "1.0.0"

# Cadena de conexión para SQLAlchemy
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"