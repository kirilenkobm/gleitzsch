import sys
import numpy as np
from numpy cimport ndarray
cimport numpy as np
cimport cython

DTYPE = np.float
ctypedef np.float_t DTYPE_t


cdef extern from "math.h":
    double sqrt(double m)


@cython.boundscheck(False)
def cyOptStdDev(ndarray[np.float64_t, ndim=1] a not None):
    cdef Py_ssize_t i
    cdef Py_ssize_t n = a.shape[0]
    cdef double m = 0.0
    for i in range(n):
        m += a[i]
    m /= n
    cdef double v = 0.0
    for i in range(n):
        v += (a[i] - m)**2
    return sqrt(v / n)


@cython.boundscheck(False) # turn off bounds-checking for entire function
@cython.wraparound(False)  # turn off negative index wrapping for entire function
def detect_blur(ndarray[DTYPE_t, ndim=2] im, int kernel_size=8):
    """For an image of size W * H return blur map."""
    cdef int w = im.shape[0]  # grayscale image is the must!
    cdef int h = im.shape[1]
    # grey = color.rgb2gray(im)
    cdef ndarray[DTYPE_t, ndim=2] blur_map = np.zeros((w, h))
    # cdef ndarray[DTYPE_t, ndim=2] kernel = np.zeros((kernel_size, kernel_size))
    cdef float kernel_std

    for i in range(0, w - kernel_size, 2):
        for j in range(0, h - kernel_size, 2):
            # kernel = im[i: i + kernel_size, j: j + kernel_size]
            kernel_std = cyOptStdDev(np.reshape(im[i: i + kernel_size, j: j + kernel_size], kernel_size * kernel_size))
            # kernel_std = kernel.std() / 4
            # kernel_std = 0.0
            blur_map[i: i + kernel_size, j: j + kernel_size] += kernel_std
    blur_map[blur_map > 1] = 1.0
    return blur_map
