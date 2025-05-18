# Gleitzsch

*Gleitzsch* is an iOS app for real-time glitch-art camera effects. It captures frames from the camera, applies modular image processing filters (including FFT-based distortions), and renders the result to screen in real time.

Architecture is modular and designed for extensions such as additional filters, video capture, and configuration UI.

This README is intended for both human readers and LLMs to understand the system behavior and codebase structure.

---

## 🔧 Architecture Overview

The app processes camera frames through a streaming pipeline:

```
CameraManager
↓
CIImage (oriented right) → CGImage
↓
FrameProcessor
↓
FramePipeline
↓
CameraViewModel
↓
SwiftUI ContentView
```

All image processing is offloaded from the main thread. The UI observes the latest processed frame via @Published and renders it.

---

## ⚙️ Frame Flow

Each camera frame follows this transformation chain:

```
CIImage (oriented) → gamma correction
→ chromatic aberration
→ FFT glitch filter (applied row-wise)
→ iFFT → CGImage
```

Filters are composed in FrameProcessor.swift. The current pipeline includes:
    •    GammaFilter (placeholder)
    •    ColorFFTFilter (applies FFT/iFFT effects row-wise, preserving RGB)

Filters are modular and can be added/removed easily via the ProcessingGraph object.

## 🧠 FFT Glitch Details

The core FFT-based filter (ColorFFTFilter) processes each horizontal row (visually) of the image separately:
    •    Each RGB channel is extracted as a float array.
    •    Data is transposed so that FFT can be applied across horizontal image rows.
    •    A 1D FFT is applied to each row via vDSP_fft_zip.
    •    A frequency-domain glitch filter (e.g. KillLowFrequencies) is applied in-place.
    •    An inverse FFT (iFFT) is applied, and the result is normalized and reassembled into a new CGImage.

This row-wise FFT strategy enables glitch effects that are aligned with the visual structure of the image.

## 🧪 Device Orientation

- Frames are always captured in landscape.
- The UI elements (e.g. buttons) are rotated using `UIDevice.orientationDidChangeNotification`.
- Captured images are saved with correct `UIImageOrientation` (`.right`) for EXIF consistency.

---

## 📦 Project Structure

```
Gleitzsch/
├── Camera/             // CameraManager — raw frame capture and orientation
├── Processing/         // Image filters, including FFT-based ones
├── Pipeline/           // FramePipeline — connects camera to processing and publishing
├── ViewModels/         // CameraViewModel — binds frames to SwiftUI
├── Views/              // ContentView and UI components
├── Models/             // Optional helpers like FrameBuffer
├── Utils/              // Image conversion, normalization, extensions
├── GleitzschApp.swift  // App entry point
```

## 🧩 Key Classes and Responsibilities

| File / Class                     | Role                                                                 |
|----------------------------------|----------------------------------------------------------------------|
| `CameraManager.swift`            | Captures camera frames using AVFoundation, orients them `.right`    |
| `FramePipeline.swift`            | Connects camera to processing, runs filters off-main-thread         |
| `FrameProcessor.swift`           | Manages filters, resizes input to 512×512, applies filters, resizes back |
| `ProcessingGraph.swift`          | Applies a sequence of `ImageFilter`s to a `CGImage`                 |
| `GammaFilter.swift`              | Placeholder image filter (currently passthrough)                    |
| `ChromaticAberration.swift`      | Image-space RGB shift (implemented, but currently unused)           |
| `ColorFFTFilter.swift`           | Main FFT/iFFT-based glitch filter; applies FFT per **visual row**   |
| `KillLowFrequencies.swift`       | Glitch filter: zeroes out low frequencies in FFT buffer             |
| `CameraViewModel.swift`          | Binds processed frames to `@Published` property for the UI          |
| `ContentView.swift`              | SwiftUI preview with capture button                                 |
| `FrameBuffer.swift`              | Unused ring buffer for past frames                                  |
| `AppConstants.swift`             | App-wide constants (currently only buffer size, unused)             |

## 📐 Orientation Handling

- Captured frames are always rotated .right (landscape mode).
- UI elements remain upright using UIDevice.orientationDidChangeNotification.
- Captured stills are saved with correct UIImageOrientation.right for EXIF.

⚙️ Implementation Notes
- Images are resized to 512×512 before processing for performance and simplicity.
- FFT size (log2n) is inferred automatically per image width/height.
- FFT setup (FFTSetup) and intermediate buffers are reused across frames to minimize allocations.
- Row-wise FFT is implemented using Accelerate’s vDSP_mtrans for efficient transposition.
    
🚧 Roadmap

Apply FFT row-wise for RGB glitch
Add filter intensity/config sliders
Implement video output (e.g. record processed video)
Add LivePhoto / AppClip support
Enable multi-filter pipelines and toggles
