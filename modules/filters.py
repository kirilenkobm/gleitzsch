"""Filters collection for gleitzsch."""
import random
import numpy as np
from skimage import exposure
from skimage import transform as tf
from skimage import filters
from skimage import color


def adjust_contrast(im, l_p, r_p):
    """Contrast correction."""
    perc_left, perc_right = np.percentile(im, (l_p, r_p))
    im = exposure.rescale_intensity(im, in_range=(perc_left, perc_right))
    return im


def rb_shift(img, kt):
    """Apply chromatic aberration."""
    shp = img.shape
    red = img[:, :, 0]
    green = img[:, :, 1]
    blue = img[:, :, 2]
    # split channels, make shift
    red = tf.resize(red, output_shape=(shp[0], shp[1]))
    green = tf.resize(green, output_shape=(shp[0] - kt, shp[1] - kt))
    blue = tf.resize(blue, output_shape=(shp[0] - 2 * kt, shp[1] - 2 * kt))

    w, h = blue.shape
    ktd2 = int(kt / 2)
    red_n = np.reshape(red[kt: -kt, kt: -kt], (w, h, 1))
    green_n = np.reshape(green[ktd2: -1 * ktd2, ktd2: -1 * ktd2], (w, h, 1))
    blue_n = np.reshape(blue[:, :], (w, h, 1))

    new_im = np.concatenate((red_n, green_n, blue_n), axis=2)
    new_im = tf.resize(new_im, (shp[0], shp[1]))
    return new_im


def glitter(im, alen=250):
    """Make glitter."""
    dots = []
    w, h, d = im.shape
    for i in range(alen):
        dx = random.choice(range(w))
        dy = random.choice(range(h))
        dots.append((dx, dy))

    for dot in dots:
        try:
            im[dot[0] - 1: dot[0], dot[1] - 3: dot[1] + 3, :] = -1
        except IndexError:
            pass

    return im


def black(im, thr):
    """Return two-colored bw image."""
    # get pixel sum (one number) instead of pixel (3 nums)
    col_sum = np.sum(im, axis=2)
    black_im = np.zeros((col_sum.shape[0], col_sum.shape[1]))
    # 0 - less than thr, 1 - more than
    black_im[col_sum > thr] = 1
    black_im = np.reshape(black_im, (black_im.shape[0], black_im.shape[1], 1))
    return np.concatenate((black_im, black_im, black_im), axis=2)


def remove_whites(im):
    """Diminish colors that are brighter than a threshold set. For an image."""
    col_sum = np.sum(im, axis=2)
    over_thr = np.reshape((col_sum - 2), (im.shape[0], im.shape[1], 1))
    over_thr = np.concatenate((over_thr, over_thr, over_thr), axis=2)
    new_im = np.where(over_thr > 0, im - over_thr, im)
    new_im[new_im < 0.0] = 0.0
    new_im[new_im > 1.0] = 1.0
    return new_im


def rainbow_layer(im):
    new_im = rb_shift(im, kt=88)
    new_im = filters.gaussian(new_im, sigma=30, multichannel=True, mode='reflect', cval=0.6)
    img_hsv = color.rgb2hsv(new_im)
    img_hsv[..., 1] *= 3
    img_hsv[..., 2] *= 1.4
    img_hsv[img_hsv >= 1.0] = 1.0
    new_im = color.hsv2rgb(img_hsv)
    new_im = remove_whites(new_im)
    return new_im


def make_rainbow(im):
    """Apply rainbow filter."""
    black_instance = black(im, thr=2.1)
    rainbow_pic = rainbow_layer(black_instance)
    rainbow_pic /= 2
    new_arr = rainbow_pic + im
    new_arr[new_arr > 1.0] = 1.0
    return new_arr
