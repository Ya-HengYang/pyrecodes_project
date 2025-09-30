#!/usr/bin/env bash
#SBATCH --job-name=pyrecodes1
#SBATCH --partition=normal.4h
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out

set -euo pipefail
echo "SLURM_CPUS_PER_TASK=${SLURM_CPUS_PER_TASK:-unset}"
srun bash "$HOME/run_pyrecodes/sh_file_1.sh"
