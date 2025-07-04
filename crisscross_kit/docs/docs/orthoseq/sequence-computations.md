# Sequence Computations

The sequence computations module provides comprehensive tools for analyzing DNA sequences, calculating binding energies, and ensuring orthogonality in DNA handle libraries.

## Overview

Accurate sequence analysis is fundamental to successful DNA megastructure design. This module offers:

- **Binding Energy Calculation**: Predict hybridization energies
- **Thermodynamic Analysis**: Assess sequence stability
- **Orthogonality Assessment**: Ensure sequences don't cross-react
- **Sequence Metrics**: Calculate various sequence properties
- **Batch Processing**: Analyze large sequence libraries efficiently

## Core Functions

::: orthoseq_generator.sequence_computations

## Key Features

### Energy Calculations

The module provides several methods for calculating binding energies:

- **Nearest Neighbor Model**: Standard thermodynamic predictions
- **Advanced Thermodynamics**: Account for complex secondary structures
- **Salt Concentration Effects**: Adjust for experimental conditions
- **Temperature Dependence**: Calculate energies at different temperatures

### Orthogonality Analysis

Ensure your sequences don't interfere with each other:

- **Cross-hybridization Prediction**: Identify potential interactions
- **Specificity Scoring**: Quantify sequence specificity
- **Mismatch Tolerance**: Account for experimental variation
- **Library Validation**: Verify entire handle libraries

## Usage Examples

!!! example "Basic Energy Calculation"
    ```python
    from orthoseq_generator import sequence_computations
    
    # Calculate binding energy for a sequence pair
    seq1 = "ATCGATCGATCG"
    seq2 = "CGATCGATCGAT"  # complement
    
    energy = sequence_computations.calculate_binding_energy(seq1, seq2)
    print(f"Binding energy: {energy:.2f} kcal/mol")
    ```

!!! example "Orthogonality Check"
    ```python
    # Check orthogonality of a sequence library
    sequences = ["ATCGATCG", "GCTAGCTA", "TTAACCGG"]
    
    orthogonality = sequence_computations.check_orthogonality(
        sequences, 
        temperature=37,
        salt_concentration=50e-3
    )
    
    print(f"Library is orthogonal: {orthogonality}")
    ```

!!! example "Batch Processing"
    ```python
    # Process large sequence library
    large_library = load_sequence_library("library.fasta")
    
    results = sequence_computations.batch_analyze(
        large_library,
        include_secondary_structure=True,
        parallel=True
    )
    ```

## Related Modules

- [Vertex Cover Algorithms](vertex-cover.md) - Optimization algorithms for sequence selection
- [Helper Functions](helper-functions.md) - Utility functions for sequence manipulation
