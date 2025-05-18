// MetalFFTFilter.swift  (целиком)

import Foundation
import Metal

final class MetalFFTFilter: FloatRGBFilter {
    // MARK: -- Pipelines
    private let context = MetalContext.shared
    private var fftPipeline:       MTLComputePipelineState?
    private var ifftPipeline:      MTLComputePipelineState?
    private var killPipeline:      MTLComputePipelineState?
    private var transposePipeline: MTLComputePipelineState?

    // MARK: -- Runtime knobs
    var lowRatio:  Float = 0.00
    var highRatio: Float = 0.90
    
    // MARK: -- Buffers
    private var realBuffer : MTLBuffer?
    private var imagBuffer : MTLBuffer?
    private var tempBuffer : MTLBuffer?   // для transpose
    private var outBuffer  : MTLBuffer?
    private var byteCap    : Int = 0      // сколько реально выделено

    // MARK: -- Threadgroup размеры (512×512 → плитка 16×16)
    private let tgTile  = MTLSize(width: 16, height: 16, depth: 1)
    private let tgGrid  = MTLSize(width: 32, height: 32, depth: 1)   // 32*16 = 512

    // MARK: -- Init
    init() {
        guard
            let device   = context?.device,
            let library  = device.makeDefaultLibrary(),
            let fftFn    = library.makeFunction(name: "fft1D_512"),
            let ifftFn   = library.makeFunction(name: "ifft1D_512"),
            let transFn  = library.makeFunction(name: "transpose512")
        else {
            print("MetalFFTFilter: cannot make library / kernels")
            return
        }

        killPipeline      = try? device.makeComputePipelineState(function: library.makeFunction(name: "killBands_1D_512")!)
        fftPipeline       = try? device.makeComputePipelineState(function: fftFn)
        ifftPipeline      = try? device.makeComputePipelineState(function: ifftFn)
        transposePipeline = try? device.makeComputePipelineState(function: transFn)
    }

    // MARK: -- Ensure buffers
    private func ensureBuffers(device: MTLDevice, bytes: Int) {
        guard bytes > byteCap else { return }             // уже есть

        realBuffer = device.makeBuffer(length: bytes, options: .storageModeShared)
        imagBuffer = device.makeBuffer(length: bytes, options: .storageModeShared)
        tempBuffer = device.makeBuffer(length: bytes, options: .storageModeShared)
        outBuffer  = device.makeBuffer(length: bytes, options: .storageModeShared)
        byteCap    = bytes
    }

    // MARK: -- API
    func apply(r: inout [Float], g: inout [Float], b: inout [Float],
               width: Int, height: Int)
    {
        guard
            let ctx  = context,
            let fft  = fftPipeline,
            let ifft = ifftPipeline,
            width == 512
        else { return }

        let device     = ctx.device
        let count      = width * height
        let bytes      = count * MemoryLayout<Float>.size
        let tgLine     = MTLSize(width: 512, height: 1, depth: 1)
        let tgLines    = MTLSize(width: height, height: 1, depth: 1)

        ensureBuffers(device: device, bytes: bytes)

        func gpuTranspose(cmd: MTLCommandBuffer, src: MTLBuffer, dst: MTLBuffer, channelNum: Int) {
            guard let enc = cmd.makeComputeCommandEncoder(),
                  let pipe = transposePipeline else { return }

            enc.setComputePipelineState(pipe)
            enc.setBuffer(src, offset: 0, index: 0)
            enc.setBuffer(dst, offset: 0, index: 1)

            var seed: UInt32 = UInt32.random(in: 0...UInt32.max)   // frameSeed
            // var vhsIntensity: Float = 1.0  // TODO: PARAM
            var vhsIntensity: Float = if channelNum == 0 {
                0.24
            } else if channelNum == 1{
                0.4
            } else {
                1.0
            }
            
            enc.setBytes(&seed,         length: 4, index: 2)
            enc.setBytes(&vhsIntensity, length: 4, index: 3)

            enc.dispatchThreadgroups(tgGrid, threadsPerThreadgroup: tgTile)
            enc.endEncoding()
        }

        func process(_ channel: inout [Float], _ channelNum: Int) {
            // ------- CPU → realBuffer --------------------------------------
            _ = channel.withUnsafeBytes { raw in
                memcpy(realBuffer!.contents(), raw.baseAddress!, bytes)
            }
            memset(imagBuffer!.contents(), 0, bytes)

            /* >>> VHS tear – one cyclic row shift <<< */
            let tearIntensity: Float = 1.0   // 0…1 slider
            if tearIntensity > 0 {
                let width  = 512                                // N
                let row    = Int.random(in: 0..<height)
                var shift  = Int.random(in: -32...32)
                shift = Int(Float(shift) * tearIntensity)       // scale by UI

                if shift != 0 {
                    let ptr = realBuffer!.contents()
                        .assumingMemoryBound(to: Float.self)
                    let rowPtr = ptr + row * width

                    let absShift = abs(shift)
                    let byteCnt  = (width - absShift) * MemoryLayout<Float>.size

                    if shift > 0 {
                        /* right: copy left → right, then wrap leftmost part */
                        memmove(rowPtr + shift, rowPtr, byteCnt)
                        memcpy(rowPtr, rowPtr + width - shift,
                               absShift * MemoryLayout<Float>.size)
                    } else {
                        /* left: copy right → left, then wrap rightmost part */
                        memmove(rowPtr, rowPtr - shift, byteCnt)
                        memcpy(rowPtr + width + shift, rowPtr,
                               absShift * MemoryLayout<Float>.size)
                    }
                }
            }
            
            // ------- GPU ----------------------------------------------------
            guard let cmd = ctx.commandQueue.makeCommandBuffer() else { return }

            // a) transpose: real → temp (теперь столбцы ⇒ строки)
            gpuTranspose(cmd: cmd, src: realBuffer!, dst: tempBuffer!, channelNum: channelNum)

            // b) FFT   (по строкам, но это бывшие столбцы)
            if let enc = cmd.makeComputeCommandEncoder() {
                enc.setComputePipelineState(fft)
                enc.setBuffer(tempBuffer, offset: 0, index: 0)
                enc.setBuffer(imagBuffer, offset: 0, index: 1)
                enc.dispatchThreadgroups(tgLines, threadsPerThreadgroup: tgLine)
                enc.endEncoding()
            }

            // c) Kill bands
            runKillBands(cmd,
                         real: tempBuffer!, imag: imagBuffer!, rows: height, channelNum: channelNum)

            // d) iFFT  → outBuffer
            if let enc = cmd.makeComputeCommandEncoder() {
                enc.setComputePipelineState(ifft)
                enc.setBuffer(tempBuffer, offset: 0, index: 0)
                enc.setBuffer(imagBuffer, offset: 0, index: 1)
                enc.setBuffer(outBuffer,  offset: 0, index: 2)
                enc.dispatchThreadgroups(tgLines, threadsPerThreadgroup: tgLine)
                enc.endEncoding()
            }

            // e) transpose back: outBuffer → realBuffer (снова row-major)
            gpuTranspose(cmd: cmd, src: outBuffer!, dst: realBuffer!, channelNum: channelNum)

            cmd.commit()
            cmd.waitUntilCompleted()

            // ------- GPU → CPU ---------------------------------------------
            _ = channel.withUnsafeMutableBytes { dst in
                memcpy(dst.baseAddress!, realBuffer!.contents(), bytes)
            }
        }

        process(&r, 0)
        process(&g, 1)
        process(&b, 2)

        // ------- нормализация, чтобы не темнело ----------------------------
        r = r.normalizeToZeroOneSafe()
        g = g.normalizeToZeroOneSafe()
        b = b.normalizeToZeroOneSafe()
    }

    // MARK: -- Kill-bands kernel
    private func runKillBands(_ cmd: MTLCommandBuffer,
                              real: MTLBuffer, imag: MTLBuffer, rows: Int, channelNum: Int)
    {
        guard let pipe = killPipeline,
              let enc  = cmd.makeComputeCommandEncoder() else { return }

        enc.setComputePipelineState(pipe)
        enc.setBuffer(real, offset: 0, index: 0)
        enc.setBuffer(imag, offset: 0, index: 1)

        var cutLo = UInt32(Float(512) * lowRatio)
        var cutHi = UInt32(Float(512) * highRatio)
//        
//        var seed: UInt32 = UInt32.random(in: 0...UInt32.max)
//        // TODO: param
//        var vhsIntensity: Float = if channelNum == 0 {
//            0.01
//        } else if channelNum == 1 {
//            0.01
//        } else {
//            0.01
//        }
        
        enc.setBytes(&cutLo, length: 4, index: 2)
        enc.setBytes(&cutHi, length: 4, index: 3)
//        enc.setBytes(&seed,         length: 4, index: 4)
//        enc.setBytes(&vhsIntensity, length: 4, index: 5)

        let tgLine  = MTLSize(width: 512, height: 1, depth: 1)
        let tgLines = MTLSize(width: rows, height: 1, depth: 1)
        enc.dispatchThreadgroups(tgLines, threadsPerThreadgroup: tgLine)
        enc.endEncoding()
    }
}
