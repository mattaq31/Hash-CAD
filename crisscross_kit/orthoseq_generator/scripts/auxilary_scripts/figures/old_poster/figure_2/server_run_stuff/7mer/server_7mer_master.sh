#!/bin/bash

set -euo pipefail

sbatch server_7mer_sigma0p25.sh
sbatch server_7mer_sigma0p5.sh
sbatch server_7mer_sigma1.sh
sbatch server_7mer_sigma1p5.sh
