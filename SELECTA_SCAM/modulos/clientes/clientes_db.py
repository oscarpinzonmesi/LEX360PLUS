# SELECTA_SCAM/modulos/clientes/clientes_db.py
import logging
from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import or_, cast, String
from ...db.models import Cliente
from ...utils.db_manager import get_db_session

logger = logging.getLogger(__name__)

class ClientesDB:
    def __init__(self):
        self.logger = logger

    @contextmanager
    def get_session(self):
        session = get_db_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            self.logger.error("Error en transacción, haciendo rollback: %s", e, exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

    def get_clientes_data(self, incluir_eliminados=False, solo_eliminados=False, query=None):
        with self.get_session() as session:
            session.expire_all()
            q = session.query(
                Cliente.id,
                Cliente.nombre,
                Cliente.tipo_identificacion,
                Cliente.numero_identificacion,
                Cliente.email,
                Cliente.telefono,
                Cliente.direccion,
                Cliente.tipo_cliente,
                Cliente.fecha_creacion,
                Cliente.eliminado
            )

            conditions = []
            if solo_eliminados: conditions.append(Cliente.eliminado == True)
            elif not incluir_eliminados: conditions.append(Cliente.eliminado == False)
            if query:
                pattern = f"%{query}%"
                conditions.append(or_(Cliente.nombre.ilike(pattern), cast(Cliente.id, String).ilike(pattern)))
            if conditions: q = q.filter(*conditions)
            resultados = q.order_by(Cliente.id).all()
            return resultados


    def delete_cliente_permanently(self, cliente_id: int) -> bool:
        """
        Elimina un cliente de forma permanente de la base de datos.
        """
        with self.get_session() as session:
            cliente = session.query(Cliente).get(cliente_id)
            if cliente:
                session.delete(cliente)
                return True
            self.logger.warning(f"No se encontró el cliente con ID {cliente_id} para eliminación definitiva.")
            return False


    def add_cliente(self, **data):
        with self.get_session() as session:
            new_cliente = Cliente(**data, fecha_creacion=datetime.now(), eliminado=False)
            session.add(new_cliente)
            session.flush()
            return new_cliente.id

    def update_cliente(self, cliente_id, **data):
        with self.get_session() as session:
            cliente = session.query(Cliente).get(cliente_id)
            if cliente:
                for key, value in data.items(): setattr(cliente, key, value)
                return True
            return False

    def get_cliente_details_as_dict(self, cliente_id: int) -> dict | None:
        """
        Obtiene los datos de un cliente y los devuelve como un diccionario seguro,
        evitando el DetachedInstanceError.
        """
        with self.get_session() as session:
            cliente = session.query(Cliente).get(cliente_id)
            if cliente:
                # Convertimos el objeto a un diccionario ANTES de que se cierre la sesión
                return {
                    'id': cliente.id,
                    'nombre': cliente.nombre,
                    'tipo_identificacion': cliente.tipo_identificacion,
                    'numero_identificacion': cliente.numero_identificacion,
                    'email': cliente.email,
                    'telefono': cliente.telefono,
                    'direccion': cliente.direccion,
                    'tipo_cliente': cliente.tipo_cliente
                }
            return None


    def get_all_clientes_ids_names(self) -> list[tuple]:
        """
        Obtiene una lista de tuplas con el ID y el nombre de todos los clientes activos.
        """
        with self.get_session() as session:
            try:
                # La consulta ahora selecciona solo el id y el nombre, no el objeto completo.
                # Esto es más eficiente y evita el DetachedInstanceError.
                return session.query(Cliente.id, Cliente.nombre).filter(Cliente.eliminado == False).order_by(Cliente.nombre).all()
            except Exception as e:
                self.logger.error("Error al obtener IDs y nombres de clientes: %s", e)
                return []


    def search_clientes_by_name(self, name_text: str) -> list[tuple]:
        """
        Ejecuta una consulta para buscar clientes por nombre y devuelve tuplas.
        """
        with self.get_session() as session:
            try:
                # Usa .options(joinedload(Cliente.procesos)) para cargar datos relacionados
                # Usa .all() para forzar la ejecución de la consulta antes de que la sesión se cierre
                clientes = session.query(Cliente).filter(Cliente.nombre.ilike(f'%{name_text}%')).all()
                # Extrae los datos necesarios en un formato simple (list of tuples)
                return [(c.id, c.nombre) for c in clientes]
            except Exception as e:
                self.logger.error(f"Error al buscar clientes por nombre en la base de datos: {e}", exc_info=True)
                return []
    
    # SELECTA_SCAM/modulos/clientes/clientes_db.py
# ... (código existente) ...

    def get_cliente_by_id(self, cliente_id: int):
        """
        Obtiene un cliente por su ID y devuelve sus datos como un diccionario.
        """
        with self.get_session() as session:
            try:
                cliente = session.query(Cliente).filter(Cliente.id == cliente_id).first()
                if cliente:
                    # Devuelve un diccionario con los datos del cliente.
                    return {"id": cliente.id, "nombre": cliente.nombre}
                return None
            except Exception as e:
                self.logger.error(f"Error al obtener cliente por ID: {e}", exc_info=True)
                return None