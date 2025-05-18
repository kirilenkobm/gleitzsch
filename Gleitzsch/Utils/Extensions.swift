//
//  Extensions.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import CoreImage
import Foundation

import CoreImage
import Foundation
import Accelerate

extension CGImage {
    func downsampled(to size: CGSize) -> CGImage {
        return self
    }

    func toGrayscaleFloatData() -> [Float]? {
        guard let colorSpace = CGColorSpace(name: CGColorSpace.linearGray) else { return nil }
        let width = self.width
        let height = self.height
        var buffer = [Float](repeating: 0, count: width * height)

        guard let context = CGContext(data: &buffer,
                                      width: width,
                                      height: height,
                                      bitsPerComponent: 32,
                                      bytesPerRow: width * MemoryLayout<Float>.size,
                                      space: colorSpace,
                                      bitmapInfo: CGImageAlphaInfo.none.rawValue | CGBitmapInfo.floatComponents.rawValue) else {
            return nil
        }

        context.draw(self, in: CGRect(x: 0, y: 0, width: width, height: height))
        return buffer
    }
}
