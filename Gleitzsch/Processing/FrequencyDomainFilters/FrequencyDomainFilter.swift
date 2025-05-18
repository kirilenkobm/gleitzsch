//
//  FrequencyDomainFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

protocol FrequencyDomainFilter {
    func apply(real: UnsafeMutablePointer<Float>, imag: UnsafeMutablePointer<Float>, count: Int)
}
