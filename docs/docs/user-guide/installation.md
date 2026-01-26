# #-CAD Installation
##  #-CAD Installation

\#-CAD is available as a native desktop application for macOS, Windows, and Linux, or as a stand-alone web app.

### Download

Download the latest release for your platform from our [GitHub Releases](https://github.com/mattaq31/Hash-CAD/releases) page.

| Platform | Download                |
|----------|-------------------------|
| macOS (Intel & Apple Silicon) | `Hash-CAD-macos.dmg`    |
| Windows | `Hash-CAD-windows-installer.exe`  |
| Linux | `Hash-CAD-linux.tar.gz` |

### MacOS Installation

1. Download the `.zip` file
2. Extract the zip and drag #-CAD to your Applications folder
3. On first launch, you will need to go to the 'Privacy & Security' tab in your system preferences and allow #-CAD to open anyway (we unfortunately do not have a developer certificate yet).

![macOS Security Settings](https://github.com/mattaq31/Hash-CAD/raw/main/graphics_screenshots/installation/macos_security_check.png){ width="600" }

### Windows Installation

1. Download the `.exe` installer file
2. Run the installer 
3. Windows Defender may show a warning; click "More info" then "Run anyway"
4. Follow the usual on-screen prompts to install the package
5. Done!

### Linux Installation (we are working on a better install method)

1. Download and extract the `.tar.gz` file
2. Run the `flutter_app` executable from the extracted folder

### Web Version (no install needed)

A web version of #-CAD is also available at [hash-cad.com](https://www.hash-cad.com).

!!! note
    The web version does not have access to the evolutionary algorithm system, but can still calculate parasitic valencies.

## Python Libraries Installation

All python libraries are available on PyPI in one install:

```bash
pip install crisscross_kit
```

For optional 3D graphics and Blender support for the crisscross library use the below command instead:

```bash
pip install crisscross_kit[3d]
pip install crisscross_kit[blender]
```

The packages were developed using Python 3.11, although any version from 3.10 onwards should work well.
