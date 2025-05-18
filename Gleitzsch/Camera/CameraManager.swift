//
//  CameraManager.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import AVFoundation
import Combine
import CoreImage

class CameraManager: NSObject, ObservableObject {
    @Published private(set) var currentFrame: CGImage?

    private let captureSession = AVCaptureSession()
    private let sessionQueue = DispatchQueue(label: "camera.session")
    private let processingQueue = DispatchQueue(label: "camera.processing")
    private let ciContext = CIContext()

    func start() {
        sessionQueue.async { [weak self] in
            guard let self = self else { return }
            self.setupSession()
        }
    }

    private func setupSession() {
        guard let device = AVCaptureDevice.default(for: .video),
              let input = try? AVCaptureDeviceInput(device: device) else {
            print("No camera input")
            return
        }

        captureSession.beginConfiguration()
        captureSession.sessionPreset = .vga640x480

        if captureSession.canAddInput(input) {
            captureSession.addInput(input)
        }

        let output = AVCaptureVideoDataOutput()
        output.setSampleBufferDelegate(self, queue: processingQueue)
        output.alwaysDiscardsLateVideoFrames = true

        if captureSession.canAddOutput(output) {
            captureSession.addOutput(output)
        }

        captureSession.commitConfiguration()
        captureSession.startRunning()
    }
}

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {
    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        autoreleasepool {
            guard let buffer = CMSampleBufferGetImageBuffer(sampleBuffer) else { return }
            let ciImage = CIImage(cvImageBuffer: buffer).oriented(.right)

            guard let cgImage = ciContext.createCGImage(ciImage, from: ciImage.extent) else { return }

            DispatchQueue.main.async {
                self.currentFrame = cgImage
            }
        }
    }
}
