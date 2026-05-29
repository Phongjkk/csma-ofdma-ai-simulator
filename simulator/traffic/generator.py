"""Poisson packet arrival generator — pre-schedules all events."""
import random
from typing import List, Tuple

from simulator.network.packet import Packet, reset_counter


def generate_poisson_arrivals(
    station_id: int,
    lam: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
    rng: random.Random,
) -> List[Packet]:
    """Generate Poisson-distributed packet arrivals for one station."""
    packets: List[Packet] = []
    t = rng.expovariate(lam)
    while t < sim_time:
        pkt = Packet(
            station_id=station_id,
            size_bytes=payload_bytes + mac_header_bytes,
            arrival_time=t,
        )
        packets.append(pkt)
        t += rng.expovariate(lam)
    return packets


def generate_cbr_arrivals(
    station_id: int,
    interval: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
) -> List[Packet]:
    """Constant Bit Rate arrivals."""
    packets: List[Packet] = []
    t = interval
    while t < sim_time:
        pkt = Packet(
            station_id=station_id,
            size_bytes=payload_bytes + mac_header_bytes,
            arrival_time=t,
        )
        packets.append(pkt)
        t += interval
    return packets


def generate_ramp_arrivals(
    station_id: int,
    lam_start: float,
    lam_end: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
    rng: random.Random,
) -> List[Packet]:
    """Linearly increasing Poisson rate from lam_start to lam_end."""
    packets: List[Packet] = []
    t = 0.0
    while t < sim_time:
        frac = t / sim_time
        lam = lam_start + frac * (lam_end - lam_start)
        lam = max(lam, 0.1)
        dt = rng.expovariate(lam)
        t += dt
        if t < sim_time:
            pkt = Packet(
                station_id=station_id,
                size_bytes=payload_bytes + mac_header_bytes,
                arrival_time=t,
            )
            packets.append(pkt)
    return packets


def generate_spike_arrivals(
    station_id: int,
    lam_base: float,
    lam_spike: float,
    spike_start: float,
    spike_end: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
    rng: random.Random,
) -> List[Packet]:
    """Poisson with a spike period of higher rate."""
    packets: List[Packet] = []
    t = rng.expovariate(lam_base)
    while t < sim_time:
        lam = lam_spike if spike_start <= t < spike_end else lam_base
        pkt = Packet(
            station_id=station_id,
            size_bytes=payload_bytes + mac_header_bytes,
            arrival_time=t,
        )
        packets.append(pkt)
        t += rng.expovariate(lam)
    return packets


def generate_oscillating_arrivals(
    station_id: int,
    lam_min: float,
    lam_max: float,
    period: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
    rng: random.Random,
) -> List[Packet]:
    """Sinusoidally varying Poisson rate."""
    import math
    packets: List[Packet] = []
    t = 0.0
    while t < sim_time:
        phase = (t % period) / period
        lam = lam_min + (lam_max - lam_min) * (0.5 + 0.5 * math.sin(2 * math.pi * phase))
        lam = max(lam, 0.1)
        dt = rng.expovariate(lam)
        t += dt
        if t < sim_time:
            pkt = Packet(
                station_id=station_id,
                size_bytes=payload_bytes + mac_header_bytes,
                arrival_time=t,
            )
            packets.append(pkt)
    return packets


def generate_all_arrivals(
    n_stations: int,
    lam: float,
    sim_time: float,
    payload_bytes: int,
    mac_header_bytes: int,
    pattern: str,
    rng: random.Random,
) -> List[Packet]:
    """Generate arrival packets for all stations."""
    reset_counter()
    all_packets: List[Packet] = []
    for sid in range(n_stations):
        if pattern == "poisson":
            pkts = generate_poisson_arrivals(sid, lam, sim_time, payload_bytes, mac_header_bytes, rng)
        elif pattern == "cbr":
            pkts = generate_cbr_arrivals(sid, 1.0 / lam, sim_time, payload_bytes, mac_header_bytes)
        elif pattern == "ramp":
            pkts = generate_ramp_arrivals(sid, lam * 0.1, lam, sim_time, payload_bytes, mac_header_bytes, rng)
        elif pattern == "spike":
            pkts = generate_spike_arrivals(sid, lam * 0.2, lam, sim_time * 0.4, sim_time * 0.7, sim_time, payload_bytes, mac_header_bytes, rng)
        elif pattern == "oscillate":
            pkts = generate_oscillating_arrivals(sid, lam * 0.2, lam, sim_time / 3, sim_time, payload_bytes, mac_header_bytes, rng)
        else:
            pkts = generate_poisson_arrivals(sid, lam, sim_time, payload_bytes, mac_header_bytes, rng)
        all_packets.extend(pkts)
    return sorted(all_packets, key=lambda p: p.arrival_time)
