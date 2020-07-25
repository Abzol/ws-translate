#!/usr/bin/python3

from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw
from PIL import ImageFont
import requests
from bs4 import BeautifulSoup
import re
import sys

COLORS = {
    'Yellow': (112, 124, 26),
    'Green': (49, 75, 46),
    'Red': (98, 32, 34),
    'Blue': (37, 59, 82),
    'Purple': (81, 32, 61) 
}

if __name__ == '__main__':
    filename = sys.argv[1]
    cardno = filename.split('.')[0].replace('_', '/')

    #fetch some card info
    r = requests.get('https://www.heartofthecards.com/code/cardlist.html?card=WS_' + cardno)
    soup = BeautifulSoup(r.text, 'html.parser')
    text = str(soup.find_all('td', class_='cards3')[2]).replace('<br/>','\n') #use a sensible linebreak character (requests or bs4 handles closing <br> tag for you)
    text = re.sub('<[^<]+?>','',text) #remove all html tags
    name = soup.find('div', class_='tcgrcontainer').next_sibling.next_sibling
    name = name.next_element.next_sibling.next_element.next_element.next_element.next_element
    cards2 = soup.find_all('td', class_='cards2')
    color = cards2[3].contents[0]
    cardtype = cards2[5].contents[0]
    #hotc uses two standards here
    if (len(cards2) == 12):
        traits = cards2[11].contents[0].split(',')
    if (len(cards2) == 13):
        traits = [cards2[10].contents[0], cards2[12].contents[0]]
    #if climax, find triggers
    if (cardtype == "Climax"):
        if (len(cards2) == 12):
            triggers = cards2[10].contents[0].split()
        if (len(cards2) == 13):
            triggers = cards2[11].contents[0].split()

    TRIGGERS = {
        'Draw': '\n(Draw): When this triggers, you may draw one card from your deck.',
        'Standby': '\n(Standby): When this triggers, you may choose one character with a level up to one higher than you in your waiting room, and put it on any slot on stage, Rested.',
        'Bounce': '\n(Bounce): When this triggers, you may return one of your opponents characters to their hand.',
        'Shot': '\n(Shot): If this attack gets damage canceled, deal one damage. (This damage can be canceled).',
        'Treasure': '\n(Treasure): When this triggers, return it to your hand. You may put the top card of your deck into your stock.',
        'Door': '\n(Door): When this triggers, you may return one character from your Waiting Room to your hand.',
        'Gate': '\n(Gate): When this triggers, you may return one climax from your Waiting Room to your hand.',
        'Stock': '\n(Stock): When this triggers, you may put the top card of your deck into your Stock.',
        'Soul': '', #You should learn this one yourself
        '2': '' #thanks, HOTC
    }

    #setup pillow
    im = Image.open(filename)
    #rotate climax cards 90 degrees counterclockwise
    if (cardtype == "Climax"):
        im = im.rotate(90, expand = 1)
    font = ImageFont.truetype('georgia.ttf', size=14)
    draw = ImageDraw.Draw(im)

    def splitText(draw, text, font):
        parts = []
        effects = text.split('\n')
        for effect in effects:
            parts.append(splitLines(draw, effect, font))
        return '\n'.join(parts)

    def splitLines(draw, text, font):
        lines = []
        words = text.split()
        while(len(words) > 0):
            width = draw.textsize(words[0], font)[0]
            c = 1
            while (width < int(effectAreaWidth*im.size[0])):
                c += 1
                if (c > len(words)):
                    break
                width = draw.textsize(" ".join(words[0:c]), font)[0]
            c -= 1
            lines.append(" ".join(words[0:c]))
            words = words[c:]
        return '\n'.join(lines)

    #set some anchors
    if (cardtype == "Character"):
        effectAnchorBottom = 0.876
        effectAnchorLeft = 0.05
        effectAreaWidth = 0.9
        nameAnchorTop = 0.8986
        nameAnchorCenter = 0.577
        nameAreaWidth = 0.466
        nameAreaHeight = 0.0356
    elif (cardtype == "Event"):
        effectAnchorBottom = 0.9
        effectAnchorLeft = 0.05
        effectAreaWidth = 0.9
        nameAnchorTop = 0.9205
        nameAnchorCenter = 0.577
        nameAreaWidth = 0.466
        nameAreaHeight = 0.0356
    elif (cardtype == "Climax"):
        effectAnchorBottom = 0.968
        effectAnchorLeft = 0.0228
        effectAreaWidth = 0.3462
        nameAnchorTop = 0.888
        nameAnchorCenter = 0.7735
        nameAreaWidth = 0.3248
        nameAreaHeight = 0.06

    #add reminder text for Climax cards, since HOTC leaves it out
    if cardtype == "Climax":
        for trigger in triggers:
            text += TRIGGERS[trigger]

    #split the effect text
    text = splitText(draw, text, font)
    textheight = int(draw.multiline_textsize(text, font)[1])

    #glass pane effect to hide japanese effect text
    im_blur = im.copy().filter(ImageFilter.GaussianBlur(5))
    white = Image.new('RGB', im.size, (255, 255, 255))
    im_blur = Image.blend(im_blur, white, 0.3)
    im_blur = im_blur.crop((int(effectAnchorLeft * im.size[0]),
                            int(effectAnchorBottom * im.size[1]) - textheight,
                            int((effectAnchorLeft + effectAreaWidth) *im.size[0]),
                            int(effectAnchorBottom * im.size[1])))
    im.paste(im_blur,(int(effectAnchorLeft * im.size[0]),int(effectAnchorBottom * im.size[1]) - textheight))

    #draw the english effect text
    draw.multiline_text((int(effectAnchorLeft*im.size[0] - 1), int(effectAnchorBottom * im.size[1]) - textheight - 1), text, fill=(255, 255, 255), font=font)
    draw.multiline_text((int(effectAnchorLeft*im.size[0] - 1), int(effectAnchorBottom * im.size[1]) - textheight + 1), text, fill=(255, 255, 255), font=font)
    draw.multiline_text((int(effectAnchorLeft*im.size[0] + 2), int(effectAnchorBottom * im.size[1]) - textheight - 1), text, fill=(255, 255, 255), font=font)
    draw.multiline_text((int(effectAnchorLeft*im.size[0] + 2), int(effectAnchorBottom * im.size[1]) - textheight + 1), text, fill=(255, 255, 255), font=font)
    draw.multiline_text((int(effectAnchorLeft*im.size[0]), int(effectAnchorBottom * im.size[1]) - textheight), text, fill=(128, 128, 128), font=font)
    draw.multiline_text((int(effectAnchorLeft*im.size[0] + 1), int(effectAnchorBottom * im.size[1]) - textheight), text, fill=(0, 0, 0), font=font)

    #effect formatting bonuses
    lines = text.split('\n')
    for i in range(len(lines)):
        if lines[i].startswith('[A]') or lines[i].startswith('[C]') or lines[i].startswith('[S]'):
            offset = draw.multiline_textsize('#' + '\n.'*(len(lines)-i-1), font)[1]
            draw.rectangle((effectAnchorLeft*im.size[0]-1, (effectAnchorBottom*im.size[1])-offset-0.5, effectAnchorLeft*im.size[0]+20, (effectAnchorBottom * im.size[1]) - offset + 15), fill=(0, 0, 0))
            draw.text((effectAnchorLeft*im.size[0], (effectAnchorBottom*im.size[1])-offset-1), lines[i][0:3], fill=(255, 255, 255), font=font)
            draw.text((effectAnchorLeft*im.size[0]+1, (effectAnchorBottom*im.size[1])-offset-1), lines[i][0:3], fill=(255, 255, 255), font=font)
        if 'CX COMBO' in lines[i]:
            textsize = draw.multiline_textsize('CX COMBO' + '\n'*(len(lines)-i-1), font)
            offset = textsize[1]
            width = textsize[0]
            draw.rectangle((effectAnchorLeft*im.size[0]+23, (effectAnchorBottom*im.size[1])-offset-0.5, effectAnchorLeft*im.size[0]+width+23, (effectAnchorBottom * im.size[1]) - offset + 15), fill=(255, 0, 0))
            draw.text((effectAnchorLeft*im.size[0]+23, (effectAnchorBottom*im.size[1])-offset), 'CX COMBO', fill=(255, 255, 255), font=font)
            draw.text((effectAnchorLeft*im.size[0]+24, (effectAnchorBottom*im.size[1])-offset), 'CX COMBO', fill=(255, 255, 255), font=font)
        if (re.search('\[\w\]', lines[i][3:]) != None):
            positions = [m.start() for m in re.finditer('\[\w\]', lines[i][3:])]
            for j in positions:
                textsize = draw.multiline_textsize(lines[i][0:j+3] + '\n'*(len(lines)-i-1), font)
                offset = textsize[1]
                width = textsize[0]
                draw.rectangle((effectAnchorLeft*im.size[0]-1+width, (effectAnchorBottom*im.size[1])-offset-0.5, effectAnchorLeft*im.size[0]+width+20, (effectAnchorBottom * im.size[1]) - offset + 15), fill=(0, 0, 0))
                draw.text((effectAnchorLeft*im.size[0]+width, (effectAnchorBottom*im.size[1])-offset-1), lines[i][j+3:j+6], fill=(255, 255, 255), font=font)
                draw.text((effectAnchorLeft*im.size[0]+width+1, (effectAnchorBottom*im.size[1])-offset-1), lines[i][j+3:j+6], fill=(255, 255, 255), font=font)
 
    #name
    font = ImageFont.truetype('georgia.ttf', size=24)
    nameCanvas = Image.new('RGBA', draw.textsize(name, font), COLORS[color])
    nameCanvasDraw = ImageDraw.Draw(nameCanvas)
    nameCanvasDraw.text((0,0), name, (255, 255, 255), font)
    nameCanvas = nameCanvas.resize((min(int(nameAreaWidth*im.size[0]), nameCanvas.size[0]), int(nameAreaHeight*im.size[1])), resample=Image.BILINEAR)
    im.paste(nameCanvas,(int((nameAnchorCenter-((nameCanvas.size[0]/2)/im.size[0]))*im.size[0]), int(nameAnchorTop*im.size[1])+1))

    #traits
    font = ImageFont.truetype('georgia.ttf', size=14)
    for i in range(len(traits)):
        if traits[i] != "None":
            trait = traits[i].split('(')[1][:-1]
            traitCanvas = Image.new('RGBA', draw.textsize(trait, font), (238, 222, 52))
            traitCanvasDraw = ImageDraw.Draw(traitCanvas)
            traitCanvasDraw.text((0,0), trait, (0,0,0), font)
            traitCanvas = traitCanvas.resize((min(int(0.2*im.size[0]), traitCanvas.size[0]), 14))
            draw.rectangle((int((0.7020-(0.2340*i))*im.size[0]), int(0.9452*im.size[1])+2, int((0.9020-(0.2340*i))*im.size[0]), int(0.9644*im.size[1])+2), fill=(238, 222, 52))
            im.paste(traitCanvas,(int((0.8020-(0.2340*i)-((traitCanvas.size[0]/2)/im.size[0]))*im.size[0]), int(0.9452*im.size[1])+2))

    #rotate climax cards back to normal orientation
    if (cardtype == "Climax"):
        im = im.rotate(-90, expand = 1)

    im.save(filename.split('.')[0]+ " EN.jpg")