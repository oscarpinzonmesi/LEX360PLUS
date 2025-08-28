# usuarios/permisos.py

# Definición de módulos permitidos por cada rol
PERMISOS = {
    "administrador": ["clientes", "procesos", "documentos", "contabilidad", "liquidadores", "calendario"],
    "abogado":       ["clientes", "procesos", "documentos", "calendario"],
    "asistente":    ["clientes", "procesos", "documentos", "calendario"]
}
