from abc import ABC, abstractmethod
import random
from PIL import Image, ImageDraw, ImageFont
import math
import collections.abc

def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el

def listifyArray(array):
    return list(flatten(array));


class EvalGame:

    def __init__(self,gameClass,**kwargs):
        self.gameClass = gameClass;
        self.initInputs = kwargs;

    def start(self,runnerConfig):
        return self.gameClass(runnerConfig,self.initInputs);

class RunGame(ABC):
    def __init__(self,runnerConfig,kwargs):
        self.steps = 0;
        self.runConfig = runnerConfig;

    def getData(self):
        mappedData = self.getMappedData();
        returnData = self.runConfig.returnData;
        result = [];
        for datum in returnData:
            if (isinstance(datum,str)):
                result.append(mappedData.get(datum));
            elif (datum.data_type == 'array'):
                result += listifyArray(mappedData.get(datum.name));
        return result;

    
        

    def getFitnessScore(self):
        return self.runConfig.fitnessFromGameData(self.getMappedData());

    def getMappedData(self):
        mappedData = self.getOutputData();
        mappedData['steps'] = self.steps;
        return mappedData;

    @abstractmethod
    def getOutputData(self):
        #return dict of all data available from game, sans 'steps'
        pass;

    @abstractmethod
    def processInput(self, inputs):
        pass;

    @abstractmethod
    def renderInput(self,inputs):
        pass;

    def close(self):
        #does nothing unless game needs it to
        return;

    def isRunning(self):
        return self.runConfig.gameStillRunning(self.getMappedData());

    

class HoldRightGame(RunGame):
    def __init__(self,runnerConfig,kwargs):
        super().__init__(runnerConfig);
        self.coeff = runnerConfig.rightCoeff;
        self.position = 0.0;

    def processInput(self,inputs):
        self.steps += 1;
        self.position += inputs[0] * self.coeff;

    def renderInput(self,inputs):
        self.processInput(inputs);
        fitness = self.runConfig.fitnessFromGameData(self.getMappedData());
        baseImage = self.getFieldWithAvatar(self.position,(Image.open('images\\mario_avatar.png') if self.steps%2==0 else Image.open('images\\mario_avatar_2.png')),self.runConfig.animation_pixel_per_unit,self.runConfig.animation_unit_per_sign);
        draw = ImageDraw.Draw(baseImage);
        font = ImageFont.truetype('arial.ttf',22);
        draw.text((5,5),'fitness: {0}'.format(fitness),fill=(0,255,0))
        return baseImage;
        
    def getOutputData(self):
        return {"position":self.position};

    def getSignImage(self,text,color=(0,0,0)):
        text = str(text);
        font = ImageFont.truetype('arial.ttf',22);
        signBase = Image.open('images\\sign.jpg');
        signSpace = (58,28);
        yPosition = 3;
        if (len(text)>6 or font.getsize(text)[1]>signSpace[1]):
            font = ImageFont.truetype('arial.ttf',10);
            yPosition = 5;
        width = font.getsize(text)[0];
        xPosition = int((signSpace[0] - width)/2)+1;
        signDrawer = ImageDraw.Draw(signBase);
        signDrawer.text((xPosition,yPosition),text,font=font,fill=color);
        return signBase;
            

    def getSignedField(self,position,pixels_per_unit,units_per_sign):
        background = Image.open('images\\background.jpg');
        decimal_end = '.' in str(units_per_sign);
        field_unit_width = background.width / pixels_per_unit;
        left_unit = position - field_unit_width/2;
        sign_units = [(i+math.ceil(left_unit/units_per_sign))*units_per_sign for i in range(math.ceil(field_unit_width/units_per_sign))];
        sign_positions = [int((unit-left_unit)*pixels_per_unit-30) for unit in sign_units];
        sign_unit_strings = [str(unit) + ('.0' if decimal_end and not '.' in str(unit) else '') for unit in sign_units];
        [background.paste(self.getSignImage(sign_unit_strings[i]),(sign_positions[i],145)) for i in range(len(sign_units))];
        return background;

    def getFieldWithAvatar(self,position, avatar_image, pixels_per_unit, units_per_sign):
        signed_field = self.getSignedField(position,pixels_per_unit,units_per_sign);
        signed_field.paste(avatar_image,(int(signed_field.width/2-avatar_image.width/2),165),avatar_image if (avatar_image.mode == 'RGBA') else None);
        return signed_field;

class StarSmash(RunGame):
    def __init__(self,runnerConfig,kwargs):
        super().__init__(runnerConfig);
        self.height = 1; #0-7 height
        self.score = 0;
        self.level = 0;
        self.asteroids=[[random.randint(1,6),15]];
        self.cooldown = 0;
        self.alive = True;
        self.firing = False;

    def renderInput(self,inputs):
        self.firing = False;
        self.processInput(inputs);
        if (not self.runConfig.gameStillRunning(self.getMappedData())):
            return Image.open('images\\epic_fail.png');
        fitness = self.runConfig.fitnessFromGameData(self.getMappedData());
        baseImage = self.get_screen(self.height,self.firing,self.asteroids,inputs);
        draw = ImageDraw.Draw(baseImage);
        font = ImageFont.truetype('arial.ttf',50);
        draw.text((5,5),'Fitness: ' + str(fitness),fill=(200,25,25));
        
        
        return baseImage;
        
        
    def processInput(self,inputs):
        self.steps += 1;
        if (inputs[2] > 0 and self.cooldown == 0):
            self.cooldown = 2;
            self.firing = True;
            self.fire();
        else:
            heightInc = -1 if inputs[0] > 0.1 else 0;
            heightInc += 1 if inputs[1] > 0.1 else 0;
            self.height += heightInc;
            self.height = 1 if self.height < 1 else (6 if self.height > 6 else self.height);
            self.cooldown = self.cooldown - 1 if self.cooldown > 0 else 0;
        self.advanceAsteroids();
        self.checkForCollisions();

    def getFirstAsteroid(self):
        firstAsteroidNum = 0;
        closestAsteroid = 15;
        for i in range(len(self.asteroids)):
            asteroid = self.asteroids[i];
            if (asteroid[1] < closestAsteroid):
                closestAsteroid = asteroid[1];
                firstAsteroidNum = i;
        resultroid = self.asteroids[firstAsteroidNum];
        return {"height":resultroid[0],"distance":resultroid[1]};

    def getSecondAsteroid(self):
        firstAsteroidNum = 0;
        closestAsteroid = 15;
        secondAsteroidNum = 0;
        secondClosestAsteroid = 15;
        for i in range(len(self.asteroids)):
            asteroid = self.asteroids[i];
            if (asteroid[1] < closestAsteroid):
                secondAsteroidNum = firstAsteroidNum;
                secondClosestAsteroid = closestAsteroid;
                closestAsteroid = asteroid[1];
                firstAsteroidNum = i;
            elif (asteroid[1] < secondClosestAsteroid):
                 secondAsteroidNum = i;
                 secondClosestAsteroid = asteroid[1];
        resultroid = self.asteroids[secondAsteroidNum];
        return {"height":resultroid[0],"distance":resultroid[1]};

    def checkForCollisions(self):
        for asteroid in self.asteroids:
            if (asteroid[1] == 0):
                if (asteroid[0] < self.height+2 and asteroid[0] > self.height-2):
                    self.alive = False;
                else:
                    asteroid[0] = random.randint(1,6);
                    asteroid[1] = 15;

    def advanceAsteroids(self):
        for asteroid in self.asteroids:
            asteroid[1] -= 1;

    def fire(self):
        for asteroid in self.asteroids:
            if (asteroid[0] == self.height):
                asteroid[0] = random.randint(1,6);
                asteroid[1] = 15;
                self.score += 1;
        if (self.score > (self.level+1)*5):
            self.level += 1;
            self.asteroids.append([random.randint(1,6),15]); 
    
    def getOutputData(self):
        return {"height":self.height,
		"score":self.score,
		"level":self.level,
		"first_asteroid_height":self.getFirstAsteroid().get("height"),
		"first_asteroid_distance":self.getFirstAsteroid().get("distance"),
		"second_asteroid_height":self.getSecondAsteroid().get("height"),
		"second_asteroid_distance":self.getSecondAsteroid().get("distance"),
		"alive":self.alive};

    

    def get_screen(self,ship_height,is_firing,asteroids,inputs):
        bg = Image.open('images\\calc_bg.png');
        self.paste_ship(bg,ship_height);
        if (is_firing):
            self.paste_beam(bg, ship_height);
        [self.paste_asteroid(bg,asteroid[1],asteroid[0]) for asteroid in asteroids];
        up = Image.open('images\\up_norm.png') if (inputs[0] <= 0) else Image.open('images\\up_press.png');
        down = Image.open('images\\down_norm.png') if (inputs[1] <= 0) else Image.open('images\\down_press.png');
        beamin = Image.open('images\\beam_norm.png') if (not(self.firing)) else Image.open('images\\beam_press.png');
    
        bg.paste(up,(855,15),up);
        bg.paste(down,(855,55),down);
        bg.paste(beamin,(900,35),beamin);
        draw = ImageDraw.Draw(bg);
        draw.text((900,15),str(inputs[2]),fill=(255 if inputs[2]>0 else 0,0,0));
        draw.text((830,30),str(inputs[0]),fill=(255 if inputs[0]>0.1 else 0,0,0));
        draw.text((830,70),str(inputs[1]),fill=(255 if inputs[1]>0.1 else 0,0,0));

        #print('inputs: {0}, {1}, {2}'.format(str(inputs[0]),str(inputs[1]),str(inputs[2])));
        
        return bg;

    def paste_asteroid(self,bg,x,y):
        asteroid_pic = Image.open('images\\asteroid.png');
        self.add_char_to_calc_grid(x,y,asteroid_pic,bg);

    def paste_beam(self,bg,height,left=2):
        beam = Image.open('images\\beam.png');
        self.add_char_to_calc_grid(left,height,beam,bg);

    def paste_ship(self,bg,height):
        self.add_char_to_calc_grid(0,height-1,Image.open('images\\ship_filled.png'),bg);

    def add_char_to_calc_grid(self,x,y,char,bg):
        bg.paste(char,(x*60,y*80),char);
