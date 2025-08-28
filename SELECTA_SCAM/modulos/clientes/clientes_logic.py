# SELECTA_SCAM/modulos/clientes/clientes_logic.py
import logging
from .clientes_db import ClientesDB
from sqlalchemy.exc import SQLAlchemyError
# Debes importar el modelo Cliente para las consultas en la capa de la base de datos
from ...db.models import Cliente

logger = logging.getLogger(__name__)

class ClientesLogic:
    def __init__(self, clientes_db: ClientesDB):
        self.clientes_db = clientes_db
        self.logger = logger

    def get_clientes_data(self, **kwargs):
        return self.clientes_db.get_clientes_data(**kwargs)

    def add_new_cliente(self, **data):
        return self.clientes_db.add_cliente(**data)

    def get_cliente_details_for_edit(self, cliente_id):
        return self.clientes_db.get_cliente_details_as_dict(cliente_id)

    def update_cliente_details(self, cliente_id, **data):
        return self.clientes_db.update_cliente(cliente_id, **data)
    
    def get_all_clientes_for_combobox(self):
        # Esta función ya está bien, ya que llama a un método de la base de datos que devuelve tuplas.
        return self.clientes_db.get_all_clientes_ids_names()

    def marcar_como_eliminado(self, cliente_id: int) -> bool:
        return self.clientes_db.update_cliente(cliente_id, eliminado=True)

    def restaurar_clientes(self, cliente_ids: list) -> bool:
        try:
            for cliente_id in cliente_ids:
                self.clientes_db.update_cliente(cliente_id, eliminado=False)
            return True
        except Exception as e:
            self.logger.error("Error al restaurar múltiples clientes: %s", e)
            return False

    def eliminar_definitivo(self, cliente_id: int) -> bool:
        return self.clientes_db.delete_cliente_permanently(cliente_id)
    
    def marcar_multiples_como_eliminados(self, cliente_ids: list) -> bool:
        try:
            for cliente_id in cliente_ids:
                self.clientes_db.update_cliente(cliente_id, eliminado=True)
            return True
        except Exception as e:
            self.logger.error("Error al marcar múltiples clientes como eliminados: %s", e)
            return False

    def eliminar_clientes_definitivo(self, cliente_ids: list) -> bool:
        try:
            for cliente_id in cliente_ids:
                self.clientes_db.delete_cliente_permanently(cliente_id)
            return True
        except Exception as e:
            self.logger.error("Error al eliminar clientes permanentemente: %s", e)
            return False

    # >>> ¡CORRECCIÓN EN EL MÉTODO search_clientes! <<<
    # SELECTA_SCAM/modulos/clientes/clientes_logic.py
# ... (código existente) ...
    def search_clientes(self, search_text: str) -> list:
        """
        Busca clientes por nombre o ID.
        """
        self.logger.info(f"Buscando clientes con el texto: '{search_text}'")
        try:
            # Intenta buscar por ID
            cliente_id = int(search_text)
            # Ahora get_cliente_by_id devuelve un diccionario o None.
            cliente_data = self.clientes_db.get_cliente_by_id(cliente_id)
            if cliente_data:
                # Si se encuentra, retorna una lista con una tupla del diccionario.
                return [(cliente_data["id"], cliente_data["nombre"])]
            else:
                return []
        except ValueError:
            # Si no es un ID, busca por nombre.
            clientes = self.clientes_db.search_clientes_by_name(search_text)
            # search_clientes_by_name ya devuelve tuplas, por lo que no necesita cambios.
            return clientes
        except Exception as e:
            self.logger.error(f"Error inesperado al buscar clientes: {e}")
            return []