# En: SELECTA_SCAM/modulos/contabilidad/contabilidad_pdf.py

import os
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch

# (Tu dataclass ContabilidadReportData debe estar en contabilidad_logic.py)
# from .contabilidad_logic import ContabilidadReportData 

# En: SELECTA_SCAM/modulos/contabilidad/contabilidad_pdf.py

def generar_pdf_resumen_contabilidad(ruta_guardar: str, report_data) -> bool:
    try:
        doc = SimpleDocTemplate(ruta_guardar, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # ... (el código del Título y Resumen se mantiene igual) ...
        titulo = Paragraph("Reporte de Resumen Contable", styles['h1'])
        story.append(titulo)
        story.append(Spacer(1, 0.2*inch))
        info_filtros = f"<b>Filtros Aplicados:</b> {report_data.filtros}"
        story.append(Paragraph(info_filtros, styles['Normal']))
        story.append(Spacer(1, 0.2*inch))
        resumen_texto = f"""
        <b>Total Ingresos:</b> <font color='green'>${report_data.total_ingresos:,.2f}</font><br/>
        <b>Total Gastos:</b> <font color='red'>${report_data.total_gastos:,.2f}</font><br/>
        <b>Saldo Neto:</b> ${report_data.saldo_neto:,.2f}
        """
        story.append(Paragraph(resumen_texto, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph("Detalle de Registros:", styles['h3']))
        story.append(Spacer(1, 0.1*inch))
        
        headers = ["ID", "Cliente", "Proceso", "Tipo", "Descripción", "Valor", "Fecha"]
        table_data = [headers]
        for record in report_data.records:
            cliente_nombre = record.cliente.nombre if record.cliente else "N/A"
            proceso_radicado = record.proceso.radicado if record.proceso else "N/A"
            tipo_nombre = report_data.tipos_contables_map.get(record.tipo_contable_id, 'Desconocido')
            
            table_data.append([
                record.id,
                Paragraph(cliente_nombre, styles['Normal']),
                Paragraph(proceso_radicado, styles['Normal']),
                Paragraph(tipo_nombre, styles['Normal']),
                Paragraph(record.descripcion, styles['Normal']),
                f"${record.monto:,.2f}",
                record.fecha.strftime("%Y-%m-%d")
            ])
            
        # --- CORRECCIÓN DEL ANCHO DE COLUMNAS ---
        tabla = Table(table_data, colWidths=[0.4*inch, 1.2*inch, 0.8*inch, 1.2*inch, 2.2*inch, 0.9*inch, 0.7*inch])
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#5D566F")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F0F5")),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ])
        tabla.setStyle(style)
        
        for i, row in enumerate(table_data):
            if i % 2 == 0 and i != 0:
                tabla.setStyle(TableStyle([('BACKGROUND', (0, i), (-1, i), colors.HexColor("#FFFFFF"))]))

        story.append(tabla)
        story.append(Spacer(1, 0.5*inch))
        
        # Esta línea ahora funcionará porque datetime está importado
        fecha_generacion = f"Generado por SELECTA SCAM el {datetime.now().strftime('%Y-%m-%d a las %H:%M:%S')}"
        story.append(Paragraph(fecha_generacion, styles['Normal']))

        doc.build(story)
        return True

    except Exception as e:
        # Usamos logger si está disponible, si no, un print
        print(f"Error al generar el PDF con ReportLab Platypus: {e}")
        return False
    def draw_header(canvas_obj, y_pos):
        """Dibuja el encabezado de la página."""
        nonlocal page_number
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica-Bold", 20)
        canvas_obj.setFillColorRGB(0.827, 0.42, 0.573)
        canvas_obj.drawCentredString(width / 2.0, y_pos, "Reporte de Resumen Contable")

        temp_logo_path = logo_path
        if isinstance(temp_logo_path, (list, tuple)):
            temp_logo_path = temp_logo_path[0] if temp_logo_path else ''

        if temp_logo_path and os.path.exists(temp_logo_path):
            try:
                logo = ImageReader(temp_logo_path)
                canvas_obj.drawImage(logo, width - 120, y_pos - 20, width=70, height=70, preserveAspectRatio=True)
            except Exception as e:
                print(f"Advertencia: No se pudo cargar la imagen del logo: {e}")

        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColorRGB(0.2, 0.2, 0.2)
        canvas_obj.drawString(width - 70, 30, f"Página {page_number}")
        canvas_obj.restoreState()
        return y_pos - 60

    y_position = draw_header(c, y_position)

    # --- Totales de Resumen ---
    c.setFont("Helvetica-Bold", 14)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(50, y_position, f"Filtros Aplicados: {report_data.filtros}")
    y_position -= line_height * 2

    c.setFont("Helvetica", 14)
    c.drawString(50, y_position, f"Total Ingresos: ${report_data.total_ingresos:,.2f}")
    y_position -= line_height
    c.drawString(50, y_position, f"Total Gastos: ${report_data.total_gastos:,.2f}")
    y_position -= line_height * 2

    c.setFont("Helvetica-Bold", 16)
    if report_data.saldo_neto < 0:
        c.setFillColorRGB(0.8, 0.0, 0.0)
    elif report_data.saldo_neto > 0:
        c.setFillColorRGB(0.0, 0.5, 0.0)
    else:
        c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(50, y_position, f"Saldo Neto: ${report_data.saldo_neto:,.2f}")
    y_position -= line_height * 2

    # --- Detalle de Registros ---
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(50, y_position, "Detalle de Registros:")
    y_position -= line_height

    # Encabezados de la tabla de detalles
    headers = ["ID", "Cliente", "Proceso", "Tipo", "Descripción", "Valor", "Fecha"]
    col_widths = [40, 100, 80, 80, 120, 80, 80]
    x_position = 50

    c.setFont("Helvetica-Bold", 10)
    for i, header in enumerate(headers):
        c.drawString(x_position, y_position, header)
        x_position += col_widths[i]
    y_position -= line_height

    # Dibuja la línea horizontal del encabezado de la tabla
    c.line(50, y_position + 5, 550, y_position + 5)
    
    # Rellena los datos de los registros
    c.setFont("Helvetica", 8)
    
    # Reemplaza tu bucle for completo con este:
    for i, record in enumerate(report_data.records):
        if y_position < 70:
            c.showPage()
            page_number += 1
            y_position = draw_header(c, height - 60)
            c.setFont("Helvetica-Bold", 10)
            x_position_restart = 50
            for j, header in enumerate(headers):
                c.drawString(x_position_restart, y_position, header)
                x_position_restart += col_widths[j]
            y_position -= line_height
            c.line(50, y_position + 5, 550, y_position + 5)
            y_position -= line_height
            c.setFont("Helvetica", 8)

        # --- INICIO DE LA CORRECCIÓN ---
        # "Traducimos" los datos del objeto 'record' a variables simples
        cliente_nombre = record.cliente.nombre if record.cliente else "N/A"
        proceso_radicado = record.proceso.radicado if record.proceso else "N/A"
        tipo_nombre = report_data.tipos_contables_map.get(record.tipo_contable_id, 'Desconocido')
        # --- FIN DE LA CORRECCIÓN ---

        x_position_restart = 50
        data_row = [
            str(record.id),
            cliente_nombre,       # <-- Usamos la variable corregida
            proceso_radicado,     # <-- Usamos la variable corregida
            tipo_nombre,          # <-- Usamos la variable corregida
            record.descripcion,
            f"${record.monto:,.2f}",
            record.fecha.strftime("%Y-%m-%d")
        ]
        
        for j, data in enumerate(data_row):
            c.drawString(x_position_restart, y_position, data)
            x_position_restart += col_widths[j]
        y_position -= line_height

    temp_firma_path = firma_path
    if isinstance(temp_firma_path, (list, tuple)):
        temp_firma_path = temp_firma_path[0] if temp_firma_path else ''

    if temp_firma_path and os.path.exists(temp_firma_path):
        try:
            firma = ImageReader(temp_firma_path)
            c.drawImage(firma, width - 200, 50, width=150, height=50, preserveAspectRatio=True)
        except Exception as e:
            print(f"Advertencia: No se pudo cargar la imagen de la firma: {e}")

    c.setFont("Helvetica-Oblique", 10)
    c.setFillColorRGB(0.2, 0.2, 0.2)
    c.drawString(50, 30, "Generado por SELECTA SCAM - Asistencia Jurídica")

    try:
        c.save()
        QMessageBox.information(None, "PDF Generado", f"El resumen de contabilidad se guardó exitosamente en:\n{ruta_guardar}")
    except Exception as e:
        QMessageBox.critical(None, "Error de Operación", f"No se pudo guardar el PDF. Error: {e}")