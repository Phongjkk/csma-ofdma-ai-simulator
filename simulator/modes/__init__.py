"""Simulation mode facades: SU-only, OFDMA-only, combined."""
from simulator.modes.mode_su import run_su, run_su_scenario
from simulator.modes.mode_ofdma import run_ofdma, run_ofdma_scenario
from simulator.modes.mode_combined import run_combined, run_combined_scenario

__all__ = ["run_su", "run_su_scenario", "run_ofdma", "run_ofdma_scenario",
           "run_combined", "run_combined_scenario"]
