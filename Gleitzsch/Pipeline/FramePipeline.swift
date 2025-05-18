//
//  FramePipeline.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import Combine
import CoreImage

final class FramePipeline {
    private let cameraManager = CameraManager()
    private let processor = FrameProcessor()

    private let frameSubject = PassthroughSubject<CGImage, Never>()
    var framePublisher: AnyPublisher<CGImage, Never> {
        frameSubject.eraseToAnyPublisher()
    }

    private var cancellables = Set<AnyCancellable>()

    private var isProcessing = false
    private var latestFrame: CGImage?

    func start() {
        cameraManager.$currentFrame
            .compactMap { $0 }
            .sink { [weak self] frame in
                guard let self = self else { return }

                self.latestFrame = frame

                guard !self.isProcessing else { return }

                self.isProcessing = true
                DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                    guard let self = self else { return }

                    while true {
                        guard let frame = self.latestFrame else { break }
                        self.latestFrame = nil

                        let processed = self.processor.process(frame)
                        DispatchQueue.main.async {
                            self.frameSubject.send(processed)
                        }

                        // If another frame is waiting, continue
                        if self.latestFrame == nil { break }
                    }

                    self.isProcessing = false
                }
            }
            .store(in: &cancellables)

        cameraManager.start()
    }
}
