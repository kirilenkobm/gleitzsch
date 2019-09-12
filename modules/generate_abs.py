#!/usr/bin/env python3
"""Generate random abstract image."""
import numpy as np
from skimage import io
from skimage import draw
from skimage import filters
LINES_NUM = 0
SQUARE_FIELD = 60
SQ_X, SQ_Y = 2, 8


def make_abs(shape, x_shift=0, y_shift=0, skip_half=0, red=False):
    """Returns random image of the shape given."""
    canvas = np.zeros(shape)
    print(canvas.shape)
    x_0, x_sigma = shape[0] / 2 + x_shift, shape[0] / 10
    y_0, y_sigma = shape[1] / 2 + y_shift, shape[1] / 10
    x_1s = np.random.normal(x_0, x_sigma, LINES_NUM)
    y_1s = np.random.normal(y_0, y_sigma, LINES_NUM)
    for i in range(LINES_NUM):
        color = np.random.choice([0.1, 0.3, 1.0], 3, replace=True) if not red else [1.0, 0.0, 0.0]
        # print(color)
        x_1 = int(x_1s[i])
        y_1 = int(y_1s[i])
        try:
            k = (y_0 - y_1) / (x_0 - x_1)
            b = y_1 - k * x_1
            x_1 = x_0 + 10 if x_1 == x_0 else x_1
            x_inf = int(shape[0] if x_1 > x_0 else 0)
            y_inf = int(k * x_inf + b)
            rr_raw, cc_raw, val_raw = draw.line_aa(x_1, y_1, x_inf, y_inf)
            rr, cc, val = [], [], []
            for elem in zip(rr_raw, cc_raw, val_raw):
                if elem[0] < 0 or elem[1] < 0:
                    continue
                elif elem[0] >= shape[0] or elem[1] >= shape[1]:
                    continue
                else:
                    rr.append(elem[0])
                    cc.append(elem[1])
                    val.append(elem[2])
            canvas[rr, cc] = color
        except ZeroDivisionError:
            pass  # happens
        except IndexError:
            pass  # also happens but should not
    # remove a half if required
    if skip_half == -1:
        canvas[[range(int(x_0))]] = 0
    elif skip_half == 1:
        canvas[[range(int(x_0), shape[0])]] = 0

    # get vertical lines
    tops = np.random.uniform(low=0, high=shape[1], size=SQUARE_FIELD)
    for i in range(SQUARE_FIELD):
        step_sh = np.random.choice(10, 1)[0]
        color = np.random.choice([0.1, 0.3, 1.0], 3, replace=True) if not red else [1.0, 0.0, 0.0]
        top = int(tops[i])
        bottom_frange = list(range(top - 29, top + 30))
        bottoms = [x for x in bottom_frange if 0 <= x < shape[1]]
        bottom = np.random.choice(bottoms, 1)[0]
        # print(shape[0], top, 0, bottom)
        rr, cc = draw.line(shape[0] - 1, top, 0, bottom)
        for num, point in enumerate(zip(rr, cc)):
            if (num + step_sh) % 15 != 0:
                continue
            r = [point[0] + SQ_X, point[0] + SQ_X, point[0] - SQ_X, point[0] - SQ_X]
            c = [point[1] + SQ_Y, point[1] - SQ_Y, point[1] - SQ_Y, point[1] + SQ_Y]
            rr, cc = draw.polygon(r, c, shape=canvas.shape)
            canvas[rr, cc] = color
    canvas = filters.gaussian(canvas, sigma=3)
    return canvas


if __name__ == "__main__":
    shape = (533, 800, 3)
    im = make_abs(shape)
    io.imsave("test_abs.jpg", im)
