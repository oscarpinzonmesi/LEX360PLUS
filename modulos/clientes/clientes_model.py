class ClientesModel:
    def __init__(self, db_manager):
        self.db = db_manager.clientes_db  # Acceso directo al módulo de clientes

    def obtener_clientes(self):
        # Usar el método get_clientes para obtener los clientes activos
        return self.db.get_clientes(incluir_eliminados=False)


    def buscar_por_id_o_nombre(self, texto):
        texto_lower = texto.lower()
        query = """
            SELECT * FROM clientes 
            WHERE (nombre LIKE ? OR identificacion LIKE ? OR id LIKE ?) 
            AND eliminado = ?
        """
        # Usar el método get_clientes para ejecutar la consulta
        return self.db.execute(query, (f"%{texto_lower}%", f"%{texto_lower}%", f"%{texto_lower}%", 0))

    def buscar_eliminados(self, texto=""):
        texto_lower = texto.lower()
        query = """
            SELECT * FROM clientes 
            WHERE (nombre LIKE ? OR id LIKE ?) 
            AND eliminado = ?
        """
        return self.db.execute(query, (f"%{texto_lower}%", f"%{texto_lower}%", 1))

    def marcar_como_eliminado(self, cliente_id):
        self.db.delete_cliente(cliente_id)  # Usar el método delete_cliente en lugar de un query directo

    def recuperar_cliente(self, cliente_id):
        self.db.restaurar_cliente(cliente_id)  # Usar el método restaurar_cliente en lugar de un query directo

    def agregar_cliente(self, nombre, tipo_id, identificacion, correo, telefono, direccion):
        # Verificación previa de existencia en la base de datos
        if self.buscar_por_identificacion(identificacion):
            raise ValueError("El cliente con esa identificación ya está registrado.")
        
        self.db.add_cliente(nombre, tipo_id, identificacion, correo, telefono, direccion)  # Usar el método add_cliente


    def actualizar_cliente(self, id_cliente, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado=0):
        self.db.actualizar_cliente(id_cliente, nombre, tipo_id, identificacion, correo, telefono, direccion, eliminado)  # Usar el método actualizar_cliente

    def debug_imprimir_clientes_eliminados(self):
        # Aquí ya no se necesita ejecutar un query directamente, sino que usar el método de la base de datos
        return self.db.debug_imprimir_clientes_eliminados()  # Usar el método debug_imprimir_clientes_eliminados de ClientesDB
