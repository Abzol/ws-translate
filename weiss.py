#!/usr/bin/python3

from PIL import Image
from PIL import ImageFilter
from PIL import ImageDraw
from PIL import ImageFont
from PIL import ImageOps
import requests
from bs4 import BeautifulSoup
import re
import sys
import os.path
import html
import json

TEXTFONT = 'NotoSerif-SemiCondensed.ttf'
SYMBOLSFONT = 'NotoSansSymbols-Regular.ttf'
LINESPACING = 3
PALETTE = False # true renders cards in png8, false renders in png24. Filesize is ~500kb for png24, ~150kb for png8 

IMAGESIZE = (500, 700)

STOCKNUMBERS = '⓪①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
SYMBOLS = True #set to false if you prefer (2) over ②

CARD_IMAGE_URL_BASE = 'https://ws-tcg.com/wordpress/wp-content/images/cardlist/'

COLORS = {
    'Yellow': (112, 124, 26),
    'Green': (49, 75, 46),
    'Red': (98, 32, 34),
    'Blue': (37, 59, 82),
    'Purple': (81, 32, 61) 
}

TRIGGERS = {
    'Draw': '\n(Draw): When this triggers, you may draw one card from your deck.',
    'Standby': '\n(Standby): When this triggers, you may choose one character with a level up to one higher than you in your waiting room, and put it on any slot on stage, Rested.',
    'Bounce': '\n(Bounce): When this triggers, you may return one of your opponents characters to their hand.',
    'Shot': '\n(Shot): If this attack gets damage canceled, deal one damage. (This damage can be canceled).',
    'Treasure': '\n(Treasure): When this triggers, return it to your hand. You may put the top card of your deck into your stock.',
    'Door': '\n(Door): When this triggers, you may return one character from your Waiting Room to your hand.',
    'Salvage': '\n(Door): When this triggers, you may return one character from your Waiting Room to your hand.', #thanks, HOTC
    'Gate': '\n(Gate): When this triggers, you may return one climax from your Waiting Room to your hand.',
    'Stock': '\n(Stock): When this triggers, you may put the top card of your deck into your Stock.',
    'Choice': '\n(Choice): When this triggers, you may put a character with a (Soul) trigger from your Waiting Room to your hand or your Stock.',
    'Soul': '', #You should learn this one yourself. Also it doesn't have reminder text on real English cards either.
    '2': '', #thanks again, HOTC
    '' : ''
}

#setup pillow
def renderCard(path, filename, cardinfo, output=''):

    name = cardinfo['en']
    color = cardinfo['color']
    cardtype = cardinfo['type']
    triggers = cardinfo['triggers']
    text = cardinfo['text']
    traits = cardinfo['traits']

    im = Image.open(os.path.join(path, filename)).convert('RGB')
    #before resizing, stamp over the name field!
    nameslot = Image.open('name-' + cardtype.lower() + '-' +  color.lower() + '.png')
    position = {'character':(int(0.285 *im.size[0]), int(0.8891*im.size[1])),
                'event':    (int(0.28  *im.size[0]), int(0.9106*im.size[1])),
                'climax':   (int(0.5635*im.size[0]), int(0.875 *im.size[1]))}
    im.paste(nameslot, position[cardtype.lower()])
    #resize to let text render better
    if cardtype.lower() == 'climax':
        global IMAGESIZE
        IMAGESIZE = (IMAGESIZE[::-1])
    im = im.resize(IMAGESIZE, resample=Image.BILINEAR)
    #rotate climax cards 90 degrees counterclockwise
    #if (cardtype == 'Climax'):
    #    im = im.rotate(90, expand = 1)
    font = ImageFont.truetype(TEXTFONT, size=14)
    if SYMBOLS:
        symbolsFont = ImageFont.truetype(SYMBOLSFONT, size=16)
    draw = ImageDraw.Draw(im)

    #set some anchors
    if (cardtype == 'Character'):
        effectAnchorBottom = 0.876 * im.size[1]
        effectAnchorLeft = 0.05 * im.size[0]
        effectAreaWidth = 0.9 * im.size[0]
        nameAnchorTop = 0.885 * im.size[1]
        nameAnchorCenter = 0.577 * im.size[0]
        nameAreaWidth = 0.466 * im.size[0]
        nameAreaHeight = 0.0356 * im.size[1]
    elif (cardtype == 'Event'):
        effectAnchorBottom = 0.9 * im.size[1]
        effectAnchorLeft = 0.05 * im.size[0]
        effectAreaWidth = 0.9 * im.size[0]
        nameAnchorTop = 0.91 * im.size[1]
        nameAnchorCenter = 0.577 * im.size[0]
        nameAreaWidth = 0.466 * im.size[0]
        nameAreaHeight = 0.0356 * im.size[1]
    elif (cardtype == 'Climax'):
        effectAnchorBottom = 0.968 * im.size[1]
        effectAnchorLeft = 0.0228 * im.size[0]
        effectAreaWidth = 0.3462 * im.size[0]
        nameAnchorTop = 0.87 * im.size[1]
        nameAnchorCenter = 0.7735 * im.size[0]
        nameAreaWidth = 0.3248 * im.size[0]
        nameAreaHeight = 0.06 * im.size[1]

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
            while (width < int(effectAreaWidth)):
                c += 1
                if (c > len(words)):
                    break
                width = draw.textsize(' '.join(words[0:c]), font)[0]
            c -= 1
            lines.append(' '.join(words[0:c]))
            words = words[c:]
        return '\n'.join(lines)

    def drawOutlined(canvas, position, width, text, font):
        x, y = position
        if (len(text.split('\n')) > 1):
            for xo, yo in [(-1, -1), (-1, 1), (width, -1), (width, 1)]:
                canvas.multiline_text((x+xo, y+yo), text, fill=(255, 255, 255), font=font, spacing=LINESPACING)
            for i in range(width):
                canvas.multiline_text((x+i, y), text, fill=(0, 0, 0), font=font, spacing=LINESPACING)
        else:
            for xo, yo in [(-1, -1), (-1, 1), (width, -1), (width, 1)]:
                canvas.text((x+xo, y+yo), text, fill=(255, 255, 255), font=font)
            for i in range(width):
                canvas.text((x+i, y), text, fill=(0, 0, 0), font=font)

    #add reminder text for Climax cards, since HOTC leaves it out
    if cardtype == 'Climax':
        for trigger in triggers:
            text += TRIGGERS[trigger]

    #split the effect text
    if not(text.startswith('--None--')):
        text = html.unescape(text)
        text = splitText(draw, text, font)
        textheight = int(draw.multiline_textsize(text, font, spacing=LINESPACING)[1])
        
        #add stock numbers
        if (SYMBOLS):
            text = re.sub('\((\d)\)', lambda x: STOCKNUMBERS[int(x[1])] + '...', text)
    
        #glass pane effect to hide japanese effect text
        im_blur = im.copy().filter(ImageFilter.GaussianBlur(5))
        white = Image.new('RGB', im.size, (255, 255, 255))
        im_blur = Image.blend(im_blur, white, 0.3)
        if (SYMBOLS):
            im_copy = im_blur.copy()
        im_blur = im_blur.crop((int(effectAnchorLeft),
                                int(effectAnchorBottom) - textheight,
                                int((effectAnchorLeft + effectAreaWidth)),
                                int(effectAnchorBottom)))
        im.paste(im_blur,(int(effectAnchorLeft),int(effectAnchorBottom) - textheight))

        #draw the english effect text
        drawOutlined(draw, (int(effectAnchorLeft), int(effectAnchorBottom) - textheight), 2, text, font)

        #effect formatting bonuses
        lines = text.split('\n')
        for i in range(len(lines)):
            if lines[i].startswith('[A]') or lines[i].startswith('[C]') or lines[i].startswith('[S]'):
                offset = draw.multiline_textsize('#' + '\n.'*(len(lines)-i-1), font, spacing=LINESPACING)[1]
                draw.rectangle((effectAnchorLeft-1, effectAnchorBottom-offset+2, effectAnchorLeft+20, effectAnchorBottom - offset + 16), fill=(0, 0, 0))
                draw.rectangle((effectAnchorLeft, effectAnchorBottom-offset+1, effectAnchorLeft+19, effectAnchorBottom - offset + 17), fill=(0, 0, 0))
                draw.text((effectAnchorLeft, effectAnchorBottom-offset-1), lines[i][0:3], fill=(255, 255, 255), font=font)
                draw.text((effectAnchorLeft+1, effectAnchorBottom-offset-1), lines[i][0:3], fill=(255, 255, 255), font=font)
            if 'CX COMBO' in lines[i]:
                textsize = draw.multiline_textsize('CX COMBO' + '\n'*(len(lines)-i-1), font, spacing=LINESPACING)
                offset = textsize[1]
                width = textsize[0]
                draw.rectangle((effectAnchorLeft+23, effectAnchorBottom-offset+1, effectAnchorLeft+width+23, effectAnchorBottom - offset + 17), fill=(255, 0, 0))
                draw.text((effectAnchorLeft+23, effectAnchorBottom-offset), 'CX COMBO', fill=(255, 255, 255), font=font)
                draw.text((effectAnchorLeft+24, effectAnchorBottom-offset), 'CX COMBO', fill=(255, 255, 255), font=font)
            if (re.search('\[\w\]', lines[i][3:]) != None):
                positions = [m.start() for m in re.finditer('\[\w\]', lines[i][3:])]
                for j in positions:
                    textsize = draw.multiline_textsize(lines[i][0:j+3] + '\n'*(len(lines)-i-1), font, spacing=LINESPACING)
                    offset = textsize[1]
                    width = textsize[0]
                    draw.rectangle((effectAnchorLeft-1+width, effectAnchorBottom-offset+2, effectAnchorLeft+width+20, effectAnchorBottom - offset + 16), fill=(0, 0, 0))
                    draw.rectangle((effectAnchorLeft+width, effectAnchorBottom-offset+1, effectAnchorLeft+width+19, effectAnchorBottom - offset + 17), fill=(0, 0, 0))
                    draw.text((effectAnchorLeft+width, effectAnchorBottom-offset-1), lines[i][j+3:j+6], fill=(255, 255, 255), font=font)
                    draw.text((effectAnchorLeft+width+1, effectAnchorBottom-offset-1), lines[i][j+3:j+6], fill=(255, 255, 255), font=font)
            if (SYMBOLS):
                match = re.search('['+STOCKNUMBERS+']', lines[i])
                if (match):
                    offset = draw.multiline_textsize(lines[i][0:match.start()] + '\n.'*(len(lines)-i-1), font, spacing=LINESPACING)
                    fontOffset = (0.5*(draw.textsize(STOCKNUMBERS[0], symbolsFont)[1] - draw.textsize('A', font)[1]))+LINESPACING
                    mask = Image.new('1', im.size)
                    maskDraw = ImageDraw.Draw(mask)
                    maskDraw.rectangle((effectAnchorLeft+offset[0], effectAnchorBottom-offset[1], effectAnchorLeft+offset[0]+16, effectAnchorBottom-offset[1]+15), fill=(1))
                    im.paste(im_copy, mask=mask)
                    drawOutlined(draw,(effectAnchorLeft+offset[0], effectAnchorBottom-offset[1]-fontOffset), 2, lines[i][match.start():match.end()], symbolsFont)

    #--end the 'if card text isn't --None--' block--

    #name
    for textcolor in [(0, 0, 0, 128), (225, 225, 225, 225)]: #once in semi black, once in white
        font = ImageFont.truetype(TEXTFONT, size=24)
        nameCanvas = Image.new('RGBA', draw.textsize(name, font), '#ffffff00')
        nameCanvasDraw = ImageDraw.Draw(nameCanvas)
        nameCanvasDraw.text((0,0), name, textcolor, font)
        if nameAreaWidth < nameCanvas.size[0]:
            nameCanvas = nameCanvas.resize((int(nameAreaWidth), nameCanvas.size[1]), resample=Image.BILINEAR) #requires shrink to fit
            x = 4
        else: 
            x = 1
        for _ in range(x):
            if textcolor == (0, 0, 0, 128):
                offset = 2
            else:
                offset = 0
            im.paste(nameCanvas,(int((nameAnchorCenter-((nameCanvas.size[0]/2))))+offset, int(nameAnchorTop)+1+offset), mask=nameCanvas) # when shrinking text, opacity goes way down, so stap 4 times

    #traits
    font = ImageFont.truetype(TEXTFONT, size=14)
    for i in range(len(traits)):
        if traits[i] != "None":
            try:  
                trait = traits[i].split('(')[1][:-1]
            except IndexError: #properly formatted
                trait = traits[i]
            slot = Image.open('slot-trait.png')
            im.paste(slot,(int((0.692-(0.226*i))*im.size[0]),  int(0.9380*im.size[1])), mask=slot)
            traitCanvas = Image.new('RGBA', draw.textsize(trait, font), (255, 255, 255))
            if (traitCanvas.size[0] > 0.2*im.size[0]):
                traitCanvasDraw = ImageDraw.Draw(traitCanvas)
                traitCanvasDraw.text((0,0), trait, (0, 0 , 0), font)
                traitCanvasMask = ImageOps.invert(traitCanvas.convert('L'))
                traitCanvas.putalpha(traitCanvasMask)
                traitCanvas = traitCanvas.resize((min(int(0.2*im.size[0]), traitCanvas.size[0]), 14))
                for _ in range(4):
                    im.paste(traitCanvas, (int((0.8020-(0.2340*i)-((traitCanvas.size[0]/2)/im.size[0]))*im.size[0]), int(0.9380*im.size[1])), mask=traitCanvas)
                    #stamp it four times to *really* stick it because the resize makes the transparency completely
            else:
                imDraw = ImageDraw.Draw(im)
                imDraw.text((int((0.806-(0.225*i)-((traitCanvas.size[0]/2)/im.size[0]))*im.size[0]), int(0.9380*im.size[1])), trait, (0,0,0), font)

    #rotate climax cards back to normal orientation
    #if (cardtype == 'Climax'):
    #    im = im.rotate(-90, expand = 1)

    if PALETTE:
        im = im.convert('P', palette=1)
    else:
        im = im.convert('RGB')
    with open(os.path.join(path, output, filename.split('.')[0]+ ' EN.png'), 'wb') as f:
        im.save(f, format='png')
    #im.save(os.path.join(path, filename.split('.')[0]+ " EN.jpg"))

#download card text per card:
def downloadCardText(cardno):
    r = requests.get('https://www.heartofthecards.com/code/cardlist.html?card=WS_' + cardno)
    soup = BeautifulSoup(r.text, 'html.parser')
    text = str(soup.find_all('td', class_='cards3')[2]).replace('<br/>','\n') #use a sensible linebreak character (requests or bs4 handles closing <br> tag for you)
    text = re.sub('<[^<]+?>','',text) #remove all html tags
    #this line replaces (x) with the matching unicode circled number version.
    if (SYMBOLS):
        text = re.sub('\((\d)\)', lambda x: STOCKNUMBERS[int(x[1])] + '...', text)
        #extra periods to space the symbol out becasue emspace renders as tofu and I'm too lazy to make drawtext scale automatically for now.
    name = soup.find('div', class_='tcgrcontainer').next_sibling.next_sibling
    name = name.next_element.next_sibling.next_element.next_element.next_element.next_element
    cards2 = soup.find_all('td', class_='cards2')
    color = cards2[3].contents[0]
    cardtype = cards2[5].contents[0]
    triggers = []
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
    return {'text':text, 'name':name, 'color':color, 'type':cardtype, 'traits':traits, 'triggers':triggers}

#get some card text
def getCardText(cardno, carddb=None):
    if carddb:
        cardid = cardno.upper().split('/')
        cardid = cardid[0] + '/' + cardid[1] + '-' + cardid[2] #format id as KMD/W96-001
        return carddb[cardid]
    else:
        return (downloadCardText(cardno))

def generateTranslations(filename):
    with open(os.path.join(sys.argv[1], 'tl.txt'), 'r') as tl:
        translations = tl.read().split('================================================================================') #help
        cards = {}
        for chunk in translations:
            data = chunk.split('\n')
            try:
                card = {}
                card['en'] = data[2]
                card['jp'] = data[3]
                line = [x for x in data[4].split(' ') if not len(x) == 0] # get rid of double space issues
                card['id'] = line[2]
                card['rarity'] = line[4]
                line = [x for x in data[5].split(' ') if not len(x) == 0] # get rid of double space issues
                card['color'] = line[1]
                card['type'] = line[4]
                line = [x for x in data[6].split(' ') if not len(x) == 0] # get rid of double space issues
                card['level'] = line[1]
                card['cost'] = line[3]
                card['power'] = line[5]
                card['soul'] = line[7]
                card['traits'] = [x[1:-1] for x in re.findall(r'\(.*?\)', data[7])]
                card['triggers'] = data[8].split(' ')[1:]
                card['flavor'] = data[9][8:] #final slice to cut away 'Flavor: ' marker.
                line = ""
                for piece in data[10:]:
                    if piece.startswith('['):
                        line += '\n' + piece + ' '
                    else:
                        line += piece + ' '
                card['text'] = line[6:] # final slice to cut away 'TEXT: ' marker.
                cards[card['id']] = card # identify by print number
            except IndexError:
                pass # bad chunk
    with open(os.path.join(sys.argv[1], 'set.json'), 'w') as o:
        json.dump(cards, o, indent=2)

def translateCard(filename, output='', carddb=None):
    path, filename = os.path.split(filename)
    cardno = filename.split('.')[0].replace('_', '/')
    cardinfo = getCardText(cardno, carddb)
    renderCard(path, filename, cardinfo, output=output)

def downloadCard(cardid):
    setname, setnumber, number = re.split('_|\.|-|/', cardid.lower())[:3]
    print(f'Downloading {cardid}...')
    r = requests.get(f'{CARD_IMAGE_URL_BASE}{setname[0]}/{setname}_{setnumber}/{setname}_{setnumber}_{number}.png')
    try:
        os.makedirs(f'cards/{setname}')
    except FileExistsError:
        pass
    with open(f'cards/{setname}/{setname}_{setnumber}_{number}.png', 'wb') as f:
        f.write(r.content)

if __name__ == '__main__':
    if (os.path.isdir(sys.argv[1])):
        try:
            os.mkdir(sys.argv[1].rstrip('/') + '/EN')
        except FileExistsError:
            pass

        #if we have a card library locally
        carddb = None
        if (os.path.isfile(os.path.join(sys.argv[1], 'tl.txt'))):
            if not(os.path.isfile(os.path.join(sys.argv[1], 'set.json'))):
                generateTranslations('tl.txt')
        if (os.path.isfile(os.path.join(sys.argv[1], 'set.json'))):
            with open(os.path.join(sys.argv[1], 'set.json'), 'r') as f:
                carddb = json.load(f)

        filenames = [x for x in os.listdir(sys.argv[1]) if x.endswith('.png')]
        index = 0
        for filename in filenames:
            if os.path.isfile(os.path.join(sys.argv[1], filename)):
                index += 1
                if os.path.isfile(os.path.join(sys.argv[1], 'EN', filename.split('.')[0] + ' EN.png')):
                    print('(%d/%d) Skipping %s, already done.' % (index, len(filenames), filename))
                    continue
                print('(%d/%d) Translating %s' % (index, len(filenames), filename))
                translateCard(os.path.join(sys.argv[1], filename), './EN', carddb)
    else:
        if (os.path.isfile(sys.argv[1])):
            translateCard(sys.argv[1])
        else:
            downloadCard(sys.argv[1])