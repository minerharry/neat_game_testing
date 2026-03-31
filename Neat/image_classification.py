from baseGame import RunGame
from PIL import Image, ImageDraw
import numpy as np

class ImageClassification(RunGame):
    def __init__(self,runnerConfig,kwargs):
        super().__init__(runnerConfig,kwargs);
        self.scoring = [];
        self.image_id = -1;
        self.image_set = kwargs['images']
        self.loadedImage = self.load_next_image();
        self.previous_digit = -1;
        self.highest_score = 0;
        



    def load_next_image(self):
        self.image_id +=1;
        if (self.image_id >= len(self.image_set[0])-1):
            self.done = True;
        return (self.image_set[0][self.image_id],self.image_set[1][self.image_id]);
        
    def renderInput(self,inputs):
        pastImage = self.loadedImage;
        self.processInput(inputs);
        return self.image_from_image_data(pastImage[0],pastImage[1],self.highestScore);
        

    def image_from_image_data(self,image,digit,selectedDigit):
        bg_image = Image.new('L',(80,60));
        image = (np.reshape(image,(-1,28)));
        drawn_image = Image.fromarray(np.uint8(image*255),mode='L');
        drawn_image.resize((56,56));
        bg_image.paste(drawn_image,(1,1));
        draw = ImageDraw.Draw(bg_image);
        draw.text((58,2),f"{digit}",fill=(255));
        draw.text((58,20),f"{selectedDigit}",fill=(255));
        return bg_image;
        
        

        
    def processInput(self,inputs):
        self.steps += 1;
        self.scoring = inputs;
        self.highestScore = inputs.index(max(inputs));
        self.previous_digit = self.loadedImage[1];
        self.loadedImage = self.load_next_image();

        
    def getOutputData(self):
        return {"image":self.loadedImage[0],"digit":self.previous_digit,"best_digit":self.highest_score,"digit_scores":self.scoring};

