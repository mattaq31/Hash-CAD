"""
Compatibility shim for the historical `sequence_computations` module.

The implementation now lives in:
- `sequence_generation.py`
- `energy_computations.py`
- `energy_plots.py`

Keep this module as a re-export layer until callers are migrated.
"""

from orthoseq_generator.energy_computations import *  # noqa: F401,F403
from orthoseq_generator.energy_plots import *  # noqa: F401,F403
from orthoseq_generator.sequence_generation import *  # noqa: F401,F403
