//
//  MetalContext.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import Metal
import MetalKit

class MetalContext {
    static let shared = MetalContext()

    let device: MTLDevice
    let commandQueue: MTLCommandQueue

    private init?() {
        guard let dev = MTLCreateSystemDefaultDevice(),
              let queue = dev.makeCommandQueue() else {
            print("Metal not supported on this device")
            return nil
        }
        self.device = dev
        self.commandQueue = queue
    }
}
