// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "LunzikoAIEngine",
    platforms: [.macOS(.v12), .iOS(.v15)],
    products: [
        .library(name: "LunzikoAIEngine", targets: ["LunzikoAIEngine"]),
    ],
    targets: [
        .target(name: "LunzikoAIEngine"),
    ]
)
