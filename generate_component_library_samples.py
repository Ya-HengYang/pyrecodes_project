#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate multiple component library samples by randomly sampling
'Supply' Amount values within [Amount/2, Amount*2] using uniform distribution,
and print summary statistics.
"""

import json
import numpy as np
from pathlib import Path
import argparse
import copy
from collections import defaultdict

def generate_samples(base_file, output_dir, num_samples):
    base_file = Path(base_file)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with base_file.open("r", encoding="utf-8") as f:
        base_data = json.load(f)

    supply_dict = base_data["EmergencyResponseCenter"]["Supply"]

    # collection supply samples
    stats = defaultdict(list)

    for i in range(1, num_samples + 1):
        new_data = copy.deepcopy(base_data)
        new_supply = {}

        for k, v in supply_dict.items():
            base_amount = v["Amount"]
            sampled_amount = float(np.random.uniform(base_amount / 2, base_amount * 2))
            stats[k].append(sampled_amount)
            new_supply[k] = {
                "Amount": sampled_amount,
                "FunctionalityToAmountRelation": v["FunctionalityToAmountRelation"]
            }

        new_data["EmergencyResponseCenter"]["Supply"] = new_supply

        out_path = output_dir / f"{base_file.stem}_{i}.json"
        with out_path.open("w", encoding="utf-8") as out_f:
            json.dump(new_data, out_f, indent=2)

        print(f"✅ Generated: {out_path}")

    # --- print summary ---
    print("\n[SUMMARY] Sampling statistics (Amount ranges):")
    print(f"{'Supply Key':<30}{'Min':>12}{'Mean':>13}{'Max':>13}")
    print("-" * 70)
    for k, values in stats.items():
        print(f"{k:<30}{min(values):12.2f}{np.mean(values):13.2f}{max(values):13.2f}")
    print("-" * 70)
    print("[INFO] Sampling summary complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate component library samples.")
    parser.add_argument("--baseFile", required=True, help="Path to base Alameda_ComponentLibrary.json")
    parser.add_argument("--outputDir", required=True, help="Output directory for generated samples")
    parser.add_argument("--numSamples", type=int, default=10, help="Number of samples to generate")
    args = parser.parse_args()

    generate_samples(args.baseFile, args.outputDir, args.numSamples)
