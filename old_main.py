#!/usr/local/bin/python3
"""Entry point."""
import argparse
import sys
import os
from datetime import datetime as dt
import subprocess
import numpy as np
from skimage import io
from skimage import img_as_float
from skimage import transform as tf
from skimage import exposure
from modules.filters import adjust_contrast, rb_shift, glitter, make_rainbow
from modules.bytes_glitch import glitch_bytes
from modules.process_mp3 import process_mp3


def eprint(line, end="\n"):
    """Like print but for stdout."""
    sys.stderr.write(line + end)


def die(msg, rc=1):
    """Die with rc and show msg."""
    eprint(msg + "\n")
    sys.exit(rc)


def parse_args():
    """Parse and check args."""
    app = argparse.ArgumentParser()
    app.add_argument("input", type=str, help="Input image.")
    app.add_argument("output", type=str, help="Output file.")
    app.add_argument("--size", type=int, default=800, help="Long dimension, 800 as default.")
    app.add_argument("--temp_dir", type=str, default="temp", help="Directory to hold temp files.")
    app.add_argument("--blue_red_shift", "-b", type=int, default=16, help="use red/blue shift")
    app.add_argument("--shift", type=int, default=227, help="Horizontal shift correction, pixels.")
    app.add_argument("--gamma", "-g", type=float, default=0.5,
                     help="Gamma correction before mp3-ing. 0.5 as default.")
    app.add_argument("--right_pecrentile", "-r", type=int, default=98,
                     help="Contrast stretching, right percentile, 90 as default. "
                          "Int in range [left percentile..100]")
    app.add_argument("--left_pecrentile", "-l", type=int, default=2,
                     help="Contrast stretching, left percentile, 2 as default. "
                          "Int in range [0..right_percentile]")
    app.add_argument("--proc_sound", action="store_true", dest="proc_sound", help="Glitch at the mp3 sound level.")
    app.add_argument("--bytes", action="store_true", dest="bytes", help="Glitch at the image bytes level.")
    args = app.parse_args()
    # create temp dir if not exists
    os.mkdir(args.temp_dir) if not os.path.isdir(args.temp_dir) else None
    # TODO check if r_b is an even number
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
    im = tf.resize(image=matrix, output_shape=(int(matrix.shape[0] / scale_k), int(matrix.shape[1] / scale_k)))
    return im


def der_prozess(cmd):
    """Run process, die if fails."""
    eprint("Calling {0}".format(cmd))
    rc = subprocess.call(cmd, shell=True)
    if rc != 0:  # subprocess died
        die("Error! Command {0} failed.".format(cmd))


def process_channel(channel, num, temp_dir, proc_sound):
    """Process channel through mp3 converter."""
    temp_file = os.path.join(temp_dir, "initial_file.jpg")
    io.imsave(fname=temp_file, arr=channel)
    # get dimensions
    dim_cmd = """identify "{0}" | tr ' ' '\n' | egrep '[0-9]+x[0-9]+' | head -1 | tr x ' '""".format(temp_file)
    dimensions = subprocess.check_output(dim_cmd, shell=True).decode(encoding='utf-8')[:-1]

    # convert to a raw bytes file
    gray_file = os.path.join(temp_dir, "img.gray")
    convert_cmd = 'convert "{0}" {1}'.format(temp_file, gray_file)
    der_prozess(convert_cmd)

    # compress as mp3
    mp3_addr = os.path.join(temp_dir, "img.mp3")
    mp3_cmd = 'lame -r -s 32 -q 9 -m j --resample 32 --bitwidth 8 -b 8 -m m $* {0} "{1}"'.format(gray_file, mp3_addr)
    der_prozess(mp3_cmd)

    # modify the mp3
    process_mp3(mp3_addr, dimensions, chan_num=num) if proc_sound else None

    # decode mp3 to a raw bytes file
    decode_cmd = 'lame --decode -x -t "{0}" {1}'.format(mp3_addr, gray_file)
    der_prozess(decode_cmd)

    # restore the image
    pgm_addr = os.path.join(temp_dir, "img.pgm")
    restore_cmd = r"python restore_cmd.py {0} < {1} > {2}".format(dimensions, gray_file, pgm_addr)
    der_prozess(restore_cmd)

    # convert into a readable format
    png_addr = os.path.join(temp_dir, "img.png")
    png_cmd = 'convert {0} "{1}"'.format(pgm_addr, png_addr)
    der_prozess(png_cmd)

    # load the result
    new_channel = io.imread(png_addr)
    x, y = new_channel.shape[0], new_channel.shape[1]
    new_channel = np.resize(new_channel, (x, y, 1))

    # remove temp files
    temp_files = [temp_file, gray_file, mp3_addr, pgm_addr, png_addr]
    for tfile in temp_files:
        os.remove(tfile) if os.path.isfile(tfile) else None
    return new_channel


def main():
    """Main func."""
    t0 = dt.now()
    args = parse_args()
    # pre-process the image if required
    glitch_bytes(args.input) if args.bytes else None
    im = read_image(args.input, args.size)  # read image
    # correct gamma before mp3-ing
    im = exposure.adjust_gamma(image=im, gain=args.gamma)
    # split in channels and mp3 them separately
    red, green, blue = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    mp3d_chan = [process_channel(channel, num, args.temp_dir, args.proc_sound)
                 for num, channel in enumerate([red, green, blue])]
    mp3d_im = np.concatenate((mp3d_chan[0], mp3d_chan[1], mp3d_chan[2]), axis=2)
    # mp3 processing dramatically decreases contrast, let's increase it before the processing:
    im = adjust_contrast(mp3d_im, args.left_pecrentile, args.right_pecrentile)
    # apply aberration if required
    im = rb_shift(im, args.blue_red_shift) if args.blue_red_shift > 0 else im
    # apply rainbow
    # im = make_rainbow(im)
    # save img
    io.imsave(fname=args.output, arr=im)
    eprint("Estimated time: {0}".format(dt.now() - t0))
    sys.exit(0)


if __name__ == "__main__":
    main()
