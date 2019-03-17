# coding: utf-8
import codecs

import freetype
from freetype import (FT_LOAD_DEFAULT, FT_LOAD_NO_BITMAP, FT_LOAD_NO_HINTING,
                      FT_LOAD_RENDER, FT_RENDER_MODE_NORMAL, Face, Vector)
from PIL import Image


def f26d6_to_int(val):
    ret = (abs(val) & 0x7FFFFFC0) >> 6
    if val < 0:
        return -ret
    else:
        return ret

def f16d16_to_int(val):
    ret = (abs(val) & 0x3FFFC0) >> 16
    if val < 0:
        return -ret
    else:
        return ret

class CTRFontImage(object):
    def __init__(self, img_path, fnt_path):
        img = Image.open(img_path)
        self.load_local_info(img)
        self.Image = img
        self.__x = 0
        self.__y = 0
        self.Font = freetype.Face(fnt_path)
        self.Font.set_pixel_sizes(self.FontWidth - 2, self.FontWidth - 2)
    
    def draw_char(self, c, pos=None):
        if pos:
            self.X, self.Y = pos
        flags = FT_LOAD_RENDER | FT_LOAD_NO_HINTING
        self.Font.load_char(c, flags)

        glyphslot = self.Font.glyph
        bitmap = glyphslot.bitmap

        adv = f26d6_to_int(glyphslot.metrics.horiAdvance)
        horiBearingX = f26d6_to_int(glyphslot.metrics.horiBearingX)
        horiBearingY = f26d6_to_int(glyphslot.metrics.horiBearingY)

        dxo = self.TexOrignX + ((self.CellWidth - adv) / 2)
        dy = self.TexOrignY + self.BaseLine - horiBearingY - 3
        dy = dy if dy + bitmap.rows < self.TexOrignY + self.CellHeight else self.TexOrignY + self.CellHeight - bitmap.rows

        for x in range(dxo, adv + dxo):
            self.Image.putpixel((x, self.WidthLineOrignY), (255, 0, 0, 0))
        
        dxo += horiBearingX
        for y in range(bitmap.rows):
            dx = dxo
            for x in range(bitmap.width):
                pos = y * bitmap.width + x
                a = ((bitmap.buffer[pos]) & 0xFF)
                self.Image.putpixel((dx, dy), (255-a, 255-a, 255-a, a))
                dx += 1
            dy += 1
        
    def load_local_info(self, img):
        reversed_pixel = img.getpixel((0,0))
        if reversed_pixel != (255, 255, 255, 0):
            raise ValueError('Reversed pixel error! value: ' + str(reversed_pixel))
        
        for i in range(1, img.width):
            pix = img.getpixel((i, 0))
            if pix == (255, 255, 255, 0):
                self.Left = i
                break
        
        for i in range(self.Left + 1, img.width):
            pix = img.getpixel((i, 0))
            if pix == (255, 255, 255, 0):
                self.Right = i
                break
        
        for i in range(1, img.height):
            pix = img.getpixel((0, i))
            if pix == (255, 255, 255, 0):
                self.Ascender = i
                break
        
        for i in range(self.Ascender + 1, img.height):
            pix = img.getpixel((0, i))
            if pix == (255, 255, 255, 0):
                self.BaseLine = i
                break
        
        for i in range(self.BaseLine + 1, img.height):
            pix = img.getpixel((0, i))
            if pix == (255, 255, 255, 0):
                self.Descender = i
                break
        
        self.MarginColor = img.getpixel((1,1))
        self.MarginWidth = 0
        for i in range(1, img.width):
            pix = img.getpixel((i, 1))
            if pix != self.MarginColor:
                break
            self.MarginWidth += 1
        
        self.MarginHeight = 0
        for i in range(1, img.height):
            pix = img.getpixel((1, i))
            if pix != self.MarginColor:
                break
            self.MarginHeight += 1

    def save(self, path):
        self.Image.save(path)

    @property
    def CellWidth(self):
        return self.MarginWidth - 2
    
    @property
    def CellHeight(self):
        return self.MarginHeight - 4
    
    @property
    def BlockWidth(self):
        return self.MarginWidth + 2

    @property
    def BlockHeight(self):
        return self.MarginHeight + 2
    
    @property
    def FontWidth(self):
        return self.Right - self.Left
    
    @property
    def FontHeight(self):
        return self.Descender - self.Ascender

    @property
    def Columns(self):
        return self.Image.width / self.BlockWidth
    
    @property
    def Rows(self):
        return self.Image.height / self.BlockHeight

    @property
    def X(self):
        return self.__x
    @X.setter
    def X(self, value):
        if value > self.Columns:
            raise ValueError("X value exceed.")
        self.__x = value
    
    @property
    def Y(self):
        return self.__y
    @Y.setter
    def Y(self, value):
        if value > self.Rows:
            raise ValueError("Y value exceed.")
        self.__y = value
    
    @property
    def TexOrignX(self):
        return self.__x * self.BlockWidth + 2
    @property
    def TexOrignY(self):
        return self.__y * self.BlockHeight + 2
    
    @property
    def WidthLineOrignX(self):
        return self.TexOrignX
    @property
    def WidthLineOrignY(self):
        return self.TexOrignY + self.CellHeight + 1
    
    @property
    def Index(self):
        return (self.Y * self.Columns) + self.X
    @Index.setter
    def Index(self, value):
        self.X = value % self.Columns
        self.Y = 0 if (value - self.X) == 0 else (value - self.X) / self.Columns

    def __repr__(self):
        return '''Left: %d\nRight: %d\nAscender: %d\nDescender: %d\nBaseline: %d\nBlock Size: (%d, %d)\nMargin: (%d, %d)\nCell: (%d, %d)\nColumns: %d\nRows: %d'''%(
            self.Left, self.Right, 
            self.Ascender, self.Descender, self.BaseLine,
            self.BlockWidth, self.BlockHeight,
            self.MarginWidth, self.MarginHeight, 
            self.CellWidth, self.CellHeight,
            self.Columns, self.Rows)

def getenc(path):
    with open(path,'rb')as inputfile:
        if inputfile.read(2) == '\xff\xfe':
            return 'utf-16le'
        inputfile.seek(0,0)
        if inputfile.read(2) == '\xfe\xff':
            return 'utf-16be'
        inputfile.seek(0,0)
        if inputfile.read(3) == '\xef\xbb\xbf':
            return 'utf-8-sig'
        return 'utf-8'

def draw(img_path, fnt_path, chars_path, img_out_path, start_index=0):
    cfimg = CTRFontImage(img_path, fnt_path)
    chars = codecs.open(chars_path, 'r', getenc(chars_path)).read().replace('\n', '').replace('\r', '')
    
    for c in chars:
        cfimg.Index = start_index
        cfimg.draw_char(c)
        start_index += 1
    
    cfimg.save(img_out_path)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Nintendo Ware font image tool. Created by LITTOMA, Team PB.")
    parser.add_argument('-i', '--image', help="Set input image file path.", required=True, type=str)
    parser.add_argument('-f', '--font', help="Set TrueType font file path.", required=True, type=str)
    parser.add_argument('-c', '--charset', help="Set charset file path.", required=True)
    parser.add_argument('-o', '--output', help="Set output image file path.", required=True)
    parser.add_argument('-s', '--start', help="Set draw start index.", required=True, type=int)
    
    options = parser.parse_args()
    draw(options.image, options.font, options.charset, options.output, options.start)