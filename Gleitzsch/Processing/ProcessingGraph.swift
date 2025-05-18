//
//  ProcessingGraph.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Foundation
import CoreImage

class ProcessingGraph {
    private var filters: [ImageFilter] = []

    func addFilter(_ filter: ImageFilter) {
        filters.append(filter)
    }

    func process(_ image: CGImage) -> CGImage {
        filters.reduce(image) { result, filter in
            filter.apply(to: result)
        }
    }
}
