//
//  MetalFFTFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//

// MetalFFTFilter.swift
// Drop-in replacement for ColorFFTFilter

import Foundation
import Metal

class MetalFFTFilter: FloatRGBFilter {
    private let context = MetalContext.shared
    private var fftPipeline: MTLComputePipelineState?
    private var ifftPipeline: MTLComputePipelineState?

    init() {
        guard let device = context?.device,
              let library = device.makeDefaultLibrary(),
              let fftKernel = library.makeFunction(name: "fft1D_512"),
              let ifftKernel = library.makeFunction(name: "ifft1D_512") else {
            print("Failed to set up MetalFFTFilter")
            return
        }

        do {
            fftPipeline = try device.makeComputePipelineState(function: fftKernel)
            ifftPipeline = try device.makeComputePipelineState(function: ifftKernel)
        } catch {
            print("Failed to create pipeline state: \(error)")
        }
    }

    func apply(r: inout [Float], g: inout [Float], b: inout [Float], width: Int, height: Int) {
        guard let context = context,
              let fftPipeline = fftPipeline,
              let ifftPipeline = ifftPipeline else { return }

        let channelSize = width * height * MemoryLayout<Float>.size

        func process(_ data: inout [Float]) {
            guard let buffer = context.device.makeBuffer(bytes: &data, length: channelSize, options: []),
                  let commandBuffer = context.commandQueue.makeCommandBuffer() else { return }

            let threadGroupSize = MTLSize(width: 1, height: 1, depth: 1)
            let threadGroups = MTLSize(width: height, height: 1, depth: 1)  // запуск 512 потоков (по строкам)

            if let encoder1 = commandBuffer.makeComputeCommandEncoder() {
                encoder1.setComputePipelineState(fftPipeline)
                encoder1.setBuffer(buffer, offset: 0, index: 0)
                encoder1.dispatchThreadgroups(threadGroups, threadsPerThreadgroup: threadGroupSize)
                encoder1.endEncoding()
            }

            if let encoder2 = commandBuffer.makeComputeCommandEncoder() {
                encoder2.setComputePipelineState(ifftPipeline)
                encoder2.setBuffer(buffer, offset: 0, index: 0)
                encoder2.dispatchThreadgroups(threadGroups, threadsPerThreadgroup: threadGroupSize)
                encoder2.endEncoding()
            }

            commandBuffer.commit()
            commandBuffer.waitUntilCompleted()

            memcpy(&data, buffer.contents(), channelSize)
        }

        process(&r)
        process(&g)
        process(&b)
    }
}
