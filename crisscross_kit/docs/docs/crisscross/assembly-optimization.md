# Assembly Handle Optimization

The assembly handle optimization module provides access to our evolutionary algorithm for intelligently assigning assembly handles to a megastructure design.  The below are the main functions and classes available in this module.

## Handle Evolution

Core evolutionary algorithm implementation for handle sequence evolution.

::: crisscross.assembly_handle_optimization.handle_evolution

## Hamming Compute

Functions for calculating Hamming distances and sequence metrics.

::: crisscross.assembly_handle_optimization.hamming_compute

## Handle Mutation

Mutation operators for genetic algorithm optimization.

::: crisscross.assembly_handle_optimization.handle_mutation

## Random Hamming Optimizer

Random search baseline algorithm.

::: crisscross.assembly_handle_optimization.random_hamming_optimizer

## Optuna Integration

Hyperparameter optimization using the Optuna framework (optional, mainly for debugging).  Requires `optuna` to be installed.

::: crisscross.assembly_handle_optimization.handle_evolve_with_optuna
