#!/bin/bash
#SBATCH -c 20
#SBATCH --mem=20G
#SBATCH -t 0:15:00
#SBATCH -p priority
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=florian_katzmeier@dfci.hms.edu

module load conda/miniforge3/24.11.3-0
conda activate cc
python -u Hash-CAD/crisscross_kit/orthoseq_generator/scripts/figures/figure_2/run_pipeline.py --config 6mer_sigma1p5.toml
