//
//  ColorFFTFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate
import CoreImage



class FFTFilter: FloatRGBFilter {
    private var scratch: ColorFFTScratch?
    let filter = KillLowFrequencies()

    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        if scratch == nil || scratch?.width != width || scratch?.height != height {
            scratch = ColorFFTScratch(width: width, height: height)
        }

        guard let scratch = scratch else { return }
        
        let setupWrapper = FFTSetupStore.shared

        let log2n = scratch.log2n
        let normFactor = Float(height)

        let group = DispatchGroup()

        var rCopy = r
        var gCopy = g
        var bCopy = b

    
        group.enter()
        DispatchQueue.global(qos: .userInitiated).async {
            self.processChannel(input: &rCopy, buffer: &scratch.rBuffer,
                                tempReal: &scratch.tempRealR, tempImag: &scratch.tempImagR,
                                width: width, height: height,
                                log2n: log2n, setup: setupWrapper.setup, normFactor: normFactor)
            group.leave()
        }

        group.enter()
        DispatchQueue.global(qos: .userInitiated).async {
            self.processChannel(input: &gCopy, buffer: &scratch.gBuffer,
                                tempReal: &scratch.tempRealG, tempImag: &scratch.tempImagG,
                                width: width, height: height,
                                log2n: log2n, setup: setupWrapper.setup, normFactor: normFactor)
            group.leave()
        }

        group.enter()
        DispatchQueue.global(qos: .userInitiated).async {
            self.processChannel(input: &bCopy, buffer: &scratch.bBuffer,
                                tempReal: &scratch.tempRealB, tempImag: &scratch.tempImagB,
                                width: width, height: height,
                                log2n: log2n, setup: setupWrapper.setup, normFactor: normFactor)
            group.leave()
        }

        group.wait()

        r = scratch.rBuffer.real.normalizeToZeroOneSafe()
        g = scratch.gBuffer.real.normalizeToZeroOneSafe()
        b = scratch.bBuffer.real.normalizeToZeroOneSafe()
    }

    private func processChannel(
        input: inout [Float],
        buffer: inout FFT2DChannelBuffer,
        tempReal: inout [Float],
        tempImag: inout [Float],
        width: Int,
        height: Int,
        log2n: vDSP_Length,
        setup: FFTSetup,
        normFactor: Float
    ) {
        var transposed = [Float](repeating: 0, count: width * height)
        vDSP_mtrans(input, 1, &transposed, 1, vDSP_Length(height), vDSP_Length(width))

        var output = [Float](repeating: 0, count: width * height)

        for row in 0..<width {
            let rowStart = row * height

            for i in 0..<height {
                tempReal[i] = transposed[rowStart + i]
                tempImag[i] = 0
            }

            tempReal.withUnsafeMutableBufferPointer { real in
                tempImag.withUnsafeMutableBufferPointer { imag in
                    var split = DSPSplitComplex(realp: real.baseAddress!, imagp: imag.baseAddress!)
                    vDSP_fft_zip(setup, &split, 1, log2n, FFTDirection(FFT_FORWARD))

                    filter.apply(real: real.baseAddress!, imag: imag.baseAddress!, count: height)

                    vDSP_fft_zip(setup, &split, 1, log2n, FFTDirection(FFT_INVERSE))
                    vDSP_vsdiv(real.baseAddress!, 1, [normFactor], real.baseAddress!, 1, vDSP_Length(height))

                    for i in 0..<height {
                        output[rowStart + i] = real[i]
                    }
                }
            }
        }

        vDSP_mtrans(output, 1, &buffer.real, 1, vDSP_Length(width), vDSP_Length(height))
    }

}
