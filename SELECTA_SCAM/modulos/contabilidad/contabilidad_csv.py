# SELECTA_SCAM/modulos/contabilidad/contabilidad_csv.py

import csv

def generar_csv_resumen_contabilidad(ruta_guardar: str, report_data) -> bool:
    """
    Genera un reporte de contabilidad simple en formato CSV.
    """
    try:
        headers = ["ID", "Cliente", "Proceso", "Tipo", "Descripción", "Valor", "Fecha"]
        
        with open(ruta_guardar, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers) # Escribir encabezados
            
            for record in report_data.records:
                cliente_nombre = record.cliente.nombre if record.cliente else "N/A"
                proceso_radicado = record.proceso.radicado if record.proceso else "N/A"
                tipo_nombre = report_data.tipos_contables_map.get(record.tipo_contable_id, 'Desconocido')
                
                writer.writerow([
                    record.id,
                    cliente_nombre,
                    proceso_radicado,
                    tipo_nombre,
                    record.descripcion,
                    record.monto,
                    record.fecha.strftime("%Y-%m-%d")
                ])
        return True
    except Exception as e:
        print(f"Error al generar CSV: {e}")
        return False