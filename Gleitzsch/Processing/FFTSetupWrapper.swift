//
//  FFTSetupWrapper.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate

final class FFTSetupWrapper: @unchecked Sendable {
    let setup: FFTSetup

    init() {
        let log2n = vDSP_Length(log2(Float(AppConstants.targetSize.height)))
        self.setup = vDSP_create_fftsetup(log2n, FFTRadix(kFFTRadix2))!
    }

    deinit {
        vDSP_destroy_fftsetup(setup)
    }
}
