//
//  ImageFilter.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 18.05.25.
//
import CoreImage

protocol ImageFilter {
    func apply(to image: CGImage) -> CGImage
}
