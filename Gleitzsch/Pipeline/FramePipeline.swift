//
//  FramePipeline.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import Combine
import CoreImage

class FramePipeline {
    private let cameraManager = CameraManager()
    private let processor = FrameProcessor()

    private let frameSubject = PassthroughSubject<CGImage, Never>()
    var framePublisher: AnyPublisher<CGImage, Never> {
        frameSubject.eraseToAnyPublisher()
    }

    private var cancellables = Set<AnyCancellable>()

    func start() {
        cameraManager.$currentFrame
            .compactMap { $0 }
            .receive(on: DispatchQueue.global(qos: .userInitiated))
            .map { [processor] frame in
                return processor.process(frame)
            }
            .sink { [weak self] processedFrame in
                self?.frameSubject.send(processedFrame)
            }
            .store(in: &cancellables)
        
        cameraManager.start()
    }
}
