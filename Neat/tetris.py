#!/usr/bin/env python
#-*- coding: utf-8 -*-

# Very simple tetris implementation
# 
# Control keys:
# Down - Drop stone faster
# Left/Right - Move stone
# Up - Rotate Stone clockwise
# Escape - Quit game
# P - Pause game
#
# Have fun!

# Copyright (c) 2010 "Kevin Chabowski"<kevin@kch42.de>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# Tetris game software copy-pasted and hackjobbed by "Harrison Truscott" for use as a game
# with which to train a NEAT evolutionary machine learning algorithm. The core functionality is
# the same as Kevin's, but the display and I/O bits were hijacked to interface with the rest
# of the neat program.

##Lose all hope, ye who enter here

from random import randrange as rand
import sys#pygame, sys
from runnerConfiguration import RunnerConfig
from PIL import Image, ImageDraw
import baseGame




# The configuration
config = {
        'cell_size':	20,
        'cols':		10,
        'rows':		20,
        'delay':	750,
        'maxfps':	30
}

colors = [
(0,   0,   0  ),
(255, 0,   0  ),
(0,   150, 0  ),
(0,   0,   255),
(255, 120, 0  ),
(255, 255, 0  ),
(180, 0,   255),
(0,   220, 220)
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

def rotate_clockwise(shape):
        return [ [ shape[y][x]
                        for y in range(len(shape)) ]
                for x in range(len(shape[0]) - 1, -1, -1) ]

def check_collision(board, shape, offset):
        off_x, off_y = offset
        for cy, row in enumerate(shape):
                for cx, cell in enumerate(row):
                        try:
                                if cell and board[ cy + off_y ][ cx + off_x ]:
                                        return True
                        except IndexError:
                                return True
        return False


        
def join_matrixes(mat1, mat2, mat2_off):
        off_x, off_y = mat2_off
        for cy, row in enumerate(mat2):
                for cx, val in enumerate(row):
                        mat1[cy+off_y-1	][cx+off_x] += val
        return mat1

def new_board(rows,cols):
        board = [ [ 0 for x in range(cols) ]
                        for y in range(rows) ]
        board += [[ 1 for x in range(cols)]]
        return board


class TetrisRunnerConfig(RunnerConfig):
    def __init__(self,gameFitnessFunction,gameRunningFunction,recurrent=False,trial_fitness_aggregation='average',custom_fitness_aggregation=None,time_step=0.05,num_trials=10,parallel=False,returnData=[],
                 num_generations=300,cols=10,rows=20,gameName='Tetris'):
        super().__init__(gameFitnessFunction,gameRunningFunction,recurrent=recurrent,trial_fitness_aggregation=trial_fitness_aggregation,custom_fitness_aggregation=custom_fitness_aggregation,time_step=time_step,num_trials=num_trials,parallel=parallel,returnData=returnData,
                 num_generations=num_generations,gameName=gameName);
        self.cols = cols;
        self.rows = rows;
        self.cell_size = 20;
        self.frames_per_drop = 8;

class Tetris(baseGame.RunGame):
        def __init__(self,runnerConfig,kwargs):
                super().__init__(runnerConfig,kwargs);
                self.width = self.runConfig.cell_size*self.runConfig.cols
                self.height = self.runConfig.cell_size*self.runConfig.rows
                self.side_panel_width = 300;
                self.init_game()


        def remove_row(self, board, row):
                del board[row]
                return [[0 for i in range(self.runConfig.cols)]] + board

        
        def init_game(self):
                self.board = new_board(self.runConfig.rows,self.runConfig.cols);
                self.new_stone()
                self.gameover = False;
                self.cleared_lines = 0;

        def new_stone(self):
                self.stone_rotation = 0;
                self.stone_id = rand(len(tetris_shapes))
                self.stone = tetris_shapes[self.stone_id];
                self.stone_x = int(self.runConfig.cols / 2 - len(self.stone[0])/2)
                self.stone_y = 0
                
                if check_collision(self.board,
                                   self.stone,
                                   (self.stone_x, self.stone_y)):
                        self.gameover = True
        
               
        def center_msg(self, msg):
            ##TODO: do
            return;
      
        def draw_matrix(self, matrix, offset):
                off_x, off_y  = offset
                for y, row in enumerate(matrix):
                        for x, val in enumerate(row):
                                if val:
                                        draw = ImageDraw.Draw(self.screen);
                                        draw.rectangle([((off_x+x)*self.runConfig.cell_size,
                                                              (off_y+y)*self.runConfig.cell_size),
                                                             ((off_x+x+1)*self.runConfig.cell_size,
                                                              (off_y+y+1)*self.runConfig.cell_size)],colors[val]);
        
        def move(self, delta_x):
                if not self.gameover:
                        new_x = self.stone_x + delta_x
                        if new_x < 0:
                                new_x = 0
                        if new_x > self.runConfig.cols - len(self.stone[0]):
                                new_x = self.runConfig.cols - len(self.stone[0])
                        if not check_collision(self.board,
                                               self.stone,
                                               (new_x, self.stone_y)):
                                self.stone_x = new_x

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
                                while True:
                                        for i, row in enumerate(self.board[:-1]):
                                                if 0 not in row:
                                                        self.board = self.remove_row(
                                                          self.board, i)
                                                        #print('row cleared: {0}, lines cleared: {1}'.format(i,self.cleared_lines + 1));
                                                        self.cleared_lines += 1;
                                                        break
                                        else:
                                                break
        
        def rotate_stone(self):
                if not self.gameover:
                        new_stone = rotate_clockwise(self.stone)
                        if not check_collision(self.board,
                                               new_stone,
                                               (self.stone_x, self.stone_y)):
                                self.stone = new_stone
                                self.stone_rotation += 1;
                                max_rotation = 4;
                                if (self.stone_id == 1 or self.stone_id == 2 or self.stone_id == 5):
                                    max_rotation = 2;
                                if (self.stone_id == 6):
                                    max_rotation = 1;
                                self.stone_rotation %= max_rotation;
        
        
        def processInput(self,inputs):
            self.steps += 1;

            if (inputs[0]>0.01):
                self.move(-1);

            if (inputs[1]>0.01):
                self.move(1);

            if (inputs[2]>0):
                self.drop();

            if (inputs[3]>0):
                self.rotate_stone();

            if (self.steps % 8 == 0):
                self.drop();

            

        def renderInput(self,inputs):
            self.screen = Image.new('RGBA',(self.width+self.side_panel_width,self.height),color=(0,0,0));
            self.processInput(inputs);
            self.draw_matrix(self.board, (0,0));
            self.draw_matrix(self.stone, (self.stone_x, self.stone_y));
            draw = ImageDraw.Draw(self.screen);
            draw.text((1,1),'Fitness: {0}'.format(self.getFitnessScore()),fill=(255,0,0));
            draw.rectangle(((self.width,1),(self.width+self.side_panel_width,self.height)),fill=(0,0,255));
            draw.text((self.width + 20, 1),'Contours: \n{0}'.format(self.getBoardContours()));
            draw.text((self.width + 20, 40),'Inputs:');
            draw.text((self.width + 20, 50),'Left: ' + str(inputs[0]));
            draw.text((self.width + 20, 60),'Right: ' + str(inputs[1]));
            draw.text((self.width + 20, 70),'Down: ' + str(inputs[2]));
            draw.text((self.width + 20, 80),'Rotate: ' + str(inputs[3]));
            return self.screen;

        def getBoardContours(self):
            
            result = [0 for i in range(self.runConfig.cols)];
            for i in range(self.runConfig.rows):
                for j in range(self.runConfig.cols):
                    if (self.board[i][j] > 0 and result[j] == 0):
                        result[j]= self.runConfig.rows-i;
                        
                        
            return result;

        def getPieceDensity(self):
            boardSize = (self.runConfig.rows-1)*self.runConfig.cols;
            pieceArea = 0;
            for row in self.board:
                pieceArea += sum([(1 if j > 0 else 0) for j in row]);
            return pieceArea/boardSize;

        def getLineDensity(self):
            activeLines = 0;

            #get highest line with items in it, have to invert i because board is top-down
            for i in range(20):
                    if sum(self.board[i]) > 0:
                            activeLines = 20-i;
            if activeLines == 0:
                    return 0;

            pieceArea = 0;
            for row in self.board:
                pieceArea += sum([(1 if j > 0 else 0) for j in row]);

            return pieceArea/(activeLines*self.runConfig.cols);
            
        
        def getOutputData(self):
            return {'is_alive':not(self.gameover),'cleared_lines':self.cleared_lines,'piece_id':self.stone_id,'piece_x':self.stone_x,'piece_y':self.stone_y,'piece_rotation':self.stone_rotation,'line_density':self.getLineDensity(),'density':self.getPieceDensity(),'contours':self.getBoardContours(),'board':[[int(bool(x)) for x in self.board[y]] for y in range(len(self.board)-1)]}
        
        def run(self):
                key_actions = {
                        'LEFT':		lambda:self.move(-1),
                        'RIGHT':	lambda:self.move(+1),
                        'DOWN':		self.drop,
                        'UP':		self.rotate_stone,
                }
                
                self.gameover = False

                
                #pygame.time.set_timer(pygame.USEREVENT+1, config['delay'])
                #dont_burn_my_cpu = pygame.time.Clock()
                ticks = 0;
                while 1:
                        ticks = ticks + 1 if ticks < 7 else 0;
                        #self.screen.fill((0,0,0))
                        if self.gameover:
                                self.center_msg("""Game Over!
Press space to continue""")
                        else:

                                    self.draw_matrix(self.board, (0,0))
                                    self.draw_matrix(self.stone,
                                                     (self.stone_x,
                                                      self.stone_y))
                        #pygame.display.update()
                        inputs = [];
                        events = inputs;#pygame.event.get();

                        #if ticks == 0:
                        #   self.drop();
                        
                        for event in events:
                            if key_actions[event] != None:
                                key_actions[key]()
                        #dont_burn_my_cpu.tick(config['maxfps'])



