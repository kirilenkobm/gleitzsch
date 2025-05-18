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
    
    func normalizeToZeroOneSafe() -> [Float] {
        guard let min = self.min(), let max = self.max(), max.isFinite, min.isFinite else {
            return self.map { _ in 0 } // all black if totally broken
        }
        let range = max - min
        if range <= .ulpOfOne { // min ≈ max
            return self.map { _ in 0.5 } // mid-gray
        }

        return self.map {
            let v = ($0 - min) / range
            return v.isFinite ? v : 0
        }
    }
}

