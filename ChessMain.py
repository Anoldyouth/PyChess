"""
Это основной файл. Он будет отвечать за обработку пользовательского ввода и визуализацию текущего игрового состояния
с помощью объекта класса GameState.
"""

import pygame as pg
from Chess import ChessEngine

WIDTH = HEIGHT = 512  # Разрешение экрана (нужно подбирать по разрешению фигурок так, чтобы они выглядели хорошо)
DIMENSION = 8  # Принятая размерность шахматной доски (8х8). (должно нацело делиться на разрешение)
SQ_SIZE = WIDTH // DIMENSION  # Размер квадратов
MAX_FPS = 15  # Для анимации, которая будет позже
IMAGES = {}

"""
Создадим функцию, которая инициализирует изображения фигур. Это будет происходит только один раз и данные будут
храниться в глобальном словаре IMAGES
"""


def load_images():
    pieces = ["wP", "bP", "wR", "bR", "wN", "bN", "wB", "bB", "wQ", "bQ", "wK", "bK"]
    for piece in pieces:
        IMAGES[piece] = pg.transform.scale(pg.image.load("Chess/images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))
    # Теперь, чтобы вызвать какую-либо фигуру из словаря, достаточно написать, например, 'IMAGES["wP"]'


"""
Далее начинается основное тело программы, где будет происходить обработка ввода игроком и работа с графикой.
"""


def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    clock = pg.time.Clock()
    screen.fill(pg.Color("white"))
    gs = ChessEngine.GameState()  # Инициализируем основной класс. Ответсвеннен за все игровые аспекты
    valid_moves = gs.get_valid_moves()  # Получаем возможные ходы
    """
    Флаг, который меняет значение, когда будет совершён ход(это нужно для того чтобы не затрачивать много 
    ресурсов и не производить вычисления(например, узнавать, возможен ли ход) через каждый кадр. 
    Мы будем производить вычисления только после того, как игрок попытается этот самый ход совершить)
    """
    is_move_made = False

    animate = False  # Флаг, который указывает, нужно ли анимировать ход. Например, отмена хода не анимируется

    load_images()  # Подгружаем изображения фигур
    is_running = True
    # Кортеж, в котором будут храниться координаты по строкам и столбцам, по которым кликнул пользователь: (row, column)
    selected_square = ()
    # Список будет хранить два элемента с историей кликов игрока. Каждый из элементов списка - кортеж с координатами
    player_clicks = []

    is_game_over = False  # Флаг, чтобы, если игра завершилась, не обрабатывать запросы мыши игрока

    while is_running:
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                is_running = False

            # Обработка запросов с мыши
            elif ev.type == pg.MOUSEBUTTONDOWN:
                if not is_game_over:
                    mouse_location = pg.mouse.get_pos()  # Положение курсора по координатам (x,y)
                    # Положение курсора по квадратам шахматной доски:
                    column = mouse_location[0] // SQ_SIZE
                    row = mouse_location[1] // SQ_SIZE
                    # Если пользователь кликнул по квадрату дважды, фактически, передумав ходить этой фигурой, то мы
                    # обнуляем кортеж с выбранными координатами и историю кликов игрока.
                    if selected_square == (row, column):
                        selected_square = ()
                        player_clicks.clear()
                    # Иначе запоминаем выбранный квадрат и добавляем его в список с историей кликов
                    else:
                        selected_square = (row, column)
                        player_clicks.append(selected_square)
                    if len(player_clicks) == 2:  # Обработка второго клика пользователем
                        move = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        print(move.get_chess_notation())
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                gs.make_move(valid_moves[i])
                                # Добавить проведение пешки здесь (запрос ответа от пользователя, какую фигуру создать)
                                is_move_made = True
                                animate = True  # Ход возможен, его можно анимировать
                                selected_square = ()
                                player_clicks.clear()
                        if not is_move_made:
                            player_clicks = [selected_square]
            # Обработка запросов с клавиатуры
            if ev.type == pg.KEYDOWN:
                if ev.key == pg.K_z:  # Отменить ход, если нажата клавиша "z"
                    gs.undo_move()
                    is_move_made = True
                    animate = False  # Незачем анимировать отмену хода

                if ev.key == pg.K_r:  # Начать новую игру, если была нажата клавиша 'R'
                    gs = ChessEngine.GameState()  # Создаём новую доску
                    # Обновляем значение некоторых переменных
                    valid_moves = gs.get_valid_moves()
                    selected_square = ()
                    player_clicks = []
                    is_move_made = False
                    animate = False

        if is_move_made:
            if animate:
                move_animation(gs.move_log[-1], screen, gs.board, clock)
            valid_moves = gs.get_valid_moves()
            is_move_made = False
            animate = False

        draw_game_state(screen, gs, valid_moves, selected_square)

        if gs.checkmate:
            is_game_over = True
            if gs.white_turn:
                draw_text(screen, "Белым объявлен мат. Победа чёрных.")
            else:
                draw_text(screen, "Чёрным объявлен мат. Победа белых.")
        elif gs.stalemate:
            is_game_over = True
            draw_text(screen, "Пат.")

        clock.tick(MAX_FPS)
        pg.display.flip()


"""
Отвественна за всю графику в течение игры
"""


def draw_game_state(screen, gs, valid_moves, selected_square):
    draw_board(screen)  # Рисует квадраты на доске
    highlight_squares(screen, gs, valid_moves, selected_square)
    draw_pieces(screen, gs.board)  # Рисует фигуры


"""
Рисует квадраты на доске. Верхний левый квадрат всегда белый, независимо от того, каким цветом Вы играете.
"""


def draw_board(screen):
    global colors
    colors = [pg.Color("white"), pg.Color("gray")]
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            color = colors[(row + column) % 2]
            pg.draw.rect(screen, color, pg.Rect(column * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


"""
Отрисовка фигур
"""


def draw_pieces(screen, board):
    for row in range(DIMENSION):
        for column in range(DIMENSION):
            piece = board[row][column]
            if piece != '--':
                screen.blit(IMAGES[piece], pg.Rect(column * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))


"""
Подсветка квадрата с выбранной фигурой и подсветка возможных ходов для этой фигуры
"""


def highlight_squares(screen, gs, valid_moves, selected_square):
    if selected_square != ():  # Проверка на то, выбран ли квадрат(чтобы избежать случайных подсветок пустых квадратов)
        row, col = selected_square
        # Проверка на то, является ли выбранный квадрат фигурой, которой можно сходить
        if gs.board[row][col][0] == ('w' if gs.white_turn else 'b'):
            # Подсветка выбранного квадрата
            surface = pg.Surface((SQ_SIZE, SQ_SIZE))  # Поверхность, которую надо подсветить
            surface.set_alpha(150)  # Прозрачность. 0 - прозрачный, 255 - непрозрачный
            surface.fill(pg.Color('burlywood'))  # Цвет подсветки
            screen.blit(surface, (col * SQ_SIZE, row * SQ_SIZE))  # Отвечает за подсветку

            # Подсветка ходов выбранной фигуры
            surface.set_alpha(100)  # Для подсветки ходов ставим другую прозрачность
            surface.fill(pg.Color('cadetblue'))  # Цвет подсветки
            for move in valid_moves:
                if move.start_row == row and move.start_column == col:
                    screen.blit(surface, (SQ_SIZE * move.end_column, SQ_SIZE * move.end_row))


"""
Анимация хода
"""


def move_animation(move, screen, board, clock):
    global colors

    d_row = move.end_row - move.start_row  # Разница между конечной и начальной строкой шахматной доски
    d_col = move.end_column - move.start_column  # Разница между конечным и начальным столбцом шахматной доски
    frames_per_square = 10  # Сколько кадров будет затрачиваться на передвижение фигуры через один квадрат
    frame_count = (abs(d_row) + abs(d_col)) * frames_per_square

    for frame in range(frame_count + 1):
        # Получаем координаты каждого кадра по строкам и столбцам
        row, col = (move.start_row + d_row * frame / frame_count, move.start_column + d_col * frame / frame_count)
        draw_board(screen)
        draw_pieces(screen, board)

        # Нужно стереть фигуру из того места, куда она должна встать, чтобы отрисовать движение и чтобы только после
        # этого она там оказалась.
        color = colors[(move.end_row + move.end_column) % 2]
        end_square = pg.Rect(move.end_column * SQ_SIZE, move.end_row * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pg.draw.rect(screen, color, end_square)

        # Если на конечном квадрате стоит фигура, то ставим туда фигуру, которая будет съедена, как только анимация
        # завершится
        if move.piece_captured != "--":
            screen.blit(IMAGES[move.piece_captured], end_square)

        # Отрисовка движущейся фигуры
        screen.blit(IMAGES[move.piece_moved], pg.Rect(col * SQ_SIZE, row * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        pg.display.flip()
        clock.tick(144)


def draw_text(screen, text):
    font = pg.font.SysFont("Helvitca", 34, False, False)  # Шрифт
    text_obj = font.render(text, False, pg.Color("gray20"))
    # Размещаем текст по центру
    text_location = pg.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH / 2 - text_obj.get_width() / 2,
                                                      HEIGHT / 2 - text_obj.get_height() / 2)

    screen.blit(text_obj, text_location)
    # Добавим поверх старого текста новый, чтобы получить обводку
    text_obj = font.render(text, False, pg.Color("darkseagreen4"))
    screen.blit(text_obj, text_location.move(2, 2))



if __name__ == "__main__":
    main()
