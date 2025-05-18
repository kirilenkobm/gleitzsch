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

        let count = width * height
        let normFactor = Float(count)

        for (channel, data) in [(scratch.rBuffer, r), (scratch.gBuffer, g), (scratch.bBuffer, b)] {
            channel.real.withUnsafeMutableBufferPointer { realPtr in
                channel.imag.withUnsafeMutableBufferPointer { imagPtr in
                    data.withUnsafeBufferPointer { inputPtr in
                        guard let real = realPtr.baseAddress,
                              let imag = imagPtr.baseAddress,
                              let input = inputPtr.baseAddress else { return }

                        real.assign(from: input, count: count)
                        imag.initialize(repeating: 0, count: count)

                        var split = DSPSplitComplex(realp: real, imagp: imag)

                        vDSP_fft2d_zip(setup, &split, 1, vDSP_Stride(width), log2n, log2n, FFTDirection(FFT_FORWARD))
                        
                        // filter can be inserted here
                        
                        vDSP_fft2d_zip(setup, &split, 1, vDSP_Stride(width), log2n, log2n, FFTDirection(FFT_INVERSE))
                        vDSP_vsdiv(real, 1, [normFactor], real, 1, vDSP_Length(count))
                    }
                }
            }
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
