import os
import fitz
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFileDialog, QMessageBox, QRubberBand,
    QApplication, QSizePolicy, QTextEdit, QStackedLayout
)
from PyQt5.QtGui import QPixmap, QImage, QCursor, QGuiApplication, QPainter, QPen, QDesktopServices
from PyQt5.QtCore import Qt, QTimer, QRect, QPoint, QSize, QEvent, QUrl
import shutil
try:
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
except ImportError:
    pytesseract = None
    print("Advertencia: Las librerías 'pytesseract' o 'Pillow' no están instaladas. La funcionalidad de OCR no estará disponible.")
except Exception as e:
    pytesseract = None
    print(f"Advertencia: Error al importar 'pytesseract' o 'Pillow' o configurar Tesseract: {e}. La funcionalidad de OCR no estará disponible.")
class VisorDocumentoDialog(QDialog):
    MIN_ZOOM_FACTOR = 0.5
    MAX_ZOOM_FACTOR = 5.0
    ZOOM_STEP = 0.1
    def __init__(self, ruta_documento, documento_nombre, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Visor de Documento: {documento_nombre}")
        self.setMinimumSize(1200, 900)
        self.ruta_documento = os.path.abspath(ruta_documento).replace("\\", "/")
        self.documento_nombre = documento_nombre
        self.doc = None
        self.current_page_labels = []
        self.zoom_factor = 1.0
        self.scroll_percentage_v = 0.0
        self.main_layout = QVBoxLayout(self)
        self.setLayout(self.main_layout)
        self.zoom_controls_widget = QWidget(self)
        self.zoom_controls_layout = QHBoxLayout(self.zoom_controls_widget)
        self.zoom_out_button = QPushButton("Zoom -")
        self.zoom_out_button.clicked.connect(self.zoom_out)
        self.zoom_label = QLabel(f"Zoom: {self.zoom_factor * 100:.0f}%")
        self.zoom_in_button = QPushButton("Zoom +")
        self.zoom_in_button.clicked.connect(self.zoom_in)
        self.zoom_reset_button = QPushButton("Zoom 100%")
        self.zoom_reset_button.clicked.connect(self.reset_zoom)
        self.zoom_controls_layout.addWidget(self.zoom_out_button)
        self.zoom_controls_layout.addWidget(self.zoom_label)
        self.zoom_controls_layout.addWidget(self.zoom_in_button)
        self.zoom_controls_layout.addStretch()
        self.zoom_controls_layout.addWidget(self.zoom_reset_button)
        self.main_layout.addWidget(self.zoom_controls_widget)
        self.stacked_viewer_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_viewer_layout)
        self.pdf_image_scroll_area = QScrollArea(self)
        self.pdf_image_container = QWidget()
        self.pdf_image_vbox = QVBoxLayout(self.pdf_image_container)
        self.pdf_image_vbox.setSpacing(5)
        self.pdf_image_vbox.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.pdf_image_container.setLayout(self.pdf_image_vbox)
        self.pdf_image_scroll_area.setWidget(self.pdf_image_container)
        self.pdf_image_scroll_area.setWidgetResizable(True)
        self.stacked_viewer_layout.addWidget(self.pdf_image_scroll_area)
        self.text_viewer = QTextEdit(self)
        self.text_viewer.setReadOnly(True)
        self.text_viewer.setFontPointSize(10)
        self.stacked_viewer_layout.addWidget(self.text_viewer)
        self.unsupported_message_widget = QLabel("Tipo de archivo no soportado o archivo vacío.")
        self.unsupported_message_widget.setAlignment(Qt.AlignCenter)
        self.stacked_viewer_layout.addWidget(self.unsupported_message_widget)
        self.selecting = False
        self.selection_start_point = QPoint()
        self.selection_rubber_band = QRubberBand(QRubberBand.Rectangle, self.pdf_image_scroll_area.viewport())
        self.pdf_image_scroll_area.viewport().setMouseTracking(True)
        self.pdf_image_scroll_area.viewport().setCursor(Qt.IBeamCursor)
        self.pdf_image_scroll_area.viewport().installEventFilter(self)
        action_buttons_layout = QHBoxLayout()
        self.copy_selection_button = QPushButton("Copiar Selección")
        self.copy_selection_button.clicked.connect(self.copy_selected_text_to_clipboard)
        self.copy_selection_button.setEnabled(False)
        self.copy_all_button = QPushButton("Copiar Todo el Texto")
        self.copy_all_button.clicked.connect(self.select_all_text)
        self.save_button = QPushButton("Guardar Documento Como...")
        self.save_button.clicked.connect(self.save_document)
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        action_buttons_layout.addWidget(self.copy_selection_button)
        action_buttons_layout.addWidget(self.copy_all_button)
        action_buttons_layout.addWidget(self.save_button)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.close_button)
        self.main_layout.addLayout(action_buttons_layout)
        if not os.path.exists(self.ruta_documento):
            self.stacked_viewer_layout.setCurrentIndex(2)
            self.unsupported_message_widget.setText(f"Error: El archivo no existe en la ruta:\n{self.ruta_documento}")
            return
        QTimer.singleShot(50, self.load_document)
    
    # En: SELECTA_SCAM/modulos/documentos/visor_documento_dialog.py

    def load_document(self):
        ext = os.path.splitext(self.ruta_documento)[1].lower()
        print(f"[VISOR] Intentando cargar archivo con extensión: {ext}")

        if ext == ".pdf":
            self.zoom_controls_widget.show()
            self._load_pdf()
        
        elif ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
            self.zoom_controls_widget.show()
            self._load_image()

        elif ext in [".txt", ".log"]: # <-- Lista solo para texto plano
            self.zoom_controls_widget.hide()
            self._load_text_file()

        # --- INICIO DE LA CORRECCIÓN ---
        # Agrupamos todos los formatos de Office y Excel para que se abran externamente
        elif ext in [".docx", ".doc", ".xlsx", ".xls", ".csv", ".pptx", ".ppt"]:
            self.zoom_controls_widget.hide()
            self._open_external_application(self.ruta_documento)
            # self.close() # El close ya está dentro de _open_external_application
        # --- FIN DE LA CORRECCIÓN ---

        else:
            self.zoom_controls_widget.hide()
            self._handle_unsupported_file(ext)
    
    def _open_external_application(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "Error al Abrir", f"El archivo no existe en la ruta:\n{file_path}")
            self.close()
            return
        url = QUrl.fromLocalFile(file_path)
        if QDesktopServices.openUrl(url):
            print(f"[VISOR] El archivo '{os.path.basename(file_path)}' se está abriendo con la aplicación predeterminada del sistema.")
            self.close()
        else:
            QMessageBox.critical(self, "Error al Abrir",
                                 f"No se pudo abrir el archivo '{os.path.basename(file_path)}' con la aplicación predeterminada del sistema.\n"
                                 "Asegúrate de tener una aplicación compatible (ej. Microsoft Word/Excel/PowerPoint) instalada y asociada al tipo de archivo.")
            self.close()
    def _load_pdf(self):
        self.clear_pdf_image_viewer()
        try:
            self.doc = fitz.open(self.ruta_documento)
            print(f"[VISOR] PDF abierto exitosamente con {len(self.doc)} página(s).")
        except Exception as e:
            print(f"[ERROR] No se pudo abrir el PDF: {e}")
            self._show_error_message(f"Error al abrir el PDF:\n{e}")
            self.doc = None
            return
        if self.doc is None or len(self.doc) == 0:
            self._show_error_message("El documento está vacío o no tiene páginas.")
            return
        QTimer.singleShot(50, self._render_all_pages_pdf_or_image)
        self.stacked_viewer_layout.setCurrentIndex(0)
    def _load_image(self):
        self.clear_pdf_image_viewer()
        label = QLabel()
        pixmap = QPixmap(self.ruta_documento)
        if pixmap.isNull():
            self._show_error_message(f"Error: No se pudo cargar la imagen:\n{self.ruta_documento}")
            return
        available_viewport_width = self.pdf_image_scroll_area.viewport().width() - 20
        if available_viewport_width <= 0:
            available_viewport_width = 800
        scaled_pixmap = pixmap.scaledToWidth(available_viewport_width, Qt.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignCenter)
        label.setFixedSize(scaled_pixmap.size())
        self.pdf_image_vbox.addWidget(label)
        self.current_page_labels.append(label)
        self.zoom_factor = scaled_pixmap.width() / pixmap.width()
        self.stacked_viewer_layout.setCurrentIndex(0)
        QTimer.singleShot(50, self._adjust_scroll_after_render)
    def _load_text_file(self):
        try:
            with open(self.ruta_documento, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.text_viewer.setPlainText(content)
            self.stacked_viewer_layout.setCurrentIndex(1)
            self.copy_selection_button.setEnabled(True)
            self.copy_all_button.setEnabled(True)
        except Exception as e:
            self._show_error_message(f"Error al cargar el archivo de texto:\n{e}")
            self.stacked_viewer_layout.setCurrentIndex(2)
    def _handle_unsupported_file(self, ext):
        msg = f"El tipo de archivo '{ext}' no es soportado por este visor. "
        if ext == ".docx":
            msg += "Los archivos Word (.docx) no pueden ser visualizados directamente sin herramientas de conversión o librerías complejas. Considera convertirlo a PDF."
        QMessageBox.warning(self, "Tipo de archivo no soportado", msg)
        self.unsupported_message_widget.setText(f"Tipo de archivo no soportado:\n{ext}")
        self.stacked_viewer_layout.setCurrentIndex(2)
        self.copy_selection_button.setEnabled(False)
        self.copy_all_button.setEnabled(False)
    def _show_error_message(self, message):
        QMessageBox.critical(self, "Error de Visor", message)
        self.unsupported_message_widget.setText(message)
        self.stacked_viewer_layout.setCurrentIndex(2)
    def clear_pdf_image_viewer(self):
        while self.pdf_image_vbox.count():
            item = self.pdf_image_vbox.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.current_page_labels = []
    def _render_all_pages_pdf_or_image(self):
        if self.stacked_viewer_layout.currentIndex() == 0:
            if self.pdf_image_scroll_area.verticalScrollBar().maximum() > 0:
                current_scroll_value = self.pdf_image_scroll_area.verticalScrollBar().value()
                max_scroll_value = self.pdf_image_scroll_area.verticalScrollBar().maximum()
                self.scroll_percentage_v = current_scroll_value / max_scroll_value
            else:
                self.scroll_percentage_v = 0.0
        if not self.doc:
            if self.current_page_labels and len(self.current_page_labels) == 1:
                original_pixmap = QPixmap(self.ruta_documento)
                if not original_pixmap.isNull():
                    available_viewport_width = self.pdf_image_scroll_area.viewport().width() - 20
                    if available_viewport_width <= 0: available_viewport_width = 800
                    base_scale = available_viewport_width / original_pixmap.width()
                    final_scale = base_scale * self.zoom_factor
                    final_scale = max(0.01, final_scale)
                    scaled_pixmap = original_pixmap.scaled(
                        int(original_pixmap.width() * final_scale),
                        int(original_pixmap.height() * final_scale),
                        Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.current_page_labels[0].setPixmap(scaled_pixmap)
                    self.current_page_labels[0].setFixedSize(scaled_pixmap.size())
                QTimer.singleShot(50, self._adjust_scroll_after_render)
            return
        self.clear_pdf_image_viewer()
        available_viewport_width = self.pdf_image_scroll_area.viewport().width() - 20
        if available_viewport_width <= 0:
            available_viewport_width = 800
        for page_num in range(len(self.doc)):
            try:
                page = self.doc.load_page(page_num)
                original_page_width = int(page.rect.width)
                if original_page_width > 0:
                    base_scale_to_fit_width = available_viewport_width / original_page_width
                else:
                    base_scale_to_fit_width = 1.0
                final_scale = base_scale_to_fit_width * self.zoom_factor
                final_scale = max(0.01, final_scale)
                mat = fitz.Matrix(final_scale, final_scale)
                pix = page.get_pixmap(matrix=mat)
                image = QImage(pix.samples, pix.width, pix.height, pix.stride,
                               QImage.Format_RGBA8888 if pix.alpha else QImage.Format_RGB888)
                label = QLabel()
                q_pixmap = QPixmap.fromImage(image)
                label.setPixmap(q_pixmap)
                label.setAlignment(Qt.AlignCenter)
                label.setFixedSize(q_pixmap.size())
                self.pdf_image_vbox.addWidget(label)
                self.current_page_labels.append(label)
            except Exception as render_err:
                print(f"[ERROR] Fallo al renderizar página {page_num + 1}: {render_err}")
                error_label = QLabel(f"[ERROR] Página {page_num + 1} no pudo cargarse.")
                error_label.setAlignment(Qt.AlignCenter)
                self.pdf_image_vbox.addWidget(error_label)
        QTimer.singleShot(50, self._adjust_scroll_after_render)
    def _adjust_scroll_after_render(self):
        if self.stacked_viewer_layout.currentIndex() == 0:
            v_scroll_bar = self.pdf_image_scroll_area.verticalScrollBar()
            new_max_scroll = v_scroll_bar.maximum()
            if new_max_scroll > 0:
                target_value = int(self.scroll_percentage_v * new_max_scroll)
                target_value = max(0, min(target_value, new_max_scroll))
                v_scroll_bar.setValue(target_value)
            else:
                v_scroll_bar.setValue(0)
    def update_zoom_label(self):
        self.zoom_label.setText(f"Zoom: {self.zoom_factor * 100:.0f}%")
    def zoom_in(self):
        if self.stacked_viewer_layout.currentIndex() == 0:
            if self.zoom_factor < self.MAX_ZOOM_FACTOR:
                self.zoom_factor += self.ZOOM_STEP
                if self.zoom_factor > self.MAX_ZOOM_FACTOR:
                    self.zoom_factor = self.MAX_ZOOM_FACTOR
                self.update_zoom_label()
                self._render_all_pages_pdf_or_image()
    def zoom_out(self):
        if self.stacked_viewer_layout.currentIndex() == 0:
            if self.zoom_factor > self.MIN_ZOOM_FACTOR:
                self.zoom_factor -= self.ZOOM_STEP
                if self.zoom_factor < self.MIN_ZOOM_FACTOR:
                    self.zoom_factor = self.MIN_ZOOM_FACTOR
                self.update_zoom_label()
                self._render_all_pages_pdf_or_image()
    def reset_zoom(self):
        if self.stacked_viewer_layout.currentIndex() == 0:
            self.zoom_factor = 1.0
            self.update_zoom_label()
            self._render_all_pages_pdf_or_image()
    def keyPressEvent(self, event):
        if self.stacked_viewer_layout.currentIndex() == 0 and event.modifiers() == Qt.ControlModifier:
            if event.key() == Qt.Key_Plus:
                self.zoom_in()
                event.accept()
            elif event.key() == Qt.Key_Minus:
                self.zoom_out()
                event.accept()
            elif event.key() == Qt.Key_0:
                self.reset_zoom()
                event.accept()
            elif event.key() == Qt.Key_A:
                self.select_all_text()
                event.accept()
            else:
                super().keyPressEvent(event)
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_A:
            if self.stacked_viewer_layout.currentIndex() == 1:
                self.text_viewer.selectAll()
                event.accept()
            else:
                super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    def wheelEvent(self, event):
        if self.stacked_viewer_layout.currentIndex() == 0 and event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)
    def eventFilter(self, obj, event):
        if obj == self.pdf_image_scroll_area.viewport() and self.stacked_viewer_layout.currentIndex() == 0:
            if event.type() == QEvent.MouseButtonPress:
                self.mouse_press_event_viewport(event)
                return True
            elif event.type() == QEvent.MouseMove:
                self.mouse_move_event_viewport(event)
                return True
            elif event.type() == QEvent.MouseButtonRelease:
                self.mouse_release_event_viewport(event)
                return True
        return super().eventFilter(obj, event)
    def mouse_press_event_viewport(self, event):
        if event.button() == Qt.LeftButton:
            self.selecting = True
            self.selection_start_point = event.pos()
            self.selection_rubber_band.setGeometry(QRect(self.selection_start_point, QSize(0, 0)))
            self.selection_rubber_band.show()
            self.copy_selection_button.setEnabled(False)
    def mouse_move_event_viewport(self, event):
        if self.selecting:
            current_point = event.pos()
            self.selection_rubber_band.setGeometry(QRect(self.selection_start_point, current_point).normalized())
    def mouse_release_event_viewport(self, event):
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            #self.selection_rubber_band.hide()

            rect_in_viewport = QRect(self.selection_start_point, event.pos()).normalized()

            # Si la selección es muy pequeña, la ignoramos
            if rect_in_viewport.width() < 5 or rect_in_viewport.height() < 5:
                self.copy_selection_button.setEnabled(False)
                return

            # Calculamos el área de selección real
            rect_in_container = QRect(
                rect_in_viewport.x(),
                rect_in_viewport.y() + self.pdf_image_scroll_area.verticalScrollBar().value(),
                rect_in_viewport.width(),
                rect_in_viewport.height()
            )

            # --- LÓGICA CORREGIDA ---
            # 1. Extraemos el texto y lo guardamos en una variable
            self.extracted_selection_text = self.get_text_from_selection(rect_in_container)

            # 2. Habilitamos o deshabilitamos el botón según si se encontró texto
            if self.extracted_selection_text and self.extracted_selection_text.strip():
                self.copy_selection_button.setEnabled(True)
            else:
                self.copy_selection_button.setEnabled(False)
            # --- FIN DE LA CORRECCIÓN ---
    
    def paint_selection_on_viewport(self, event):
        pass
    def get_text_from_selection(self,rect_in_container:QRect):
        if self.stacked_viewer_layout.currentIndex()==1:
            return self.text_viewer.textCursor().selectedText()
        if not self.doc:
            if self.current_page_labels and len(self.current_page_labels)==1 and pytesseract:
                image_label=self.current_page_labels[0]
                pixmap_original_size=QPixmap(self.ruta_documento)
                current_display_width=image_label.pixmap().width()
                original_image_width=pixmap_original_size.width()
                scale_factor=original_image_width/current_display_width if current_display_width>0 else 1.0
                label_x_offset=(self.pdf_image_vbox.geometry().width()-image_label.width())/2
                rect_in_displayed_image=QRect(
                    rect_in_container.x()-label_x_offset,
                    rect_in_container.y(),
                    rect_in_container.width(),
                    rect_in_container.height()
                )
                ocr_rect=QRect(
                    int(rect_in_displayed_image.x()*scale_factor),
                    int(rect_in_displayed_image.y()*scale_factor),
                    int(rect_in_displayed_image.width()*scale_factor),
                    int(rect_in_displayed_image.height()*scale_factor)
                )
                cropped_pixmap=pixmap_original_size.copy(ocr_rect)
                if not cropped_pixmap.isNull():
                    qimage_for_ocr=cropped_pixmap.toImage()
                    byte_str=qimage_for_ocr.constBits().asstring(qimage_for_ocr.byteCount())
                    if qimage_for_ocr.format()==QImage.Format_RGBA8888:
                        mode='RGBA'
                    elif qimage_for_ocr.format()==QImage.Format_RGB888:
                        mode='RGB'
                    elif qimage_for_ocr.format()==QImage.Format_ARGB32:
                        mode='RGBA'
                    else:
                        print(f"Formato de QImage no soportado directamente por PIL para OCR: {qimage_for_ocr.format()}")
                        return ""
                    pil_image_for_ocr=Image.frombytes(
                        mode,
                        (qimage_for_ocr.width(),qimage_for_ocr.height()),
                        byte_str
                    )
                    ocr_result=pytesseract.image_to_string(pil_image_for_ocr,lang='spa')
                    return ocr_result.strip()
            return ""
        extracted_text_parts=[]
        current_y_offset_in_container=0
        for i,label in enumerate(self.current_page_labels):
            page_height_rendered=label.height()
            page_width_rendered=label.width()
            if i>0:
                prev_label=self.current_page_labels[i-1]
                current_y_offset_in_container+=prev_label.height()+self.pdf_image_vbox.spacing()
            page_rect_in_container=QRect(label.x(),current_y_offset_in_container,page_width_rendered,page_height_rendered)
            intersection_rect=rect_in_container.intersected(page_rect_in_container)
            if not intersection_rect.isEmpty():
                x_in_page_pix=intersection_rect.x()-page_rect_in_container.x()
                y_in_page_pix=intersection_rect.y()-page_rect_in_container.y()
                width_in_page_pix=intersection_rect.width()
                height_in_page_pix=intersection_rect.height()
                pix_rect_in_page=QRect(x_in_page_pix,y_in_page_pix,width_in_page_pix,height_in_page_pix)
                page=self.doc.load_page(i)
                current_page_render_scale_x=label.pixmap().width()/page.rect.width if page.rect.width>0 else 1.0
                current_page_render_scale_y=label.pixmap().height()/page.rect.height if page.rect.height>0 else 1.0
                pdf_x0=pix_rect_in_page.x()/current_page_render_scale_x
                pdf_y0=pix_rect_in_page.y()/current_page_render_scale_y
                pdf_x1=(pix_rect_in_page.x()+pix_rect_in_page.width())/current_page_render_scale_x
                pdf_y1=(pix_rect_in_page.y()+pix_rect_in_page.height())/current_page_render_scale_y
                pdf_rect=fitz.Rect(pdf_x0,pdf_y0,pdf_x1,pdf_y1)
                text_content=page.get_text("text",clip=pdf_rect)
                if text_content.strip():
                    extracted_text_parts.append(text_content.strip())
                elif pytesseract:
                    try:
                        ocr_zoom_factor=3
                        ocr_mat=fitz.Matrix(ocr_zoom_factor,ocr_zoom_factor)
                        ocr_pix=page.get_pixmap(matrix=ocr_mat,clip=pdf_rect)
                        image_data=ocr_pix.samples
                        qimage_for_ocr=QImage(image_data,ocr_pix.width,ocr_pix.height,ocr_pix.stride,
                                            QImage.Format_RGBA8888 if ocr_pix.alpha else QImage.Format_RGB888)
                        byte_str=qimage_for_ocr.constBits().asstring(qimage_for_ocr.byteCount())
                        if qimage_for_ocr.format()==QImage.Format_RGBA8888:
                            mode='RGBA'
                        elif qimage_for_ocr.format()==QImage.Format_RGB888:
                            mode='RGB'
                        elif qimage_for_ocr.format()==QImage.Format_ARGB32:
                            mode='RGBA'
                        else:
                            print(f"Formato de QImage no soportado directamente por PIL para OCR: {qimage_for_ocr.format()}")
                            continue
                        pil_image_for_ocr=Image.frombytes(
                            mode,
                            (qimage_for_ocr.width(),qimage_for_ocr.height()),
                            byte_str
                        )
                        ocr_result=pytesseract.image_to_string(pil_image_for_ocr,lang='spa')
                        if ocr_result.strip():
                            extracted_text_parts.append(f"{ocr_result.strip()}")
                    except Exception as ocr_err:
                        print(f"Error durante OCR en página {i+1}, región {pdf_rect}: {ocr_err}")
        return "\n".join(extracted_text_parts)

    def copy_selected_text_to_clipboard(self):
        """Copia el texto de la última selección al portapapeles."""
        # Verifica si hay texto extraído para copiar
        if hasattr(self, 'extracted_selection_text') and self.extracted_selection_text and self.extracted_selection_text.strip():
            QApplication.clipboard().setText(self.extracted_selection_text)
            QMessageBox.information(self, "Texto Copiado", "El texto seleccionado ha sido copiado al portapapeles.")
            self.selection_rubber_band.hide()
            self.extracted_selection_text = ""
            self.copy_selection_button.setEnabled(False)
        else:
            QMessageBox.warning(self, "Sin Selección", "No hay texto seleccionado para copiar. Arrastra el ratón sobre el PDF para seleccionar.")
            
    def select_all_text(self):
        """Selecciona todo el texto del documento y lo copia al portapapeles, adaptado por tipo de visor."""
        if self.stacked_viewer_layout.currentIndex()==1: # Si es el visor de texto
            self.text_viewer.selectAll()
            QApplication.clipboard().setText(self.text_viewer.toPlainText())
            QMessageBox.information(self,"Seleccionar Todo","Todo el texto del documento ha sido copiado al portapapeles.")
            self.copy_selection_button.setEnabled(True)
        elif not self.doc: # Si no es PDF (es imagen o no hay nada)
            if self.current_page_labels and len(self.current_page_labels)==1 and pytesseract:
                # Para imágenes, intentar OCR de toda la imagen
                full_ocr_text=self.get_text_from_selection(
                    QRect(0,0,self.current_page_labels[0].width(),self.current_page_labels[0].height()) # Una aproximación del tamaño
                )
                if full_ocr_text.strip():
                    QApplication.clipboard().setText(full_ocr_text)
                    QMessageBox.information(self,"Seleccionar Todo (Imagen)","El texto reconocido de la imagen ha sido copiado al portapapeles.")
                    self.copy_selection_button.setEnabled(True)
                else:
                    QMessageBox.warning(self,"Seleccionar Todo","No se detectó texto en la imagen para copiar.")
                    self.copy_selection_button.setEnabled(False)
            else:
                QMessageBox.warning(self,"Seleccionar Todo","El documento no contiene texto para seleccionar o la funcionalidad de OCR no está disponible.")
                self.copy_selection_button.setEnabled(False)
        else: # Es PDF
            full_document_text=[]
            for i in range(len(self.doc)):
                page=self.doc.load_page(i)
                text_content=page.get_text("text")
                if text_content.strip():
                    full_document_text.append(text_content.strip())
            combined_text="\n".join(full_document_text)
            if combined_text.strip():
                QApplication.clipboard().setText(combined_text)
                QMessageBox.information(self,"Seleccionar Todo","Todo el texto del documento ha sido copiado al portapapeles.")
                self.copy_selection_button.setEnabled(True)
            else:
                QMessageBox.warning(self,"Seleccionar Todo","El documento no contiene texto para seleccionar.")
                self.copy_selection_button.setEnabled(False)
    def save_document(self):
        """Permite al usuario guardar el documento original en una nueva ubicación."""
        if not self.ruta_documento or not os.path.exists(self.ruta_documento):
            QMessageBox.critical(self,"Error al Guardar","No hay un documento cargado o la ruta original no existe.")
            return
        suggested_filename=os.path.basename(self.ruta_documento)
        save_path,_=QFileDialog.getSaveFileName(
            self,
            "Guardar Documento Como...",
            suggested_filename,
            "Todos los archivos (*.*)" # Filtro genérico para guardar cualquier tipo de archivo
        )
        if save_path:
            try:
                shutil.copyfile(self.ruta_documento,save_path)
                QMessageBox.information(self,"Éxito al Guardar",f"Documento guardado correctamente en:\n{save_path}")
            except shutil.SameFileError:
                QMessageBox.warning(self,"Advertencia al Guardar","El archivo de destino es el mismo que el original. No se realizó ninguna copia.")
            except PermissionError:
                QMessageBox.critical(self,"Error de Permisos",f"No tienes permisos para escribir en la ubicación seleccionada:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self,"Error al Guardar",f"No se pudo guardar el documento:\n{e}")
    def closeEvent(self,event):
        """Se llama cuando el diálogo se está cerrando para limpiar recursos."""
        if self.doc:
            try:
                self.doc.close()
                print("[VISOR] Documento PDF cerrado exitosamente.")
            except Exception as e:
                print(f"[ERROR] Error al cerrar documento PDF: {e}")
        super().closeEvent(event) # Asegúrate de llamar a la implementación base