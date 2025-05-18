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
        // Add image domain filters
        graph.addFilter(GammaFilter())
        graph.addFilter(ChromaticAberration())

        // Add 2D FFT/iFFT passthrough
        graph.addFilter(ColorFFTFilter()) // заменили FFTFilter
    }

    func process(_ image: CGImage) -> CGImage {
        let square = CGSize(width: 256, height: 256)
        let resized = image.resized(to: square) ?? image
        return graph.process(resized)
    }
}
