# modulos/contabilidad/contabilidad_model.py

from utils.contabilidad_db import ContabilidadDB
from utils.db_manager import DBManager

class ContabilidadModel:
    def __init__(self):
        # Pasamos la referencia al método conectar() de DBManager
        self.db = ContabilidadDB(DBManager().conectar)

    def get_clientes(self):
        """
        Retorna una lista de (id, nombre) de la tabla 'clientes'.
        """
        return self.db.get_clientes()

    def get_contabilidad_detallada(self):
        """
        Devuelve la lista de registros de contabilidad con los campos:
            (id, nombre_cliente, tipo, descripcion, valor, fecha)
        """
        return self.db.get_contabilidad_detallada()

    def add_contabilidad(self, cliente_id, tipo, valor, descripcion, fecha):
        """
        Inserta un nuevo registro en contabilidad.
        Parámetros:
            cliente_id: int
            tipo: str
            valor: float
            descripcion: str
            fecha: str
        """
        self.db.add_contabilidad(cliente_id, tipo, valor, descripcion, fecha)

    def update_contabilidad(self, id, cliente_id, tipo, valor, descripcion, fecha):
        """
        Actualiza un registro existente.
        Parámetros:
            id: int
            cliente_id: int
            tipo: str
            valor: float
            descripcion: str
            fecha: str
        """
        self.db.update_contabilidad(id, cliente_id, tipo, valor, descripcion, fecha)

    def delete_contabilidad(self, id):
        """
        Elimina un registro de contabilidad por su ID.
        Parámetros:
            id: int
        """
        self.db.delete_contabilidad(id)
