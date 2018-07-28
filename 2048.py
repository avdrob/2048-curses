#!/usr/bin/python3

import curses
import random
# import sys

import config


# TODO: Implement help box
class HelpBox:
    pass


# TODO: Wrap the whole thing into Game class
class Game:
    def __init__(self, size=4, mode=config.Mode.Large):
        self.__size = size
        self.__mode = mode

    @property
    def size(self):
        return self.__size

    @property
    def mode(self):
        return self.__mode

    @property
    def map(self):
        return self.__map

    def init_graphics(self):
        curses.initscr()            # window object representing screen
        curses.noecho()             # turn off automatic echoing of keys
        curses.cbreak()             # cbreak mode: react to keys instantly
        curses.curs_set(False)

        # Initialize colors
        curses.start_color()
        for value, pairnum in config.color_pairs.items():
            curses.init_pair(pairnum, *config.colors[value])

    def create_new(self):
        self.__map = Map(self.size, self.mode)
        self.map.draw()

    def play_game(self):
        self.map.gen_cell()
        self.map.draw()

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
            elif key == ord('q'):
                break
            else:
                continue

            if not layout_changed:
                continue

            self.map.gen_cell()
            self.map.draw()

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
        return len(config.numbers_ascii[self.value])

    def text_width(self):
        return max([len(row) for row in config.numbers_ascii[self.value]])

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
                    config.numbers_ascii[self.value][i],
                    curses.color_pair(config.color_pairs[self.value] |
                                      curses.A_BOLD)
            )

    # Due to historical reasons we cannot just write to the last window
    # in curses.  So instead we use this workaround with insch() on each
    # cell's last line
    def draw(self):
        for i in range(self.map.cell_nlines - 1):
            self.map.window.addstr(
                    self.pos.line * self.map.cell_nlines + i,
                    self.pos.col * self.map.cell_ncols,
                    ' ' * self.map.cell_ncols,
                    curses.color_pair(config.color_pairs[self.value])
            )
        self.map.window.addstr(
                (self.pos.line + 1) * self.map.cell_nlines - 1,
                self.pos.col * self.map.cell_ncols,
                ' ' * (self.map.cell_ncols - 1),
                curses.color_pair(config.color_pairs[self.value])
        )
        self.map.window.insch(
                (self.pos.line + 1) * self.map.cell_nlines - 1,
                (self.pos.col + 1) * self.map.cell_ncols - 2,
                ' ', curses.color_pair(config.color_pairs[self.value])
        )

        if not self.is_empty():
            self.draw_text()


class Map:
    '''
    Contains grid of cells
    '''
    def __init__(self,  size, mode):
        self.__size = size
        self.__mode = mode
        # TODO: harcoded values
        self.__cell_nlines = 9
        self.__cell_ncols = 21

        self.__window = curses.newwin(
                            self.__cell_nlines * size,
                            self.__cell_ncols * size,
                            0, 0
                            # (curses.LINES - self.__cell_nlines * size) // 2,
                            # (curses.COLS - self.__cell_ncols * size) // 2
                        )
        # keypad mode: return special values for keys
        self.__window.keypad(True)

        self.__empty_num = size * size
        self.gen_grid()

        # Prepate for cells generation
        random.seed()
        self.lin_pos_prev = 0

    @property
    def size(self):
        return self.__size

    @property
    def cell_nlines(self):
        return self.__cell_nlines

    @property
    def cell_ncols(self):
        return self.__cell_ncols

    @property
    def window(self):
        return self.__window

    @property
    def grid(self):
        return self.__grid

    @property
    def empty_num(self):
        return self.__empty_num

    @empty_num.setter
    def empty_num(self, val):
        self.__empty_num = min(max(val, 0), self.size ** 2)

    def cells(self):
        '''
        A handy generator saving us from iteration over nested list
        '''
        for i in range(self.size):
            for j in range(self.size):
                yield self.grid[i][j]

    def gen_cell(self):
        # TODO: fix this
        assert(self.empty_num > 0)

        # Generate position different from the previous one
        while True:
            lin_pos = random.randint(1, self.empty_num)
            if lin_pos != self.lin_pos_prev:
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
        self.empty_num -= 1

    def gen_grid(self):
        self.__grid = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                row.append(Cell(self, MapPos(i, j), None))
            self.grid.append(row)

    def swap_cells(self, cell1, cell2):
        self.grid[cell1.pos.line][cell1.pos.col] = cell2
        self.grid[cell2.pos.line][cell2.pos.col] = cell1
        cell1.pos, cell2.pos = cell2.pos, cell1.pos

    def merge_cells(self, src, dest):
        # TODO: get rid of this
        assert(src.value == dest.value)
        prev1, prev2 = src.value, dest.value

        dest.value *= 2
        src.value = None
        self.empty_num += 1
        assert(dest.value == prev1 + prev2)

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
        return res

    def draw(self):
        for cell in self.cells():
            cell.draw()

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


if __name__ == '__main__':
    game = Game(4)
    game.init_graphics()
    game.create_new()
    game.play_game()
    game.deinit_graphics()
