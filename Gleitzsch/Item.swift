//
//  Item.swift
//  Gleitzsch
//
//  Created by Bogdan.Kirilenko on 17.05.25.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
