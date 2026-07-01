#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate component library samples using uniform and log-uniform sampling
within prescribed bounds, and export sampled inputs to a pickle file.
"""

import json
import numpy as np
from pathlib import Path
import argparse
import copy
import pickle
from collections import defaultdict

SAMPLING_CONFIG = {
    "RepairCrew_Buildings": {
        "bounds": (3000, 20000),
        "dist": "log_uniform"
    },
    "CleanUpCrew": {
        "bounds": (40, 300),
        "dist": "log_uniform"
    },
    "RepairCrew_Transportation": {
        "bounds": (100, 2000),
        "dist": "log_uniform"
    },
    "RepairCrew_Water": {
        "bounds": (10, 300),
        "dist": "log_uniform"
    },
    "FirstResponderEngineer": {
        "bounds": (10, 100),
        "dist": "log_uniform"
    },
    "Money": {
        "bounds": (2e5, 4e6),
        "dist": "log_uniform"
    },
    "SeniorEngineer": {
        "bounds": (50, 600),
        "dist": "log_uniform"
    },
    "Contractor": {
        "bounds": (50, 600),
        "dist": "log_uniform"
    },
    "DemolitionCrew": {
        "bounds": (10, 50),
        "dist": "log_uniform"
    },
    "PlanCheckEngineeringTeam": {
        "bounds": (50, 600),
        "dist": "log_uniform"
    },
    "SitePreparationCrew": {
        "bounds": (20, 200),
        "dist": "log_uniform"
    },
    "EngineeringDesignTeam": {
        "bounds": (100, 1000),
        "dist": "log_uniform"
    }
}

def sample_value(bounds, dist):
    low, high = bounds

    if dist == "uniform":
        return float(np.random.uniform(low, high))

    elif dist == "log_uniform":
        return float(np.exp(
            np.random.uniform(np.log(low), np.log(high))
        ))

    else:
        raise ValueError(f"Unknown distribution type: {dist}")


def generate_samples(base_file, output_dir, num_samples):
    base_file = Path(base_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with base_file.open("r", encoding="utf-8") as f:
        base_data = json.load(f)

    base_supply = base_data["EmergencyResponseCenter"]["Supply"]

    # store all sampled inputs for pickle export
    sampled_inputs = defaultdict(list)

    for i in range(1, num_samples + 1):
        new_data = copy.deepcopy(base_data)
        new_supply = {}

        for key, cfg in SAMPLING_CONFIG.items():
            if key not in base_supply:
                raise KeyError(f"Supply key '{key}' not found in base file")

            sampled_amount = sample_value(cfg["bounds"], cfg["dist"])
            sampled_inputs[key].append(sampled_amount)

            new_supply[key] = {
                "Amount": sampled_amount,
                "FunctionalityToAmountRelation":
                    base_supply[key]["FunctionalityToAmountRelation"]
            }

        new_data["EmergencyResponseCenter"]["Supply"] = new_supply

        out_path = output_dir / f"{base_file.stem}_{i}.json"
        with out_path.open("w", encoding="utf-8") as out_f:
            json.dump(new_data, out_f, indent=2)

        print(f"Generated: {out_path}")

    # --- export samples to pickle ---
    pickle_path = output_dir / "sampled_inputs.pkl"
    with pickle_path.open("wb") as pf:
        pickle.dump(dict(sampled_inputs), pf)

    print(f"\nSaved sampled inputs to: {pickle_path}")

    # --- optional summary ---
    print("\n[SUMMARY] Sampling statistics:")
    print(f"{'Variable':<35}{'Min':>12}{'Mean':>13}{'Max':>13}")
    print("-" * 75)
    for k, values in sampled_inputs.items():
        print(f"{k:<35}{min(values):12.2f}{np.mean(values):13.2f}{max(values):13.2f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate component library samples.")
    parser.add_argument("--baseFile", required=True, help="Path to base component library JSON")
    parser.add_argument("--outputDir", required=True, help="Output directory for samples")
    parser.add_argument("--numSamples", type=int, default=50, help="Number of samples")
    args = parser.parse_args()

    generate_samples(args.baseFile, args.outputDir, args.numSamples)
