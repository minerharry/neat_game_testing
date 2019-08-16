from PIL import Image, ImageDraw, ImageFont
import math
from videofig import videofig as vidfig

im = Image.open('testImage.png');

drawn = ImageDraw.Draw(im);
drawn.text((10,10), "Hello World",fill=(0,0,0));

skyColor = (79, 213, 255)
grassColor=(20, 127, 15)

background = Image.open('background.jpg');
#sign = Image.new('RGB',(60,50));
#sign.paste(Image.new('RGB',(58,49),color=(255,255,255)),(1,1));
#sign.paste(Image.new('RGB',(27,21)),(0,29));
#sign.paste(Image.new('RGB',(27,21)),(33,29));
#sign.paste(Image.new('RGB',(26,20),color=skyColor),(0,30));
#sign.paste(Image.new('RGB',(26,20),color=skyColor),(34,30));

#sign.show();

#sign.save('sign.jpg');

signFile = Image.open('sign.jpg');
sign = signFile;

textSign1 = sign.copy();

textSignDrawer = ImageDraw.Draw(textSign1);

def getSignImage(text,color=(0,0,0)):
    text = str(text);
    font = ImageFont.truetype('arial.ttf',16);
    signBase = Image.open('sign.jpg');
    signSpace = (58,28);
    yPosition = 3;
    if (len(text)>6 or font.getsize(text)[1]>signSpace[1]):
        font = ImageFont.truetype('arial.ttf',10);
        yPosition = 5;
    width = font.getsize(text)[0];
    xPosition = int((signSpace[0] - width)/2)+1;
    signDrawer = ImageDraw.Draw(signBase);
    #print('({0},{1})'.format(xPosition,yPosition));
    
    signDrawer.text((xPosition,yPosition),text,font=font,fill=color);
#    signBase.show();
    return signBase;
        

def getSignedField(position,pixels_per_unit,units_per_sign):
    background = Image.open('background.jpg');
    decimal_end = '.' in str(units_per_sign);
    field_unit_width = background.width / pixels_per_unit;
    left_unit = position - field_unit_width/2;
    sign_units = [(i+math.ceil(left_unit/units_per_sign))*units_per_sign for i in range(math.ceil(field_unit_width/units_per_sign))];
    sign_positions = [int((unit-left_unit)*pixels_per_unit-30) for unit in sign_units];
    sign_unit_strings = [str(unit) + ('.0' if decimal_end and not '.' in str(unit) else '') for unit in sign_units];
    [background.paste(getSignImage(sign_unit_strings[i]),(sign_positions[i],145)) for i in range(len(sign_units))];
    return background;

def getFieldWithAvatar(position, avatar_image, pixels_per_unit, units_per_sign):
    signed_field = getSignedField(position,pixels_per_unit,units_per_sign);
    signed_field.paste(avatar_image,(int(signed_field.width/2-avatar_image.width/2),165),avatar_image if (avatar_image.mode == 'RGBA') else None);
    return signed_field;
    
font = ImageFont.truetype('arial.ttf',16);


#fieldWithAvatar = getFieldWithAvatar(0,Image.open('mario_avatar.png'),20,5.0);

#fieldWithAvatar.show();

#getFieldWithAvatar(4.9,Image.open('mario_avatar_2.png'),20,5.0).show();

#textSign1.show();

background.paste(sign,(80,145));

#background.paste(getSignImage('9324587'),(680,145));

#background.show();
avatar1 = Image.open('mario_avatar.png');
avatar2 = Image.open('mario_avatar_2.png');
def getAnimationFrame(f,axes):
    image = getFieldWithAvatar(f*3.4,avatar1 if f%2 == 0 else avatar2,25,5.0);
    if not getAnimationFrame.initialized:
      getAnimationFrame.im = axes.imshow(image, animated=True)
      getAnimationFrame.initialized = True
    else:
      getAnimationFrame.im.set_array(image)
getAnimationFrame.initialized = False;
#vidfig(300,getAnimationFrame,play_fps=30);


calc_bg = (90, 114, 95);

background = Image.open('calc_bg.png');

bg_size = (950,630);
asteroid_pic = Image.open('asteroid.png');
ship_beam = Image.open('ship_beam.png');
ship_eyes = Image.open('ship_eyes.png');
ship_flank = Image.open('ship_flank.png');
ship_tip = Image.open('ship_tip.png');

def add_char_to_calc_grid(x,y,char,bg):
    bg.paste(char,(x*60,y*80),char);

#def paste_ship(bg,height):
 #   add_char_to_calc_grid(0,height-1,ship_flank,bg);
  #  add_char_to_calc_grid(0,height,ship_eyes,bg);
   # add_char_to_calc_grid(1,height,ship_tip,bg);
    #add_char_to_calc_grid(0,height+1,ship_flank,bg);

#paste_ship(background,3);
#background.show();

#ship_blank = Image.new('RGBA',(120,240),color=(0,0,0,0));
#ship_blank.save('ship_blank_bg.png');

def paste_ship(bg,height):
    add_char_to_calc_grid(0,height-1,Image.open('ship_filled.png'),bg);

paste_ship(background,4);
#background.show();

beam = Image.open('beam.png');

def paste_beam(bg,height,left=2):
    add_char_to_calc_grid(left,height,beam,bg);

def paste_asteroid(bg,x,y):
    add_char_to_calc_grid(x,y,asteroid_pic,bg);

paste_beam(background,4);
#background.show();

def get_screen(ship_height,is_firing,asteroids):
    bg = Image.open('calc_bg.png');
    paste_ship(bg,ship_height);
    if (is_firing):
        paste_beam(bg, ship_height);
    [paste_asteroid(bg,asteroid[1],asteroid[0]) for asteroid in asteroids];
    return bg;

def get_inputdisplay_screen(ship_height,is_firing,asteroids,inputs):
    baseScreen = get_screen(ship_height,is_firing,asteroids);
    up = Image.open('up_norm.png') if (inputs[0] <= 0) else Image.open('up_press.png');
    down = Image.open('down_norm.png') if (inputs[1] <= 0) else Image.open('down_press.png');
    beamin = Image.open('beam_norm.png') if (inputs[2] <= 0) else Image.open('beam_press.png');
    
    baseScreen.paste(up,(865,30),up);
    baseScreen.paste(down,(865,70),down);
    baseScreen.paste(beamin,(910,50),beamin);
    return baseScreen;

get_screen(2,True,[[3,7],[6,10]]).show();

get_inputdisplay_screen(2,True,[[3,7],[6,10]],[1,-1,1]).show();

background = Image.open('calc_bg.png');

add_char_to_calc_grid(1,3,Image.open('you_epic.png'),background);
add_char_to_calc_grid(10,3,Image.open('fail.png'),background);
background.show();
background.save('epic_fail.png');
