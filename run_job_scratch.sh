#!/usr/bin/env bash
#SBATCH --job-name=pyrecodes_scratch
#SBATCH --partition=normal.4h
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=%x_%j.out

set -euo pipefail
echo "[JOB] start: $(date) on $(hostname)"
echo "[JOB] jobid=$SLURM_JOB_ID cpus=$SLURM_CPUS_PER_TASK"

HOME_PROJ="$HOME/run_pyrecodes"
SCRATCH_PROJ="/cluster/scratch/$USER/run_pyrecodes"

#
JOB_TAG="${SLURM_JOB_ID:-run}"
SCR_INPUT="$SCRATCH_PROJ/input_data_common"
SCR_RESULTS="$SCRATCH_PROJ/run_dir/results"
SCR_OUTPUT="$SCRATCH_PROJ/output_dir/$JOB_TAG"

mkdir -p "$SCR_INPUT" "$SCR_RESULTS" "$SCR_OUTPUT"

#
HOME_OUTPUT_BASE="$HOME_PROJ/output_dir"
HOME_OUTPUT="$HOME_OUTPUT_BASE/$JOB_TAG"
mkdir -p "$HOME_OUTPUT_BASE" 

# 
source "$HOME_PROJ/activate_env.sh"


rsync -a "$HOME_PROJ/input_data_common/" "$SCR_INPUT/"
rsync -a "$HOME_PROJ/run_dir/results/" "$SCR_RESULTS/"

#
mkdir -p "$SCRATCH_PROJ"
cd "$SCRATCH_PROJ"
echo "[JOB] workdir: $(pwd)"

#
srun python "$HOME_PROJ/run_pyrecodes_single_proc.py" \
  --mainFile                "$SCR_INPUT/Alameda_Main.json" \
  --SystemConfigurationFile "$HOME_PROJ/system_config_samples/Alameda_SystemConfiguration_1.json" \
  --ComponentLibraryFile    "$SCR_INPUT/Alameda_ComponentLibrary.json" \
  --r2dRunDir               "$SCR_RESULTS" \
  --inputDataDir            "$SCR_INPUT" \
  --outputDir               "$SCR_OUTPUT"

#
echo "[JOB] syncing results → $HOME_OUTPUT"
rsync -a "$SCR_OUTPUT/" "$HOME_OUTPUT/"

#
ln -sfn "$HOME_OUTPUT" "$HOME_OUTPUT_BASE/latest"

echo "[JOB] done: $(date)"
