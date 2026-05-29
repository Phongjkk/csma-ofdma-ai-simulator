"""Dataclass holding all LSTM + training hyperparameters."""
from dataclasses import dataclass


@dataclass
class HyperParams:
    # Model architecture
    n_features: int = 6
    hidden_size: int = 64
    num_layers: int = 2
    dropout: float = 0.2
    seq_in: int = 50       # look-back window (5 sec × 10 Hz)
    seq_out: int = 50      # prediction horizon (5 sec × 10 Hz)

    # Training
    epochs: int = 50
    batch_size: int = 64
    lr: float = 1e-3
    weight_decay: float = 1e-5
    grad_clip: float = 1.0

    # LR scheduler (ReduceLROnPlateau)
    lr_patience: int = 5
    lr_factor: float = 0.5
    lr_min: float = 1e-6

    # Early stopping
    early_stop_patience: int = 10
    early_stop_delta: float = 1e-5

    # Data
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15

    # Misc
    seed: int = 42
    device: str = "cpu"   # "cuda" if available
    save_path: str = "ai/saved_models/lstm_checkpoint.pt"
