//
//  GammaFloatFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate

class GammaFilter: FloatRGBFilter {
    var gamma: Float

    init(gamma: Float = 1.0) {
        self.gamma = gamma
    }

    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        let count = width * height
        for i in 0..<count {
            r[i] = pow(r[i], gamma)
            g[i] = pow(g[i], gamma)
            b[i] = pow(b[i], gamma)
        }
    }
}
