"""Simulation facade: CSMA/CA + OFDMA combined (IEEE 802.11ax style)."""
from simulator.modes.mode_combined import run_combined, run_combined_scenario

__all__ = ["run_combined", "run_combined_scenario"]
