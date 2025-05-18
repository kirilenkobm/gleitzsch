# Gleitzsch

*real‑time glitch‑art camera for iOS*

Gleitzsch captures the live camera feed, runs it through a **Metal‑accelerated FFT glitch pipeline** and shows the result with <8 ms total latency on modern iPhones. The architecture is deliberately modular, so you can hot‑swap filters or add UI sliders without touching the core loop.

---

## 🔧 High‑level pipeline

```text
AVFoundation camera (NV12)
↓
CIImage  →  CGImage                 // oriented to `.right`
↓        resize to 512×512 (CPU)
FrameProcessor
↓
MetalFFTFilter (GPU)
   ├── transpose512        // row‑major → col‑major
   ├── fft1D_512           // 1‑D FFT per visual *column*
   ├── killBands_1D_512    // zero low / high freq bins
   ├── ifft1D_512          // inverse FFT
   └── transpose512        // col‑major → row‑major
↓
CGImage  →  SwiftUI
```

All heavy lifting (FFT + frequency surgery) happens on the GPU; the CPU only copies the RGB float array into a persistent Metal buffer and back.

---

## ⚙️  Metal filter details

| Step               | Kernel             | Notes                                                                                                                                                |
| ------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Transpose**      | `transpose512`     | 16×16 tiled transpose to turn columns into contiguous rows.                                                                                          |
| **FFT**            | `fft1D_512`        | Cooley‑Tukey radix‑2, unrolled for **N = 512**. Runs once per visual column (i.e. per original row).                                                 |
| **Kill Bands**     | `killBands_1D_512` | Zeros bins `< lowRatio·N` and `> (1‑highRatio)·N` on both real & imag. Defaults:<br> `lowRatio = 0`, `highRatio = 0.9` (kills top 90 % of spectrum). |
| **iFFT**           | `ifft1D_512`       | Same code base, reverse sign + `1/N` scale.                                                                                                          |
| **Transpose back** | `transpose512`     | Returns data to row‑major so the CPU can convert to CGImage.                                                                                         |

**Buffers are allocated once** and reused; no per‑frame `makeBuffer(bytes:)` calls.

```swift
/// Runtime knobs you can tweak from SwiftUI sliders
var lowRatio:  Float = 0.00   // kill low  freq bins (0…1)
var highRatio: Float = 0.90   // kill high freq bins (0…1)
```

---

## 🧠  Why *column* FFT?

The iPhone sensor delivers portrait‑native pixels. Applying 1‑D FFT **across columns** produces glitches that follow the natural orientation (horizontal artefacts when the phone is held upright). Two cheap transpose passes (<0.05 ms each) are faster than strided memory access in a column‑native FFT.

---

## 📈  Performance (iPhone 15 Pro)

* 512 × 512 RGB → GPU → back → display: **≈ 5.8 ms**
* Sustains **60 fps** with \~30 % A17 GPU utilisation.
* CPU stays <3 % because of persistent buffers.

---

## 🗺️  Directory map

```
Gleitzsch/
├── Processing/
│   ├── MetalFFTFilter.swift   # <— this file
│   ├── FFTShader.metal        # kernels listed above
│   ├── ImageFilters/…         # optional CPU filters (chromatic, gamma, …)
│   └── (legacy) FFTFilter.swift
├── Pipeline/FramePipeline.swift  # frame throttling & off‑main‑thread proc
├── Camera/CameraManager.swift    # AVFoundation capture
└── …
```

---

## 🚧  Roadmap

* Expose `lowRatio` / `highRatio` / phase‑shift as UI sliders.
* Record processed video (AVAssetWriter).
* LivePhoto support / App Clip demo.
* Generic “multi‑filter” graph once more GPU filters appear.

---

## 🕰️  Legacy / fallback CPU path

`FFTFilter.swift` (Accelerate/vDSP) still exists as a reference implementation and as a simulator fallback. It processes **rows** instead of columns and normalises each channel after iFFT.

Enable it by swapping the filter in **FrameProcessor**:

```swift
// graph.addFilter(MetalFFTFilter())
graph.addFilter(FFTFilter())
```

---

Happy glitching! ✨
