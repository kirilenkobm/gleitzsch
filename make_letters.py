#!/usr/bin/env python3
"""Convert font to images of letters."""
import sys
import os
from PIL import Image, ImageFont, ImageDraw

LETTER_SIZE = 46

try:
    font_file = sys.argv[1]
    output_folder = sys.argv[2]
except IndexError:
    sys.stderr.write("Usage: {} [ttf file] [output folder]\n".format(sys.argv[0]))
    sys.exit(0)

font_name = os.path.basename(font_file).split(".")[0]
font = ImageFont.truetype(font_file, LETTER_SIZE)
im = Image.new("RGB", (LETTER_SIZE, LETTER_SIZE))
draw = ImageDraw.Draw(im)
symbols = [ord(c) for c in "!?.,'[].()’-"]
up_lat = list(range(ord("A"), ord("Z") + 1))
lo_lat = list(range(ord("a"), ord("z") + 1))
# up_cyr = list(range(ord("А"), ord("Я") + 1))
# lo_cyr = list(range(ord("а"), ord("я") + 1))
numbers = list(range(ord("0"), ord("9") + 1))
characters = symbols + up_lat + lo_lat + numbers  # + up_cyr + lo_cyr

for code in characters:
    w, h = draw.textsize(chr(code), font=font)
    im = Image.new("RGB", (w, h), color="#FFFFFF")
    draw = ImageDraw.Draw(im)
    draw.text((1, 10), chr(code), font=font, fill="#000000")
    im.save(os.path.join(output_folder, "{0}_{1}.png".format(font_name, chr(code))))
