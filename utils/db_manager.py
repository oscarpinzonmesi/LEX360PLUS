import importlib
import sqlite3
from config import DATABASE_PATH
from modulos.clientes.clientes_db import ClientesDB
from utils.procesos_db import ProcesosDB
from utils.documentos_db import DocumentosDB
from utils.contabilidad_db import ContabilidadDB
from utils.calendario_db import CalendarioDB
from utils.liquidadores_db import LiquidadoresDB

class DBManager:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH

        # Inicializar acceso a módulos sin el argumento self.conectar
        self.clientes_db = ClientesDB(self.conectar)  # Correcto
        self.procesos_db = ProcesosDB(self.conectar)  # Añadido el argumento conectaro
        self.documentos_db = DocumentosDB()  # Sin argumento
        self.contabilidad_db = ContabilidadDB(self.conectar) 
        self.calendario_db = CalendarioDB(self.conectar)  
        self.liquidadores_db = LiquidadoresDB(self.conectar) 

        # Cargar dinámicamente el módulo de usuarios
        UsuariosDB = importlib.import_module("utils.usuarios_db").UsuariosDB
        self.usuarios_db = UsuariosDB(self.conectar)



    def conectar(self):
        return sqlite3.connect(self.db_path)

    def debug_imprimir_todos_los_clientes(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, tipo_id, identificacion, eliminado FROM clientes")
        resultados = cursor.fetchall()
        for cliente in resultados:
            print("🧾 Cliente:", cliente)
        conn.close()
        return resultados

    
    def execute(self, query, params=()):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        conn.close()

    def create_tables(self):
        conn = self.conectar()
        cursor = conn.cursor()

    def actualizar_cliente(self, id_cliente, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado=0):
        conn = self.conectar()  # ✅
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE clientes
            SET nombre = ?, tipo_id = ?, identificacion = ?, correo = ?, telefono = ?, direccion = ?, eliminado = ?
            WHERE id = ?
        ''', (nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado, id_cliente))
        conn.commit()
        conn.close()
    
    def buscar_por_identificacion(self, identificacion):
        conn = self.conectar()  # ✅
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM clientes WHERE identificacion = ?", (identificacion,))
        return cursor.fetchone()

    def migrar_columna_cedula_a_identificacion(self):
        conn = self.conectar()
        cursor = conn.cursor()

        # Verificar si la columna 'identificacion' ya existe
        cursor.execute("PRAGMA table_info(clientes);")
        columnas = [col[1] for col in cursor.fetchall()]
        if "identificacion" in columnas:
            print("La columna 'identificacion' ya existe. Migración no necesaria.")
            return

        # Crear tabla temporal con el nuevo esquema
        cursor.execute('''
            CREATE TABLE clientes_nueva (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo_id TEXT,
                identificacion TEXT UNIQUE,
                telefono TEXT,
                direccion TEXT,
                correo TEXT,
                eliminado INTEGER DEFAULT 0
            )
        ''')

        # Copiar datos de la tabla antigua a la nueva
        cursor.execute('''
            INSERT INTO clientes_nueva (id, nombre, tipo_id, identificacion, telefono, direccion, correo, eliminado)
            SELECT id, nombre, tipo_id, cedula, telefono, direccion, correo, eliminado FROM clientes
        ''')

        # Eliminar tabla antigua y renombrar la nueva
        cursor.execute('DROP TABLE clientes')
        cursor.execute('ALTER TABLE clientes_nueva RENAME TO clientes')

        conn.commit()
        conn.close()
        print("Migración completada: 'cedula' renombrada a 'identificacion'")


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contrasena TEXT NOT NULL,
                rol TEXT NOT NULL
            )
        """)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                tipo_id TEXT,
                identificacion TEXT UNIQUE,
                telefono TEXT,
                direccion TEXT,
                correo TEXT,
                eliminado INTEGER DEFAULT 0
            )
        ''')

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS procesos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                tipo TEXT,
                descripcion TEXT,
                juzgado TEXT,
                estado TEXT,
                fecha_inicio TEXT,
                nombre TEXT, 
                fecha_fin TEXT, 
                radicado TEXT,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proceso_id INTEGER NOT NULL,
                cliente_id INTEGER NOT NULL,
                nombre TEXT NOT NULL,
                archivo TEXT,
                fecha TEXT,
                clase TEXT,
                ruta_archivo TEXT,
                eliminado INTEGER DEFAULT 0,
                FOREIGN KEY (proceso_id) REFERENCES procesos (id),
                FOREIGN KEY (cliente_id) REFERENCES clientes (id)
            )
        """)


        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contabilidad (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proceso_id INTEGER NOT NULL,
                descripcion TEXT,
                monto REAL,
                fecha TEXT,
                tipo TEXT,
                FOREIGN KEY (proceso_id) REFERENCES procesos (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendario (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                fecha TEXT NOT NULL,
                hora TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS liquidadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proceso_id INTEGER NOT NULL,
                nombre TEXT,
                archivo TEXT,
                fecha TEXT,
                FOREIGN KEY (proceso_id) REFERENCES procesos (id)
            )
        """)

        conn.commit()
        conn.close()

    def debug_imprimir_todos_los_clientes(self):
        conn = self.conectar()  # ✅
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, tipo_id, identificacion, eliminado FROM clientes")
        resultados = cursor.fetchall()
        for cliente in resultados:
            print("🧾 Cliente:", cliente)
        return resultados
    def get_contabilidad_por_proceso(self, proceso_id):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contabilidad WHERE proceso_id = ?", (proceso_id,))
        contabilidad = cursor.fetchall()
        conn.close()
        return contabilidad
    def agregar_contabilidad(self, proceso_id, descripcion, monto, fecha, tipo):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contabilidad (proceso_id, descripcion, monto, fecha, tipo)
            VALUES (?, ?, ?, ?, ?)
        ''', (proceso_id, descripcion, monto, fecha, tipo))
        conn.commit()
        conn.close()
    def actualizar_contabilidad(self, id_contabilidad, descripcion, monto, fecha, tipo):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE contabilidad
            SET descripcion = ?, monto = ?, fecha = ?, tipo = ?
            WHERE id = ?
        ''', (descripcion, monto, fecha, tipo, id_contabilidad))
        conn.commit()
        conn.close()
    def eliminar_contabilidad(self, id_contabilidad):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contabilidad WHERE id = ?", (id_contabilidad,))
        conn.commit()
        conn.close()
    def get_clientes(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM clientes")  # Asegúrate de que las columnas sean correctas
        clientes = cursor.fetchall()
        conn.close()
        return clientes
    def get_procesos_por_cliente(self, cliente_id):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procesos WHERE cliente_id = ?", (cliente_id,))
        procesos = cursor.fetchall()
        conn.close()
        return procesos
    def get_contabilidad_detallada(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contabilidad")  # Consulta que obtiene todos los registros contables
        contabilidad = cursor.fetchall()
        conn.close()
        return contabilidad
    def add_contabilidad(self, cliente_id, proceso_id, concepto, monto_total, abonado, restante, fecha, documento):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contabilidad (cliente_id, proceso_id, concepto, monto_total, abonado, restante, fecha, documento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cliente_id, proceso_id, concepto, monto_total, abonado, restante, fecha, documento))
        conn.commit()
        conn.close()
    def update_contabilidad(self, id_contabilidad, cliente_id, proceso_id, concepto, monto_total, abonado, restante, fecha, documento):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE contabilidad
            SET cliente_id = ?, proceso_id = ?, concepto = ?, monto_total = ?, abonado = ?, restante = ?, fecha = ?, documento = ?
            WHERE id = ?
        ''', (cliente_id, proceso_id, concepto, monto_total, abonado, restante, fecha, documento, id_contabilidad))
        conn.commit()
        conn.close()

    def delete_contabilidad(self, id_contabilidad):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM contabilidad WHERE id = ?", (id_contabilidad,))
        conn.commit()
        conn.close()



    # Método para obtener todos los eventos del calendario
    def get_calendario(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM calendario")
        eventos = cursor.fetchall()
        conn.close()
        return eventos

    # Método para agregar un nuevo evento al calendario
    def add_evento(self, evento, fecha, descripcion):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO calendario (titulo, fecha, descripcion)
            VALUES (?, ?, ?)
        ''', (evento, fecha, descripcion))
        conn.commit()
        conn.close()

    # Método para eliminar un evento por su ID
    def delete_evento(self, evento_id):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM calendario WHERE id = ?
        ''', (evento_id,))
        conn.commit()
        conn.close()

    # Método para actualizar un evento en el calendario
    def update_evento(self, evento_id, nuevo_evento, nueva_fecha, nueva_descripcion):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE calendario
            SET titulo = ?, fecha = ?, descripcion = ?
            WHERE id = ?
        ''', (nuevo_evento, nueva_fecha, nueva_descripcion, evento_id))
        conn.commit()
        conn.close()

    # Método para obtener los eventos filtrados por texto
    def search_evento(self, search_text):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM calendario WHERE titulo LIKE ?
        ''', ('%' + search_text + '%',))
        eventos = cursor.fetchall()
        conn.close()
        return eventos

    # Método para obtener todos los eventos del calendario con el texto de búsqueda
    def load_filtered_data(self, search_text):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM calendario WHERE titulo LIKE ?", ('%' + search_text + '%',))
        eventos = cursor.fetchall()
        conn.close()
        return eventos

    def get_liquidadores(self):
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM liquidadores")  # ajusta si la tabla tiene otro nombre
        resultados = cursor.fetchall()
        conn.close()
        return resultados
   