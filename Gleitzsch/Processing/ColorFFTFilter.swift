//
//  ColorFFTFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate
import CoreImage

class ColorFFTFilter: ImageFilter {
    private var scratch: ColorFFTScratch?
    private var setup: FFTSetup?
    let filter = KillLowFrequencies()

    func apply(to image: CGImage) -> CGImage {
        let width = image.width
        let height = image.height

        if scratch == nil || scratch?.width != width || scratch?.height != height {
            scratch = ColorFFTScratch(width: width, height: height)
        }

        guard let scratch = scratch else { return image }

        let (r, g, b) = image.toRGBFloatChannels()
        guard r.count == width * height else { return image }

        let log2n = scratch.log2n
        if setup == nil {
            setup = vDSP_create_fftsetup(log2n, FFTRadix(kFFTRadix2))
        }
        guard let setup = setup else { return image }

        let count = width
        let normFactor = Float(count)

        // Обрабатываем каждый канал
        for (channel, data) in [(scratch.rBuffer, r), (scratch.gBuffer, g), (scratch.bBuffer, b)] {
            // Транспонируем входной массив: width×height → height×width
            var transposed = [Float](repeating: 0, count: width * height)
            vDSP_mtrans(data, 1, &transposed, 1, vDSP_Length(height), vDSP_Length(width))

            var output = [Float](repeating: 0, count: width * height)

            for row in 0..<width {
                let rowStart = row * height

                // временные буферы
                var tempReal = [Float](repeating: 0, count: height)
                var tempImag = [Float](repeating: 0, count: height)

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

            // Обратно транспонируем output: height×width → width×height
            vDSP_mtrans(output, 1, &channel.real, 1, vDSP_Length(width), vDSP_Length(height))
        }

        let rOut = scratch.rBuffer.real.normalizeToZeroOne()
        let gOut = scratch.gBuffer.real.normalizeToZeroOne()
        let bOut = scratch.bBuffer.real.normalizeToZeroOne()

        return CGImage.fromRGBFloatChannels(
            r: rOut,
            g: gOut,
            b: bOut,
            width: width,
            height: height
        ) ?? image
    }

    deinit {
        if let setup = setup {
            vDSP_destroy_fftsetup(setup)
        }
    }
}
