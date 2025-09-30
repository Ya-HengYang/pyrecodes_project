cat > ~/run_pyrecodes/job_euler.slurm << 'SLURM'
#!/bin/bash
#SBATCH --partition=normal.4h
#SBATCH --job-name=pyrecodes
#SBATCH --nodes 1
#SBATCH --ntasks=2
#SBATCH --time=02:00:00
#SBATCH --output=pyrecodes.%j.out
#SBATCH --error=pyrecodes.%j.err

set -euo pipefail

# --- Modules + env (matches your working interactive setup) ---
source $HOME/run_pyrecodes/activate_env.sh

# Non-GUI matplotlib backend (still allows plt.savefig)
export MPLBACKEND=Agg

# Your parallel driver expects this
export python_path="$(which python)"

# --- Paths ---
CODE_DIR="$HOME/run_pyrecodes"
RUNROOT="/cluster/scratch/$USER/run_pyrecodes_runs"
RUNDIR="$RUNROOT/${SLURM_JOB_ID}"
mkdir -p "$RUNDIR"

# Optionally snapshot code+inputs into SCRATCH (faster I/O, reproducible)
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
SLURM