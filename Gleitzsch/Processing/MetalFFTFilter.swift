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

    func apply(r: inout [Float],
               g: inout [Float],
               b: inout [Float],
               width: Int,
               height: Int)
    {
        guard let context = context,
              let fftPipeline = fftPipeline,
              let ifftPipeline = ifftPipeline else { return }

        guard width == 512 else {
            print("MetalFFTFilter only supports width = 512")
            return
        }

        let device      = context.device
        let count       = width * height
        let byteCount   = count * MemoryLayout<Float>.size
        let tgSize      = MTLSize(width: 512, height: 1, depth: 1)
        let tgGroups    = MTLSize(width: height,  height: 1, depth: 1)

        func process(_ data: inout [Float]) {
            guard let commandBuffer = context.commandQueue.makeCommandBuffer() else { return }

            // --- входной (real) буфер ---
            guard let realBuffer = data.withUnsafeBytes({ raw -> MTLBuffer? in
                guard let base = raw.baseAddress else { return nil }
                return device.makeBuffer(bytes: base,
                                         length: byteCount,
                                         options: .storageModeShared)
            }) else {
                print("MetalFFTFilter: realBuffer creation failed")
                return
            }

            // --- пустой imag + выходной буферы ---
            guard let imagBuffer   = device.makeBuffer(length: byteCount,
                                                       options: .storageModeShared),
                  let outputBuffer = device.makeBuffer(length: byteCount,
                                                       options: .storageModeShared) else {
                print("MetalFFTFilter: imag/output buffer creation failed")
                return
            }
            memset(imagBuffer.contents(), 0, byteCount)

            // --- FFT ---
            if let enc = commandBuffer.makeComputeCommandEncoder() {
                enc.setComputePipelineState(fftPipeline)
                enc.setBuffer(realBuffer, offset: 0, index: 0)
                enc.setBuffer(imagBuffer, offset: 0, index: 1)
                enc.dispatchThreadgroups(tgGroups, threadsPerThreadgroup: tgSize)
                enc.endEncoding()
            }

            // --- iFFT ---
            if let enc = commandBuffer.makeComputeCommandEncoder() {
                enc.setComputePipelineState(ifftPipeline)
                enc.setBuffer(realBuffer, offset: 0, index: 0)
                enc.setBuffer(imagBuffer, offset: 0, index: 1)
                enc.setBuffer(outputBuffer, offset: 0, index: 2)
                enc.dispatchThreadgroups(tgGroups, threadsPerThreadgroup: tgSize)
                enc.endEncoding()
            }

            commandBuffer.commit()
            commandBuffer.waitUntilCompleted()

            // --- копируем результат обратно в массив ---
            let outPtr = outputBuffer.contents().bindMemory(to: Float.self, capacity: count)
            data = Array(UnsafeBufferPointer(start: outPtr, count: count))
        }

        process(&r)
        process(&g)
        process(&b)
    }
}
