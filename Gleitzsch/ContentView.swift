//
//  ContentView.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 17.05.25.
//

import SwiftUI
import SwiftData

struct ContentView: View {
    @StateObject private var viewModel = CameraViewModel()

    var body: some View {
        VStack {
            if let frame = viewModel.currentFrame {
                Image(decorative: frame, scale: 1.0, orientation: .up)
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
                    .background(Color.black)
            } else {
                Text("Camera is inactive")
            }

            Button(action: {
                viewModel.captureFrame()
            }) {
                Image(systemName: "camera.circle.fill")
                    .resizable()
                    .frame(width: 64, height: 64)
                    .foregroundColor(.white)
            }
        }
        .onAppear {
            viewModel.start()
        }
    }
}
