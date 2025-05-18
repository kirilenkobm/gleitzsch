//
//  ProcessingGraph.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Foundation
import CoreImage

class ProcessingGraph {
    private var filters: [FloatRGBFilter] = []

    func addFilter(_ filter: FloatRGBFilter) {
        filters.append(filter)
    }

    func process(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        for filter in filters {
            filter.apply(r: &r, g: &g, b: &b, width: width, height: height)
        }
    }
}
