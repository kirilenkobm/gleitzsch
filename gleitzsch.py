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
from modules import filters as fltrs
from skimage import color
from skimage import util
from modules.bytes_glitch import glitch_bytes
from modules.generate_abs import make_abs
from modules.make_text import make_text
# from modules import blur_detection
# from modules import audio_compression


__author__ = "Bogdan Kirilenko, 2018"
__version__ = 2.0
temp_files = []
# where the lame binary actually is
if os.name == "nt":  # windows
    LAME_BINARY = r".\lame.exe"
else:  # using linux/macos
    LAME_BINARY = "lame"
MP3_ITER_LIMIT = 10


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
    app.add_argument("--size", type=int, default=1000, help="Long dimension, 800 as default.")
    app.add_argument("--temp_dir", type=str, default="temp", help="Directory to hold temp files.")
    app.add_argument("--blue_red_shift", "-b", type=int, default=0, help="use red/blue shift")
    app.add_argument("--shift", type=int, default=-190, help="Horizontal shift correction, pixels.")
    app.add_argument("--gamma", "--gm", type=float, default=None,
                     help="Gamma correction before mp3-ing. 0.5 as default.")
    app.add_argument("--bayer", action="store_true", dest="bayer", help="Apply Bayer filter.")
    app.add_argument("--amplify", "-a", action="store_true", dest="amplify", help="Apply amplify filter.")
    app.add_argument("--figures", "-f", action="store_true", dest="figures", help="Draw random shapes.")
    app.add_argument("--right_pecrentile", "--rp", type=int, default=95,
                     help="Contrast stretching, right percentile, 90 as default. "
                          "Int in range [left percentile..100]")
    app.add_argument("--left_pecrentile", "--lp", type=int, default=10,
                     help="Contrast stretching, left percentile, 2 as default. "
                          "Int in range [0..right_percentile]")
    app.add_argument("--hue_shift", type=float, default=None, help="Change colors throw HSV space."
                                                                   "Float value from -1 to 1.")
    app.add_argument("--text", default=None, help="add some text")
    app.add_argument("--text_font", default="emboss", help="Text fond, emboss as default.")
    app.add_argument("--bytes", action="store_true", dest="bytes", help="Glitch at the image bytes level.")
    app.add_argument("--interlacing", "-i", action="store_true", dest="interlacing", help="Interlacing")
    app.add_argument("--vertical", action="store_true", dest="vertical", help="Vertical lines.")
    app.add_argument("--kHz", type=float, default=16, help="Mp3 resampling. Recommended values are: "
                     "15.98, 15.99, 16.0 (default), 16.01")
    app.add_argument("--sound_quality", "-q", default=9, help="Sound quality, 0..9")
    app.add_argument("--stripes", "-s", action="store_true", dest="stripes", help="stripes.")
    app.add_argument("--bitrate", default=16, type=int, help="Mp3 bitrate.")
    app.add_argument("--rainbow", "-r", action="store_true", dest="rainbow", help="Add rainbow.")
    app.add_argument("--magic", action="store_true", dest="magic", help="magic.")
    app.add_argument("--glitter", "-g", action="store_true", dest="glitter", help="Add some glitter.")
    app.add_argument("--v_streaks", "-v", action="store_true", dest="v_streaks", help="Add vertical streaks.")
    app.add_argument("--hor_shifts", "--hs", action="store_true", dest="hor_shifts", help="Add horizontal.. hm....")
    app.add_argument("--add_iterations", "--ai", default=0, type=int, help="Additional de/en-code cycles.")

    args = app.parse_args()
    # create temp dir if not exists
    os.mkdir(args.temp_dir) if not os.path.isdir(args.temp_dir) else None
    die("Error! --blue_red_shift must be an even number!") if args.blue_red_shift % 2 != 0 else None
    return args


def read_image(input, size):
    """Read image, return 3D array of a size requested."""
    die("Error! File {0} doesn't exist!".format(input)) if not os.path.isfile(input) else None
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
    # print(np.median(im))
    return 0.4


def der_prozess(cmd):
    """Run process, die if fails."""
    eprint("Calling {0}".format(cmd))
    devnull = open(os.devnull, 'w')
    rc = subprocess.call(cmd, shell=True, stderr=devnull)
    devnull.close()
    if rc != 0:  # subprocess died
        die("Error! Command {0} failed.".format(cmd))


def process_channel(channel, temp_dir, khz, bitrate, sound_quality):
    """Do in one step."""
    w, h, d = channel.shape
    channel_flat = np.reshape(channel, newshape=(w * h * d))
    int_form_nd = np.around(channel_flat * 255, decimals=0)
    int_form_nd[int_form_nd > 255] = 255
    int_form_nd[int_form_nd < 0] = 0
    int_form = list(map(int, int_form_nd))
    bytes_str = bytes(int_form)

    # define temp files | lame cannot work with stdin \ stdout
    raw_channel = os.path.join(temp_dir, "init_{0}.blob".format(id_gen()))
    mp3_compressed = os.path.join(temp_dir, "compr_{0}.mp3".format(id_gen()))
    mp3_decompressed = os.path.join(temp_dir, "decompr_{0}.mp3".format(id_gen()))
    temp_files.extend([raw_channel, mp3_compressed, mp3_decompressed])
    # temp_files.extend([raw_channel, mp3_decompressed])

    # define commands
    # bitrate 12 -- 32 is fine
    mp3_compr = '{lame} -r --unsigned -s {0} -q {1} --resample 16 --bitwidth 8 -b {2} -m m {3} "{4}"'\
        .format(khz, sound_quality, bitrate, raw_channel, mp3_compressed, lame=LAME_BINARY)
    mp3_decompr = '{lame} --decode -x -t "{0}" {1}'.format(mp3_compressed, mp3_decompressed, lame=LAME_BINARY)

    # write initial file | raw image
    with open(raw_channel, "wb") as f:
        f.write(bytes_str)

    # call lame
    der_prozess(mp3_compr)  # compress
    der_prozess(mp3_decompr)  # decompress

    # read decompressed file | get raw sequence
    with open(mp3_decompressed, "rb") as f:
        mp3_bytes = f.read()

    eprint("Compressed array of len {0}".format(len(bytes_str)))
    eprint("Decompressed array of len {0}".format(len(mp3_bytes)))
    proportion = len(mp3_bytes) // len(bytes_str)
    eprint("Proportion {0}".format(proportion))
    bytes_num = len(bytes_str) * proportion
    decompressed = mp3_bytes[:bytes_num]

    # get average of each bytes pair / return 0..1 range of values | return initial shape
    # glitched = np.array([(sum(pair) / proportion) / 255 for pair in parts(decompressed, n=proportion)])
    glitched = np.array([pair[0] / 255 for pair in parts(decompressed, n=proportion)])
    glitched = np.reshape(glitched, newshape=(w, h, d))
    # just in case
    glitched[glitched > 1] = 1.0
    glitched[glitched < 0] = 0.0
    # io.imsave("wat.jpg", glitched)
    return glitched


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
    im = (im + make_abs(im.shape, skip_half=0, x_shift=80, red=False)) if args.stripes else im
    im[im > 1.0] = 1.0
    # blurre = blur_detection.detect_blur(color.rgb2gray(im))

    im = fltrs.horizonal_shifts(im) if args.hor_shifts else im
    im = fltrs.vert_streaks(im) if args.v_streaks else im
    im = fltrs.add_figs(im) if args.figures else im
    im = fltrs.amplify(im) if args.amplify else im
    im = util.random_noise(im, mode="speckle")
    im = fltrs.color_shift(im, args.hue_shift) if args.hue_shift else im

    if args.text:
        if len(args.text.replace(" ", "")) == 0:
            eprint("Warning, empty sequence in text.")
        else:
            text_layer = make_text(args.text, args.text_font)
            text_h, text_w, _ = text_layer.shape
            new_text_w = int(shape[1] / 1.5)
            print(new_text_w)
            w_kt = text_w / new_text_w
            new_text_h = int(text_h / w_kt)
            text_layer = tf.resize(text_layer, (new_text_h, new_text_w))
            text_x = random.choice(range(new_text_h, shape[0] - new_text_h * 2))
            text_y = random.choice(range(20, shape[1] - (new_text_w + 50)))
            im[text_x: text_x + new_text_h, text_y: text_y + new_text_w, :] = text_layer

    im = fltrs.make_rainbow(im) if args.rainbow else im
    im = fltrs.glitter(im) if args.glitter else im
    im = exposure.adjust_gamma(image=im, gain=gamma)
    im = fltrs.bayer(im) if args.bayer else im
    im = fltrs.interlace(im) if args.interlacing else im
    im = fltrs.rgb_shift(im, args.blue_red_shift) if args.blue_red_shift > 0 else im
    # split in channels and mp3 them separately | concat channels back
    # red, green, blue = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    # mp3d_chan = [process_channel(channel, shape, args.temp_dir, args.kHz) for channel in [red, green, blue]]
    # mp3d_im = np.concatenate((mp3d_chan[0], mp3d_chan[1], mp3d_chan[2]), axis=2)

    # mp3d_im = audio_compression.compress_sound(im)
    mp3d_im = process_channel(im, args.temp_dir, args.kHz, args.bitrate, args.sound_quality)
    extra_iters = MP3_ITER_LIMIT if args.add_iterations >= MP3_ITER_LIMIT else args.add_iterations
    for i in range(extra_iters):  # repeatedly compress and decompress
        mp3d_im = process_channel(mp3d_im, args.temp_dir, 16.0, args.bitrate, args.sound_quality)
    args.shift = args.shift if extra_iters == 0 else args.shift * (1 + extra_iters)

    # mp3d_im = mp3d_im if not args.interlacing else interlace(mp3d_im)
    # stretch vertical bands if requred
    mp3d_im = fltrs.add_vertical(mp3d_im) if args.vertical else mp3d_im
    # mp3d_im = rgb_shift(mp3d_im, args.blue_red_shift) if args.blue_red_shift > 0 else mp3d_im
    # correct contrast + misc postprocess
    im = fltrs.adjust_contrast(mp3d_im, args.left_pecrentile, args.right_pecrentile)
    # correct shift
    im = np.roll(a=im, axis=1, shift=args.shift)
    im = fltrs.reconstruct(im, args.kHz)
    # save img
    io.imsave(fname=args.output, arr=im)
    # remove temp files
    for tfile in temp_files:
        os.remove(tfile) if os.path.isfile(tfile) else None
    eprint("Estimated time: {0}".format(dt.now() - t0))
    sys.exit(0)


if __name__ == "__main__":
    main()
