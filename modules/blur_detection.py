#!/usr/bin/env python3
"""Make blur map."""
import argparse
from skimage import io
from skimage import transform as tf
from skimage import color
import numpy as np


def parse_args():
    """Parse and check args."""
    app = argparse.ArgumentParser()
    app.add_argument("input", type=str, help="Input image.")
    app.add_argument("output", type=str, help="Output file.")
    app.add_argument("--kernel_size", type=int, default=8)
    args = app.parse_args()
    return args


def detect_blur(im, kernel_size=8):
    """For an image of size W * H return blur map."""
    w, h, d = im.shape
    grey = color.rgb2gray(im)
    blur_map = np.zeros((w, h))
    for i in range(w - kernel_size):
        for j in range(h - kernel_size):
            kernel = grey[i: i + kernel_size, j: j + kernel_size]
            kernel_std = kernel.std() / 5
            blur_map[i: i + kernel_size, j: j + kernel_size] += kernel_std
    blur_map[blur_map > 1] = 1.0
    return blur_map


if __name__ == "__main__":
    args = parse_args()
    im = tf.resize(io.imread(args.input), (600, 800))
    blur_map = detect_blur(im, args.kernel_size)
    io.imsave(args.output, blur_map)
