# SELECTA_SCAM/modulos/contabilidad/contabilidad_excel.py

import pandas as pd

def generar_excel_resumen_contabilidad(ruta_guardar: str, report_data) -> bool:
    """
    Genera un reporte de contabilidad en Excel con datos y dos gráficos:
    uno de barras y otro circular (torta) en 3D.
    """
    try:
        # 1. Preparar los datos (sin cambios aquí)
        datos_para_tabla = []
        for record in report_data.records:
            cliente_nombre = record.cliente.nombre if record.cliente else "N/A"
            proceso_radicado = record.proceso.radicado if record.proceso else "N/A"
            tipo_nombre = report_data.tipos_contables_map.get(record.tipo_contable_id, 'Desconocido')
            
            datos_para_tabla.append({
                "ID": record.id, "Cliente": cliente_nombre, "Proceso": proceso_radicado,
                "Tipo": tipo_nombre, "Descripción": record.descripcion, "Valor": record.monto,
                "Fecha": record.fecha.strftime("%Y-%m-%d")
            })
        
        df_registros = pd.DataFrame(datos_para_tabla)
        writer = pd.ExcelWriter(ruta_guardar, engine='xlsxwriter')
        
        df_registros.to_excel(writer, sheet_name='Registros', index=False)
        
        # --- Hoja de Resumen (sin cambios aquí) ---
        workbook = writer.book
        resumen_sheet = workbook.add_worksheet('Resumen')
        
        resumen_sheet.write('A1', 'Concepto')
        resumen_sheet.write('B1', 'Total Ingresos')
        resumen_sheet.write('C1', 'Total Gastos')
        resumen_sheet.write('A2', 'Totales')
        resumen_sheet.write('B2', report_data.total_ingresos)
        resumen_sheet.write('C2', report_data.total_gastos)
        resumen_sheet.write('A4', 'Saldo Neto')
        resumen_sheet.write('B4', report_data.saldo_neto)

        # --- Gráfico 1: Barras (el que ya funciona) ---
        chart_bar = workbook.add_chart({'type': 'column'})
        chart_bar.add_series({
            'name':       '=Resumen!$B$1',
            'categories': '=Resumen!$A$2',
            'values':     '=Resumen!$B$2',
            'fill':       {'color': '#107C10'}, # Verde
            'border':     {'none': True},
        })
        chart_bar.add_series({
            'name':       '=Resumen!$C$1',
            'categories': '=Resumen!$A$2',
            'values':     '=Resumen!$C$2',
            'fill':       {'color': '#D83B01'}, # Rojo
            'border':     {'none': True},
        })
        chart_bar.set_title({'name': 'Resumen de Ingresos y Gastos'})
        chart_bar.set_y_axis({'name': 'Valor ($)', 'major_gridlines': {'visible': False}})
        chart_bar.set_x_axis({'visible': False})
        chart_bar.set_legend({'position': 'top'})
        resumen_sheet.insert_chart('E2', chart_bar) # Posición del primer gráfico

        # --- INICIO DE LA NUEVA LÓGICA ---
        # --- Gráfico 2: Torta / Circular 3D ---
        chart_pie = workbook.add_chart({'type': 'pie'})
        chart_pie.set_style(10) # Estilo 3D

        # Usamos el método de colorear por 'puntos' que es ideal para gráficos de torta
        chart_pie.add_series({
            'name':       'Distribución de Ingresos y Gastos',
            'categories': '=Resumen!$B$1:$C$1', # Etiquetas: "Total Ingresos", "Total Gastos"
            'values':     '=Resumen!$B$2:$C$2', # Valores correspondientes
            'points': [
                {'fill': {'color': '#107C10'}}, # Verde
                {'fill': {'color': '#D83B01'}}, # Rojo
            ],
        })
        chart_pie.set_title({'name': 'Distribución Porcentual'})
        resumen_sheet.insert_chart('E18', chart_pie) # Posición del segundo gráfico, más abajo
        # --- FIN DE LA NUEVA LÓGICA ---

        # Ajustar anchos de columna
        writer.sheets['Registros'].set_column('B:B', 30)
        writer.sheets['Registros'].set_column('E:E', 40)
        writer.sheets['Registros'].set_column('F:F', 15)
        writer.sheets['Resumen'].set_column('A:C', 20)

        writer.close()
        return True

    except Exception as e:
        print(f"Error al generar Excel: {e}")
        return False