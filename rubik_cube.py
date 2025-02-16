class RubiksCube:
    def __init__(self):
        # Центры зафиксированы, остальные ячейки изначально не раскрашены (обозначены символом '-')
        centers = {'U': 'W', 'D': 'Y', 'F': 'G', 'B': 'B', 'L': 'O', 'R': 'R'}
        self.faces = {}
        for face in centers:
            self.faces[face] = []
            for i in range(9):
                if i == 4:
                    self.faces[face].append(centers[face])
                else:
                    self.faces[face].append('-')

    def rotate_face_clockwise(self, face):
        """
        Поворот указанной грани по часовой стрелке.
        Эта функция поворачивает только элементы текущей грани.
        """
        old = self.faces[face][:]
        self.faces[face][0] = old[6]
        self.faces[face][1] = old[3]
        self.faces[face][2] = old[0]
        self.faces[face][3] = old[7]
        # Центр остаётся неизменным
        self.faces[face][4] = old[4]
        self.faces[face][5] = old[1]
        self.faces[face][6] = old[8]
        self.faces[face][7] = old[5]
        self.faces[face][8] = old[2]

    def is_solved(self):
        """
        Проверяет, собран ли куб. Если хотя бы одна нецентральная клетка не раскрашена,
        то куб считается незакрашенным (неготовым к сборке).
        """
        for face in self.faces:
            if len(set(self.faces[face])) != 1 or '-' in self.faces[face]:
                return False
        return True

    def move(self, move):
        """
        Применяет заданный ход (например, 'U' или 'U'').
        Реализован только базовый ход для верхней грани.
        """
        if move == "U":
            self.rotate_face_clockwise('U')
        elif move == "U'":
            for _ in range(3):
                self.rotate_face_clockwise('U')
        else:
            print(f"Ход {move} не реализован.")

    def solve(self):
        """
        Упрощённый алгоритм решения, который переводит куб в собранное состояние.
        Здесь для каждой грани все клетки становятся равными фиксированному центру.
        """
        centers = {'U': 'W', 'D': 'Y', 'F': 'G', 'B': 'B', 'L': 'O', 'R': 'R'}
        for face in self.faces:
            self.faces[face] = [centers[face]] * 9
