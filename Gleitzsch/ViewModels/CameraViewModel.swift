//
//  CameraViewModel.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import Combine
import CoreImage
import UIKit

class CameraViewModel: ObservableObject {
    @Published var currentFrame: CGImage?
    
    @Published var deviceOrientation: UIDeviceOrientation = UIDevice.current.orientation

    private var orientationObserver: Any?
    
    private let pipeline = FramePipeline()
    
    private var cancellables = Set<AnyCancellable>()

    func start() {
        UIDevice.current.beginGeneratingDeviceOrientationNotifications()
        
        pipeline.framePublisher
            .receive(on: DispatchQueue.main)
            .sink { [weak self] frame in
                self?.currentFrame = frame
            }
            .store(in: &cancellables)
        
        pipeline.start()
        
        orientationObserver = NotificationCenter.default.addObserver(
            forName: UIDevice.orientationDidChangeNotification,
            object: nil,
            queue: .main
        ) { [weak self] _ in
            self?.deviceOrientation = UIDevice.current.orientation
        }
    }

    func captureFrame() {
        guard let image = currentFrame else { return }

        let orientation: UIImage.Orientation = {
            switch deviceOrientation {
            case .portrait: return .right
            case .portraitUpsideDown: return .left
            case .landscapeLeft: return .down
            case .landscapeRight: return .up
            default: return .right
            }
        }()

        let imageToSave = UIImage(cgImage: image, scale: 1.0, orientation: orientation)
        UIImageWriteToSavedPhotosAlbum(imageToSave, nil, nil, nil)
    }
}
