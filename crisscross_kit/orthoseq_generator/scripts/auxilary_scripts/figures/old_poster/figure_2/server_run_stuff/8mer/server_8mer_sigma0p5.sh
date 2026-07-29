#!/bin/bash
#SBATCH -c 20
#SBATCH --mem=120G
#SBATCH -t 108:00:00
#SBATCH -p medium
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=florian_katzmeier@dfci.hms.edu

module load conda/miniforge3/24.11.3-0
conda activate cc
python -u Hash-CAD/crisscross_kit/orthoseq_generator/scripts/figures/figure_2/run_pipeline.py --config 8mer_sigma0p5.toml
