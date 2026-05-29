"""CLI: python scripts/generate_dataset.py --runs 200 --out results/datasets/"""
import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Generate AI training dataset from simulator")
    parser.add_argument("--runs", type=int, default=3, help="Repeats per scenario")
    parser.add_argument("--out", type=str, default="results/datasets", help="Output directory")
    parser.add_argument("--sim-time", type=float, default=30.0, help="Simulation time (s)")
    parser.add_argument("--seq-in", type=int, default=50, help="Look-back window size")
    parser.add_argument("--seq-out", type=int, default=50, help="Prediction horizon size")
    parser.add_argument("--max-scenarios", type=int, default=None, help="Limit scenarios (debug)")
    args = parser.parse_args()

    from ai.data.dataset_generator import generate_dataset
    print(f"Generating dataset: repeats={args.runs}, out={args.out}")
    X, y, scaler = generate_dataset(
        n_repeats=args.runs,
        sim_time=args.sim_time,
        seq_in=args.seq_in,
        seq_out=args.seq_out,
        output_dir=args.out,
        max_scenarios=args.max_scenarios,
    )
    print(f"Done. X_train shape: {X.shape}, y_train shape: {y.shape}")


if __name__ == "__main__":
    main()
