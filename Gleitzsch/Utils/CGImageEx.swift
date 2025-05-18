//
//  CGImageEx.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import CoreImage
import Foundation
import Accelerate

extension CGImage {
    func resized(to targetSize: CGSize) -> CGImage? {
        let context = CGContext(
            data: nil,
            width: Int(targetSize.width),
            height: Int(targetSize.height),
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
        )
        context?.interpolationQuality = .high
        context?.draw(self, in: CGRect(origin: .zero, size: targetSize))
        return context?.makeImage()
    }
    
    func padded(to size: CGSize) -> CGImage? {
        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let context = CGContext(
            data: nil,
            width: Int(size.width),
            height: Int(size.height),
            bitsPerComponent: 8,
            bytesPerRow: 0,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue
        )

        guard let context else { return nil }

        // Center the original image in the padded canvas
        let origin = CGPoint(
            x: (size.width - CGFloat(self.width)) / 2.0,
            y: (size.height - CGFloat(self.height)) / 2.0
        )

        context.draw(self, in: CGRect(origin: origin, size: CGSize(width: self.width, height: self.height)))
        return context.makeImage()
    }
    
    func cropped(to rect: CGRect) -> CGImage? {
        self.cropping(to: rect)
    }
    
    func toRGBFloatChannels() -> ([Float], [Float], [Float]) {
        let width = self.width
        let height = self.height
        var r = [Float](repeating: 0, count: width * height)
        var g = [Float](repeating: 0, count: width * height)
        var b = [Float](repeating: 0, count: width * height)

        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let context = CGContext(
            data: nil,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: 4 * width,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue
        )!

        context.draw(self, in: CGRect(x: 0, y: 0, width: width, height: height))

        guard let data = context.data else { return (r, g, b) }

        let buffer = data.bindMemory(to: UInt8.self, capacity: width * height * 4)
        for i in 0..<width * height {
            r[i] = Float(buffer[i * 4 + 0]) / 255.0
            g[i] = Float(buffer[i * 4 + 1]) / 255.0
            b[i] = Float(buffer[i * 4 + 2]) / 255.0
        }

        return (r, g, b)
    }
    

    static func fromRGBFloatChannels(r: [Float], g: [Float], b: [Float], width: Int, height: Int) -> CGImage? {
        var rgba = [UInt8](repeating: 255, count: width * height * 4)
        for i in 0..<width * height {
            rgba[i * 4 + 0] = safe255(r[i])
            rgba[i * 4 + 1] = safe255(g[i])
            rgba[i * 4 + 2] = safe255(b[i])
            rgba[i * 4 + 3] = 255
        }

        let colorSpace = CGColorSpaceCreateDeviceRGB()
        let context = CGContext(
            data: &rgba,
            width: width,
            height: height,
            bitsPerComponent: 8,
            bytesPerRow: width * 4,
            space: colorSpace,
            bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue
        )

        return context?.makeImage()
    }
}

func safe255(_ x: Float) -> UInt8 {
    if !x.isFinite || x.isNaN || x.isInfinite {
        return 0
    }
    let clamped = max(0.0, min(1.0, x)) // clamp to [0...1]
    return UInt8(clamping: Int(clamped * 255))
}
