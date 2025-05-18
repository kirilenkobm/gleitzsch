//
//  FFTFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Foundation
import Accelerate
import CoreImage

class FFTFilter: ImageFilter {
    private let filters: [FrequencyDomainFilter]

    private var scratch: FFTScratch?

    init(filters: [FrequencyDomainFilter]) {
        self.filters = filters
    }

    func apply(to image: CGImage) -> CGImage {
        guard let grayData = image.toGrayscaleFloatData() else { return image }

        if scratch == nil || scratch?.count != grayData.count {
            scratch = FFTScratch(count: grayData.count)
        }

        guard let scratch = scratch else { return image }

        scratch.load(from: grayData)

        var split = scratch.splitComplex
        for f in filters {
            f.apply(real: split.realp, imag: split.imagp, count: scratch.count)
        }

        return image // placeholder
    }
}
