"""Filters collection for gleitzsch."""
import random
import numpy as np
from skimage import exposure
from skimage import transform as tf
from skimage import filters
from skimage import color


def parts(lst, n=25):
    """Split an iterable into list of iterables of size n."""
    return [lst[i:i + n] for i in iter(range(0, len(lst), n))]


def adjust_contrast(im, l_p, r_p):
    """Contrast correction."""
    perc_left, perc_right = np.percentile(im, (l_p, r_p))
    im = exposure.rescale_intensity(im, in_range=(perc_left, perc_right))
    return im


def xyz_shift(img, kt):
    """Apply chromatic aberration."""
    img = color.rgb2xyz(img)
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
    new_im = color.xyz2rgb(new_im)
    return new_im


def rgb_shift(img, kt):
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


def __bayer(im):
    """Make monochrome pixels."""
    h, w, d = im.shape
    for i in range(h):
        for j in range(w):
            channels_to_rm = np.random.choice(range(3), size=2, replace=False)
            im[i][j][channels_to_rm[0]] = 0.0
            im[i][j][channels_to_rm[1]] = 0.0
    return im


def _bayer(im):
    """Apply bayer filter to the image."""
    w, h, d = im.shape
    for i in range(0, w, 2):
        for j in range(0, h, 2):
            im[i, j][0], im[i, j][2] = 0.0, 0.0
            im[i, j][1] /= 2.0
            try:
                im[i + 1, j][0], im[i + 1, j][1] = 0.0, 0.0
                im[i, j + 1][1], im[i, j + 1][2] = 0.0, 0.0
                im[i + 1, j + 1][0], im[i + 1, j + 1][2] = 0.0, 0.0
                im[i + 1, j + 1][1] /= 2.0
            except IndexError:
                pass  # we are out of the array
    return im


def bayer(im):
    """It is not a bayer filter anymore actually."""
    w, h, d = im.shape
    imlen = w * h * d
    pix_num = w * h
    chan_numbers = np.random.choice([0, 1, 2], pix_num)
    im_flat, new_im_flat = np.reshape(im, imlen), []
    # new_im_flat = [im_flat[i] if yes_not[i] == 1 else 0.0 for i in range(imlen)]
    for num, pixel in enumerate(parts(im_flat, n=3)):
        color = [0.0, 0.0, 0.0]
        chan_num = chan_numbers[num]
        color[chan_num] = pixel[chan_num]
        new_im_flat.extend(color)
    print(len(new_im_flat))
    new_im = np.reshape(np.array(new_im_flat), (w, h, d))
    return new_im


def _bayer(im):
    """It is not a bayer filter anymore actually."""
    w, h, d = im.shape
    imlen = w * h * d
    # yes_not = np.random.choice([0, 1], imlen, p=[0.1, 0.9])
    chan_numbers = np.random.choice([0, 1, 2], imlen)
    im_flat, new_im_flat = np.reshape(im, imlen), []
    # new_im_flat = [im_flat[i] if yes_not[i] == 1 else 0.0 for i in range(imlen)]
    for i in range(imlen):
        chan = chan_numbers[i]
        if chan == 0:
            color = [im_flat[0], 0, 0]
        elif chan == 1:
            color = [0, im_flat[1], 0]
        else:
            color = [0, 0, im_flat[2]]
        new_im_flat.extend(color)
    new_im = np.reshape(np.array(new_im_flat), (w, h, d))
    return new_im


def amplify(im):
    """Self-overlap."""
    REPEATS = 0
    shift = int(np.random.uniform(low=30, high=130))
    sign = np.random.choice([-1, 1], 1)[0]
    shift *= sign
    print(shift)
    delim, kt = 1, 3
    layer_sh = np.roll(a=im, axis=1, shift=shift) / kt
    im += layer_sh
    delim += 1 / kt
    kt /= 3

    for _ in range(REPEATS):
        layer_sh = np.roll(a=layer_sh, axis=1, shift=shift) / kt
        im += layer_sh
        delim += 1 / kt
        kt /= 3

    im /= delim
    # im[im > 1] = 1.0
    return im


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
            im[dot[0] - 1: dot[0], dot[1] - 3: dot[1] + 3, :] = 1
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
    new_im = rgb_shift(im, kt=88)
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


def interlace(im, zero_prob=0.9):
    """Add interlacing fields."""
    w, h, d = im.shape
    coeff, processed = 3, []
    shift_wide = 2
    # zero_prob = 0.9
    # half_prob = 0.05
    half_prob = (1 - zero_prob) / 2
    half_probs = [half_prob / shift_wide for _ in range(shift_wide)]
    shift_probs = half_probs + [zero_prob] + half_probs
    shif_pos = list(range(- shift_wide, shift_wide + 1))
    shift = 0

    for num, i in enumerate(range(0, w, coeff)):
        row = im[i: i + coeff + 1, :, :]
        row = row / 1.05 if num % 2 == 0 else row
        shift_p = np.random.choice(shif_pos, 1, p=shift_probs)[0]
        shift += shift_p
        row = np.roll(a=row, axis=0, shift=shift)  # small part
        row = np.roll(a=row, axis=1, shift=shift)  # long size
        # row = np.roll(a=row, axis=2, shift=shift_p)  # color
        processed.append(row)

    merge = np.concatenate(processed, axis=0)
    merge = tf.resize(merge, (w, h))
    return merge


def add_vertical(image):
    """Hard to say."""
    first_row = np.reshape(image[0, :, :], newshape=(1, image.shape[1], image.shape[2]))
    stretch = np.repeat(first_row, image.shape[0], axis=0)
    # stretch[stretch > 0.95] = 0
    add = image + stretch / 10
    add[add > 1] = 1.0
    return add

