import cv2
import numpy as np
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QImage, QWheelEvent, QMouseEvent
from PyQt5.QtCore import Qt, QRectF


class ZoomableImageView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(self.renderHints() | Qt.SmoothTransformation)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._pixmap_item = None
        self._original_cv_img = None
        self._zoom = 1.0
        self._pan = False
        self._start_pos = None
        self._fit_to_view = True

    def load_cv_image(self, path, fit_to_view=True):
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            print("Failed to load image:", path)
            return

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self._original_cv_img = img
        self._zoom = 1.0
        self._fit_to_view = fit_to_view
        self.display_zoomed_image()

    def display_zoomed_image(self):
        if self._original_cv_img is None:
            return

        if self._fit_to_view:
            view_size = self.viewport().size()
            h, w, _ = self._original_cv_img.shape
            scale_h = view_size.height() / h
            self._zoom = scale_h  # scale to 100% of height only

        zoomed_img = cv2.resize(self._original_cv_img, (0, 0), fx=self._zoom, fy=self._zoom, interpolation=cv2.INTER_LINEAR)

        height, width, channel = zoomed_img.shape
        bytes_per_line = 3 * width
        qimg = QImage(zoomed_img.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)

        self.scene().clear()
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene().addItem(self._pixmap_item)
        self.setSceneRect(QRectF(pixmap.rect()))
        self.centerOn(self._pixmap_item)

    def wheelEvent(self, event: QWheelEvent):
        if self._original_cv_img is None:
            return

        zoom_in = event.angleDelta().y() > 0
        factor = 1.25 if zoom_in else 0.8

        self._zoom *= factor
        self._zoom = max(0.1, min(self._zoom, 10.0))
        self._fit_to_view = False

        self.display_zoomed_image()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._pan = True
            self._start_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._pan:
            delta = self._start_pos - event.pos()
            self._start_pos = event.pos()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self._zoom = 1.0
        self._fit_to_view = True
        self.display_zoomed_image()
        self.centerOn(self._pixmap_item)
