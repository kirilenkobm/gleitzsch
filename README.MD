# Gleitzsch

**Gleitzsch** is a glitch-art camera app for iOS. It captures live video, processes frames in real time, and applies visual effects like FFT-based distortions (to be added). The architecture is modular, extensible, and optimized for real-time performance.

---

## 🔧 Architecture Overview

The app is split into clear layers:

Camera → Resize/Orientation → Processing → Display → Capture

Each step is separated for maintainability and testability.

### 🧩 Components

| Layer             | Class               | Responsibility |
|------------------|---------------------|----------------|
| Capture          | `CameraManager`     | Captures frames via `AVCaptureVideoDataOutput` and orients them correctly |
| Processing       | `FrameProcessor`    | Applies visual effects (FFT glitch etc.) — currently a passthrough |
| Pipeline         | `FramePipeline`     | Connects capture and processing layers, handles data flow |
| View Model       | `CameraViewModel`   | Binds processed frames to the UI and manages state |
| UI               | `ContentView`       | SwiftUI layout showing the live preview and capture controls |

---

## ⚙️ How it works

- The app uses `AVCaptureSession` to get live camera frames.
- Each frame is converted to `CGImage`, corrected for orientation, and passed through the pipeline.
- Future versions will apply FFT-based glitching and color channel effects.
- The UI uses SwiftUI and automatically adapts to device orientation.

---

## 🚀 Planned features

- Real-time glitch effects (FFT, chromatic aberration, gamma distortion)
- Adjustable effect intensity
- Snapshots with visual effects applied
- Optional video recording

---

## 📁 Project Structure

Gleitzsch/
├── Camera/             // Frame capture logic
├── Processing/         // Frame processing and filters
├── Pipeline/           // Connects camera to processor
├── ViewModels/         // Bindings and logic for the UI
├── Views/              // SwiftUI interface
├── Utils/              // Constants, extensions, etc.
