//
//  FloatRGBFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

protocol FloatRGBFilter {
    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int)
}
