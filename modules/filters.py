"""Filters collection for gleitzsch."""
import sys
import random
import numpy as np
from skimage import exposure
from skimage import transform as tf
from skimage import filters
from skimage import color
from skimage.draw import polygon
# from modules.blur_detection import detect_blur


def eprint(line, end="\n"):
    """Like print but for stdout."""
    sys.stderr.write(line + end)


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


def color_shift(im, val):
    """Change color throw HSV space."""
    im_hsv = color.rgb2hsv(im)
    hue = im_hsv[:, :, 0]
    hue += val
    hue[hue > 1] = hue[hue > 1] - 1
    hue[hue < 0] = hue[hue < 0] + 1
    im_hsv[:, :, 0] = hue
    im_rgb = color.hsv2rgb(im_hsv)
    return im_rgb


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


def vert_streaks(im):
    """Add some vertical streaks on image."""
    w, h, d = im.shape
    processed = []
    streaks_borders_num = random.choice(range(6, 16, 2))
    streaks_borders = [0] + list(sorted(np.random.choice(range(h), streaks_borders_num, replace=False))) + [h]
    for num, border in enumerate(streaks_borders[1:]):
        prev_border = streaks_borders[num]
        pic_piece = im[:, prev_border: border, :]
        if num % 2 != 0:  # don't touch this part
            processed.append(pic_piece)
            continue
        piece_h, piece_w, _ = pic_piece.shape
        piece_rearranged = []
        shifts_raw = sorted([i if i > 0 else -i for i in map(int, np.random.normal(5, 10, piece_w))])
        shifts_add = np.random.choice(range(-5, 2), piece_w)
        shifts_mod = [shifts_raw[i] + shifts_add[i] for i in range(piece_w)]
        # shift_probs = [i / sum(range(22)) for i in range(22)]
        # shifts_raw = sorted(np.random.choice(range(22), piece_w, p=shift_probs))
        shifts_left = [shifts_mod[i] for i in range(0, piece_w, 2)]
        shifts_right = sorted([shifts_mod[i] for i in range(1, piece_w, 2)], reverse=True)
        shifts = shifts_left + shifts_right
        for col_num, col_ind in enumerate(range(piece_w)):
            col = pic_piece[:, col_ind: col_ind + 1, :]
            col = np.roll(col, axis=0, shift=shifts[col_num])
            piece_rearranged.append(col)
        piece_shifted = np.concatenate(piece_rearranged, axis=1)
        processed.append(piece_shifted)
    new_im = np.concatenate(processed, axis=1)
    new_im = tf.resize(new_im, (w, h))
    return new_im


def horizonal_shifts(im, colorized=True):
    """Add random horizontal shifts."""
    w, h, d = im.shape
    processed = []
    shifts_borders_num = random.choice(range(6, 16, 2))
    shifts_borders = [0] + list(sorted(np.random.choice(range(w), shifts_borders_num, replace=False))) + [h]
    for num, border in enumerate(shifts_borders[1:]):
        prev_border = shifts_borders[num]
        pic_piece = im[prev_border: border, :, :]
        shift = 0 if num % 2 != 0 else random.choice(range(40))
        shifted = np.roll(pic_piece, shift=shift, axis=1)
        shifted = shifted if not colorized else np.roll(shifted, shift=shift, axis=2)
        processed.append(shifted)
    new_im = np.concatenate(processed, axis=0)
    new_im = tf.resize(new_im, (w, h))
    return new_im


def _vert_streaks(im, kernel=1, partial=False):
    """Add some vertical streaks on image."""
    w, h, d = im.shape
    processed = []
    shifts = np.random.choice([-2, -1, 0, 1, 2], h)
    current_shift = 0
    change_points = np.random.choice([False, True], h, p=[0.97, 0.03]) if partial else [0 for _ in range(h)]
    point = True
    for num, i in enumerate(range(0, h, kernel)):
        change_ = change_points[num]
        point = not point if change_ else point
        col = im[:, i: i + kernel + 1, :]
        if not point:
            processed.append(col)
            current_shift = 0
            continue
        current_shift += shifts[num]
        col = np.roll(col, axis=0, shift=current_shift)
        processed.append(col)
    merge = np.concatenate(processed, axis=1)
    merge = tf.resize(merge, (w, h))
    return merge


def add_magic(im):
    """Add some magic."""
    eprint("detecting blur...")
    w, h, d = im.shape
    blur_map_layer = np.reshape(detect_blur(im, kernel_size=8), (w, h, 1))
    blur_map_layer = filters.gaussian(blur_map_layer, sigma=5)
    blur_map = np.concatenate((blur_map_layer, blur_map_layer, blur_map_layer), axis=2)
    blur_map[blur_map < 0] = 0.0
    blur_map[blur_map > 1] = 1.0
    eprint("blur detected")
    magic_layer = im
    magic_layer = rgb_shift(magic_layer, kt=28)
    magic_layer = vert_streaks(magic_layer)
    magic_layer = filters.gaussian(magic_layer, sigma=3)
    magic_layer -= blur_map
    magic_layer[magic_layer < 0] = 0.0
    im += magic_layer
    im[im > 1] = 1.0
    return im


def add_figs(im):
    """Add random shapes."""
    figs = np.zeros((im.shape[0], im.shape[1], 3))
    wide = np.random.choice(range(10, 200), 1)[0]
    poly = np.array((
        (0, 0),
        (0, wide),
        (1000, wide),
        (1000, 0),
    ))
    rr, cc = polygon(poly[:, 0], poly[:, 1], figs.shape)
    figs[rr, cc, 0] = 0.7
    figs[rr, cc, 1] = 0.1
    figs[rr, cc, 2] = 0.2
    # figs = interlace(figs, zero_prob=0.85)
    figs = np.roll(figs, shift=np.random.choice(range(1000), 1)[0], axis=1)
    figs = filters.gaussian(figs, sigma=5, multichannel=True, mode='reflect', cval=0.6)
    im += figs
    im[im > 1.0] = 1.0
    return im


def reconstruct(im, kHz):
    """Reconstruct shifted rows."""
    if kHz == 16.0:
        return im
    w, h, d = im.shape
    processed = []
    for num, i in enumerate(range(0, w, 1)):
        row = im[i: i + 1, :, :]
        if kHz == 16.01:
            shift = int(num * 0.5)
        elif kHz == 15.99:
            shift = int(num * -0.5)
        elif kHz == 15.98:
            shift = int(num * -1)
        else:
            shift = 0
        row = np.roll(a=row, axis=1, shift=shift)
        processed.append(row)
    merge = np.concatenate(processed, axis=0)
    merge = tf.resize(merge, (w, h))
    return merge


def increase_saturation(im):
    """Increase saturation."""
    hsl_im = color.rgb2hsv(im)
    # hsl_im[:, :, 0] /= 2
    # hsl_im[:, :, 0] += 0.1
    hsl_im[:, :, 1] *= 1.45
    # hsl_im[:, :, 2] *= 1
    hsl_im[hsl_im > 1] = 1.0
    im = color.hsv2rgb(hsl_im)
    return im
