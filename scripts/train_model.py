"""CLI: python scripts/train_model.py --model lstm --epochs 50"""
import argparse
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    parser = argparse.ArgumentParser(description="Train AI prediction model")
    parser.add_argument("--model", type=str, default="lstm",
                        choices=["lstm", "moving_average", "linear_regression", "arima"],
                        help="Model type")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--hidden", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--data-dir", type=str, default="results/datasets")
    parser.add_argument("--save-path", type=str, default="ai/saved_models/lstm_checkpoint.pt")
    args = parser.parse_args()

    # Load data
    data_dir = args.data_dir
    X_train = np.load(os.path.join(data_dir, "X_train.npy"))
    y_train = np.load(os.path.join(data_dir, "y_train.npy"))
    X_val = np.load(os.path.join(data_dir, "X_val.npy"))
    y_val = np.load(os.path.join(data_dir, "y_val.npy"))
    X_test = np.load(os.path.join(data_dir, "X_test.npy"))
    y_test = np.load(os.path.join(data_dir, "y_test.npy"))
    print(f"Loaded: train={X_train.shape}, val={X_val.shape}, test={X_test.shape}")

    from ai.evaluation.comparator import ModelComparator
    comparator = ModelComparator()

    if args.model == "lstm":
        from ai.training.hyperparams import HyperParams
        from ai.training.trainer import Trainer
        hp = HyperParams(
            n_features=X_train.shape[-1],
            hidden_size=args.hidden,
            num_layers=args.layers,
            epochs=args.epochs,
            batch_size=args.batch_size,
            save_path=args.save_path,
        )
        trainer = Trainer(hp)
        model = trainer.train(X_train, y_train, X_val, y_val)
        preds = model.predict(X_test)
        comparator.add("LSTM", y_test, preds)

    elif args.model == "moving_average":
        from ai.models.moving_average import MovingAverageModel
        m = MovingAverageModel(n_steps=y_train.shape[1])
        m.fit(X_train, y_train)
        preds = m.predict(X_test)
        comparator.add("MovingAverage", y_test, preds)

    elif args.model == "linear_regression":
        from ai.models.linear_regression import LinearRegressionModel
        m = LinearRegressionModel(n_steps=y_train.shape[1])
        m.fit(X_train, y_train)
        preds = m.predict(X_test)
        comparator.add("LinearRegression", y_test, preds)

    comparator.print_summary()
    print("Training complete.")


if __name__ == "__main__":
    main()
