"""LIGHT / MEDIUM / HEAVY load profiles (λ packets/sec/STA)."""
from dataclasses import dataclass
from typing import Dict


@dataclass
class LoadProfile:
    name: str
    lam: float       # packets/sec per station (Poisson rate)
    cbr_interval: float  # seconds between packets for CBR (= 1/lam)
    description: str

    @classmethod
    def from_lambda(cls, name: str, lam: float, description: str = "") -> "LoadProfile":
        return cls(name=name, lam=lam, cbr_interval=1.0 / lam, description=description)


LIGHT = LoadProfile.from_lambda("light", lam=5.0, description="Low load: ~5 pkt/s per STA")
MEDIUM = LoadProfile.from_lambda("medium", lam=20.0, description="Medium load: ~20 pkt/s per STA")
HEAVY = LoadProfile.from_lambda("heavy", lam=100.0, description="High load: ~100 pkt/s per STA")

PROFILES: Dict[str, LoadProfile] = {
    "light": LIGHT,
    "medium": MEDIUM,
    "heavy": HEAVY,
}


def get_profile(name: str) -> LoadProfile:
    if name not in PROFILES:
        raise ValueError(f"Unknown load profile '{name}'. Choose from: {list(PROFILES)}")
    return PROFILES[name]


def lambda_from_load(traffic_load: float) -> float:
    """Convert normalised load [0,1] to packets/sec per station."""
    return max(1.0, traffic_load * 100.0)
