# pyrecodes_project
A project using R2D-pyrecodes wrapper for Alameda Regional Recovery and Resource Allocation Study

This repository runs regional disaster-recovery simulations for Alameda using the [pyrecodes](https://github.com/NikolaBlagojevic/pyrecodes) framework and damage/loss results produced by the NHERI SimCenter R2D workflow on the ETH Zurich cluster. It supports individual simulations and parallel parameter studies on SLURM/MPI clusters. The results will be used for surrogate modeling training in the manuscript paper "Identifying Early-Phase Recovery Bottlenecks Through Regional Resilience Simulations and Outcome-Based Metrics".

## Main files

- `run_job_scratch_parallel.sh` — The main script for submitting the pyrecodes simulation to an HPC cluster.
- `activate_env.sh` — Loads the required cluster modules and Python environment.
- `run_pyrecodes_single_proc.py` — Runs pyrecodes simulations using a single process.
- `run_pyrecodes_parallel.py` — Runs multiple simulation configurations in parallel using MPI.
- `generate_component_library_samples.py` — Generates different recovery-resource allocation samples.
- `requirements.txt` — Lists the required Python packages.

## Main folders

- `input_data_common/` — Common input data, including Alameda configuration files, infrastructure networks, geographic data, and R2D results.
- `component_library_samples/` — Sampled component libraries with different recovery-resource quantities.
- `system_config_samples/` — Sampled pyrecodes system configurations.
- `run_dir/results/` — Damage and loss results used as simulation inputs.
- `output_dir/` — Simulation outputs for different samples and realizations.
- `pyrecodes/` — The pyrecodes source code used by this study.

