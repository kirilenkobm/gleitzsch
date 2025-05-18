//
//  FFTShader.metal
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

// FFTShader.metal
#include <metal_stdlib>
using namespace metal;

#define N 512

uint bitReverse9(uint x) {
    x = ((x & 0xAA) >> 1) | ((x & 0x55) << 1);
    x = ((x & 0xCC) >> 2) | ((x & 0x33) << 2);
    x = ((x & 0xF0) >> 4) | ((x & 0x0F) << 4);
    return ((x >> 1) & 0xFF) | ((x & 1) << 8);
}

kernel void fft1D_512(
    device float* data [[buffer(0)]],
    uint rowIndex [[thread_position_in_grid]]) {

    if (rowIndex >= N) return;

    float real[N];
    float imag[N];

    // Load row from global buffer
    for (uint i = 0; i < N; ++i) {
        real[i] = data[rowIndex * N + i];
        imag[i] = 0.0;
    }

    // Bit-reversal reorder
    float rTemp[N], iTemp[N];
    for (uint i = 0; i < N; ++i) {
        uint j = bitReverse9(i);
        rTemp[i] = real[j];
        iTemp[i] = imag[j];
    }

    for (uint i = 0; i < N; ++i) {
        real[i] = rTemp[i];
        imag[i] = iTemp[i];
    }

    // Cooley–Tukey FFT
    for (uint s = 1; s <= 9; ++s) {
        uint m = 1 << s;
        uint m2 = m >> 1;
        float theta = -2.0 * 3.141592653589793 / float(m);

        for (uint k = 0; k < N; k += m) {
            for (uint j = 0; j < m2; ++j) {
                float wReal = cos(theta * j);
                float wImag = sin(theta * j);

                uint i = k + j;
                uint l = i + m2;

                float tReal = wReal * real[l] - wImag * imag[l];
                float tImag = wReal * imag[l] + wImag * real[l];

                float uReal = real[i];
                float uImag = imag[i];

                real[i] = uReal + tReal;
                imag[i] = uImag + tImag;

                real[l] = uReal - tReal;
                imag[l] = uImag - tImag;
            }
        }
    }

    // Write result back (real part only)
    for (uint i = 0; i < N; ++i) {
        data[rowIndex * N + i] = real[i];
    }
}

kernel void ifft1D_512(
    device float* data [[buffer(0)]],
    uint rowIndex [[thread_position_in_grid]]) {

    if (rowIndex >= N) return;

    float real[N];
    float imag[N];

    // Load row
    for (uint i = 0; i < N; ++i) {
        real[i] = data[rowIndex * N + i];
        imag[i] = 0.0;
    }

    // Bit-reversal
    float rTemp[N], iTemp[N];
    for (uint i = 0; i < N; ++i) {
        uint j = bitReverse9(i);
        rTemp[i] = real[j];
        iTemp[i] = imag[j];
    }

    for (uint i = 0; i < N; ++i) {
        real[i] = rTemp[i];
        imag[i] = iTemp[i];
    }

    // Cooley–Tukey IFFT
    for (uint s = 1; s <= 9; ++s) {
        uint m = 1 << s;
        uint m2 = m >> 1;
        float theta = 2.0 * 3.141592653589793 / float(m);

        for (uint k = 0; k < N; k += m) {
            for (uint j = 0; j < m2; ++j) {
                float wReal = cos(theta * j);
                float wImag = sin(theta * j);

                uint i = k + j;
                uint l = i + m2;

                float tReal = wReal * real[l] - wImag * imag[l];
                float tImag = wReal * imag[l] + wImag * real[l];

                float uReal = real[i];
                float uImag = imag[i];

                real[i] = uReal + tReal;
                imag[i] = uImag + tImag;

                real[l] = uReal - tReal;
                imag[l] = uImag - tImag;
            }
        }
    }

    // Normalize
    for (uint i = 0; i < N; ++i) {
        data[rowIndex * N + i] = real[i] / float(N);
    }
}
