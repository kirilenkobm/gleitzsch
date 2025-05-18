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

    var rBuffer: FFT2DChannelBuffer
    var gBuffer: FFT2DChannelBuffer
    var bBuffer: FFT2DChannelBuffer

    var tempRealR: [Float]
    var tempImagR: [Float]

    var tempRealG: [Float]
    var tempImagG: [Float]

    var tempRealB: [Float]
    var tempImagB: [Float]

    init(width: Int, height: Int) {
        self.width = width
        self.height = height
        self.fftSize = max(width, height)
        self.log2n = vDSP_Length(log2(Float(fftSize)))

        rBuffer = FFT2DChannelBuffer(width: width, height: height)
        gBuffer = FFT2DChannelBuffer(width: width, height: height)
        bBuffer = FFT2DChannelBuffer(width: width, height: height)

        tempRealR = [Float](repeating: 0, count: height)
        tempImagR = [Float](repeating: 0, count: height)
        tempRealG = [Float](repeating: 0, count: height)
        tempImagG = [Float](repeating: 0, count: height)
        tempRealB = [Float](repeating: 0, count: height)
        tempImagB = [Float](repeating: 0, count: height)
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
