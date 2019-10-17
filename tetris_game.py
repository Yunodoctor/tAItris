# ===============================================================================================#
# Name        : Tetris.py                                                                       #
# Description : Python version of the tetris game                                               #
# Author      : Nguyen Vu Tuong Lam                                                             #
# Date        : 08.11.2017                                                                      #
# --------------------------------------------------------------------------------------------- #
# Updated     : 10.10.2019                                                                      #
# By          : Ronja Faltin                                                                    #
# ===============================================================================================#


from random import randrange as rand

import pygame
import sys
import numpy as np

# The configuration
cell_size = 30
cell_size_inner = 30
cols = 10
rows = 22
max_fps = 60
font_size = 16
pygame.init()
pygame.mixer.init()

colors = [
    (0, 0, 0),
    (237, 80, 104),  # Pink
    (255, 176, 0),  # Orange
    (31, 163, 158),  # Bluegreen
    (35, 51, 135),  # Blue
    (250, 128, 114),  # Salmon
    (230, 220, 210),  # Cream white
    (255, 119, 0),  # Yellow
    (20, 20, 20)  # Helper color for background grid
]

# Define the shapes of the single parts
tetris_shapes = [
    [[1, 1, 1],
     [0, 1, 0]],

    [[0, 2, 2],
     [2, 2, 0]],

    [[3, 3, 0],
     [0, 3, 3]],

    [[4, 0, 0],
     [4, 4, 4]],

    [[0, 0, 5],
     [5, 5, 5]],

    [[6, 6, 6, 6]],

    [[7, 7],
     [7, 7]]
]


# ================================================================================================#
#                                       Function Definitions                                     #
# ================================================================================================#

def rotate_clockwise(shape):
    return [[shape[y][x]
             for y in range(len(shape))]
            for x in range(len(shape[0]) - 1, -1, -1)]


def check_collision(board, shape, offset):
    off_x, off_y = offset
    # Add score if a block is seated
    for cy, row in enumerate(shape):
        for cx, cell in enumerate(row):
            try:
                if cell and board[cy + off_y][cx + off_x]:
                    return True
            except IndexError:
                return True
    return False


def remove_row(board, row):
    del board[row]
    return [[0 for i in range(cols)]] + board


def join_matrixes(mat1, mat2, mat2_off):
    off_x, off_y = mat2_off
    for cy, row in enumerate(mat2):
        for cx, val in enumerate(row):
            mat1[cy + off_y - 1][cx + off_x] += val
    return mat1


def create_board():
    board = [[0 for x in range(cols)]
             for y in range(rows)]
    board += [[1 for x in range(cols)]]
    return board


# ================================================================================================#
#                                       Main Game Part                                           #
# ================================================================================================#

class TetrisApp(object):
    def __init__(self):
        pygame.init()
        pygame.key.set_repeat()  # Delay in milliseconds (250, 25) -> No delay needed?
        self.width = cell_size * (cols + 6)
        self.height = cell_size * rows
        self.r_lim = cell_size * cols

        # Make the grid in the background, 8 and 3 is the color
        self.b_ground_grid = [[8 if x % 2 == y % 2 else 0 for x in range(cols)] for y in range(rows)]

        #  Change the font in the game
        self.default_font = pygame.font.Font(
            pygame.font.get_default_font(), font_size)

        self.screen = pygame.display.set_mode((self.width, self.height))
        # We do not need mouse movement events, so we block them.
        pygame.event.set_blocked(pygame.MOUSEMOTION)

        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.init_game()

        self.actions = {
            0: lambda: self.move(-1),  # Left
            1: lambda: self.move(+1),  # Right
            2: self.rotate_stone,  # Rotate
            3: self.instant_drop  # Instant drop
        }

    def new_stone(self):
        self.stone = self.next_stone[:]
        self.next_stone = tetris_shapes[rand(len(tetris_shapes))]
        self.stone_x = int(cols / 2 - len(self.stone[0]) / 2)
        self.stone_y = 0

        if check_collision(self.board,
                           self.stone,
                           (self.stone_x, self.stone_y)):
            self.gameover = True
            self.reward = -2  # -> Score for game over :)

    def init_game(self):
        self.board = create_board()
        self.new_stone()
        self.level = 1
        self.score = 0
        self.reward = 0
        self.lines = 0
        self.action_reward = 0

        # Init variables for the function bumpiness
        self.total_bumpiness = 0
        self.prev_col = float('NaN')  # Not to start outside of board
        self.col = 0
        self.bump_counter = 0

        # Init variables in for number_of_holes function
        """self.total_holes = 0
        self.prev_cell = float('NaN')  # Not to start outside of board
        self.holes_counter = 0"""

    def display_msg(self, msg, top_left):
        x, y = top_left
        for line in msg.splitlines():
            self.screen.blit(
                self.default_font.render(line, False, (255, 255, 255), (0, 0, 0)), (x, y))
            y += 30

    def center_msg(self, msg):
        for i, line in enumerate(msg.splitlines()):
            msg_image = self.default_font.render(line, False,
                                                 (0, 0, 255), (0, 0, 0))
            msg_im_center_x, msg_im_center_y = msg_image.get_size()
            msg_im_center_x //= 2
            msg_im_center_y //= 2

            self.screen.blit(msg_image, (
                self.width // 2 - msg_im_center_x,
                self.height // 2 - msg_im_center_y + i * 22))

    def draw_matrix(self, matrix, offset):
        off_x, off_y = offset
        for y, row in enumerate(matrix):

            for x, val in enumerate(row):

                if val:
                    pygame.draw.rect(self.screen, colors[val],
                                     pygame.Rect((off_x + x) * cell_size, (off_y + y) * cell_size, cell_size_inner,
                                                 cell_size_inner), 0)
                    pygame.draw.rect(self.screen, colors[val],
                                     pygame.Rect((off_x + x) * cell_size, (off_y + y) * cell_size, cell_size,
                                                 cell_size), 2)

    def add_cl_lines(self, n):
        self.lines += n
        self.score += n*10

    def move(self, delta_x):
        if not self.gameover:
            new_x = self.stone_x + delta_x
            if new_x < 0:
                new_x = 0
            if new_x > cols - len(self.stone[0]):
                new_x = cols - len(self.stone[0])
            if not check_collision(self.board,
                                   self.stone,
                                   (new_x, self.stone_y)):
                self.stone_x = new_x
        else:
            self.reward = -2  # -> Score for game over :)

    def get_state(self):
        return self.stone_x, self.stone_y

    def quit(self):
        self.center_msg("Exiting...")
        pygame.display.update()
        sys.exit()

    def drop(self):
        if not self.gameover:
            self.stone_y += 1
            if check_collision(self.board,
                               self.stone,
                               (self.stone_x, self.stone_y)):
                self.board = join_matrixes(
                    self.board,
                    self.stone,
                    (self.stone_x, self.stone_y))
                self.new_stone()
                # self.reward += 1  # Reward when a brick is seated
                self.bumpiness()  # Calculate bumpiness when a stone is seated
                # self.number_of_holes()  # Calculate number of holes when a stone is seated
                cleared_rows = 0
                while True:
                    for i, row in enumerate(self.board[:-1]):
                        if 0 not in row:
                            self.board = remove_row(self.board, i)
                            cleared_rows += 1
                            break
                    else:
                        break
                self.add_cl_lines(cleared_rows)
                return True
        else:
            self.reward = -2  # -> Score for game over :)
        return False

    def instant_drop(self):
        self.score += 1
        if not self.gameover:
            while not self.drop():
                pass

    def rotate_stone(self):
        if not self.gameover:
            new_stone = rotate_clockwise(self.stone)
            if not check_collision(self.board,
                                   new_stone,
                                   (self.stone_x, self.stone_y)):
                self.stone = new_stone
        else:
            self.reward = -2  # -> Score for game over :)

    # Calculate the bumpiness in the board
    def bumpiness(self):
        self.total_bumpiness = 0
        for c in zip(*self.board):

            for val in c:
                if val == 0:
                    self.bump_counter += 1
                else:
                    break
            self.col = abs(self.bump_counter - rows)
            if not np.isnan(self.prev_col):
                self.total_bumpiness = self.total_bumpiness + abs(self.prev_col - self.col)

            self.prev_col = self.col
            self.col = 0
            self.bump_counter = 0

        return self.total_bumpiness

    """def number_of_holes(self):
        self.total_holes = 0

        for col in zip(*self.board):
            for val in col:

                if val == 0 and not np.isnan(self.prev_cell) and not self.prev_cell != 0:
                    self.holes_counter += 1
                    print(self.holes_counter)

            self.prev_cell = val
            print("Next column!")

        self.total_holes = self.holes_counter
        print("Number of holes: ", self.total_holes)
        return self.total_holes"""



    def start_game(self, terminated):
        # print(terminated)
        self.gameover = terminated

        if not self.gameover:
            self.init_game()

    def get_reward(self):
        action_reward = self.reward + self.score - 0.2*self.total_bumpiness
        return action_reward

    def reset_reward(self):
        self.reward = 0

    def get_terminated(self):
        return self.gameover

    def play(self, action):
        self.action_from_agent = action
        for x in self.actions:
            if x == self.action_from_agent:
                self.actions[self.action_from_agent]()

        self.render_game()
        self.drop()
        return self.get_state(), self.get_reward(), self.get_terminated(), self.total_bumpiness

    def render_game(self):  # Skicka in x och rotation?
        dont_burn_my_cpu = pygame.time.Clock()

        # Fills the screen background with black (RGB)
        self.screen.fill((0, 0, 0))

        pygame.draw.line(self.screen,
                         (255, 255, 255),
                         (self.r_lim + 1, 0),
                         (self.r_lim + 1, self.height - 1))
        self.display_msg("Next:", (
            self.r_lim + cell_size,
            2))
        self.display_msg("Score: %d\nLevel: %d\nLines: %d\nAction reward: %d\nAction: %d\nBumpiness: %d" % (self.score, self.level, self.lines, self.get_reward(), self.action_from_agent, self.total_bumpiness),
                         (self.r_lim + cell_size, cell_size * 5))

        self.draw_matrix(self.b_ground_grid, (0, 0))
        self.draw_matrix(self.board, (0, 0))
        self.draw_matrix(self.stone,
                         (self.stone_x, self.stone_y))
        self.draw_matrix(self.next_stone,
                         (cols + 1, 2))

        pygame.display.update()

        dont_burn_my_cpu.tick(max_fps)
