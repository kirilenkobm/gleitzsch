// FFTShader.metal
#include <metal_stdlib>
using namespace metal;

#define N 512
inline uint bitReverse9(uint x) { return reverse_bits(x) >> 23; } // 32-9 = 23

inline uint hash_u32(uint x)                // very cheap LCG hash
{
    x ^= x >> 16;  x *= 0x7feb352d;
    x ^= x >> 15;  x *= 0x846ca68b;
    x ^= x >> 16;  return x;
}

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

kernel void alt_killBands_1D_512(device   float *real  [[buffer(0)]],
                                 device   float *imag  [[buffer(1)]],
                                 constant uint  &cutLo [[buffer(2)]],
                                 constant uint  &cutHi [[buffer(3)]],
                                 constant uint  &seed  [[buffer(4)]],   // frameSeed
                                 constant float &intensity [[buffer(5)]], // 0 … 1
                                 uint gid [[thread_position_in_grid]])
{
    uint  freq = gid % N;                       // 0 … 511
    if (freq == 0) return;                      // keep DC

    /* attenuation 0–1 (scaled by intensity) */
    float att = mix(1.0f,
                    0.0f,
                    smoothstep(float(cutLo), float(N - cutHi), float(freq)));
    att = mix(1.0f, att, intensity);           // intensity = 0 → no att

    /* random phase (scaled by intensity) */
    float phi = 6.2831853f *
                fract(float(hash_u32(freq + seed)) * 2.3283064e-10f) *
                intensity;                     // intensity = 0 → no shift

    float re = real[gid] * att;
    float im = imag[gid] * att;

    real[gid] =  re * cos(phi) - im * sin(phi);
    imag[gid] =  re * sin(phi) + im * cos(phi);
}

kernel void transpose512(device   float *src   [[buffer(0)]],
                         device   float *dst   [[buffer(1)]],
                         constant uint  &seed  [[buffer(2)]],
                         constant float &intensity [[buffer(3)]], // 0-1
                         uint2 tid [[thread_position_in_threadgroup]],
                         uint2 gid [[threadgroup_position_in_grid]])
{
    constexpr uint TILE = 16;
    threadgroup float tile[TILE][TILE+1];

    /* load */
    uint gx = gid.x * TILE + tid.x;
    uint gy = gid.y * TILE + tid.y;
    tile[tid.y][tid.x] = src[gy * 512 + gx];
    threadgroup_barrier(mem_flags::mem_threadgroup);

    /* transpose coords */
    gx = gid.y * TILE + tid.x;
    gy = gid.x * TILE + tid.y;

    /* VHS tweaks — scaled by intensity */
    float scanMul = 1.0f - (0.08f * intensity) * float(gy & 1);
    int   rawJit  = int(hash_u32(gy + seed) & 7) - 3;     // −3…+3
    int   jitter  = int(float(rawJit) * intensity);       // scale

    dst[gy * 512 + gx] = tile[tid.x][tid.y] * scanMul;

    uint jx = (uint)clamp(int(gx) + jitter, 0, 511);
    dst[gy * 512 + jx] = tile[tid.x][tid.y];
}
