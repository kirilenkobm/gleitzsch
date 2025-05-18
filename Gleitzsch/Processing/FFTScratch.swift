//
//  FFTScratch.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

import Accelerate

class ColorFFTScratch {
    let width: Int
    let height: Int
    let fftSize: Int
    let log2n: vDSP_Length

    let rBuffer: FFT2DChannelBuffer
    let gBuffer: FFT2DChannelBuffer
    let bBuffer: FFT2DChannelBuffer

    init(width: Int, height: Int) {
        self.width = width
        self.height = height
        self.fftSize = max(width, height) // ideally both are powers of 2
        self.log2n = vDSP_Length(log2(Float(fftSize)))

        rBuffer = FFT2DChannelBuffer(width: width, height: height)
        gBuffer = FFT2DChannelBuffer(width: width, height: height)
        bBuffer = FFT2DChannelBuffer(width: width, height: height)
    }
}

class FFT2DChannelBuffer {
    let width: Int
    let height: Int
    var real: [Float]
    var imag: [Float]

    init(width: Int, height: Int) {
        self.width = width
        self.height = height
        self.real = .init(repeating: 0, count: width * height)
        self.imag = .init(repeating: 0, count: width * height)
    }
}
