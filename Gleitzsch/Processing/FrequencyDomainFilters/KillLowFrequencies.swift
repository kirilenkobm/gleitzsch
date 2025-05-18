//
//  KillLowFrequencies.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate

class KillLowFrequencies: FrequencyDomainFilter {
    func apply(real: UnsafeMutablePointer<Float>, imag: UnsafeMutablePointer<Float>, count: Int) {
        let side = Int(sqrt(Double(count)))
        let cutoff = side / 2

        for y in 0..<cutoff {
            for x in 0..<cutoff {
                let i = y * side + x
                real[i] = 0
                imag[i] = 0
            }
        }
    }
}
