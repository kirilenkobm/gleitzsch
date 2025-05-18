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

        // Add FFT filter which wraps frequency domain filters
        let fftFilter = FFTFilter(filters: [KillLowFrequencies()])
        graph.addFilter(fftFilter)
    }

    func process(_ image: CGImage) -> CGImage {
        return graph.process(image)
    }
}
