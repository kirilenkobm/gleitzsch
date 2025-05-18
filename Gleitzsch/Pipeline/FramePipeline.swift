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
            .sink { [weak self] frame in
                // Пока фильтров нет, просто прокидываем
                self?.frameSubject.send(frame)
            }
            .store(in: &cancellables)
        
        cameraManager.start()
    }
}
