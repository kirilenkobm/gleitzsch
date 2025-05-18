// FFTShader.metal
#include <metal_stdlib>
using namespace metal;

#define N 512
inline uint bitReverse9(uint x) { return reverse_bits(x) >> 23; } // 32-9 = 23

/* ---------- FFT ---------- */
kernel void fft1D_512(device float *realOut [[buffer(0)]],
                      device float *imagOut [[buffer(1)]],
                      uint3  tidPos         [[thread_position_in_threadgroup]],
                      uint3  gidPos         [[threadgroup_position_in_grid]])
{
    uint tid  = tidPos.x;
    if (tid >= N) return;

    uint row  = gidPos.x;
    uint idx  = row * N + tid;

    uint rev  = bitReverse9(tid);

    threadgroup float real[N];
    threadgroup float imag[N];

    real[rev] = realOut[idx];
    imag[rev] = 0.0f;
    threadgroup_barrier(mem_flags::mem_threadgroup);

    /* 9 стадий бабочек */
    for (uint s = 1; s <= 9; ++s)
    {
        uint m  = 1u << s;
        uint m2 = m >> 1;
        float theta = -2.0f * M_PI_F / float(m);
        float wReal = cos(theta * float(tid & (m2 - 1)));
        float wImag = sin(theta * float(tid & (m2 - 1)));

        uint i = tid;
        uint j = tid ^ m2;            // «партнёр» в бабочке

        if ((tid & m2) == 0)
        {
            float tR = wReal * real[j] - wImag * imag[j];
            float tI = wReal * imag[j] + wImag * real[j];

            float uR = real[i];
            float uI = imag[i];

            real[i] = uR + tR;
            imag[i] = uI + tI;

            real[j] = uR - tR;
            imag[j] = uI - tI;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);
    }

    realOut[idx] = real[tid];
    imagOut[idx] = imag[tid];
}

/* ---------- iFFT ---------- */
kernel void ifft1D_512(device float *realIn  [[buffer(0)]],
                       device float *imagIn  [[buffer(1)]],
                       device float *output  [[buffer(2)]],
                       uint3  tidPos         [[thread_position_in_threadgroup]],
                       uint3  gidPos         [[threadgroup_position_in_grid]])
{
    uint tid = tidPos.x;
    if (tid >= N) return;

    uint row = gidPos.x;

    uint rev = bitReverse9(tid);
    uint src = row * N + rev;

    threadgroup float real[N];
    threadgroup float imag[N];

    real[tid] = realIn[src];
    imag[tid] = imagIn[src];
    threadgroup_barrier(mem_flags::mem_threadgroup);

    for (uint s = 1; s <= 9; ++s)
    {
        uint m  = 1u << s;
        uint m2 = m >> 1;
        float theta =  2.0f * M_PI_F / float(m);
        float wReal = cos(theta * float(tid & (m2 - 1)));
        float wImag = sin(theta * float(tid & (m2 - 1)));

        uint i = tid;
        uint j = tid ^ m2;

        if ((tid & m2) == 0)
        {
            float tR = wReal * real[j] - wImag * imag[j];
            float tI = wReal * imag[j] + wImag * real[j];

            float uR = real[i];
            float uI = imag[i];

            real[i] = uR + tR;
            imag[i] = uI + tI;

            real[j] = uR - tR;
            imag[j] = uI - tI;
        }
        threadgroup_barrier(mem_flags::mem_threadgroup);
    }

    output[row * N + tid] = real[tid] / float(N);
}

kernel void killBands_1D_512(device float *real   [[buffer(0)]],
                             device float *imag   [[buffer(1)]],
                             constant uint &cutLo [[buffer(2)]], // N_low
                             constant uint &cutHi [[buffer(3)]], // N_high
                             uint   gid           [[thread_position_in_grid]])
{
    uint freq = gid % N;
    if ((freq == 0) ||
        (freq >= cutLo && freq < N - cutHi)) {
    } else {
        real[gid] = imag[gid] = 0.0f;
    }
}


kernel void transpose512(device float *src [[buffer(0)]],
                         device float *dst [[buffer(1)]],
                         uint2  tid [[thread_position_in_threadgroup]],
                         uint2  gid [[threadgroup_position_in_grid]])
{
    // работаем плиткой 16×16 (ровно 512/32 = 16 групп)
    constexpr uint TILE = 16;
    threadgroup float tile[TILE][TILE+1];       // +1 чтобы избежать bank conflict

    uint gx = gid.x * TILE + tid.x;             // глобальные координаты
    uint gy = gid.y * TILE + tid.y;

    tile[tid.y][tid.x] = src[gy * 512 + gx];    // читаем
    threadgroup_barrier(mem_flags::mem_threadgroup);
    gx = gid.y * TILE + tid.x;                  // меняем местами
    gy = gid.x * TILE + tid.y;
    dst[gy * 512 + gx] = tile[tid.x][tid.y];    // пишем
}
