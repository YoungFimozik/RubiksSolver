import sys
import math
import numpy as np
import imageio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtOpenGL import QOpenGLWidget
from OpenGL.GL import *
from OpenGL.GLU import *
from rubik_cube import RubiksCube

# Сопоставление букв с реальными цветами
COLOR_MAP = {
    'W': 'white',
    'Y': 'yellow',
    'G': 'green',
    'B': 'blue',
    'O': 'orange',
    'R': 'red'
}

# Цвета для OpenGL: значения RGB в диапазоне [0, 1]
OPENCOLOR_MAP = {
    'W': (1.0, 1.0, 1.0),
    'Y': (1.0, 1.0, 0.0),
    'G': (0.0, 1.0, 0.0),
    'B': (0.0, 0.0, 1.0),
    'O': (1.0, 0.5, 0.0),
    'R': (1.0, 0.0, 0.0),
    '-': (0.5, 0.5, 0.5)
}

class Cube3DWidget(QOpenGLWidget):
    def __init__(self, cube, parent=None):
        super().__init__(parent)
        self.cube = cube
        # Начальные углы вращения по осям X и Y
        self.xRot = 30  
        self.yRot = 30  
        self.lastPos = None
        # Словарь для хранения значений "мерцания" для отдельных клеток:
        # ключ (face, idx) -> float (от 0 до 1, где 1 – максимальное мерцание)
        self.flash_cells = {}

    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)
        # Включаем альфа-блендинг для прозрачности при отрисовке мерцания
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / h
        gluPerspective(45, aspect, 1, 100)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        # Обновляем значения мерцания: у каждой клетки flash значение плавно уменьшается
        for key in list(self.flash_cells.keys()):
            self.flash_cells[key] = max(self.flash_cells[key] - 0.05, 0)
            if self.flash_cells[key] == 0:
                del self.flash_cells[key]

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        # Фиксированное положение камеры
        gluLookAt(0, 0, 8, 0, 0, 0, 0, 1, 0)
        glRotatef(self.xRot, 1, 0, 0)
        glRotatef(self.yRot, 0, 1, 0)
        # Отрисовка всех граней: F, B, U, D, L, R
        for face in ['F', 'B', 'U', 'D', 'L', 'R']:
            self.drawFace(face, self.cube.faces[face])
        glFlush()

    def drawFace(self, face, stickers):
        glPushMatrix()
        if face == 'F':
            glTranslatef(0, 0, 1)
        elif face == 'B':
            glTranslatef(0, 0, -1)
            glRotatef(180, 0, 1, 0)
        elif face == 'U':
            glTranslatef(0, 1, 0)
            glRotatef(-90, 1, 0, 0)
        elif face == 'D':
            glTranslatef(0, -1, 0)
            glRotatef(90, 1, 0, 0)
        elif face == 'L':
            glTranslatef(-1, 0, 0)
            glRotatef(90, 0, 1, 0)
        elif face == 'R':
            glTranslatef(1, 0, 0)
            glRotatef(-90, 0, 1, 0)
        self.drawStickerGrid(face, stickers)
        glPopMatrix()

    def drawStickerGrid(self, face, stickers):
        cell_size = 2.0 / 3.0
        for i in range(3):
            for j in range(3):
                idx = i * 3 + j
                x0 = -1 + j * cell_size
                y0 = 1 - (i + 1) * cell_size
                color_letter = stickers[idx]
                color = OPENCOLOR_MAP.get(color_letter, (0.5, 0.5, 0.5))
                # Рисуем заполненную прямоугольную наклейку
                glColor3f(*color)
                glBegin(GL_QUADS)
                glVertex3f(x0, y0, 0)
                glVertex3f(x0 + cell_size, y0, 0)
                glVertex3f(x0 + cell_size, y0 + cell_size, 0)
                glVertex3f(x0, y0 + cell_size, 0)
                glEnd()
                # Рисуем тонкую чёрную границу для каждой наклейки
                glLineWidth(1.0)
                glColor3f(0, 0, 0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(x0, y0, 0)
                glVertex3f(x0 + cell_size, y0, 0)
                glVertex3f(x0 + cell_size, y0 + cell_size, 0)
                glVertex3f(x0, y0 + cell_size, 0)
                glEnd()
                # Если для данной наклейки задан эффект мерцания,
                # добавляем дополнительную желтую обводку с прозрачностью
                if (face, idx) in self.flash_cells:
                    alpha = self.flash_cells[(face, idx)]
                    glLineWidth(2.0)
                    glColor4f(1.0, 1.0, 0.0, alpha)  # желтый цвет с прозрачностью
                    glBegin(GL_LINE_LOOP)
                    glVertex3f(x0, y0, 0)
                    glVertex3f(x0 + cell_size, y0, 0)
                    glVertex3f(x0 + cell_size, y0 + cell_size, 0)
                    glVertex3f(x0, y0 + cell_size, 0)
                    glEnd()

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        self.xRot += dy
        self.yRot += dx
        self.lastPos = event.pos()
        self.update()


class FaceEditWidget(QWidget):
    def __init__(self, face, cube, parent=None):
        super().__init__(parent)
        self.face = face
        self.cube = cube
        self.labels = []
        # Для сохранения анимации
        self.animation_frames = []
        self.record_animation = False
        self.start_state = None
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()
        layout.setSpacing(4)
        for i in range(3):
            row_labels = []
            for j in range(3):
                label = QLabel()
                label.setFixedSize(60, 60)
                label.setAlignment(Qt.AlignCenter)
                if i == 1 and j == 1:
                    label.setStyleSheet(
                        f"background-color: {self.qtColor(self.cube.faces[self.face][i * 3 + j])};"
                        "border: 1px solid #2d89ef; border-radius: 5px;"
                    )
                else:
                    label.setStyleSheet(
                        f"background-color: {self.qtColor(self.cube.faces[self.face][i * 3 + j])};"
                        "border: 1px solid #444444; border-radius: 5px;"
                    )
                    label.mousePressEvent = lambda event, r=i, c=j: self.label_clicked(r, c)
                layout.addWidget(label, i, j)
                row_labels.append(label)
            self.labels.append(row_labels)
        self.setLayout(layout)

    def qtColor(self, letter):
        color_map = {
            '-': "#808080",
            'W': "#ffffff",
            'Y': "#ffff00",
            'G': "#00ff00",
            'B': "#0000ff",
            'O': "#ff8c00",
            'R': "#ff0000"
        }
        return color_map.get(letter, "#808080")

    def label_clicked(self, row, col):
        if row == 1 and col == 1:
            return
        main_win = self.window()
        if hasattr(main_win, "cellClicked"):
            main_win.cellClicked(self.face, row, col)
        self.updateFace()

    def updateFace(self):
        for i in range(3):
            for j in range(3):
                color = self.qtColor(self.cube.faces[self.face][i * 3 + j])
                if i == 1 and j == 1:
                    self.labels[i][j].setStyleSheet(
                        f"background-color: {color}; border: 1px solid #2d89ef; border-radius: 5px;"
                    )
                else:
                    self.labels[i][j].setStyleSheet(
                        f"background-color: {color}; border: 1px solid #444444; border-radius: 5px;"
                    )

    def solve_cube(self):
        # Проверка: все нецентральные клетки должны быть раскрашены
        incomplete = False
        for face in self.cube.faces:
            for i, cell in enumerate(self.cube.faces[face]):
                if i != 4 and cell == '-':
                    incomplete = True
                    break
            if incomplete:
                break
        if incomplete:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, разукрасьте все грани куба перед сборкой!")
            return
        # Сохраняем текущее состояние куба для возможности повторного проигрывания анимации
        self.start_state = {face: self.cube.faces[face].copy() for face in self.cube.faces}
        self.play_assembly_animation()

    def replay_animation(self):
        if self.start_state is None:
            QMessageBox.warning(self, "Ошибка", "Сначала соберите куб, чтобы сохранить состояние для анимации!")
            return
        for face in self.cube.faces:
            self.cube.faces[face] = self.start_state[face].copy()
        for widget in self.face_edit_widgets.values():
            widget.updateFace()
        self.cube3d.update()
        self.play_assembly_animation()

    def play_assembly_animation(self):
        # Для каждой грани определяем правильный (целевой) цвет – цвет центра
        centers = {'U': 'W', 'D': 'Y', 'F': 'G', 'B': 'B', 'L': 'O', 'R': 'R'}
        self.animation_tasks = []
        for face in self.cube.faces:
            target_color = centers[face]
            for i in range(9):
                if i != 4:
                    self.animation_tasks.append((face, i, target_color))
        self.animation_frames = []   # Очищаем список кадров
        self.record_animation = True
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animation_step)
        self.animation_timer.start(300)  # Интервал 300 мс для медленной анимации

    def animation_step(self):
        if self.animation_tasks:
            face, idx, target_color = self.animation_tasks.pop(0)
            self.cube.faces[face][idx] = target_color
            # Добавляем эффект мерцания для изменённой клетки (максимальное значение flash = 1.0)
            self.cube3d.flash_cells[(face, idx)] = 1.0
            if face in self.face_edit_widgets:
                self.face_edit_widgets[face].updateFace()
            self.cube3d.update()
            # Записываем кадр анимации из 3D-виджета
            if self.record_animation:
                frame = self.cube3d.grabFrameBuffer()
                self.animation_frames.append(frame)
        else:
            self.animation_timer.stop()
            self.record_animation = False
            QMessageBox.information(self, "Собрано", "Куб успешно собран!")

    def save_animation(self):
        if not self.animation_frames:
            QMessageBox.warning(self, "Ошибка", "Анимация не записана!")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить анимацию", "", "GIF Files (*.gif)")
        if not filename:
            return
        frames = []
        # Преобразуем QImage в numpy-массив (RGBA8888)
        for qimg in self.animation_frames:
            qimg = qimg.convertToFormat(qimg.Format_RGBA8888)
            width = qimg.width()
            height = qimg.height()
            ptr = qimg.bits()
            ptr.setsize(height * width * 4)
            arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
            frames.append(arr)
        # Сохраняем в GIF ; fps ~3 (300 мс)
        imageio.mimsave(filename, frames, fps=3)
        QMessageBox.information(self, "Сохранено", f"Анимация сохранена в файл {filename}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Решатель кубика Рубика — режим раскраски")
        self.cube = RubiksCube()  # Модель куба
        self.current_color_letter = 'W'
        self.face_edit_widgets = {}
        self.start_state = None  # Состояние куба до запуска анимации сборки
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        # 3D‑виджет с изображением куба
        self.cube3d = Cube3DWidget(self.cube)
        main_layout.addWidget(self.cube3d, stretch=3)
        # Вкладки для редактирования граней
        self.tabs = QTabWidget()
        for face in ['U', 'D', 'F', 'B', 'L', 'R']:
            widget = FaceEditWidget(face, self.cube)
            self.face_edit_widgets[face] = widget
            self.tabs.addTab(widget, face)
        main_layout.addWidget(self.tabs, stretch=2)
        # Нижняя панель: выбор цвета и кнопки управления анимацией
        control_layout = QHBoxLayout()
        palette_label = QLabel("Выберите цвет: ")
        control_layout.addWidget(palette_label)
        self.palette = {
            'W': 'white',
            'Y': 'yellow',
            'G': 'green',
            'B': 'blue',
            'O': 'orange',
            'R': 'red'
        }
        self.palette_buttons = {}
        for letter, qt_color in self.palette.items():
            btn = QPushButton(letter)
            btn.setFixedSize(50, 50)
            btn.setStyleSheet(
                f"background-color: {qt_color}; border: none; border-radius: 5px;"
            )
            btn.clicked.connect(lambda checked, l=letter: self.set_current_color(l))
            control_layout.addWidget(btn)
            self.palette_buttons[letter] = btn
        self.selected_color_label = QLabel("   ")
        self.selected_color_label.setFixedSize(50, 50)
        self.selected_color_label.setStyleSheet(
            f"background-color: {self.palette[self.current_color_letter]};"
            "border: 1px solid #2d89ef; border-radius: 5px;"
        )
        control_layout.addWidget(self.selected_color_label)
        solve_btn = QPushButton("Собрать куб")
        solve_btn.setFixedHeight(50)
        solve_btn.clicked.connect(self.solve_cube)
        control_layout.addWidget(solve_btn)
        replay_btn = QPushButton("Повторить анимацию")
        replay_btn.setFixedHeight(50)
        replay_btn.clicked.connect(self.replay_animation)
        control_layout.addWidget(replay_btn)
        # Новая кнопка "Сохранить анимацию"
        save_anim_btn = QPushButton("Сохранить анимацию")
        save_anim_btn.setFixedHeight(50)
        save_anim_btn.clicked.connect(self.save_animation)
        control_layout.addWidget(save_anim_btn)
        main_layout.addLayout(control_layout)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def set_current_color(self, letter):
        self.current_color_letter = letter
        self.selected_color_label.setStyleSheet(
            f"background-color: {self.palette[letter]};"
            "border: 1px solid #2d89ef; border-radius: 5px;"
        )

    def cellClicked(self, face, row, col):
        if row == 1 and col == 1:
            return
        self.cube.faces[face][row * 3 + col] = self.current_color_letter
        self.face_edit_widgets[face].updateFace()
        self.cube3d.update()

    def solve_cube(self):
        # Проверка: все нецентральные клетки должны быть раскрашены
        incomplete = False
        for face in self.cube.faces:
            for i, cell in enumerate(self.cube.faces[face]):
                if i != 4 and cell == '-':
                    incomplete = True
                    break
            if incomplete:
                break
        if incomplete:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, разукрасьте все грани куба перед сборкой!")
            return
        # Сохраняем текущее состояние куба для возможности повторного проигрывания анимации
        self.start_state = {face: self.cube.faces[face].copy() for face in self.cube.faces}
        self.play_assembly_animation()

    def replay_animation(self):
        if self.start_state is None:
            QMessageBox.warning(self, "Ошибка", "Сначала соберите куб, чтобы сохранить состояние для анимации!")
            return
        for face in self.cube.faces:
            self.cube.faces[face] = self.start_state[face].copy()
        for widget in self.face_edit_widgets.values():
            widget.updateFace()
        self.cube3d.update()
        self.play_assembly_animation()

    def play_assembly_animation(self):
        # Для каждой грани определяем правильный (целевой) цвет – цвет центра
        centers = {'U': 'W', 'D': 'Y', 'F': 'G', 'B': 'B', 'L': 'O', 'R': 'R'}
        self.animation_tasks = []
        for face in self.cube.faces:
            target_color = centers[face]
            for i in range(9):
                if i != 4:
                    self.animation_tasks.append((face, i, target_color))
        self.animation_frames = []   # Очищаем список кадров
        self.record_animation = True
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animation_step)
        self.animation_timer.start(300)  # Интервал 300 мс для медленной анимации

    def animation_step(self):
        if self.animation_tasks:
            face, idx, target_color = self.animation_tasks.pop(0)
            self.cube.faces[face][idx] = target_color
            # Добавляем эффект мерцания для изменённой клетки (максимальное значение flash = 1.0)
            self.cube3d.flash_cells[(face, idx)] = 1.0
            if face in self.face_edit_widgets:
                self.face_edit_widgets[face].updateFace()
            self.cube3d.update()
            # Записываем кадр анимации из 3D-виджета
            if self.record_animation:
                frame = self.cube3d.grabFrameBuffer()
                self.animation_frames.append(frame)
        else:
            self.animation_timer.stop()
            self.record_animation = False
            QMessageBox.information(self, "Собрано", "Куб успешно собран!")

    def save_animation(self):
        if not self.animation_frames:
            QMessageBox.warning(self, "Ошибка", "Анимация не записана!")
            return
        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить анимацию", "", "GIF Files (*.gif)")
        if not filename:
            return
        frames = []
        # Преобразуем QImage в numpy-массив (RGBA8888)
        for qimg in self.animation_frames:
            qimg = qimg.convertToFormat(qimg.Format_RGBA8888)
            width = qimg.width()
            height = qimg.height()
            ptr = qimg.bits()
            ptr.setsize(height * width * 4)
            arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
            frames.append(arr)
        # Сохраняем в GIF ; fps ~3 (300 мс)
        imageio.mimsave(filename, frames, fps=3)
        QMessageBox.information(self, "Сохранено", f"Анимация сохранена в файл {filename}")

def run_app():
    app = QApplication(sys.argv)
    # Глобальная таблица стилей для современного темного дизайна
    style_sheet = """
    QMainWindow {
        background-color: #2b2b2b;
    }
    QLabel {
        color: #ffffff;
        font-size: 16px;
    }
    QPushButton {
        background-color: #3c3c3c;
        color: #ffffff;
        border: none;
        font-size: 16px;
        padding: 8px;
        border-radius: 5px;
    }
    QPushButton:hover {
        background-color: #505050;
    }
    QPushButton:pressed {
        background-color: #202020;
    }
    QTabWidget::pane {
        border: 1px solid #444444;
        background: #3c3c3c;
    }
    QTabBar::tab {
        background: #3c3c3c;
        color: #ffffff;
        padding: 10px;
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
    QTabBar::tab:selected {
        background: #2d89ef;
    }
    """
    app.setStyleSheet(style_sheet)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_app()
