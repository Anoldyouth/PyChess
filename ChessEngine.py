"""
Этот класс отвечает за хранение всей информации о текущей игре, также он будет завершать ходы, если они возможны, и
будет хранить информация о ходах.
"""


class GameState:
    def __init__(self):
        """
        Доска представляет собой двумерный список, размером 8х8, каждый элемент которой имеет два параметра:
        первый - цвет: 'b' - чёрный, 'w' - белый
        второй - фигура: 'K' - король, 'Q' - ферзь, 'B' - слон и т.д.
        Ячейки '--' обозначают пустое пространство без фигуры, два минуса используются для удобства, так как, если бы
        мы обозначали пустую ячейку как '0', то пришлось бы всё время задумываться о том, чтобы проверять тип данных
        рассматриваемой ячейки.

        self.whiteTurn будет показывать, чья очередь ходить: True - белых, False = чёрных
        self.moveLog используется для хранения ходов, чтобы игрок в любой момент времени мог отменить свой ход.

        self.move_functions - словарь, ключи которого - фигуры, а в их значениях хранятся 'шаблоны' функций, которые
        вызываются, в зависимости от того, какой фигурой будет совершаться ход.

        self.white_king_location, self.black_king_location - позиция белого и чёрного королей в начале игры. Нужно для
        того, чтобы следить, не попадает ли король под шахи, если попытаться совершить тот или иной ход.
        self.in_check - булевая переменная, указывающая на то, объявлен ли шах.
        self.pins - список 'закреплений' фигур (например, если какая-либо фигура стоит перед королём, защищая его от
        шаха, то она является 'закреплённой', так как она не может совершить ход.)
        self.checks - список с объявленными шахами. Нужен для того чтобы различать шахи одной фигурой или двумя
        self.checkmate - указывает на то, стоит ли мат
        self.stalemate - указывает на то, стоит ли пат

        self.en_passant_square - кортеж, который будет хранить координаты квадрата, где возможно съедение пешки
        'на проходе'

        self.current_castle_rights - хранит информацию о возможных рокировках обоих игроков. По умолчанию рокировка
        возможна, так как не было совершено ни ходов королём, ни ладьёй, т.е. возможность рокироватсья есть, если
        между королём и ладьёй не будет фигур. Как только сдвинется либо король, либо одна из ладей, рокировка
        не будет возможна.
        self.castle_rights_log - лог с изменениями возможностей на рокировку. Нужен для того чтобы корректо отменить
        ход, если потребуется. По умолчанию заполняется копией объекта self.current_castle_rights
        """
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP", "bP", "bP", "bP", "bP", "bP", "bP", "bP"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wP", "wP", "wP", "wP", "wP", "wP", "wP", "wP"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.white_turn = True
        self.move_log = []

        self.move_functions = {"P": self.get_pawn_moves, "R": self.get_rook_moves, "N": self.get_knight_moves,
                               "B": self.get_bishop_moves, "Q": self.get_queen_moves, "K": self.get_king_moves}

        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.in_check = False
        self.pins = []
        self.checks = []
        self.checkmate = False
        self.stalemate = False

        self.en_passant_square = ()

        self.current_castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                               self.current_castle_rights.wqs, self.current_castle_rights.bqs)]

    """
    Метод 'совершает ход'.
    """

    def make_move(self, move):
        self.board[move.end_row][move.end_column] = move.piece_moved
        self.board[move.start_row][move.start_column] = "--"
        self.move_log.append(move)  # добавляем в лог сделанный ход
        self.white_turn = not self.white_turn  # меняем очередь хода

        # Обновляем позицию короля
        if move.piece_moved == 'wK':
            self.white_king_location = (move.end_row, move.end_column)
        elif move.piece_moved == 'bK':
            self.black_king_location = (move.end_row, move.end_column)

        # Проведение пешки до последнего ряда
        if move.pawn_promotion:
            # По умолчанию ставим ферзя вместо пешки
            self.board[move.end_row][move.end_column] = move.piece_moved[0] + 'Q'

        # Если текущий ход - ход пешкой на два квадрата вперёд, то следующим ходом возможно съедение пешки 'на проходе'
        if move.piece_moved[1] == 'P' and abs(move.start_row - move.end_row) == 2:
            self.en_passant_square = ((move.end_row + move.start_row) // 2, move.end_column)
        else:
            self.en_passant_square = ()
        # Если ход - съедение 'на проходе', то надо обновить состояние доски, чтобы съесть пешку
        if move.is_en_passant_move:
            self.board[move.start_row][move.end_column] = "--"

        # Рокировка
        if move.is_castling_move:
            if move.end_column - move.start_column == 2:    # Означает, что была сделана короткая рокировка
                # Перемещаем ладью на новое место
                self.board[move.end_row][move.end_column - 1] = self.board[move.end_row][move.end_column + 1]
                self.board[move.end_row][move.end_column + 1] = "--"    # Убираем ладью из старого квадрата
            else:   # Длинная рокировка
                # Перемещаем ладью на новое место
                self.board[move.end_row][move.end_column + 1] = self.board[move.end_row][move.end_column - 2]
                self.board[move.end_row][move.end_column - 2] = "--"    # Убираем ладью из старого квадрата

        # Если возможность рокировка была нарушена, то обновим значения соответствующих переменных
        self.update_castle_rights(move)
        self.castle_rights_log.append(CastleRights(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                                   self.current_castle_rights.wqs, self.current_castle_rights.bqs))

    """
    Отменяет последний совершённый ход
    """

    def undo_move(self):
        if len(self.move_log) != 0:  # Проверка на то, совершались ли ходы
            last_move = self.move_log.pop()
            self.board[last_move.start_row][last_move.start_column] = last_move.piece_moved
            self.board[last_move.end_row][last_move.end_column] = last_move.piece_captured
            self.white_turn = not self.white_turn

            # Обновляем позицию короля
            if last_move.piece_moved == 'wK':
                self.white_king_location = (last_move.start_row, last_move.start_column)
            elif last_move.piece_moved == 'bK':
                self.black_king_location = (last_move.start_row, last_move.start_column)

            # Отмена съедения 'на проходе'
            if last_move.is_en_passant_move:
                # Убираем пешку, которая была поставлена на 'неправильный' квадрат
                self.board[last_move.end_row][last_move.end_column] = "--"
                # Ставим пешку обратно в тот квадрат, откуда её съели
                self.board[last_move.start_row][last_move.end_column] = last_move.piece_captured
                # Делаем так, чтобы съедение на проходе после отмены хода снова было возможным
                self.en_passant_square = (last_move.end_row, last_move.end_column)

            # Отмена хода на два квадрата вперёд может вызвать баги, если не обнулить возможность съедения 'на проходе'
            if last_move.piece_moved[1] == 'P' and abs(last_move.start_row - last_move.end_row) == 2:
                self.en_passant_square = ()

            # Обновить возможность рокировки при отмене хода
            # Избавляемся от тех возможных рокировках, которые могли быть на ходе, который мы отменили
            self.castle_rights_log.pop()
            # Устанавливаем 'правильные' возможности рокировок, которые были актуальны до совершения предыдущего хода
            new_rights = self.castle_rights_log[-1]
            self.current_castle_rights = CastleRights(new_rights.wks, new_rights.bks, new_rights.wqs, new_rights.bqs)

            # Отменить рокировку
            if last_move.is_castling_move:
                if last_move.end_column - last_move.start_column == 2:  # Короткая рокировка
                    # Ставим ладью на предыдущую позицию
                    self.board[last_move.end_row][last_move.end_column + 1] = \
                        self.board[last_move.end_row][last_move.end_column - 1]
                    self.board[last_move.end_row][last_move.end_column - 1] = "--"
                else:   # Длинная рокировка
                    # Ставим ладью на предыдущую позицию
                    self.board[last_move.end_row][last_move.end_column - 2] = \
                        self.board[last_move.end_row][last_move.end_column + 1]
                    self.board[last_move.end_row][last_move.end_column + 1] = "--"

    """
    Метод для обновления значений, отвечающих за возможность рокировки
    """

    def update_castle_rights(self, move):
        ally_color = move.piece_moved[0]  # Устанавливаем цвет фигуры текущего хода

        if ally_color == 'w':  # Если ход белых
            if move.piece_moved[1] == 'K':  # Если ход был совершён королём, то рокировка более невозможна
                self.current_castle_rights.wks = False
                self.current_castle_rights.wqs = False
            # Если ход был совершён ладьёй, проверяем, на каком фланге и убираем возможность рокировки на этом фланге
            elif move.piece_moved[1] == 'R':
                if move.start_row == 7:
                    if move.start_column == 0:
                        self.current_castle_rights.wqs = False
                    elif move.start_column == 7:
                        self.current_castle_rights.wks = False

        elif ally_color == 'b':  # Если ход чёрных
            if move.piece_moved[1] == 'K':  # Если ход был совершён королём, то рокировка более невозможна
                self.current_castle_rights.bks = False
                self.current_castle_rights.bqs = False
            # Если ход был совершён ладьёй, проверяем, на каком фланге и убираем возможность рокировки на этом фланге
            elif move.piece_moved[1] == 'R':
                if move.start_row == 0:
                    if move.start_column == 0:
                        self.current_castle_rights.bqs = False
                    elif move.start_column == 7:
                        self.current_castle_rights.bks = False

    """
    Возможные ходы с учётом шахов
    """

    def get_valid_moves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.check_for_pins_and_checks()
        temp_castle_rights = CastleRights(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                          self.current_castle_rights.wqs, self.current_castle_rights.bqs)

        # Для начала нужно понять, чей сейчас ход, чтобы запомнить позицию короля, чтобы корректно сформировать
        # возможные ходы без получения шахов
        if self.white_turn:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        # Теперь проверяем, находится ли король под шахом и обрабатываем возможные ситуации
        if self.in_check:
            if len(self.checks) == 1:  # объявлен шах одной фигурой => можно заблокироваться другой фигурой (если шах
                # ставит не конь) или отойти
                moves = self.get_all_possible_moves()

                # Блокировка от шаха. Чтобы заблокироваться достаточно поставить какую-либо из фигур между королём
                # и фигурой, объявляющей шах
                check = self.checks[0]
                check_row = check[0]
                check_col = check[1]
                checking_piece = self.board[check_row][check_col]  # Узнаём, какая фигура поставила шах
                valid_squares = []  # Сюда будут записываться квадраты, на которые можно встать, чтобы заблокироваться

                # Если шах поставил конь, то, чтобы избавиться от шаха можно только забрав коня или отойдя королём
                if checking_piece[1] == 'N':
                    valid_squares = [(check_row, check_col)]
                # В остальных случаях можно заблокироваться
                else:
                    for i in range(1, 8):
                        # check[2] и check[3] показывают направление, откуда объявлен шах
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        # В случае, если для того чтобы избавиться от шаха, можно ТОЛЬКО съесть фигуру, то это
                        # единственный возможный ход и нет необходимости рассматривать другие. Прерываем цикл
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break

                # Теперь нужно удалить все остальные, недоступные при шахе ходы
                # Чтобы корректно удалить ходы, их нужно удалять в обратном порядке, для этого будем итерироваться
                # с конца
                for i in range(len(moves) - 1, -1, -1):
                    if moves[i].piece_moved[1] != 'K':
                        # Если ход не блокирует шах или не 'съедает' фигуру, которая ставит шах, то убираем ход
                        # из списка возможных
                        if (moves[i].end_row, moves[i].end_column) not in valid_squares:
                            moves.remove(moves[i])
            else:  # Объявлен двойной шах. В этом случае избавитсья от шаха можно только сходив королём
                self.get_king_moves(king_row, king_col, moves)
        else:  # Шахи не объявлены, значит все ходы возможны
            moves = self.get_all_possible_moves()
            # Отдельно добавляем ходы для рокировки
            if self.white_turn:
                self.get_castle_moves(self.white_king_location[0], self.white_king_location[1], moves)
            else:
                self.get_castle_moves(self.black_king_location[0], self.black_king_location[1], moves)

        self.current_castle_rights = temp_castle_rights

        # Проверка, не стоит ли мат или пат
        if len(moves) == 0:
            if self.in_check:
                self.checkmate = True
            else:
                self.stalemate = True

        return moves

    """
    Возможные ходы без учёта шахов
    """

    def get_all_possible_moves(self):
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[row])):
                # Переменной turn присваивается значение первого символа ячейки, таким образом можно узнать, есть ли
                # в текущей ячейке фигура и, если она там есть, то мы будем знать, какого она цвета.
                turn = self.board[row][col][0]
                if (turn == 'w' and self.white_turn) or (turn == "b" and not self.white_turn):
                    piece = self.board[row][col][1]
                    self.move_functions[piece](row, col, moves)  # Вызывает метод для конкретных фигур из словаря
        return moves

    """
    Получить все возможные ходы для пешки, расположенной в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_pawn_moves(self, row, col, moves):
        piece_pinned = False
        pin_direction = ()

        for i in range(len(self.pins) - 1, -1, -1):  # Проверяем, 'закреплена' ли текущая пешка
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                # Устанавливаем направление, откуда идёт 'закрепление' пешки
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        # Устанавливаем характеристики ходов для текущего цвета фигуры
        if self.white_turn:
            squares_amount = -1
            start_row = 6
            enemy_color = 'b'
        else:
            squares_amount = 1
            start_row = 1
            enemy_color = 'w'

        if self.board[row + squares_amount][col] == "--":  # Движение на 1 клетку вперёд
            if not piece_pinned or pin_direction == (squares_amount, 0):
                moves.append(Move((row, col), (row + squares_amount, col), self.board))
                if row == start_row and self.board[row + 2 * squares_amount][col] == "--":  # Продвижение на 2 клетки
                    moves.append(Move((row, col), (row + 2 * squares_amount, col), self.board))

        if col - 1 >= 0:  # Съедение пешки слева
            if not piece_pinned or pin_direction == (squares_amount, -1):
                if self.board[row + squares_amount][col - 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + squares_amount, col - 1), self.board))
                if (row + squares_amount, col - 1) == self.en_passant_square:  # Съедение 'на проходе'
                    moves.append(Move((row, col), (row + squares_amount, col - 1), self.board, is_en_passant_move=True))

        if col + 1 <= 7:  # Съедение пешки справа
            if not piece_pinned or pin_direction == (squares_amount, 1):
                if self.board[row + squares_amount][col + 1][0] == enemy_color:
                    moves.append(Move((row, col), (row + squares_amount, col + 1), self.board))
                if (row + squares_amount, col + 1) == self.en_passant_square:  # Съедение 'на проходе'
                    moves.append(Move((row, col), (row + squares_amount, col + 1), self.board, is_en_passant_move=True))

    """
    Получить все возможные ходы для ладьи, расположенной в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_rook_moves(self, row, col, moves):
        piece_pinned = False
        pin_direction = ()

        for i in range(len(self.pins) - 1, -1, -1):  # Проверяем, 'закреплена' ли ладья
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != 'Q':  # Так как ферзь заимствует возможные ходы ладьи, то нужна проверка
                    self.pins.remove(self.pins[i])
                break

        directions = ((-1, 0), (0, 1), (1, 0), (0, -1))  # Четыре всевозможных направления для ходов ладьи
        enemy_color = 'b' if self.white_turn else 'w'  # Помечаем цвет фигуры противника

        for direction in directions:  # Проверяем каждое из направлений
            for i in range(1, 8):
                # В начале каждого цикла проверяем следующую по направлению клетку.
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i

                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    # Проверка на то, 'закреплена' ли фигура, если да, то её ходы ограничены.
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0],
                                                                                           -direction[1]):
                        next_square = self.board[end_row][end_col]

                        if next_square == "--":  # Проверка на то, пустая ли следующая клетка
                            moves.append(Move((row, col), (end_row, end_col), self.board))

                        elif next_square[0] == enemy_color:  # Стоит ли на следующей клетке вражеска фигура
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break

                        else:  # Иначе упираемся в союзную фигуру, ходы невозможны
                            break
                else:  # Выход за доску
                    break

    """
    Получить все возможные ходы для коня, расположенного в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_knight_moves(self, row, col, moves):
        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):  # Проверка 'закрепления' фигуры
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        # Всевозможные ходы конём от текущего положения фигуры.
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        ally_color = 'w' if self.white_turn else 'b'  # Получаем цвет союзной фигуры

        for move in knight_moves:
            end_row = row + move[0]
            end_col = col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:  # Проверка на то, чтобы не выйти за границы доски
                if not piece_pinned:  # Проверяем, не 'закреплена' ли фигура
                    end_piece = self.board[end_row][end_col]
                    # Если на конечной клетке фигурыы нет союзной фигуры, то мы можем поместить туда коня.
                    if end_piece[0] != ally_color:
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    """
    Получить все возможные ходы для слона, расположенного в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_bishop_moves(self, row, col, moves):
        piece_pinned = False
        pin_direction = ()

        for i in range(len(self.pins) - 1, -1, -1):  # Проверка, 'закрепления' фигуры
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemy_color = 'b' if self.white_turn else 'w'  # Помечаем цвет фигуры противника

        for direction in directions:  # Проверяем каждое из направлений
            for i in range(1, 8):
                # В начале каждого цикла проверяем следующую по направлению клетку.
                end_row = row + direction[0] * i
                end_col = col + direction[1] * i

                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    # Проверка на то, не 'закреплена' ли фигура
                    if not piece_pinned or pin_direction == direction or pin_direction == (-direction[0],
                                                                                           -direction[1]):
                        next_square = self.board[end_row][end_col]

                        if next_square == "--":  # Проверка на то, пустая ли следующая клетка
                            moves.append(Move((row, col), (end_row, end_col), self.board))

                        elif next_square[0] == enemy_color:  # Стоит ли на следующей клетке вражеска фигура
                            moves.append(Move((row, col), (end_row, end_col), self.board))
                            break

                        else:  # Иначе упираемся в союзную фигуры, ходы невозможны
                            break
                else:  # Выход за доску
                    break

    """
    Получить все возможные ходы для ферзя, расположенного в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_queen_moves(self, row, col, moves):
        self.get_rook_moves(row, col, moves)
        self.get_bishop_moves(row, col, moves)

    """
    Получить все возможные ходы для короля, расположенного в конкретной ячейке (row, col) и добавить эти ходы в список
    """

    def get_king_moves(self, row, col, moves):
        # Всевозможные ходы короля
        possible_king_moves = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
        ally_color = 'w' if self.white_turn else 'b'  # Помечаем цвет союзной фигуры

        for i in range(8):
            end_row = row + possible_king_moves[i][0]
            end_col = col + possible_king_moves[i][1]

            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                next_square = self.board[end_row][end_col]

                # Проверка на то, является ли следующий квадрат союзной фигурой.
                if next_square[0] != ally_color:
                    # Чтобы понять, возможен ли ход королём, надо проверить, вызывает ли этот ход шах.
                    # Для этого временно установим новое положение короля (в зависимости от цвета)
                    if ally_color == 'w':
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    # И проверяем, попадает ли король под шахи
                    in_check, pins, checks = self.check_for_pins_and_checks()
                    # Если нет, то ход возможен
                    if not in_check:
                        moves.append(Move((row, col), (end_row, end_col), self.board))
                    # Иначе ход не будет добавлен в список возможных. В конце итерации делаем положение короля прежним.
                    if ally_color == 'w':
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

    """
    Функция определяет, находится ли конкретный квадрат под атакой. Нужно для корректного проведения рокировки.
    """

    def square_under_attack(self, row, col):
        self.white_turn = not self.white_turn  # Меняем очередь хода
        enemy_moves = self.get_all_possible_moves()  # Получаем все ходы противника
        self.white_turn = not self.white_turn  # Меняем очерёдность обратно
        for move in enemy_moves:
            if move.end_row == row and move.end_column == col:  # Если это условие выполняется - квадрат под атакой
                return True
        return False  # Если ни один из ходов противника не нападет на квадрат, возвращаем False

    """
    Сгенерировать все возможные рокировки для короля на поле (row, col) и добавить их в список возможных ходов
    """

    def get_castle_moves(self, row, col, moves):
        if self.square_under_attack(row, col):  # Возможности рокироваться нет, если король под шахом
            return
        if (self.white_turn and self.current_castle_rights.wks) or \
                (not self.white_turn and self.current_castle_rights.bks):
            self.get_king_side_castle_moves(row, col, moves)
        if (self.white_turn and self.current_castle_rights.wqs) or \
                (not self.white_turn and self.current_castle_rights.bqs):
            self.get_queen_side_castle_moves(row, col, moves)

    """
    get_king_side_castle_moves и get_queen_side_castle_moves - функции, вспомогательные к get_castle_moves.
    Нужны для того чтобы обрабатывать рокировку в короткую и длинные стороны по отдельности.
    """

    def get_king_side_castle_moves(self, row, col, moves):
        if self.board[row][col + 1] == "--" and self.board[row][col + 2] == "--":
            if not self.square_under_attack(row, col + 1) and not self.square_under_attack(row, col + 2):
                moves.append(Move((row, col), (row, col + 2), self.board, is_castling_move=True))

    def get_queen_side_castle_moves(self, row, col, moves):
        if self.board[row][col - 1] == "--" and self.board[row][col - 2] == "--" and self.board[row][col - 3] == "--":
            if not self.square_under_attack(row, col - 1) and not self.square_under_attack(row, col - 2):
                moves.append(Move((row, col), (row, col - 2), self.board, is_castling_move=True))

    """
    Метод для того чтобы получить возможные 'закрепления' фигур и шахи
    """

    def check_for_pins_and_checks(self):
        pins = []  # Список с квадратами, где 'закреплены' союзные фигуры и направление, откуда фигура 'закреплена'
        checks = []  # Квадраты, из которых может быть поставлен шах
        in_check = False

        if self.white_turn:
            ally_color = 'w'
            enemy_color = 'b'
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            ally_color = 'b'
            enemy_color = 'w'
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]

        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            direction = directions[j]
            possible_pin = ()  # Обновляем возможные 'закрепления'
            for i in range(1, 8):
                end_row = start_row + direction[0] * i
                end_col = start_col + direction[1] * i
                if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                    end_piece = self.board[end_row][end_col]  # Присваиваем значение конкретного квадрата на доске
                    # Если этот квадрат оказался фигурой, то она потенциально может быть 'закреплена'
                    if end_piece[0] == ally_color and end_piece[1] != 'K':
                        # Проверка на то первая ли текущая фигура в заданном направление перед королём, и если да,
                        # то эта фигура может быть 'закреплена'
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, direction[0], direction[1])
                        # В противном случае перед королём в заданном направлении две или более фигур, 'закрепления' нет
                        else:
                            break
                    elif end_piece[0] == enemy_color:
                        """
                        В следующем условном блоке рассматривается 5 возможных ситуаций:    
                        1) фигура расположена ортогонально от короля и является ладьёй
                        2) фигура расположена диагонально от короля и является слоном
                        3) фигура расположена диагонально в расстоянии 1 квадрата и является пешкой
                        4) фигура расположена в любом из направлений и является ферзём
                        5) фигура расположена в любом из направлений и является королём противника (этот блок необходим
                        для того, чтобы не допустить возможности хода королём на квадрат, который контролируется другим
                        королём)
                        """
                        piece_type = end_piece[1]

                        if (0 <= j <= 3 and piece_type == 'R') or \
                                (4 <= j <= 7 and piece_type == 'B') or \
                                (i == 1 and piece_type == 'P' and ((enemy_color == 'w' and 6 <= j <= 7) or
                                                                   (enemy_color == 'b' and 4 <= j <= 5))) or \
                                (piece_type == 'Q') or (i == 1 and piece_type == 'K'):
                            if possible_pin == ():  # Никакие фигуры не 'закреплены' => стоит шах
                                in_check = True
                                checks.append((end_row, end_col, direction[0], direction[1]))
                                break
                            else:  # Фигура стоит перед королём в заданном направлении => она 'закреплена'
                                pins.append(possible_pin)
                                break
                        else:  # Если ни одно из условий не выполняется, то фигура противника не может поставить шах
                            break
                else:  # Если по заданному направлению нет фигур, то выходим из цикла
                    break

        # Отдельно стоит рассмотреть возможные шахи конём, так как логика в этом случае отличается
        knight_moves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1))
        for move in knight_moves:
            end_row = start_row + move[0]
            end_col = start_col + move[1]
            if 0 <= end_row <= 7 and 0 <= end_col <= 7:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'N':  # Если конь ставит шах королю
                    in_check = True
                    checks.append((end_row, end_col, move[0], move[1]))

        return in_check, pins, checks


# Класс CastleRights хранит информацию о возможностях сделать рокировку в текущий момент игры
class CastleRights:
    """
    Конструктор с 4-мя параметрами:
    wks - white king side - указывает на возможность сделать рокировку на королевском фланге за белых
    bks - black king side - аналогично с wks, но за чёрных
    wqs - white queen side - указывает на возможность сделать рокировку на ферзевом фланге за белых
    bqs - black queen side - аналогично с wqs, но за чёрных
    """

    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move:
    """
    Так как в классических шахматах доска в стобцах пронумерована от "a" до "h", а строки от 1 до 8,
    то конвертируем наши координаты в эту систему. Это понадобится для того чтобы отображать совершённые ходы.
    """
    ranks_to_rows = {"1": 7, "2": 6, "3": 5, "4": 4,
                     "5": 3, "6": 2, "7": 1, "8": 0}
    rows_to_ranks = {value: key for key, value in ranks_to_rows.items()}
    files_to_columns = {"a": 0, "b": 1, "c": 2, "d": 3,
                        "e": 4, "f": 5, "g": 6, "h": 7}
    columns_to_files = {value: key for key, value in files_to_columns.items()}

    """
    При инициализации объекта данного класса, мы запоминаем совершённые игроком действия: какой фигурой он сходил,
    куда сходил, какую фигуру съел(если клетка не пустая), а после этот ход добавляется в лог, 
    это понадобится для того чтобы у игроков была возможность вернуть ход.
    """

    def __init__(self, start_square, end_square, board, is_en_passant_move=False, is_castling_move=False):
        self.start_row = start_square[0]
        self.start_column = start_square[1]
        self.end_row = end_square[0]
        self.end_column = end_square[1]
        self.piece_moved = board[self.start_row][self.start_column]
        self.piece_captured = board[self.end_row][self.end_column]

        # Является ли ход проведением пешки в конечный ряд
        self.pawn_promotion = ((self.piece_moved == 'wP' and self.end_row == 0) or
                               (self.piece_moved == 'bP' and self.end_row == 7))

        # Является ли ход съедением пешки 'на проходе'
        self.is_en_passant_move = is_en_passant_move
        if is_en_passant_move:
            self.piece_captured = 'bP' if self.piece_moved == 'wP' else 'wP'

        # Рокировка
        self.is_castling_move = is_castling_move

        # Генерация уникального moveID
        self.moveID = self.start_row * 1000 + self.start_column * 100 + self.end_row * 10 + self.end_column

    # Перегрузка метода equals
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    # Получить классические шахматные координаты(например: e2)
    def get_chess_notation(self):
        return self.get_rank_file(self.start_row, self.start_column) + self.get_rank_file(self.end_row, self.end_column)

    def get_rank_file(self, row, column):
        return self.columns_to_files[column] + self.rows_to_ranks[row]
