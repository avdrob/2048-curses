#!/usr/bin/python3

import curses
import random
import sys

import config


class Game:
    def __init__(self, mode=config.Mode.Large):
        self.__mode = mode
        self.graphics_inited = False

    @property
    def mode(self):
        return self.__mode

    @property
    def map(self):
        return self.__map

    def init_graphics(self):
        self.perform_checks()

        curses.initscr()            # window object representing screen
        curses.noecho()             # turn off automatic echoing of keys
        curses.cbreak()             # cbreak mode: react to keys instantly
        curses.curs_set(False)

        # Initialize colors
        curses.start_color()
        for value, pairnum in config.color_pairs.items():
            curses.init_pair(pairnum, *config.colors[value])

        self.graphics_inited = True

    def error_exit(self, message):
        if self.graphics_inited:
            self.deinit_graphics()
        print(message, file=sys.stderr)
        sys.exit(1)

    def perform_checks(self):
        curses.setupterm()
        colors = curses.tigetnum('colors')
        lines = curses.tigetnum('lines')
        cols = curses.tigetnum('cols')

        if colors < config.colors_num:
            self.error_exit('Sorry, your terminal has no' +
                            '{} colors support'.format(config.colors_num))

        while True:
            modeset = config.game_modes[self.mode]
            size = modeset['size']
            cell_nlines = modeset['cell_nlines']
            cell_ncols = modeset['cell_ncols']

            if (cell_nlines * size <= lines and
                    cell_ncols * size <= cols):
                break
            if self.mode == config.Mode.Large:
                self.__mode = config.Mode.Small
                continue
            else:
                self.error_exit(
                        'Sorry, your terminal size is ' +
                        'insufficient.\nTo play the game ' +
                        'you need a terminal of size at least ' +
                        '{}x{}'.format(cell_ncols * size, cell_nlines * size)
                )

    def create_new(self):
        self.perform_checks()

        self.__map = Map(self, self.mode)
        self.map.gen_cell()
        self.map.draw()

        self.score = 0
        self.moves = 0

    def __get_terminal_key(self):
        while True:
            key = self.map.window.getch()
            if key == ord('r') or key == ord('q'):
                return key

    def game_over(self):
        self.map.draw_words(self.map.game_over)
        return self.__get_terminal_key()

    def you_win(self):
        self.map.draw_words(self.map.you_win)
        return self.__get_terminal_key()

    def play_game(self):
        while True:
            layout_changed = False
            key = self.map.window.getch()

            if key == curses.KEY_UP or key == ord('k'):
                layout_changed = self.map.move_up()
            elif key == curses.KEY_DOWN or key == ord('j'):
                layout_changed = self.map.move_down()
            elif key == curses.KEY_LEFT or key == ord('h'):
                layout_changed = self.map.move_left()
            elif key == curses.KEY_RIGHT or key == ord('l'):
                layout_changed = self.map.move_right()
            elif key == ord('r'):
                self.create_new()
                continue
            elif key == ord('q'):
                break

            if not layout_changed:
                continue

            if self.map.is_thrhold_reached():
                self.map.draw()
                key = self.you_win()
                if key == ord('r'):
                    self.create_new()
                    continue
                else:
                    break

            self.map.gen_cell()
            self.map.draw()
            if not self.map.is_movable():
                key = self.game_over()
                if key == ord('r'):
                    self.create_new()
                    continue
                else:
                    break

    def deinit_graphics(self):
        curses.nocbreak()
        curses.echo()
        curses.endwin()


class MapPos:
    '''
    A helper class containing line and column position of a cell on the map
    '''
    def __init__(self, line, col):
        self.line = line
        self.col = col


class Cell:
    '''
    A cell of the game map. It can either contain value or be empty.
    In latter case value == None
    '''
    def __init__(self, map, pos, value):
        self.__map = map
        self.pos = pos
        self.value = value

    @property
    def map(self):
        return self.__map

    def text_height(self):
        return len(self.map.numbers[self.value])

    def text_width(self):
        return max([len(row) for row in self.map.numbers[self.value]])

    def is_empty(self):
        '''
        Returns whether the cell contains a numeric value or just is_empty
        '''
        return not bool(self.value)

    def above(self):
        if self.pos.line == 0:
            return None
        return self.map.grid[self.pos.line-1][self.pos.col]

    def below(self):
        if self.pos.line == self.map.size-1:
            return None
        return self.map.grid[self.pos.line+1][self.pos.col]

    def onleft(self):
        if self.pos.col == 0:
            return None
        return self.map.grid[self.pos.line][self.pos.col-1]

    def onright(self):
        if self.pos.col == self.map.size-1:
            return None
        return self.map.grid[self.pos.line][self.pos.col+1]

    def draw_text(self):
        cur_width, cur_height = self.text_width(), self.text_height()
        begin_x = (self.map.cell_ncols - cur_width) // 2
        begin_y = (self.map.cell_nlines - cur_height) // 2

        for i in range(cur_height):
            self.map.window.addstr(
                    self.pos.line * self.map.cell_nlines + begin_y + i,
                    self.pos.col * self.map.cell_ncols + begin_x,
                    self.map.numbers[self.value][i],
                    curses.color_pair(config.color_pairs[self.value] |
                                      curses.A_BOLD)
            )

    def draw(self):
        '''
        Draw cell on the map
        '''
        for i in range(self.map.cell_nlines):
            self.map.window.addstr(
                    self.pos.line * self.map.cell_nlines + i,
                    self.pos.col * self.map.cell_ncols,
                    ' ' * self.map.cell_ncols,
                    curses.color_pair(config.color_pairs[self.value])
            )

        if not self.is_empty():
            self.draw_text()


class Map:
    '''
    Contains grid of cells
    '''
    def __init__(self, game, mode):
        self.__game = game
        self.__mode = mode
        self.__modeset = config.game_modes[mode]
        self.__size = self.modeset['size']
        self.__cell_nlines = self.modeset['cell_nlines']
        self.__cell_ncols = self.modeset['cell_ncols']
        self.__numbers = self.modeset['numbers']
        self.__game_over = self.modeset['game_over']
        self.__you_win = self.modeset['you_win']
        self.__thrhold = config.thrhold

        if self.modeset['center']:
            begin_y = (curses.tigetnum('lines') -
                       self.cell_nlines * self.size) // 2
            begin_x = (curses.tigetnum('cols') -
                       self.size * self.cell_ncols) // 2
        else:
            begin_y, begin_x = 0, 0
        self.__window = curses.newwin(
                            self.cell_nlines * self.size + 1,
                            self.cell_ncols * self.size,
                            begin_y, begin_x
                        )
        # keypad mode: return special values for keys
        self.window.keypad(True)

        self.__empty_num = self.size * self.size
        self.__max_value = 0
        self.gen_grid()

        # Prepate for cells generation
        random.seed()
        self.lin_pos_prev = 0

    @property
    def size(self):
        return self.__size

    @property
    def mode(self):
        return self.__mode

    @property
    def modeset(self):
        return self.__modeset

    @property
    def cell_nlines(self):
        return self.__cell_nlines

    @property
    def cell_ncols(self):
        return self.__cell_ncols

    @property
    def numbers(self):
        return self.__numbers

    @property
    def game_over(self):
        return self.__game_over

    @property
    def you_win(self):
        return self.__you_win

    @property
    def thrhold(self):
        return self.__thrhold

    @property
    def window(self):
        return self.__window

    @property
    def game(self):
        return self.__game

    @property
    def grid(self):
        return self.__grid

    @property
    def empty_num(self):
        return self.__empty_num

    @property
    def max_value(self):
        return self.__max_value

    def cells(self):
        '''
        A handy generator saving us from iteration over nested list
        '''
        for i in range(self.size):
            for j in range(self.size):
                yield self.grid[i][j]

    def gen_cell(self):
        '''
        Generate new cell position different from the previous one
        '''
        while True:
            lin_pos = random.randint(1, self.empty_num)
            if lin_pos != self.lin_pos_prev or self.empty_num < 2:
                self.lin_pos_prev = lin_pos
                break
        value = 4 if random.randint(1, 100) <= config.four_probability else 2

        cnt = 0
        for cell in self.cells():
            if cell.is_empty():
                cnt += 1
            if cnt == lin_pos:
                target = cell
                break

        pos = target.pos
        self.grid[pos.line][pos.col] = Cell(self, pos, value)
        self.__empty_num -= 1

    def gen_grid(self):
        self.__grid = [[Cell(self, MapPos(i, j), None)
                        for j in range(self.size)]
                       for i in range(self.size)]

    def swap_cells(self, cell1, cell2):
        self.grid[cell1.pos.line][cell1.pos.col] = cell2
        self.grid[cell2.pos.line][cell2.pos.col] = cell1
        cell1.pos, cell2.pos = cell2.pos, cell1.pos

    def merge_cells(self, src, dest):
        dest.value *= 2
        src.value = None
        self.__empty_num += 1
        self.__max_value = max(self.__max_value, dest.value)
        self.game.score += dest.value

    def push_right(self, cell):
        res = False
        right = cell.onright()
        while right and right.is_empty():
            self.swap_cells(cell, right)
            right = cell.onright()
            res = True
        if right and (cell.value == right.value):
            self.merge_cells(cell, right)
            res = True
        return res

    def move_right(self):
        res = False
        for j in reversed(range(self.size - 1)):
            for i in range(self.size):
                cell = self.grid[i][j]
                if cell.is_empty():
                    continue
                res = self.push_right(cell) or res
        self.game.moves += 1
        return res

    def push_left(self, cell):
        res = False
        left = cell.onleft()
        while left and left.is_empty():
            self.swap_cells(cell, left)
            left = cell.onleft()
            res = True
        if left and (cell.value == left.value):
            self.merge_cells(cell, left)
            res = True
        return res

    def move_left(self):
        res = False
        for j in range(1, self.size):
            for i in range(self.size):
                cell = self.grid[i][j]
                if cell.is_empty():
                    continue
                res = self.push_left(cell) or res
        self.game.moves += 1
        return res

    def push_up(self, cell):
        res = False
        above = cell.above()
        while above and above.is_empty():
            self.swap_cells(cell, above)
            above = cell.above()
            res = True
        if above and (cell.value == above.value):
            self.merge_cells(cell, above)
            res = True
        return res

    def move_up(self):
        res = False
        for i in range(1, self.size):
            for j in range(self.size):
                cell = self.grid[i][j]
                if cell.is_empty():
                    continue
                res = self.push_up(cell) or res
        self.game.moves += 1
        return res

    def push_down(self, cell):
        res = False
        below = cell.below()
        while below and below.is_empty():
            self.swap_cells(cell, below)
            below = cell.below()
            res = True
        if below and (cell.value == below.value):
            self.merge_cells(cell, below)
            res = True
        return res

    def move_down(self):
        res = False
        for i in reversed(range(self.size - 1)):
            for j in range(self.size):
                cell = self.grid[i][j]
                if cell.is_empty():
                    continue
                res = self.push_down(cell) or res
        self.game.moves += 1
        return res

    def draw(self):
        for cell in self.cells():
            cell.draw()

    def draw_words(self, words):
        height = {k: len(v) for k, v in words.items()}
        width = {k: max([len(row) for row in v])
                 for k, v in words.items()}
        total_height = sum(height.values()) + len(height) - 1
        total_width = max(width.values())
        total_begin_x = (self.size * self.cell_ncols - total_width) // 2
        total_begin_y = (self.size * self.cell_nlines - total_height) // 2

        lines = []
        for word in words.values():
            for line in word:
                prefix, postfix = '', ''
                diff = total_width - len(line)
                prefix = ' ' * (diff - diff // 2)
                postfix = ' ' * (diff // 2)
                lines.append(prefix + line + postfix)
            lines.append(' ' * total_width)
        del lines[len(lines) - 1]

        for i in range(len(lines)):
            self.window.addstr(
                        total_begin_y + i, total_begin_x, lines[i],
                        curses.color_pair(
                            config.color_pairs['words'] | curses.A_BOLD
                        )
            )

    def is_movable(self):
        if self.empty_num > 0:
            return True
        for cell in self.cells():
            right, below = cell.onright(), cell.below()
            if right and (right.is_empty() or cell.value == right.value):
                return True
            if below and (below.is_empty() or cell.value == below.value):
                return True
        return False

    def is_thrhold_reached(self):
        return self.max_value >= self.thrhold


if __name__ == '__main__':
    game = Game()
    game.init_graphics()
    game.create_new()
    game.play_game()
    game.deinit_graphics()
