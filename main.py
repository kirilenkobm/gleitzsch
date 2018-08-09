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
    args = app.parse_args()
    # create temp dir if not exists
    os.mkdir(args.temp_dir) if not os.path.isdir(args.temp_dir) else None
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
        die("Error! Command {0} failed.")


def process_channel(channel, temp_dir):
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
    mp3_cmd = 'lame -r -s 32 -q 9 -m j --resample 32 --bitwidth 8 -b 4 -m m $* {0} "{1}"'.format(gray_file, mp3_addr)
    der_prozess(mp3_cmd)

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
    im = read_image(args.input, args.size)  # read image
    red, green, blue = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    mp3d_chan = [process_channel(channel, args.temp_dir) for channel in [red, green, blue]]
    mp3d_im = np.concatenate((mp3d_chan[0], mp3d_chan[1], mp3d_chan[2]), axis=2)
    io.imsave(fname=args.output, arr=mp3d_im)
    eprint("Estimated time: {0}".format(dt.now() - t0))


if __name__ == "__main__":
    main()
