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
        //graph.addFilter(GammaFilter(gamma: AppConstants.gamma))
        // graph.addFilter(ChromaticAberrationFilter(intensity: AppConstants.chromaticIntensity))
        // graph.addFilter(FFTFilter())
        graph.addFilter(MetalFFTFilter())
    }

    func process(_ image: CGImage) -> CGImage {
        let start = CFAbsoluteTimeGetCurrent()

        
        let targetSize = AppConstants.targetSize
        let resized = image.resized(to: targetSize) ?? image

        var (r, g, b) = resized.toRGBFloatChannels()
        let width = Int(targetSize.width)
        let height = Int(targetSize.height)

        graph.process(r: &r, g: &g, b: &b, width: width, height: height)

        let processed = CGImage.fromRGBFloatChannels(r: r, g: g, b: b, width: width, height: height)
        let result = processed?.resized(to: CGSize(width: image.width, height: image.height)) ?? image
        
        let end = CFAbsoluteTimeGetCurrent()
        print("Frame processed in \((end - start) * 1000) ms")

        
        return result
    }
}
