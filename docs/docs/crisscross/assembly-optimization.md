# Assembly Handle Optimization

The slat handle match evolver module provides access to our evolutionary algorithm for intelligently assigning assembly handles to a megastructure design. The below are the main functions and classes available in this module.

## Handle Evolution

Core evolutionary algorithm implementation for handle sequence evolution.

::: crisscross.slat_handle_match_evolver.handle_evolution

## Handle Mutation

Mutation operators for genetic algorithm optimization.

::: crisscross.slat_handle_match_evolver.handle_mutation

## Utility Functions

Utility functions for generating random sequences.
::: crisscross.slat_handle_match_evolver

## Random Hamming Optimizer

Random search baseline algorithm.

::: crisscross.slat_handle_match_evolver.random_hamming_optimizer

## Older Tubular Slat Match Compute

Functions for calculating Hamming distances (our previous naming convention for parasitic interactions) and sequence metrics for tubular slat matching.

::: crisscross.slat_handle_match_evolver.tubular_slat_match_compute

## Optuna Integration (mostly deprecated, but can be revived if necessary)

Hyperparameter optimization using the Optuna framework (optional, mainly for debugging). Requires `optuna` to be installed.

::: crisscross.slat_handle_match_evolver.handle_evolve_with_optuna
