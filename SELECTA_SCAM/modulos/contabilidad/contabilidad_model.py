import logging
from datetime import datetime, date # Importar date y datetime
from SELECTA_SCAM.modulos.contabilidad.contabilidad_db import ContabilidadDB # Asumo que esta es la DB para Contabilidad
from SELECTA_SCAM.db.models import Contabilidad # Importar el modelo ORM de Contabilidad
from typing import Optional
from SELECTA_SCAM.db.models import Contabilidad, TipoContable

logger = logging.getLogger(__name__)

class ContabilidadModel:
    def __init__(self, contabilidad_db: ContabilidadDB):
        self.contabilidad_db = contabilidad_db
        #logger.info("ContabilidadModel: Inicializado con ContabilidadDB.")

    # Modificado: Añadir search_term
    def get_all_contabilidad_records(self, cliente_id: int = None, proceso_id: int = None, search_term: str = None) -> list[Contabilidad]:
        """
        Obtiene todos los registros de contabilidad de la base de datos, aplicando filtros.
        Retorna objetos ORM de Contabilidad.
        """
        #logger.debug(f"ContabilidadModel: Obteniendo todos los registros de contabilidad de la DB (cliente_id={cliente_id}, proceso_id={proceso_id}, search_term='{search_term}').")
        # Asegurarse de llamar al método correcto de la DB y pasar el search_term
        records = self.contabilidad_db.get_filtered_contabilidad_records(cliente_id, proceso_id, search_term)
        #logger.debug(f"ContabilidadModel: {len(records)} registros de contabilidad obtenidos de la DB.")
        return records


        
    # En: contabilidad_model.py
    # Reemplaza el método completo con este:

        # En: contabilidad_model.py

    def update_contabilidad_record(self, record_id: int, cliente_id: int, proceso_id: int, tipo_id: int, descripcion: str, valor: float, fecha):
        """
        Busca un registro en la DB, actualiza sus campos y guarda los cambios.
        """
        # Convierte la fecha de string a objeto 'date' si es necesario
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Formato de fecha inválido: {fecha}")
                raise ValueError("Formato de fecha inválido.")

        try:
            with self.contabilidad_db.get_session() as session:
                # Busca el registro que queremos actualizar
                record = session.query(Contabilidad).filter(Contabilidad.id == record_id).first()
                
                # Si se encuentra, actualiza cada uno de sus campos
                if record:
                    record.cliente_id = cliente_id
                    record.proceso_id = proceso_id
                    record.tipo_contable_id = tipo_id
                    record.descripcion = descripcion
                    record.monto = valor
                    record.fecha = fecha
                    
                    logger.info(f"Registro ID {record_id} actualizado en la sesión y listo para guardar.")
                else:
                    logger.warning(f"No se encontró el registro con ID {record_id} para actualizar.")
            
            # El context manager 'with' se encarga de hacer el commit (guardar) aquí
            logger.info(f"Cambios para el registro ID {record_id} guardados en la DB.")

        except Exception as e:
            logger.error(f"Error al actualizar registro de contabilidad en la DB: {e}")
            raise

    def delete_contabilidad_record(self, record_id: int):
        """
        Elimina un registro de contabilidad de la base de datos.
        """
        #logger.debug(f"ContabilidadModel: Intentando eliminar registro ID {record_id} de la DB.")
        # Modificado: Utilizar el context manager de ContabilidadDB y pasar la sesión
        try:
            with self.contabilidad_db.get_session() as session:
                self.contabilidad_db.delete_record(session, record_id)
            logger.info(f"ContabilidadModel: Registro de contabilidad ID {record_id} eliminado de la DB.")
        except Exception as e:
            logger.error(f"ContabilidadModel: Error al eliminar registro de contabilidad: {e}")
            raise

    def get_contabilidad_record_by_id(self, record_id: int):
        """
        Obtiene un registro de contabilidad por su ID.
        Retorna un objeto ORM de Contabilidad o None.
        """
        #logger.debug(f"ContabilidadModel: Obteniendo registro de contabilidad ID {record_id} de la DB.")
        # Modificado: Asegurarse de que este método en ContabilidadDB existe y es llamado correctamente
        record = self.contabilidad_db.get_contabilidad_record_by_id(record_id) # Usamos el nuevo método en DB
        #logger.debug(f"ContabilidadModel: Registro ID {record_id} obtenido: {record is not None}.")
        return record

    # Modificado: Añadir search_term
    def get_filtered_contabilidad_records(self, cliente_id: Optional[int] = None, proceso_id: Optional[int] = None, search_term: Optional[str] = None) -> list:
        """
        Llama al método de la capa de base de datos para obtener registros de contabilidad filtrados.
        """
        #logger.debug(f"ContabilidadModel: Solicitando registros filtrados de DB (cliente_id={cliente_id}, proceso_id={proceso_id}, search_term='{search_term}').")
        return self.contabilidad_db.get_filtered_contabilidad_records(
            cliente_id=cliente_id, 
            proceso_id=proceso_id,
            search_term=search_term # <--- ¡PASAR search_term!
        )
    
    
    def add_contabilidad_record(self, cliente_id: int, proceso_id: Optional[int], tipo_id: int, descripcion: str, valor: float, fecha: str):
        """
        Añade un nuevo registro de contabilidad a la base de datos.
        """
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"ContabilidadModel: Formato de fecha inválido para añadir: {fecha}")
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD.")
        elif not isinstance(fecha, (date, datetime)):
            logger.error(f"ContabilidadModel: Tipo de fecha inválido para añadir: {type(fecha)}")
            raise TypeError("La fecha debe ser un string en formato YYYY-MM-DD o un objeto date/datetime.")
        
        try:
            with self.contabilidad_db.get_session() as session:
                self.contabilidad_db.add_contabilidad(session, cliente_id=cliente_id,
                                            proceso_id=proceso_id, tipo_id=tipo_id,
                                            descripcion=descripcion, valor=valor, fecha=fecha)
            logger.info("ContabilidadModel: Nuevo registro de contabilidad añadido en la DB.")
        except Exception as e:
            logger.error(f"ContabilidadModel: Error al añadir registro de contabilidad: {e}")
            raise

    def get_ingreso_types(self):
        """
        Retorna una lista de los nombres de los tipos de registro que son de tipo 'ingreso'.
        """
        # Consulta la base de datos para obtener los tipos de contabilidad
        # con el atributo `es_ingreso` como verdadero.
        with self.contabilidad_db.get_session() as session:
            return [t.nombre for t in session.query(TipoContable).filter(TipoContable.es_ingreso == True).all()]

    def get_gasto_types(self):
        """
        Retorna una lista de los nombres de los tipos de registro que son de tipo 'gasto'.
        """
        # Consulta la base de datos para obtener los tipos de contabilidad
        # con el atributo `es_ingreso` como falso.
        with self.contabilidad_db.get_session() as session:
            return [t.nombre for t in session.query(TipoContable).filter(TipoContable.es_ingreso == False).all()]

            hola 