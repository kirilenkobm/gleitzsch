//
//  FrameProcessor.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import CoreImage

class FrameProcessor {
    private let graph = ProcessingGraph()

    init() {
        graph.addFilter(GammaFilter(gamma: 4.0))
        graph.addFilter(ChromaticAberrationFilter(intensity: 1.5))
        graph.addFilter(FFTFilter())
    }

    func process(_ image: CGImage) -> CGImage {
        let targetSize = CGSize(width: 512, height: 512)
        let resized = image.resized(to: targetSize) ?? image

        var (r, g, b) = resized.toRGBFloatChannels()
        let width = Int(targetSize.width)
        let height = Int(targetSize.height)

        graph.process(r: &r, g: &g, b: &b, width: width, height: height)

        let processed = CGImage.fromRGBFloatChannels(r: r, g: g, b: b, width: width, height: height)
        return processed?.resized(to: CGSize(width: image.width, height: image.height)) ?? image
    }
}
