#!/usr/bin/env python3
"""Make a picture of text."""
import sys
import os
from collections import defaultdict
from skimage import io
from skimage import img_as_float
from skimage import transform as tf
import numpy as np
STRING_LEN = 30
MAX_LEN = 180
LETTER_W = 35
LETTER_H = 40


def parts(lst, n=25):
    """Split an iterable into list of iterables of size n."""
    return [lst[i:i + n] for i in iter(range(0, len(lst), n))]


def read_letters(font):
    """Create letter: object dictionary."""
    this_folder = os.path.dirname(__file__)
    letters_dir = os.path.join(this_folder, "letters")
    letter_pics = [c for c in os.listdir(letters_dir) if c.startswith(font)]
    letters_array = {}
    for letter_pic in letter_pics:
        letter = letter_pic.split("_")[1].split(".")[0]
        letter_file = os.path.join(letters_dir, letter_pic)
        letter_array = img_as_float(io.imread(letter_file))
        letter_array = tf.resize(letter_array, (LETTER_H, LETTER_W))
        letters_array[letter] = letter_array
    letters_array[" "] = np.zeros((LETTER_H, LETTER_W, 3))
    return letters_array


def filter_text(text, letters):
    """Remove letters that are not in the dataset."""
    all_letters = set(text)
    letters_out = set(all_letters).difference(letters)
    letters_out = letters_out.difference(" ")
    for letter in letters_out:
        text = text.replace(letter, "")
    return text


def split_lines(words):
    """Split words into lines."""
    lines = defaultdict(str)
    line_num = 0
    for i in range(len(words)):
        current_line = lines[line_num]

        if len(current_line + " {}".format(words[i])) <= STRING_LEN:
            lines[line_num] += " {} ".format(words[i])

        elif len(words[i]) > STRING_LEN - 5:
            place_left = STRING_LEN - len(current_line)
            first_half = words[i][:place_left - 1]
            word_left = words[i][place_left - 1:]
            lines[line_num] += " {} ".format(first_half)
            for piece in parts(word_left, STRING_LEN):
                line_num += 1
                lines[line_num] += " {} ".format(piece)

        elif len(current_line) > STRING_LEN / 2 and len(words[i]) > 18:
            place_left = STRING_LEN - len(current_line)
            first_half = words[i][:place_left - 1]
            second_half = words[i][place_left - 1:]
            lines[line_num] += " {} ".format(first_half)
            line_num += 1
            lines[line_num] += " {} ".format(second_half)

        else:
            lines[line_num] += " "
            line_num += 1
            lines[line_num] += " {} ".format(words[i])

    return lines


def make_text(text, font):
    """Make a picture with the text requested."""
    text = text.upper()
    letters_dict = read_letters(font)
    letters_available = list(letters_dict.keys())
    text = filter_text(text, letters_available)
    if len(text) > MAX_LEN:
        sys.stderr.write("Warning! The text is very long, left first {} characters".format(MAX_LEN))
        text = text[:MAX_LEN]
    elif len(text) == 0:
        sys.stderr.write("Warning! There are no letters left after filtering.")
        return np.zeros((1, 1, 3))
    words = text.upper().split()
    lines = split_lines(words)

    letter_shape = letters_dict.get(" ").shape
    letter_h, letter_w = letter_shape[0], letter_shape[1]
    canvas = np.zeros((letter_h * len(lines), letter_w * max([len(s) for s in lines.values()]), 3))
    for num, line in lines.items():
        characters = []
        x_shifts = np.random.choice(range(-3, 3, 1), len(line))
        y_shifts = np.random.choice(range(-3, 3, 1), len(line))
        for c_num, c in enumerate(line):
            c_array = letters_dict.get(c)
            c_array = np.roll(c_array, shift=x_shifts[c_num], axis=0)
            c_array = np.roll(c_array, shift=y_shifts[c_num], axis=1)
            characters.append(c_array)
        # characters = [letters_dict.get(c) for c in line]
        left_num = canvas.shape[1] - len(characters) * letter_w
        if left_num > 0:
            left = np.zeros((letter_h, left_num, 3))
            characters.append(left)
        line_array = np.concatenate(characters, axis=1)
        row = num * 40
        canvas[row: row + 40, :, :] = line_array
    return canvas


if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = sys.argv[1]
        outfile = sys.argv[2]
    else:
        sys.stderr.write("Usage: {} \"your text\"\n".format(sys.argv[0]))
        sys.exit(0)
    text_pic = make_text(text, "BEBAS")
    io.imsave(outfile, text_pic)
