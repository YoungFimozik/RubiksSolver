import sys
from PyQt5.QtWidgets import QOpenGLWidget

# Патчим модуль PyQt5.QtOpenGL, чтобы он содержал QOpenGLWidget,
# т.к. в вашей установке PyQt5 QOpenGLWidget находится в PyQt5.QtWidgets.
import PyQt5.QtOpenGL
PyQt5.QtOpenGL.QOpenGLWidget = QOpenGLWidget

from rubik_gui import run_app

if __name__ == "__main__":
    run_app()