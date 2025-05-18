//
//  FramePipeline.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import Combine
import CoreImage
import QuartzCore

final class FramePipeline {
    private let cameraManager = CameraManager()
    private let processor = FrameProcessor()

    private let frameSubject = PassthroughSubject<CGImage, Never>()
    var framePublisher: AnyPublisher<CGImage, Never> {
        frameSubject.eraseToAnyPublisher()
    }

    private var cancellables = Set<AnyCancellable>()

    private let processingQueue = DispatchQueue(label: "frame.processing", qos: .userInitiated)
    private var frameBuffer = [CGImage?](repeating: nil, count: 2)
    private var bufferIndex = 0
    private let lock = NSLock()

    private let throttleFPS: Double = 10.0
    private var lastFrameTime: CFTimeInterval = 0

    func start() {
        cameraManager.$currentFrame
            .compactMap { $0 }
            .sink { [weak self] frame in
                guard let self = self else { return }

                let now = CACurrentMediaTime()
                if now - self.lastFrameTime < 1.0 / self.throttleFPS {
                    return
                }
                self.lastFrameTime = now

                self.lock.lock()
                self.frameBuffer[self.bufferIndex] = frame
                let indexToProcess = self.bufferIndex
                self.bufferIndex = (self.bufferIndex + 1) % self.frameBuffer.count
                self.lock.unlock()

                self.processingQueue.async { [weak self] in
                    guard let self = self else { return }

                    self.lock.lock()
                    guard let frame = self.frameBuffer[indexToProcess] else {
                        self.lock.unlock()
                        return
                    }
                    self.frameBuffer[indexToProcess] = nil
                    self.lock.unlock()

                    let processed = self.processor.process(frame)
                    DispatchQueue.main.async {
                        self.frameSubject.send(processed)
                    }
                }
            }
            .store(in: &cancellables)

        cameraManager.start()
    }
}
