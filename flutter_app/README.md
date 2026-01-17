# #-CAD Flutter Application

<p align="center">
  <img src="https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/bird_edit.png" alt="Hash-CAD Interface" style="width: 80%;">
</p>

Desktop application for DNA megastructure design with 2D/3D visualization, handle optimization, and Echo Liquid Handler export.

## Download

Download the latest release for your platform from [GitHub Releases](https://github.com/mattaq31/Hash-CAD/releases):

| Platform | Download |
|----------|----------|
| macOS | `Hash-CAD-x.x.x-macos.dmg` |
| Windows | `Hash-CAD-x.x.x-windows.zip` |
| Linux | `Hash-CAD-x.x.x-linux.tar.gz` |

## Documentation

- **User Guide**: [https://hash-cad.readthedocs.io/user-guide/](https://hash-cad.readthedocs.io/user-guide/)
- **Developer Docs**: [https://hash-cad.readthedocs.io/flutter-dev/](https://hash-cad.readthedocs.io/flutter-dev/)

## Development

### Prerequisites

- Flutter 3.19 or later
- Platform-specific build tools (see [Getting Started](https://hash-cad.readthedocs.io/flutter-dev/getting-started/))

### Build from Source

```bash
# Install dependencies
flutter pub get

# Run in debug mode
flutter run -d macos  # or windows, linux

# Build release
flutter build macos   # or windows, linux, web
```

### Project Structure

```
lib/
├── main.dart                 # App entry point
├── app_management/           # State management (Provider)
├── main_windows/             # Main UI components
├── sidebars/                 # Editing panels
├── crisscross_core/          # Data models
├── 2d_painters/              # Canvas rendering
├── graphics/                 # 3D visualization
└── grpc_client_architecture/ # Python server communication
```

For detailed architecture documentation, see the [Flutter Developer Guide](https://hash-cad.readthedocs.io/flutter-dev/).

## License

MIT License - see [LICENSE](../LICENSE) for details.
