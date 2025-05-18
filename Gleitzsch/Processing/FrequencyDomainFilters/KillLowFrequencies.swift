//
//  KillLowFrequencies.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

class KillLowFrequencies: FrequencyDomainFilter {
    func apply(real: UnsafeMutablePointer<Float>, imag: UnsafeMutablePointer<Float>, count: Int) {
        let cutoff = count / 8
        for i in 0..<cutoff {
            real[i] = 0
            imag[i] = 0
        }
    }
}
