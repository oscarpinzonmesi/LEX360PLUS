import sqlite3

def obtener_conexion():
    return sqlite3.connect("base_de_datos.db")
