import logging
from SELECTA_SCAM.modulos.procesos.procesos_db import ProcesosDB

logger = logging.getLogger(__name__)

class ProcesosLogic:
    def __init__(self, procesos_db: ProcesosDB):
        self.logger = logging.getLogger(__name__)
        #self.logger.debug("ProcesosLogic: Iniciando __init__.")
        # ESTA LÍNEA ES CORRECTA: Asigna la instancia de la base de datos a self.procesos_db
        self.procesos_db = procesos_db 
        #self.logger.info("ProcesosLogic: Inicializada.")

    def get_procesos_by_client_display(self, cliente_id: int):
        self.logger.debug(f"ProcesosLogic: Intentando obtener procesos para cliente ID: {cliente_id}.")
        try:
            self.logger.debug("ProcesosLogic: Intentando obtener sesión de ProcesosDB para get_procesos_by_cliente_id.")
            # CAMBIO: Usar self.procesos_db
            with self.procesos_db.get_session() as session: 
                self.logger.debug(f"ProcesosLogic: Sesión obtenida, llamando a ProcesosDB.get_procesos_by_cliente_id para cliente {cliente_id}.")
                # CAMBIO: Usar self.procesos_db
                procesos = self.procesos_db.get_procesos_by_cliente_id(session, cliente_id) 
                self.logger.debug(f"ProcesosLogic: Obtenidos {len(procesos) if procesos else 0} procesos para cliente {cliente_id}.")
                return [(p.id, p.radicado) for p in procesos]
        except Exception as e:
            self.logger.exception(f"ProcesosLogic: Error al obtener procesos para cliente {cliente_id}.")
            raise

    def get_proceso_radicado_by_id(self, proceso_id: int):
        self.logger.debug(f"ProcesosLogic: Intentando obtener radicado para proceso ID: {proceso_id}.")
        try:
            self.logger.debug("ProcesosLogic: Intentando obtener sesión de ProcesosDB para get_proceso.")
            # CAMBIO: Usar self.procesos_db
            with self.procesos_db.get_session() as session: 
                self.logger.debug(f"ProcesosLogic: Sesión obtenida, llamando a ProcesosDB.get_proceso para ID {proceso_id}.")
                # CAMBIO: Usar self.procesos_db
                proceso = self.procesos_db.get_proceso(session, proceso_id) 
                radicado = proceso.radicado if proceso else "Sin Proceso"
                self.logger.debug(f"ProcesosLogic: Radicado para proceso ID {proceso_id} es: '{radicado}'.")
                return radicado
        except Exception as e:
            self.logger.exception(f"ProcesosLogic: Error al obtener radicado de proceso por ID {proceso_id}.")
            return "Error"
            
    def get_proceso_id_by_radicado(self, radicado: str):
        self.logger.debug(f"ProcesosLogic: Intentando obtener ID de proceso para radicado: '{radicado}'.")
        try:
            self.logger.debug("ProcesosLogic: Intentando obtener sesión de ProcesosDB para get_proceso_by_radicado.")
            # CAMBIO: Usar self.procesos_db
            with self.procesos_db.get_session() as session: 
                self.logger.debug(f"ProcesosLogic: Sesión obtenida, llamando a ProcesosDB.get_proceso_by_radicado para radicado '{radicado}'.")
                # CAMBIO: Usar self.procesos_db
                proceso = self.procesos_db.get_proceso_by_radicado(session, radicado) 
                proceso_id = proceso.id if proceso else None
                self.logger.debug(f"ProcesosLogic: ID de proceso para radicado '{radicado}' es: {proceso_id}.")
                return proceso_id
        except Exception as e:
            self.logger.exception(f"ProcesosLogic: Error al obtener ID de proceso por radicado '{radicado}'.")
            return None
            
    def get_all_active_procesos(self) -> list:
        """
        Obtiene todos los procesos activos formateados como lista de tuplas (id, nombre).
        """
        self.logger.debug("ProcesosLogic: Obteniendo todos los procesos activos.")
        
        # Llama a la base de datos sin el argumento 'active_only'
        # y filtra los resultados en la capa de lógica.
        all_procesos = self.procesos_db.get_all_procesos()
        
        # Filtra para obtener solo los procesos activos (no eliminados).
        active_procesos = [p for p in all_procesos if not p.eliminado]
        
        return [(p.id, p.radicado) for p in active_procesos]

    def get_procesos_by_client_id(self, cliente_id: int) -> list:
        """
        Obtiene los procesos asociados a un cliente específico, formateados como
        lista de tuplas (id, nombre) para QComboBoxes.
        """
        logger.debug(f"ProcesosLogic: Obteniendo procesos para cliente_id={cliente_id}.")
        # CAMBIO: Usar self.procesos_db en lugar de self.db_manager
        procesos = self.procesos_db.get_procesos_by_client_id(cliente_id) 
        return [(p.id, p.radicado) for p in procesos] # Cambiado 'nombre' por 'radicado' para coherencia con tus otros métodos