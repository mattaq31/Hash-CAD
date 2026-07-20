# AGENTS.md

This file provides guidance to Codex, Claude Code, or other AI agents when working with code in this repository.

## Project Overview

Hash-CAD (#-CAD) is a unified CAD and scripting system for DNA megastructure (origami) design, handle library generation, and visualization. Developed in the William Shih Lab at Dana-Farber Cancer Institute / Wyss Institute, Harvard.

The system has two main components:
- **Flutter App** (`flutter_app/`): Desktop/web UI with 2D/3D visualization (current version: v1.1.2)
- **Python Library** (`crisscross_kit/`): Core computation engine, published to PyPI as `crisscross-kit` (current version: python-1.2.4)

Other directories:
- `docs/`: MkDocs-based documentation (hosted at https://hash-cad.readthedocs.io/)
- `main_paper_figure_generation/`: Scripts for generating paper figures (seqwalk comparisons, loss function analysis, etc.)
- `graphics_screenshots/`: Screenshots for documentation/paper
- `prototype_gui/`: Legacy prototype GUI (historical, not active)
- `scratch/`: Experimental scripts and prototypes

## Quick Setup

### Prerequisites
- Python >=3.10
- Flutter SDK >=3.6.1 (Dart SDK >=3.6.1)
- For gRPC code generation: `protoc` compiler with Dart plugin

### First-time setup
```bash
# Python library (from repo root)
cd crisscross_kit && pip install -e ".[3d]"

# Flutter app (from flutter_app/)
cd flutter_app && flutter pub get

# Python server (from flutter_app/python_server/)
pip install -r requirements.txt
```

## Build & Development Commands

### Python (crisscross_kit)

```bash
# Install in development mode (from crisscross_kit/)
pip install -e .

# With 3D visualization support
pip install -e ".[3d]"

# With Blender support
pip install -e ".[blender]"

# Build for PyPI
pip install build twine setuptools-scm
python -m build

# Lint/format
ruff check .
ruff format .
```

Note: The package includes a C extension (`eqcorr2d.eqcorr2d_engine`) that compiles automatically during install.

- Python >=3.10 required
- Version managed by `setuptools-scm` with git tags `python-*`
- Key dependencies: pandas, numpy, seaborn, matplotlib, openpyxl, xlsxwriter, tqdm, click, rich-click, toml

### Flutter App

```bash
# From flutter_app/
flutter pub get
flutter run -d macos  # or windows, linux
flutter build macos   # or windows, linux, web

# Lint
flutter analyze

# Run tests (redirect output to file for large results)
flutter test > /tmp/test_output.txt 2>&1 && tail -50 /tmp/test_output.txt
```

- Flutter SDK >=3.6.1
- Key packages: provider, three_js, grpc, protobuf, excel, fl_chart, window_manager, desktop_drop, csv, xml, toml, crypto
- Dev packages: mocktail, custom_lint, flutter_lints, msix

### Python Server (for Flutter integration)

```bash
# From flutter_app/python_server/
pip install -r requirements.txt

# Run server directly
python main_server.py

# Generate gRPC code (from flutter_app/)
python -m grpc_tools.protoc -I./python_dart_grpc_protocols \
  --python_out=./python_server/server_architecture \
  --pyi_out=./python_server/server_architecture \
  --grpc_python_out=./python_server/server_architecture \
  ./python_dart_grpc_protocols/hamming_evolve_communication.proto

# Generate Dart client code (from flutter_app/)
protoc -I ./python_dart_grpc_protocols/ \
  ./python_dart_grpc_protocols/hamming_evolve_communication.proto \
  --dart_out=grpc:lib/grpc_client_architecture
protoc -I ./python_dart_grpc_protocols/ \
  ./python_dart_grpc_protocols/health.proto \
  --dart_out=grpc:lib/grpc_client_architecture
```

The Python server is packaged with Nuitka for distribution (see `nuitka_package/` and `TESTEXEC.spec`).

## Architecture

### Communication Flow
```
Flutter UI (Dart) <--gRPC--> Python Server <--imports--> crisscross_kit
```

### Key Python Modules (`crisscross_kit/`)

- `crisscross/core_functions/megastructures.py`: Main `Megastructure` class - central data container for designs
- `crisscross/core_functions/slats.py`: Slat entity class
- `crisscross/core_functions/handle_link_manager.py`: `HandleLinkManager` class (linked groups, enforced values, blocked handles)
- `crisscross/core_functions/megastructure_composition.py`: Handle generation functions (`generate_random_slat_handles`, `generate_layer_split_handles`, `apply_handle_links`)
- `crisscross/slat_handle_match_evolver/`: Evolutionary algorithms for handle optimization
- `crisscross/plate_mapping/`: Plate mapping module with `hash_cad_plates.py`, `plate_constants.py`, and `non_standard_plates/` subfolder
- `crisscross/graphics/`: Visualization (`static_plots.py`, `pyvista_3d.py`, `blender_3d.py`)
- `crisscross/helper_functions/`: Utility functions (`lab_helper_sheet_generation.py`, `simple_plate_visuals.py`, `slat_salient_quantities.py`, `slurm_process_and_run.py`, `standard_sequences.py`)
- `crisscross/cli_functions/`: CLI entry points (`handle_evolution.py`, `plate_resuspension.py`, `working_stock_creation.py`) — Click-based CLI commands
- `orthoseq_generator/`: Orthogonal sequence generation (requires separate NUPACK 4.x installation)
- `eqcorr2d/`: C extension for 2D equilibrium correction calculations

### Key Flutter Components (`flutter_app/lib/`)

- `app_management/shared_app_state.dart`: `DesignState` (main state via Provider/ChangeNotifier)
- `app_management/design_state_mixins/`: 13 mixin files that decompose `DesignState`:
  - `design_state_core_mixin.dart`: Core state operations
  - `design_state_slat_mixin.dart`: Slat placement/removal
  - `design_state_handle_mixin.dart`: Handle assignment
  - `design_state_layer_mixin.dart`: Layer management
  - `design_state_seed_mixin.dart`: Seed placement
  - `design_state_cargo_mixin.dart`: Cargo attachment
  - `design_state_phantom_mixin.dart`: Phantom/preview slats
  - `design_state_plate_mixin.dart`: Plate mapping
  - `design_state_slat_color_mixin.dart`: Slat coloring
  - `design_state_handle_link_mixin.dart`: Handle linking
  - `design_state_file_io_mixin.dart`: File I/O operations
  - `design_state_grouping_mixin.dart`: Slat grouping system
  - `design_state_contract.dart`: Contract/interface definition
- `app_management/design_io/`: Design file I/O module (`design_import.dart`, `design_export.dart`, `evolution_export.dart`, `plate_io.dart`, `handle_link_io.dart`, `assembly_handle_io.dart`, `excel_utilities.dart`, `file_picker_helpers.dart`, `save_file_desktop.dart`, `save_file_web.dart`, `design_io_constants.dart`, `parsed_design_result.dart`)
- `app_management/action_state.dart`: User action tracking
- `app_management/server_state.dart`: Server communication state
- `app_management/slat_undo_stack.dart`: Undo/redo stack for slat operations
- `app_management/update_service.dart`: Auto-update with GitHub API
- `app_management/version_tracker.dart`, `git_version_updater.dart`: Version tracking and git-based version updates
- `main_windows/split_screen.dart`: Main UI layout
- `main_windows/grid_control.dart`: 2D grid canvas control
- `main_windows/grid_control_mixins/`: 7 mixins + contract for gesture/mouse/keyboard/hover handling:
  - `grid_control_contract.dart`, `grid_control_gesture_events_mixin.dart`, `grid_control_helpers_mixin.dart`, `grid_control_hover_events_mixin.dart`, `grid_control_keyboard_events_mixin.dart`, `grid_control_mouse_events_mixin.dart`, `grid_control_painters_mixin.dart`, `grid_control_position_generators_mixin.dart`
- `main_windows/floating_main_title.dart`, `floating_switches.dart`: Floating UI overlays
- `main_windows/window_manager.dart`, `web_window_manager.dart`, `windows_app_kill_listener.dart`: Window management (platform-specific)
- `crisscross_core/`: Core DNA/slat domain logic (`slats.dart`, `cargo.dart`, `seed.dart`, `parasitic_valency.dart`, `slat_standardized_mapping.dart`, `handle_plates.dart`, `sparse_to_array_conversion.dart`, `common_utilities.dart`)
- `sidebars/`: Sidebar UI components (`slat_linker_window.dart`, `assembly_handles_sidebar.dart`, `cargo_sidebar.dart`, `echo_sidebar.dart`, `grouping_sidebar.dart`, `layer_manager.dart`, `slat_design_sidebar.dart`, `slat_add_selection_panel.dart`, `slat_edit_selection_panel.dart`, `sidebar_tools.dart`)
- `echo_and_experimental_helpers/`: Echo plate mapping UI and master mix/PEG export:
  - Echo plates: `echo_plate_window.dart`, `echo_plate_grid.dart`, `echo_plate_painters.dart`, `echo_plate_sidebar.dart`, `echo_plate_bars.dart`, `echo_barcode_painter.dart`, `echo_plate_well.dart`, `echo_plate_constants.dart`, `echo_category_colors.dart`, `echo_export.dart`, `echo_well_config_dialog.dart`
  - Master mix: `master_mix_config.dart`, `master_mix_export.dart`
  - PEG purification: `peg_purification_config.dart`, `peg_purification_export.dart`
  - Manual handles: `manual_handle_dialog.dart`, `mass_manual_handle_dialog.dart`
  - State: `plate_layout_state.dart`, `plate_undo_stack.dart`
- `dialogs/`: Shared dialog components (`alert_window.dart`, `update_dialog.dart`)
- `drag_and_drop/`: Platform-specific drag-and-drop handling (`design_drop_target.dart`, `design_drop_target_desktop.dart`, `design_drop_target_web.dart`, `design_drop_target_stub.dart`)
- `grpc_client_architecture/`: Generated gRPC client code (do not edit manually)
- `2d_painters/`: 2D canvas rendering (`grid_painter.dart`, `slat_painter.dart`, `seed_painter.dart`, `slat_hover_painter.dart`, `handle_hover_painter.dart`, `delete_painter.dart`, `drag_box_painter.dart`, `helper_functions.dart`, `2d_view_svg_exporter.dart`, `export_svg_desktop.dart`, `export_svg_web.dart`)
- `graphics/`: 3D visualization and shared graphic widgets (`3d_painter.dart`, `custom_3d_meshes.dart`, `stl_exporter.dart`, `stl_export_validation.dart`, `crosshatch_shader.dart`, `assembly_color_legend.dart`, `honeycomb_pictogram.dart`, `line_chart.dart`, `rating_indicator.dart`, `status_indicator.dart`)

### Data Format
- Designs are stored as Excel files (.xlsx)
- DNA source plates are Excel files in `crisscross/dna_source_plates/`

## gRPC Protocol

Protocol definitions are in `flutter_app/python_dart_grpc_protocols/`:
- `hamming_evolve_communication.proto`: Main design/evolution protocol
- `health.proto`: Server health checking

**Note**: After regenerating Python gRPC code, you may need to fix the import in `hamming_evolve_communication_pb2_grpc.py` to use relative imports (add `from .` prefix).

## Code Style

- Line length limit: 120 characters (do not wrap lines before this point)
- **DO NOT run `dart format` or any auto-formatter on existing code.** This project intentionally keeps longer single-line expressions (e.g. chained method calls, map literals, multi-parameter function calls) on one line for readability. Splitting these across many lines makes the code harder to scan. Only break lines when they exceed 120 characters.
- All new files must include a file-level comment explaining the module's purpose
- All new classes and non-trivial methods must have doc comments
- Complex logic should have inline comments explaining "why", not "what"

## Code Patterns

- **Dart**: Mixin-based composition for large state/control classes (see `design_state_mixins/`, `grid_control_mixins/`)
- **Dart**: Barrel files for module-level exports
- **Dart**: Platform-specific implementations via conditional imports (web vs desktop) — see `drag_and_drop/`, `2d_painters/export_svg_*.dart`, `design_io/save_file_*.dart`
- **Python**: Click-based CLI commands in `cli_functions/`
- **Python**: Megastructure class is the central data container; most operations receive/modify a Megastructure instance

## Testing

- **Flutter**: Unit tests in `flutter_app/test/unit/` with test helpers/factory:
  - `app_management/`: blocked handle, design I/O round-trip, design state slat, ensure extension, excel utilities, handle link I/O, handle link manager, slat undo stack, STL export validation tests
  - `echo_plate/`: echo export, echo plate constants, master mix export, PEG purification export, plate duplicate, plate layout state, plate sort, plate sync, plate undo stack tests
- **Python**: Lacks formal test suites; contributions for pytest tests are welcome
- **After making changes to the Flutter app, always run `flutter test` from `flutter_app/` to verify existing tests still pass**
- **Important**: Flutter test output can be very large. Always redirect to a file and read the tail:
  ```bash
  cd flutter_app && flutter test > /tmp/test_output.txt 2>&1 && tail -50 /tmp/test_output.txt
  ```

## CI/CD

- `flutter-test.yml`: Runs `flutter analyze` + `flutter test --coverage` on push/PR to main
- `flutter-web-deploy.yml`: Deploys Flutter web app to GitHub Pages on `web-deploy` branch push
- `deploy_crisscross_kit_to_pypi.yml`: Builds wheels for Python 3.8-3.13 on Ubuntu/macOS/Windows (including ARM), publishes to PyPI on `python-*` tags
- `python-server-and-desktop-app-deploy.yml`: Builds Python server (via Nuitka) and desktop app
- `dependabot.yml`: Daily dependency updates for GitHub Actions

## Versioning

- **Flutter App**: Version tags like `v1.1.2`, version in `pubspec.yaml`
- **Python Library**: Version tags like `python-1.2.4`, managed by `setuptools-scm`
- Both follow independent version tracks

## Development Guidelines

- **Avoid code duplication**: Before writing new functions, search for existing implementations that can be reused. Prefer calling existing utility functions over duplicating logic.
- **Run tests after changes**: After modifying Flutter code, always run `flutter test` from `flutter_app/` to check that existing tests still pass. If modifying code covered by tests in `flutter_app/test/`, run those specific tests to verify nothing is broken.
- **Never call the Standard Loss "Hamming"**: The handle optimization uses a custom "Standard Loss" metric. Do not refer to it as "Hamming distance" — it is a distinct metric developed for this project.
- **Platform-aware code**: When adding file I/O or UI that differs between desktop and web, follow the existing pattern of stub/desktop/web conditional imports.

## Recent Changes (as of v1.1.2, May 2026)

Key features added since v1.0.0:
- **Slat grouping system**: Users can group slats for visualization and PEG purification workflows (`design_state_grouping_mixin.dart`, `grouping_sidebar.dart`)
- **PEG purification sheets**: Complete PEG purification export system (`peg_purification_config.dart`, `peg_purification_export.dart`)
- **Master mix generation**: Revamped master mix export system for lab use (`master_mix_config.dart`, `master_mix_export.dart`)
- **3D model/STL export**: Export 3D models directly from #-CAD, with validation (`stl_exporter.dart`, `stl_export_validation.dart`, `custom_3d_meshes.dart`)
- **Manual handle selection**: Manual handle automation selection for cargo/handle positions (`manual_handle_dialog.dart`, `mass_manual_handle_dialog.dart`)
- **Echo plate group splitting**: Option to split plates by group in the echo window
- **3D-2D layer linking**: 3D viewer linked with 2D when hiding/revealing slat layers

## Documentation

Online docs: https://hash-cad.readthedocs.io/en/latest/

Build docs locally:
```bash
# Install doc dependencies
pip install -r docs/requirements.txt
pip install -e crisscross_kit/

# Generate Dart API docs (requires Flutter SDK)
cd flutter_app && flutter pub get && dart doc --output=../docs/docs/flutter-api && cd ..

# Serve docs
cd docs
mkdocs serve
```

---

## Codex-Specific Notes

If you are OpenAI Codex (or another sandboxed agent):

### Environment Setup
- You will likely not have Flutter SDK or Dart pre-installed. For Python-only changes to `crisscross_kit/`, you can work without Flutter.
- For Flutter changes, you need the Flutter SDK. Check if it's available with `flutter --version`.
- The Python library can be installed with `cd crisscross_kit && pip install -e .` — the C extension requires a C compiler (gcc/clang).

### Key Differences from Claude Code
- This repo uses **Excel files (.xlsx)** as the primary data format — not JSON or YAML. The `excel` and `openpyxl` packages handle I/O.
- The Flutter app uses **Provider** for state management (not Riverpod, Bloc, or Redux).
- 3D rendering uses **three_js** (a Dart port of three.js), not native platform 3D APIs.
- gRPC client code in `lib/grpc_client_architecture/` is auto-generated — do not modify it directly.

### Testing Without a Display
- Flutter tests can run headless: `flutter test` works without a display server.
- Python visualization tests (pyvista, matplotlib) may need `MPLBACKEND=Agg` set.

### File Paths to Watch
- `flutter_app/lib/app_management/` — Core application state; changes here have wide impact
- `crisscross_kit/crisscross/core_functions/megastructures.py` — Central data model; changes cascade
- `flutter_app/python_dart_grpc_protocols/` — Protocol definitions; changes require regenerating both Python and Dart code