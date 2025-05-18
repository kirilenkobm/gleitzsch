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
        // graph.addFilter(ChromaticAberration())

        // Add 2D FFT/iFFT passthrough
        graph.addFilter(ColorFFTFilter()) // заменили FFTFilter
    }

    func process(_ image: CGImage) -> CGImage {
        // Step 1: ресайз до квадрата 512×512
        let targetSize = CGSize(width: 512, height: 512)
        let resized = image.resized(to: targetSize) ?? image

        // Step 2: прогоняем через фильтры
        let processed = graph.process(resized)

        // Step 3: ресайз обратно к оригиналу
        let restored = processed.resized(to: CGSize(width: image.width, height: image.height)) ?? processed

        return restored
    }
}
