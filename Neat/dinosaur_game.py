from baseGame import RunGame
from PIL import Image, ImageDraw
import random


class DinosaurGame(RunGame):
    #100% stolen from Code bullet for use as a benchmark for neat stuff; not original in the slightest, only slightly more compact b/c rendering is less important to me


    player_hitbox_size = (100,100)
    player_duck_size = (140,70)
    obstacle_type_info = [(40,80,40),(60,120,60),(120,80,40),(60,50,35),(60,50,100),(60,50,180)]; #list of tuples of (width, height, pos); 0: small cactus, 1: large cactus; 2 many cacti; 3, low bird; 4, med bird; 5, high bird
    gravity = 1.2;
    screen_width = 600;
    screen_height = 400;
    bird_step_threshold = 2000;
    max_obstacles = 4;
    min_obstacle_delay = 120;
    max_obstacle_delay = 200;
    jump_velocity = 16;

    def __init__(self,runnerConfig,kwargs):
        super().__init__(runnerConfig,kwargs);
        self.obstacles = []; #list of lists (length 4): xpos, ypos, width, height; pos is of center of hitbox rectangle
        self.xVel = 1;
        self.yVel = 0;
        self.yPos = 0;
        self.xPos = 100; #so obstacles can despawn at xpos = -obstacle.width/2;
        self.ducking = False;
        self.obstacle_timer = 0;
        self.obstacle_delay = 0;
        self.dead = False;

    def processInput(self,inputs):
        self.steps += 1;
        self.ducking = inputs[1] > 0.5;
        if (self.yPos == 0 and inputs[0] > 0.5):
            self.yVel = self.jump_velocity;
        self.do_movement();
        self.xVel += 0.002;
        self.check_collisions();
        if (len(self.obstacles) < self.max_obstacles):
            self.obstacle_timer += 1;
            if (self.obstacle_timer > self.obstacle_delay):
                self.obstacle_timer = 0;
                self.obstacle_delay = random.randint(self.min_obstacle_delay,self.max_obstacle_delay);
                self.obstacles.append(self.new_obstacle());

        
    def renderInput(self,inputs):
        self.processInput(inputs);
        result = Image.new('rgb',(self.screen_width,self.screen_height),color=(255,255,255));
        draw = ImageDraw.Draw(result);
        outlineColor = (0,0,0);
        hitbox = self.getHitbox();
        draw.rectangle((self.xPos-hitbox[0]/2,self.screen_height-(self.yPos+hitbox[1]),(self.xPos+hitbox[0]/2,self.yPos)),outline=outlineColor);
        
        outlineColor = (255,0,0);
        for obstacle in self.obstacles:
            draw.rectangle(((obstacle[0]-obstacle[2]/2,self.screen_height-(obstacle[1]+obstacle[3]/2)),(obstacle[0]+obstacle[2]/2,self.screen_height-(obstacle[1]-obstacle[3]/2))),outline=outlineColor);
        return result;

    def getHitbox(self):
        return self.player_hitbox_size if (not self.ducking) else self.player_duck_size;

    def check_collisions(self):
        hitbox = self.getHitbox();
        size_inc = (hitbox[0]/2,hitbox[1]/2);
        player_pos = (self.xPos,self.yPos+size_inc[1]);
        for obstacle in self.obstacles:
            obstacle_bounds = [(obstacle[i]-obstacle[2+i],obstacle[i]+obstacle[2+i]) for i in [0,1]] #x bounds, y bounds
            within_bounds = [obstacle_bounds[i][0] < player_pos[i] and player_pos[i] < obstacle_bounds[i][1] for i in [0,1]];
            if (within_bounds[0] and within_bounds[1]):
                self.die();

    def die(self):
        self.dead = True;
        

    def do_movement(self):
        self.yPos += self.yVel;
        if (self.yPos > 0):
            self.yVel -= self.gravity;
        else:
            self.yPos = 0;
            self.yVel = 0;

        for i in range(len(self.obstacles)):
            data = self.obstacles[i];
            data[0] -= self.xVel;
            if (data[0] < -data[2]/2):
                data = [];
        for i in range(self.obstacles.count([])):
            self.obstacles.remove([]);
        
        

    def new_obstacle(self):
        type_offset = 0;
        if (self.steps > 1000 and random.random > 0.15):
            type_offset = 3;
        return self.make_obstacle(random.randint(0,2)+type_offset);   

    def make_obstacle(self,obstacleType):
        type_info = self.obstacle_type_info[obstacleType];
        return [self.screen_width,type_info[2],type_info[0],type_info[1]];
        
    def getOutputData(self):
        return {"dead":self.dead,"speed":self.xVel,"near_obstacles":self.getNearestObstacles()};

    def getNearestObstacles(self):
        self.obstacles.sort(key=lambda data: data[0]);
        return [self.obstacles[i] if i < len(self.obstacles) else [self.screen_width,0,0,0] for i in range(3)];