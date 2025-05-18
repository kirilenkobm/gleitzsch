//
//  FFTScratch.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Accelerate

class FFTScratch {
    let real: UnsafeMutablePointer<Float>
    let imag: UnsafeMutablePointer<Float>
    let count: Int

    init(count: Int) {
        self.count = count
        self.real = .allocate(capacity: count)
        self.imag = .allocate(capacity: count)
    }

    deinit {
        real.deallocate()
        imag.deallocate()
    }

    func load(from buffer: [Float]) {
        real.assign(from: buffer, count: count)
        imag.initialize(repeating: 0, count: count)
    }

    var splitComplex: DSPSplitComplex {
        .init(realp: real, imagp: imag)
    }
}
