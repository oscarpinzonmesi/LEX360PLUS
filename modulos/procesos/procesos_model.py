class ProcesosModel:
    TIPOS_ACTUACION = {
    "Notificaciones y Comunicaciones": [
        "Notificación Personal",
        "Notificación por Estado",
        "Notificación por Aviso",
        "Notificación por Edicto",
        "Notificación por Estrados",
        "Notificación por Correo Certificado",
        "Certificado de Entrega / Acuse de Recibo"
    ],
    "Providencias Judiciales": [
        "Auto de Admisión de Demanda",
        "Auto de Mandamiento de Pago",
        "Auto de Emplazamiento",
        "Auto Interlocutorio",
        "Sentencia de Primera Instancia",
        "Sentencia de Segunda Instancia",
        "Resoluciones de Pruebas",
        "Resoluciones de Medidas Cautelares",
        "Oficios Judiciales",
        "Exhortos / Cartas Rogatorias / Comisiones"
    ],
    "Medidas Cautelares y Precautelativas": [
        "Auto de Embargo",
        "Acta de Secuestro",
        "Acta de Inscripción de Medida Cautelar",
        "Acta de Levantamiento de Medida",
        "Constancia de Entrega de Bienes",
        "Informe del Secuestre o Depositario",
        "Inventario de Bienes Embargados o Secuestrados"
    ],
    "Actuaciones Probatorias": [
        "Acta de Testimonios",
        "Dictamen Pericial",
        "Auto que Decreta Prueba",
        "Acta de Inspección Judicial",
        "Acta de Interrogatorio de Parte",
        "Solicitud de Documentos",
        "Oficio para Práctica de Pruebas",
        "Respuesta a Oficio / Informe Pericial"
    ],
    "Ejecución y Cumplimiento de Sentencias": [
        "Auto de Ejecución",
        "Auto de Liquidación de Costas",
        "Acta de Remate / Subasta",
        "Acta de Entrega de Bienes",
        "Oficio de Desembolso (dinero embargado)",
        "Informe de Cumplimiento de Medidas"
    ],
    "Recursos e Impugnaciones": [
        "Recurso de Reposición",
        "Recurso de Apelación",
        "Recurso de Queja",
        "Recurso de Revisión",
        "Providencia que Resuelve el Recurso",
        "Notificación del Recurso"
    ],
    "Terminación y Archivo del Proceso": [
        "Auto de Terminación del Proceso",
        "Auto de Archivo del Expediente",
        "Liquidación de Costas",
        "Auto de Desistimiento / Transacción",
        "Oficio de Cancelación de Medidas Cautelares",
        "Constancia de Entrega de Copias",
        "Informe de Archivo"
    ],
    "Conciliación y Mediación": [
        "Solicitud de Conciliación",
        "Acta de Conciliación",
        "Constancia de No Acuerdo",
        "Informe del Centro de Conciliación",
        "Auto que Homologa el Acuerdo"
    ],
    "Documentos Personales y Administrativos": [
        "Documento de Identidad",
        "Certificado de Existencia y Representación Legal",
        "Poderes y Mandatos",
        "Contratos y Acuerdos",
        "Certificados Bancarios",
        "Certificados de Tradición y Libertad",
        "Cartas de Instrucción",
        "Recibos de Pago",
        "Autorizaciones"
    ],
    "Otros Documentos": [
        "Comunicaciones Privadas",
        "Correspondencia (Correos, Cartas)",
        "Documentos Informativos (Circular, Boletín)",
        "Documentos Externos (No relacionados con el proceso)",
        "Fotografías y Evidencias",
        "Audios y Videos"
    ]
}

    def __init__(self, db):
        self.db = db

    def obtener_todos(self):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, tipo, descripcion, cliente_id, estado, fecha_inicio, fecha_fin FROM procesos")
        return cursor.fetchall()

    def obtener_por_id(self, proceso_id):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procesos WHERE id = ?", (proceso_id,))
        resultado = cursor.fetchone()
        conn.close()
        return resultado

    def insertar(self, cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin=None):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO procesos (cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (cliente_id, radicado, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin))
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return last_id

    def obtener_documentos_por_proceso(self, proceso_id):
        """
        Retorna lista de tuplas con:
        (id, nombre, categoria, tipo_actuacion, fecha, ruta_archivo, tipo_documento)
        para los documentos asociados al proceso.
        """
        conn = self.conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, categoria, tipo_actuacion, fecha, ruta_archivo, tipo_documento
            FROM documentos
            WHERE proceso_id = ?
        """, (proceso_id,))
        resultados = cursor.fetchall()
        conn.close()
        return resultados


    def actualizar(self, proceso_id, cliente_id, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE procesos
            SET cliente_id = ?, tipo = ?, descripcion = ?, juzgado = ?, estado = ?, fecha_inicio = ?, fecha_fin = ?
            WHERE id = ?
        ''', (cliente_id, tipo, descripcion, juzgado, estado, fecha_inicio, fecha_fin, proceso_id))
        conn.commit()
        conn.close()




    def eliminar(self, proceso_id):
        conn = self.db.conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM procesos WHERE id = ?", (proceso_id,))
        conn.commit()
        conn.close()

    def obtener_radicado_por_id(self, proceso_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT descripcion FROM procesos WHERE id = ?", (proceso_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado else ""
