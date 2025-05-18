//
//  Extensions.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import CoreImage
import Foundation
import Accelerate

extension UnsafeMutablePointer<Float> {
    func toCGImage(width: Int, height: Int) -> CGImage? {
        guard let colorSpace = CGColorSpace(name: CGColorSpace.linearGray) else { return nil }

        guard let context = CGContext(data: self,
                                      width: width,
                                      height: height,
                                      bitsPerComponent: 32,
                                      bytesPerRow: width * MemoryLayout<Float>.size,
                                      space: colorSpace,
                                      bitmapInfo: CGImageAlphaInfo.none.rawValue | CGBitmapInfo.floatComponents.rawValue)
        else {
            return nil
        }

        return context.makeImage()
    }
}

extension Array where Element == Float {
    func normalizeToZeroOne() -> [Float] {
        guard let min = self.min(), let max = self.max(), max > min else {
            return self
        }

        let range = max - min
        return self.map { ($0 - min) / range }
    }
}

