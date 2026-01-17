# eqcorr2d - Parasitic Valency Compute Engine

The `eqcorr2d` module is a high-performance C extension for computing the parasitic valency matches between + and - handles in a megastructure design. It is also used internally by the evolutionary algorithm to evaluate the quality of handle assignments.
## Installation

As a user, the module is installed automatically when you install the `crisscross_kit` package.

As a developer, the C extension compiles automatically if you've installed the main repository code (via `pip install -e .` or similar). If you encounter issues, ensure you have a C compiler available:

```bash
# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt-get install build-essential

# Windows
# Install Visual Studio Build Tools
```

## Overview

The module provides functions to:

- Compute match scores between pairs of +/- handle arrays
- Support both 1D (linear) and 2D (grid) slat geometries, including their various rotations
- Generate histograms of match counts for analysis
- Compute similarity scores to detect potential slat duplication risks

## Usage Example

In most cases, you can simply call the library by using the high-level `get_parasitic_interactions` function from the `Megastructure` class:
```python
from crisscross.core_functions.megastructures import Megastructure

megastructure = Megastructure(import_design_file='path_to_design.xlsx')

parasitic_interactions = megastructure.get_parasitic_interactions()

# the parasitic_interactions dict will contain the 'worst_match_score' and 'mean_log_score',
# which are the worst interaction count and the 'Loss' from the main paper.  
# The histogram and similarity scores are also available for further analysis.
```
The `Megastructure` class will take care of all configuration details required for the algorithm to operate.  However, one can also use `eqcorr2d` directly, for which the `comprehensive_score_analysis` function is provided.  Check the [API Reference](library-reference.md) for more details.

## Low-Level C Engine

The core `compute` function is implemented in C. Its signature can be found below:

```python
def compute(
    A_list: Sequence[np.ndarray],      # Handle arrays (2D uint8)
    B_list: Sequence[np.ndarray],      # Antihandle arrays (2D uint8)
    compute_instructions: Sequence[np.ndarray],  # Computation pairs
    do_hist: int,                       # Generate histogram
    do_full: int,                       # Return full results
    report_worst: int,                  # Report worst matches
    local_histogram: int = 0,           # Per-pair histograms
) -> Tuple[
    Optional[np.ndarray],              # Global histogram
    Optional[List[List[np.ndarray]]],  # Full match matrices
    Optional[np.ndarray],              # Deprecated (always None)
    Optional[np.ndarray],              # Local histograms (3D array)
]
```
Further details can be found in the [C API Reference](c-api-reference.md).

!!! note
    In most cases, you should use the high-level `comprehensive_score_analysis` or `wrap_eqcorr2d` function from `eqcorr2d_interface` rather than calling the C engine directly.
---

For more detailed code documentation, see the [API Reference](library-reference.md).
