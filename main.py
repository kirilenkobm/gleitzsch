#!/usr/bin/env python3
"""Entry point."""
import argparse
import sys
import os
from datetime import datetime as dt
import subprocess
import string
import random
import numpy as np
from skimage import io
from skimage import img_as_float
from skimage import transform as tf
from skimage import exposure
from modules.filters import adjust_contrast, rb_shift, glitter, make_rainbow
from modules.bytes_glitch import glitch_bytes


__author__ = "Bogdan Kirilenko, 2018"
__version__ = 2.0
temp_files = []
# where the lame binary actually is
if os.name == "nt":  # windows
    LAME_BINARY = r".\lame.exe"
else:  # using linux/macos
    LAME_BINARY = "lame"


def eprint(line, end="\n"):
    """Like print but for stdout."""
    sys.stderr.write(line + end)


def die(msg, rc=1):
    """Die with rc and show msg."""
    eprint(msg + "\n")
    for tfile in temp_files:
        os.remove(tfile) if os.path.isfile(tfile) else None
    sys.exit(rc)


def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
    """Return random string for temp files."""
    return "".join(random.choice(chars) for _ in range(size))


def parts(lst, n=25):
    """Split an iterable into a list of lists of len n."""
    return [lst[i:i + n] for i in iter(range(0, len(lst), n))]


def parse_args():
    """Parse and check args."""
    app = argparse.ArgumentParser()
    app.add_argument("input", type=str, help="Input image.")
    app.add_argument("output", type=str, help="Output file.")
    app.add_argument("--size", type=int, default=800, help="Long dimension, 800 as default.")
    app.add_argument("--temp_dir", type=str, default="temp", help="Directory to hold temp files.")
    app.add_argument("--blue_red_shift", "-b", type=int, default=0, help="use red/blue shift")
    app.add_argument("--shift", type=int, default=230, help="Horizontal shift correction, pixels.")
    app.add_argument("--gamma", "-g", type=float, default=None,
                     help="Gamma correction before mp3-ing. 0.5 as default.")
    app.add_argument("--right_pecrentile", "-r", type=int, default=95,
                     help="Contrast stretching, right percentile, 90 as default. "
                          "Int in range [left percentile..100]")
    app.add_argument("--left_pecrentile", "-l", type=int, default=10,
                     help="Contrast stretching, left percentile, 2 as default. "
                          "Int in range [0..right_percentile]")
    app.add_argument("--proc_sound", action="store_true", dest="proc_sound", help="Glitch at the mp3 sound level.")
    app.add_argument("--bytes", action="store_true", dest="bytes", help="Glitch at the image bytes level.")
    app.add_argument("--vertical", action="store_true", dest="vertical", help="Vertical lines.")
    app.add_argument("--kHz", type=float, default=16)
    args = app.parse_args()
    # create temp dir if not exists
    os.mkdir(args.temp_dir) if not os.path.isdir(args.temp_dir) else None
    die("Error! --blue_red_shift must be an even number!") if args.blue_red_shift % 2 !=0 else None
    return args


def read_image(input, size):
    """Read image, return 3D array of a size requested."""
    matrix = img_as_float(io.imread(input))
    if len(matrix.shape) == 3:
        pass  # it's a 3D array already
    elif len(matrix.shape) == 2:
        # case if an image is 2D, make it 3D
        layer = np.reshape(matrix, (matrix.shape[0], matrix.shape[1], 1))
        matrix = np.concatenate((layer, layer, layer), axis=2)
    else:
        die("Image is corrupted.")
    # rescale the image
    scale_k = max(matrix.shape[0], matrix.shape[1]) / size
    new_w = int(matrix.shape[0] / scale_k)
    new_h = int(matrix.shape[1] / scale_k)
    im = tf.resize(image=matrix, output_shape=(new_w, new_h))
    return im, (new_w, new_h)


def auto_gamma(im):
    """Return the most suitable gamma for this situation."""
    # TODO
    print(np.median(im))
    return 0.4


def der_prozess(cmd):
    """Run process, die if fails."""
    eprint("Calling {0}".format(cmd))
    devnull = open(os.devnull, 'w')
    rc = subprocess.call(cmd, shell=True, stderr=devnull)
    devnull.close()
    if rc != 0:  # subprocess died
        die("Error! Command {0} failed.".format(cmd))


def process_channel(channel, shape, temp_dir, khz):
    """Process channel through mp3 converter."""
    channel_flat = np.reshape(channel, newshape=(shape[0] * shape[1]))
    # transform to 0 - 255 array of integers
    int_form = np.around(channel_flat * 255, decimals=0)
    int_form[int_form > 255] = 255
    int_form[int_form < 0] = 0
    pseudo_bytes = bytearray(map(int, int_form))
    eprint("Raw array of len {0} and shape {1}".format(len(pseudo_bytes), shape))

    # define temp files | lame cannot work with stdin \ stdout
    raw_channel = os.path.join(temp_dir, "init_{0}.jpg".format(id_gen()))
    mp3_compressed = os.path.join(temp_dir, "compr_{0}.mp3".format(id_gen()))
    mp3_decompressed = os.path.join(temp_dir, "decompr_{0}.mp3".format(id_gen()))
    temp_files.extend([raw_channel, mp3_compressed, mp3_decompressed])

    # define commands
    mp3_compr = '{lame} -r --unsigned -s {0} -q 9 --resample 18 --bitwidth 8 -b 12 -m m {1} "{2}"'\
        .format(khz, raw_channel, mp3_compressed, lame=LAME_BINARY)
    mp3_decompr = '{lame} --decode -x -t "{0}" {1}'.format(mp3_compressed, mp3_decompressed, lame=LAME_BINARY)

    # write initial file | raw image
    with open(raw_channel, "wb") as f:
        f.write(pseudo_bytes)

    # call lame
    der_prozess(mp3_compr)  # compress
    der_prozess(mp3_decompr)  # decompress

    # read decompressed file | get raw sequence
    with open(mp3_decompressed, "rb") as f:
        mp3_bytes = f.read()
    eprint("Decompressed array of len {0}".format(len(mp3_bytes)))
    proportion = len(mp3_bytes) // len(pseudo_bytes)
    eprint("Proportion {0}".format(proportion))
    bytes_num = len(pseudo_bytes) * proportion
    decompressed = mp3_bytes[:bytes_num]

    # get average of each bytes pair / return 0..1 range of values | return initial shape
    # glitched = np.array([(sum(pair) / proportion) / 255 for pair in parts(decompressed, n=proportion)])
    glitched = np.array([pair[0] / 255 for pair in parts(decompressed, n=proportion)])
    glitched = np.reshape(glitched, newshape=(shape[0], shape[1], 1))
    # just in case
    glitched[glitched > 1] = 1.0
    glitched[glitched < 0] = 0.0
    return glitched


def add_vertical(image):
    """Hard to say."""
    first_row = np.reshape(image[0, :, :], newshape=(1, image.shape[1], image.shape[2]))
    stretch = np.repeat(first_row, image.shape[0], axis=0)
    add = image + stretch / 10
    add[add > 1] = 1.0
    return add


def main():
    """Main func."""
    t0 = dt.now()
    args = parse_args()
    if args.bytes:  # apply glitch to bytes
        temp_bytes = os.path.join(args.temp_dir, "bytes_{0}.jpg".format(id_gen()))
        temp_files.append(temp_bytes)
        glitch_bytes(args.input, temp_bytes)
        im_addr = temp_bytes
    else:  # is not required
        im_addr = args.input
    # read image, preprocess it
    im, shape = read_image(im_addr, args.size)  # read image
    gamma = args.gamma if args.gamma else auto_gamma(im)
    im = exposure.adjust_gamma(image=im, gain=gamma)
    im = rb_shift(im, args.blue_red_shift) if args.blue_red_shift > 0 else im
    # split in channels and mp3 them separately | concat channels back
    red, green, blue = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    mp3d_chan = [process_channel(channel, shape, args.temp_dir, args.kHz) for channel in [red, green, blue]]
    mp3d_im = np.concatenate((mp3d_chan[0], mp3d_chan[1], mp3d_chan[2]), axis=2)
    # stretch vertical bands if requred
    mp3d_im = add_vertical(mp3d_im) if args.vertical else mp3d_im
    # correct contrast + misc postprocess
    im = adjust_contrast(mp3d_im, args.left_pecrentile, args.right_pecrentile)
    # correct shift
    im = np.roll(a=im, axis=1, shift=args.shift)
    # save img
    io.imsave(fname=args.output, arr=im)
    # remove temp files
    for tfile in temp_files:
        os.remove(tfile) if os.path.isfile(tfile) else None
    eprint("Estimated time: {0}".format(dt.now() - t0))
    sys.exit(0)


if __name__ == "__main__":
    main()
