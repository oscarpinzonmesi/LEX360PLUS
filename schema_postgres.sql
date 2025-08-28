# -*- coding: utf-8 -*-
import sqlite3
import psycopg2
import unicodedata
import traceback
import sys

# ----------------------------
# Columnas que deben tratarse como booleanas
# ----------------------------
columnas_booleanas = {
    'clientes':   ['eliminado'],
    'documentos': ['eliminado'],
    # (Solo aquí, no pongas 'procesos' ni 'usuarios'; así el id de 'procesos' jamás se convertirá a bool)
}

def limpiar_cadena(texto):
    texto = unicodedata.normalize('NFKC', texto)
    return ''.join(c for c in texto if unicodedata.category(c)[0] != 'C')

# ----------------------------
# Conexión a SQLite
# ----------------------------
try:
    sqlite_conn = sqlite3.connect('data/base_oficial.db')
    sqlite_cursor = sqlite_conn.cursor()
    print("✅ Conectado a base_oficial.db")
except Exception as e:
    print(f"❌ Error en SQLite: {e}")
    sys.exit(1)

# ----------------------------
# Conexión a PostgreSQL
# ----------------------------
try:
    pg_conn = psycopg2.connect(
        host='localhost',
        database='bd_prueba',
        user='postgres',
        password='nuevaclave123'
    )
    pg_cursor = pg_conn.cursor()

    # Crear tabla usuarios si no existe
    pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
      id         INTEGER PRIMARY KEY,
      usuario    VARCHAR(100) NOT NULL,
      contrasena VARCHAR(100) NOT NULL,
      rol        VARCHAR(50)  NOT NULL
    );
    """)
    pg_conn.commit()

except Exception as e:
    print("❌ Error en PostgreSQL:")
    try:
        print(str(e).encode('latin1').decode('latin1'))
    except:
        print(repr(e))
    traceback.print_exc()
    sys.exit(1)

# ----------------------------
# Función de migración por tabla
# ----------------------------
def migrar_tabla(tabla, columnas):
    try:
        print(f"\n🚀 Migrando tabla: {tabla}")
        sqlite_cursor.execute(f"SELECT {', '.join(columnas)} FROM {tabla}")
        registros = sqlite_cursor.fetchall()

        for fila in registros:
            fila_limpia = []
            for col_name, valor in zip(columnas, fila):
                if tabla in columnas_booleanas and col_name in columnas_booleanas[tabla]:
                    # Solo aquí convertimos 0/1 a True/False
                    if isinstance(valor, int) and valor in (0, 1):
                        fila_limpia.append(bool(valor))
                    else:
                        fila_limpia.append(valor)
                else:
                    if isinstance(valor, str):
                        fila_limpia.append(limpiar_cadena(valor))
                    else:
                        fila_limpia.append(valor)

            placeholders = ', '.join(['%s'] * len(columnas))
            columnas_str = ', '.join(columnas)
            insert_query = f"INSERT INTO {tabla} ({columnas_str}) VALUES ({placeholders})"
            pg_cursor.execute(insert_query, fila_limpia)

        print(f"✅ {len(registros)} registros insertados en {tabla}")

    except sqlite3.OperationalError as sqlite_err:
        if 'no such table' in str(sqlite_err).lower():
            print(f"⚠️ Tabla '{tabla}' no existe en SQLite. Se omite y se continúa.")
            return
        else:
            print(f"❌ Error SQLite en tabla {tabla}: {sqlite_err}")
            traceback.print_exc()
            return

    except Exception as e:
        # Si falla un INSERT en PostgreSQL, hacemos rollback de esa tabla y continuamos
        print(f"❌ Error en tabla {tabla}: {e}")
        traceback.print_exc()
        pg_conn.rollback()
        return

# ----------------------------
# Listado de tablas y columnas
# ----------------------------
tablas_columnas = {
    'clientes':       ['id', 'nombre', 'tipo_id', 'identificacion', 'correo', 'telefono', 'direccion', 'eliminado'],
    'procesos':       ['id', 'cliente_id', 'tipo', 'descripcion', 'juzgado', 'estado', 'fecha_inicio', 'nombre', 'fecha_fin', 'radicado'],
    'documentos':     ['id', 'proceso_id', 'nombre', 'archivo', 'fecha', 'categoria', 'eliminado', 'cliente_id', 'ruta_archivo', 'tipo_documento', 'tipo_actuacion'],
    'contabilidad':   ['id', 'cliente_id', 'tipo', 'valor', 'descripcion', 'fecha'],
    'calendario':     ['id', 'titulo', 'descripcion', 'fecha', 'clase'],
    'usuarios':       ['id', 'usuario', 'contrasena', 'rol'],
    'robot_busquedas':['id', 'nombre', 'estado']
}

# ----------------------------
# Ejecutar migración
# ----------------------------
for tabla, columnas in tablas_columnas.items():
    migrar_tabla(tabla, columnas)

pg_conn.commit()
pg_cursor.close()
pg_conn.close()
sqlite_cursor.close()
sqlite_conn.close()

print("\n🎉 Migración completada exitosamente.")
