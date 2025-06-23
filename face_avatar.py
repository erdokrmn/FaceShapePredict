import sys
import cv2
import numpy as np

from utils.head_pose_utils import face_mesh
import mediapipe as mp
from PyQt5 import QtWidgets, QtGui, QtCore

FACE_SIZE = 400  # Büyütülmüş yüz boyutu (örneğin 400x400)

class MaskFaceAvatar(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(FACE_SIZE, FACE_SIZE)
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.cap = cv2.VideoCapture(1)
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_avatar)
        self.timer.start(30)

        self.avatar_image = QtGui.QImage(FACE_SIZE, FACE_SIZE, QtGui.QImage.Format_ARGB32)
        self.avatar_image.fill(QtCore.Qt.transparent)

    def update_avatar(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb_frame)

        mask_image = np.zeros((FACE_SIZE, FACE_SIZE, 4), dtype=np.uint8)

        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0]
            h, w = FACE_SIZE, FACE_SIZE

            # Mesh noktalarını topla
            points = []
            for lm in landmarks.landmark:
                x = int(lm.x * w)
                y = int(lm.y * h)
                points.append([x, y])

            # Tesselation bağlantıları
            connections = mp.solutions.face_mesh.FACEMESH_TESSELATION

            # Maske için üçgenleri doldur
            for con in connections:
                i1, i2 = con
                if i1 < len(points) and i2 < len(points):
                    pt1 = points[i1]
                    pt2 = points[i2]
                    cv2.line(mask_image, tuple(pt1), tuple(pt2), (150, 150, 150, 255), 1)

            # Maske gibi görünmesi için Gaussian blur uygulanabilir
            mask_only = mask_image[:, :, :3]
            alpha = np.where(mask_only.any(axis=2), 255, 0).astype(np.uint8)
            mask_image[:, :, 3] = alpha

        # PyQt için QImage
        qimg = QtGui.QImage(mask_image.data, FACE_SIZE, FACE_SIZE, QtGui.QImage.Format_RGBA8888)
        self.avatar_image = qimg.copy()
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.drawImage(0, 0, self.avatar_image)

    def closeEvent(self, event):
        self.cap.release()
        face_mesh.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MaskFaceAvatar()
    window.move(10, 10)  # Sol üst köşeye 10px boşluk
    window.show()
    sys.exit(app.exec_())
