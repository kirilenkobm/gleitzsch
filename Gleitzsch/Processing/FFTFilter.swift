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
    private var setup: FFTSetup?
    let filter = KillLowFrequencies()

    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        if scratch == nil || scratch?.width != width || scratch?.height != height {
            scratch = ColorFFTScratch(width: width, height: height)
        }

        guard let scratch = scratch else { return }

        let log2n = scratch.log2n
        if setup == nil {
            setup = vDSP_create_fftsetup(log2n, FFTRadix(kFFTRadix2))
        }
        guard let setup = setup else { return }

        let normFactor = Float(height)

        for (input, channel) in [(r, scratch.rBuffer), (g, scratch.gBuffer), (b, scratch.bBuffer)] {
            // транспонируем: width×height → height×width
            var transposed = [Float](repeating: 0, count: width * height)
            vDSP_mtrans(input, 1, &transposed, 1, vDSP_Length(height), vDSP_Length(width))

            var output = [Float](repeating: 0, count: width * height)

            for row in 0..<width {
                let rowStart = row * height

                var tempReal = [Float](repeating: 0, count: height)
                var tempImag = [Float](repeating: 0, count: height)

                for i in 0..<height {
                    tempReal[i] = transposed[rowStart + i]
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

            // обратно: height×width → width×height
            vDSP_mtrans(output, 1, &channel.real, 1, vDSP_Length(width), vDSP_Length(height))
        }

        r = scratch.rBuffer.real.normalizeToZeroOne()
        g = scratch.gBuffer.real.normalizeToZeroOne()
        b = scratch.bBuffer.real.normalizeToZeroOne()
    }

    deinit {
        if let setup = setup {
            vDSP_destroy_fftsetup(setup)
        }
    }
}
