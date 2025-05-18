//
//  Untitled.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Accelerate
import CoreImage

class ChromaticAberration: ImageFilter {
    func apply(to image: CGImage) -> CGImage {
        let width = image.width
        let height = image.height
        let (r, g, b) = image.toRGBFloatChannels()

        // Увеличиваем размер каналов
        let gPadded = padAndCrop(channel: g, width: width, height: height, padX: 2, padY: 2)
        let bPadded = padAndCrop(channel: b, width: width, height: height, padX: 4, padY: 4)

        // R не трогаем
        let result = CGImage.fromRGBFloatChannels(r: r, g: gPadded, b: bPadded, width: width, height: height)
        return result ?? image
    }

    private func padAndCrop(channel: [Float], width: Int, height: Int, padX: Int, padY: Int) -> [Float] {
        let newWidth = width + padX
        let newHeight = height + padY
        var padded = [Float](repeating: 0, count: newWidth * newHeight)

        // Вставляем оригинал по центру
        for y in 0..<height {
            for x in 0..<width {
                let srcIndex = y * width + x
                let dstIndex = (y + padY / 2) * newWidth + (x + padX / 2)
                padded[dstIndex] = channel[srcIndex]
            }
        }

        // Обрезаем обратно до центра
        var cropped = [Float](repeating: 0, count: width * height)
        for y in 0..<height {
            for x in 0..<width {
                let dstIndex = y * width + x
                let srcIndex = (y + padY / 2) * newWidth + (x + padX / 2)
                cropped[dstIndex] = padded[srcIndex]
            }
        }

        return cropped
    }
}
