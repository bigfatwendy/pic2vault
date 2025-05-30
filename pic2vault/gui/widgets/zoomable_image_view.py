from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
from PyQt5.QtGui import QPixmap, QWheelEvent, QMouseEvent
from PyQt5.QtCore import Qt, QPointF


class ZoomableImageView(QGraphicsView):
    def __init__(self):
        super().__init__()

        self.setScene(QGraphicsScene(self))
        self.setRenderHints(self.renderHints() | Qt.SmoothTransformation)
        self.setDragMode(QGraphicsView.ScrollHandDrag)

        self._pixmap_item = None
        self._original_pixmap = None
        self._zoom = 0
        self._pan = False
        self._start_pos = None

    def setPixmap(self, pixmap: QPixmap):
        self.scene().clear()
        self._original_pixmap = pixmap
        self._pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene().addItem(self._pixmap_item)
        self._zoom = 0
        self.resetTransform()
        self.fitInView(self._pixmap_item, Qt.KeepAspectRatio)

    def update_pixmap_scale(self, zoom_factor):
        if not self._original_pixmap:
            return

        original_size = self._original_pixmap.size()
        scaled_size = original_size * zoom_factor
        scaled_pixmap = self._original_pixmap.scaled(
            scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self._pixmap_item.setPixmap(scaled_pixmap)

    def wheelEvent(self, event: QWheelEvent):
        if self._pixmap_item is None:
            return

        # Adjust zoom
        zoom_in = event.angleDelta().y() > 0
        factor = 1.1 if zoom_in else 0.9

        self._zoom = max(0.1, min(self._zoom * factor if self._zoom else 1.0 * factor, 10.0))

        # Update pixmap from full-resolution source
        self.update_pixmap_scale(self._zoom)

        # Center zoom around cursor
        cursor_pos = event.pos()
        scene_pos = self.mapToScene(cursor_pos)

        view_center = self.mapFromScene(scene_pos)
        delta = cursor_pos - view_center
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())

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
        if self._pixmap_item:
            self._zoom = 1.0
            self.update_pixmap_scale(self._zoom)
            self.centerOn(self._pixmap_item)
