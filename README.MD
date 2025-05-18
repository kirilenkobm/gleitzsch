# Gleitzsch

**Gleitzsch** is an iOS app for real-time glitch-art camera effects. It captures frames from the camera, optionally processes them (e.g. FFT-based distortions), and renders the result to the screen. Architecture is modular and ready for extension (e.g. video, filters, settings).

This README.md is written primarily for LLMs :).

---

## 🔧 Architecture Overview

The project follows a streaming pipeline:

CameraManager
↓
CIImage (oriented) → CGImage
↓
FrameProcessor (filters: gamma → chromaticAberration → FFT → glitch → iFFT)
↓
FramePipeline (binds processing to UI)
↓
CameraViewModel (exposes @Published frame)
↓
SwiftUI ContentView (renders preview)

All processing is done off-main-thread. UI only observes and renders the latest frame.

---

## 🧩 Core Components

| File / Class            | Location                  | Purpose |
|-------------------------|---------------------------|---------|
| `CameraManager.swift`   | `Camera/`                 | Captures camera frames, converts to `CGImage`, orients image (`.right`) |
| `FrameProcessor.swift`  | `Processing/`             | Processes `CGImage` (currently passthrough, future: glitch filters) |
| `FramePipeline.swift`   | `Pipeline/`               | Connects `CameraManager` to `FrameProcessor`, publishes processed frames |
| `CameraViewModel.swift` | `ViewModels/`             | Observes `FramePipeline`, exposes `@Published currentFrame` for UI |
| `ContentView.swift`     | `Views/`                  | SwiftUI UI, displays image, capture button, reacts to device orientation |

---

## ⚙️ Frame Flow

Each captured frame goes through:

CIImage (oriented) → gamma correction
→ chromatic aberration
→ FFT
→ glitch
→ iFFT → CGImage

(Current implementation is passthrough; filter logic is to be added in `FrameProcessor.swift`.)

Frames are displayed using `.scaledToFill()` and `CGImage` is rotated using `.oriented(.right)` before conversion.


## 🧪 Device Orientation

- Frames are always captured in landscape.
- The UI elements (e.g. buttons) are rotated using `UIDevice.orientationDidChangeNotification`.
- Captured images are saved with correct `UIImageOrientation` (`.right`) for EXIF consistency.

---

## 📁 Project Structure

```
Gleitzsch/
├── Camera/             // CameraManager and frame source
├── Processing/         // FrameProcessor and future filters
├── Pipeline/           // Data flow and coordination
├── ViewModels/         // CameraViewModel — binds pipeline to UI
├── Views/              // SwiftUI interface
├── Utils/              // App-wide constants and helpers
├── GleitzschApp.swift  // Entry point
```

## 🚧 Roadmap

- [ ] Implement FFT-based glitch filter
- [ ] Add intensity/config sliders
- [ ] Save processed video
- [ ] AppClip or LivePhoto support

---

