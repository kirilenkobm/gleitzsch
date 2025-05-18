//
//  ChromaticAberrationFloatFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate

class ChromaticAberrationFilter: FloatRGBFilter {
    var greenScale: Float
    var blueScale: Float

    init(intensity: Float = 1.0) {
        self.greenScale = 1.0 + 0.01 * intensity
        self.blueScale = 1.0 + 0.02 * intensity
    }
    
    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        g = stretchAndCrop(g, width: width, height: height, scaleX: greenScale, scaleY: greenScale)
        b = stretchAndCrop(b, width: width, height: height, scaleX: blueScale, scaleY: blueScale)
    }

    private func stretchAndCrop(
        _ channel: [Float],
        width: Int,
        height: Int,
        scaleX: Float,
        scaleY: Float
    ) -> [Float] {
        let newWidth = Int(Float(width) * scaleX)
        let newHeight = Int(Float(height) * scaleY)
        let resizedCount = newWidth * newHeight

        var resized = [Float](repeating: 0, count: resizedCount)

        channel.withUnsafeBufferPointer { srcPtr in
            resized.withUnsafeMutableBufferPointer { dstPtr in
                var srcBuffer = vImage_Buffer(
                    data: UnsafeMutableRawPointer(mutating: srcPtr.baseAddress!),
                    height: vImagePixelCount(height),
                    width: vImagePixelCount(width),
                    rowBytes: width * MemoryLayout<Float>.size
                )

                var dstBuffer = vImage_Buffer(
                    data: dstPtr.baseAddress!,
                    height: vImagePixelCount(newHeight),
                    width: vImagePixelCount(newWidth),
                    rowBytes: newWidth * MemoryLayout<Float>.size
                )

                let err = vImageScale_PlanarF(&srcBuffer, &dstBuffer, nil, vImage_Flags(kvImageHighQualityResampling))
                if err != kvImageNoError {
                    print("vImage resize failed: \(err)")
                }
            }
        }

        // Crop center region back to original size
        var cropped = [Float](repeating: 0, count: width * height)
        let startX = (newWidth - width) / 2
        let startY = (newHeight - height) / 2

        for y in 0..<height {
            for x in 0..<width {
                let srcIndex = (y + startY) * newWidth + (x + startX)
                let dstIndex = y * width + x
                cropped[dstIndex] = resized[srcIndex]
            }
        }

        return cropped
    }
}
