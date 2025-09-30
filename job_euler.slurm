#!/bin/bash
#SBATCH --partition=normal.4h
#SBATCH --job-name=pyrecodes
#SBATCH --ntasks=2
#SBATCH --time=02:00:00
#SBATCH --output=pyrecodes.%j.out
#SBATCH --error=pyrecodes.%j.err

set -euo pipefail

# --- Modules + env ---
module purge
module load stack/2024-06 gcc/12.2.0
module load openmpi/4.1.6
module load python/3.11.6
module load py-mpi4py/3.1.4
source ~/run_pyrecodes/venv311/bin/activate

# Non-GUI matplotlib (saving figs still works)
export MPLBACKEND=Agg

# Your parallel driver expects this
export python_path="$(which python)"

# --- Paths ---
CODE_DIR="$HOME/run_pyrecodes"
RUNROOT="/cluster/scratch/$USER/run_pyrecodes_runs"
RUNDIR="$RUNROOT/${SLURM_JOB_ID}"
mkdir -p "$RUNDIR"

# Snapshot code+inputs into SCRATCH (faster I/O, reproducible)
rsync -a --exclude ".git" --exclude "output_dir*" --exclude "run_dir/results*" \
  "$CODE_DIR/" "$RUNDIR/"

cd "$RUNDIR"

# --- Run ---
srun -n "${SLURM_NTASKS}" python run_pyrecodes_parallel.py \
  --mainFile                  input_data_common/Alameda_Main.json \
  --SystemConfigurationDir    system_config_samples \
  --SystemConfigurationBasename Alameda_SystemConfiguration \
  --ComponentLibraryFile      input_data_common/Alameda_ComponentLibrary.json \
  --r2dRunDir                 run_dir/results \
  --inputDataDir              input_data_common \
  --outputDir                 output_dir \
  --savePickleFile            True

# --- Bring results back to HOME ---
mkdir -p "$HOME/run_pyrecodes/results_archive/${SLURM_JOB_ID}"
rsync -a "$RUNDIR/output_dir/" \
  "$HOME/run_pyrecodes/results_archive/${SLURM_JOB_ID}/"
