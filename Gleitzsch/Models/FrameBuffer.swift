//
//  FrameBuffer.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Foundation
import CoreImage

class FrameBuffer {
    private var buffer: [CGImage?]
    private var index = 0
    private let size: Int

    init(size: Int = 5) {
        self.size = size
        self.buffer = Array(repeating: nil, count: size)
    }

    func push(_ frame: CGImage) {
        buffer[index % size] = frame
        index += 1
    }

    func latest() -> CGImage? {
        return buffer[(index - 1 + size) % size]
    }
}
