import numpy as np
from scipy import fftpack
# import matplotlib.pyplot as plt


def quantize(x, bits):
    """Low quality part"""
    m = max(abs(x))
    y = x / m
    y = np.floor((2 ** bits - 1) * y / 2)
    return m * 2 * y / (2 ** bits - 1)


def compress_sound(im):
    """Compress and decompress pseudo-sound.

    Based on the:
    http://www.math.kent.edu/~reichel/courses/intr.num.comp.1/fall09/lecture14/lecture14.pdf
    """
    w, h, d = im.shape
    # R = 44100
    b = np.reshape(im, newshape=(w * h * d))
    print(b)
    # sound_array = np.around(sound_array * 255, decimals=0)
    # sound_array[sound_array > 255] = 255
    # sound_array[sound_array < 0] = 0
    # b = list(map(int, sound_array))
    # N = len(b)

    c = fftpack.dct(b)
    # w = np.sqrt(2 / N)
    # f = np.linspace(0, R / 2, N)
    # plt.plot(f, w * c)

    # cutoff = 50
    # mask = [abs(w * c) < cutoff]
    # low = np.reshape(mask * c, N)
    # high = np.reshape([not mask] * c, N)
    # plt.plot(f, w * high, "r--", f, w * low, "bs")

    lowbits = 8
    low = quantize(c, lowbits)
    y = fftpack.idct(low)
    y_min, y_max = y.min(), y.max()
    y -= y_min
    y /= (y_max - y_min)
    # plt.savefig("foo.png")
    glitched = np.reshape(y, newshape=(w, h, d))
    return glitched
