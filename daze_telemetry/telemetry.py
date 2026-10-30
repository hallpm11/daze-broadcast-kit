"""Convert iRacing's shared-memory SDK fields into a small, safe overlay snapshot.

No camera commands, broadcasts, credential handling, remote network connections,
or invented live positions. Missing data is represented by null/omitted rows.
"""
from __future__ import annotations

import time
from typing import Any

# iRacing SDK SessionFlags bitmask: documented in irsdk_defines.h.
CHECKERED = 0x00000001
WHITE = 0x00000002
GREEN = 0x00000004
YELLOW = 0x00000008
RED = 0x00000010
YELLOW_WAVING = 0x00000100
CAUTION = 0x00004000
CAUTION_WAVING = 0x00008000


def _get(ir: Any, key: str, default: Any = None) -> Any:
    try:
        result = ir[key]
        return default if result is None else result
    except (KeyError, IndexError, TypeError, ValueError, AttributeError, RuntimeError):
        return default


def _field(data: Any, key: str, default: Any = None) -> Any:
    return data.get(key, default) if isinstance(data, dict) else default


def _number(value: Any, min_value: int = 0) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        n = int(value)
        return n if n >= min_value else None
    except (ValueError, TypeError, OverflowError):
        return None


def _positive_float(value: Any) -> float | None:
    try:
        n = float(value)
        return round(n, 3) if 0 < n < 3600 else None
    except (ValueError, TypeError, OverflowError):
        return None


def _item(values: Any, idx: int | None, default: Any = None) -> Any:
    if idx is None or not isinstance(values, (list, tuple)) or idx < 0 or idx >= len(values):
        return default
    return values[idx]


def _text(value: Any, length: int = 80) -> str | None:
    if value is None:
        return None
    result = ' '.join(str(value).split()).strip()
    return result[:length] or None


def flag_label(flags: Any) -> str | None:
    bits = _number(flags)
    if bits is None:
        return None
    if bits & CHECKERED:
        return 'checkered'
    if bits & RED:
        return 'red'
    if bits & (CAUTION | CAUTION_WAVING | YELLOW | YELLOW_WAVING):
        return 'yellow'
    if bits & WHITE:
        return 'white'
    if bits & GREEN:
        return 'green'
    return None


def empty_snapshot() -> dict[str, Any]:
    """Never leave a disconnected overlay displaying stale telemetry."""
    return {
        'connected': False,
        'demo': False,
        'session': {},
        'focus': None,
        'leaderboard': [],
        'table_type': None,
        'updated_at': None,
    }


def build_snapshot(ir: Any, *, demo: bool = False, now: float | None = None) -> dict[str, Any]:
    """Build a snapshot from one frozen SDK frame; caller handles freezing."""
    info = _get(ir, 'DriverInfo', {})
    weekend = _get(ir, 'WeekendInfo', {})
    session_info = _get(ir, 'SessionInfo', {})
    session_num = _number(_get(ir, 'SessionNum'))
    sessions = _field(session_info, 'Sessions', [])
    session_detail = _item(sessions, session_num, {})
    kind = _text(_field(session_detail, 'SessionType') or _field(session_detail, 'SessionName'), 32)
    track = _text(_field(weekend, 'TrackDisplayName') or _field(weekend, 'TrackDisplayShortName'), 65)
    series = _text(_field(weekend, 'SeriesName'), 65)

    positions = _get(ir, 'CarIdxPosition')
    class_positions = _get(ir, 'CarIdxClassPosition')
    laps = _get(ir, 'CarIdxLap')
    pits = _get(ir, 'CarIdxOnPitRoad')
    best_laps = _get(ir, 'CarIdxBestLapTime')
    car_drivers = _field(info, 'Drivers', [])
    if not isinstance(car_drivers, list):
        car_drivers = []

    drivers: list[dict[str, Any]] = []
    for d in car_drivers:
        idx = _number(_field(d, 'CarIdx'))
        if idx is None or _field(d, 'CarIsPaceCar') or _field(d, 'IsSpectator'):
            continue
        name = _text(_field(d, 'UserName') or _field(d, 'TeamName'), 45)
        if not name:
            continue
        car_number = _text(_field(d, 'CarNumber'), 8)
        position = _number(_item(positions, idx), min_value=1)
        cls_pos = _number(_item(class_positions, idx), min_value=1)
        drivers.append({
            'idx': idx,
            'number': car_number,
            'name': name,
            'position': position,
            'class_position': cls_pos,
            'class_name': _text(_field(d, 'CarClassShortName'), 20),
            'class_id': _number(_field(d, 'CarClassID')),
            'lap': _number(_item(laps, idx), min_value=1),
            'best_lap': _positive_float(_item(best_laps, idx)),
            'in_pit': bool(_item(pits, idx, False)),
        })

    is_timed_session = bool(kind) and kind.lower() in (
        'practice', 'qualify', 'qualifying', 'warmup', 'warm-up'
    )
    if is_timed_session:
        # Race-position arrays can remain populated with *old race* rankings in
        # practice. Never accidentally label those as the current running order.
        ranked = [d for d in drivers if d['best_lap'] is not None]
        ranked.sort(key=lambda d: (d['best_lap'], d['idx']))
        table_type = 'fastest_laps' if ranked else None
        ranked = [{**d, 'position': i + 1} for i, d in enumerate(ranked)]
    else:
        ranked = [d for d in drivers if d['position'] is not None]
        ranked.sort(key=lambda d: (d['position'], d['idx']))
        table_type = 'running_order' if ranked else None

    all_by_idx = {d['idx']: d for d in drivers}
    camera_idx = _number(_get(ir, 'CamCarIdx'))
    player_idx = _number(_get(ir, 'PlayerCarIdx'))
    focus_driver = all_by_idx.get(camera_idx) or all_by_idx.get(player_idx)
    driver_pov = all_by_idx.get(player_idx)

    leader_lap = ranked[0]['lap'] if (ranked and not is_timed_session) else None
    # In practice/qualifying, the fastest driver is not necessarily the lap leader.
    if leader_lap is None:
        leader_lap = _number(_get(ir, 'Lap'), min_value=1)
    total_laps = _number(_field(session_detail, 'SessionLaps'), min_value=1)
    if total_laps is None:
        total_laps = _number(_get(ir, 'RaceLaps'), min_value=1)
    lap_text = None
    if leader_lap is not None:
        lap_text = f'LAP {leader_lap}'
        if total_laps is not None and leader_lap <= total_laps:
            lap_text += f' / {total_laps}'

    # Best-lap ranks are not a driver's official session/finishing positions.
    if is_timed_session:
        for original in (focus_driver, driver_pov):
            if original is not None:
                original['position'] = None

    return {
        'connected': True,
        'demo': bool(demo),
        'session': {
            'track': track,
            'series': series,
            'kind': kind,
            'lap_text': lap_text,
            'flag': flag_label(_get(ir, 'SessionFlags')),
        },
        'focus': focus_driver,
        'driver': driver_pov,
        'leaderboard': ranked[:64],
        'table_type': table_type,
        'updated_at': round(time.time() if now is None else now, 3),
    }


class SampleIRSDK:
    """Explicit demo-only frame for layout testing; never used in live mode."""
    def __init__(self) -> None:
        names = [
            'Alex Morgan', 'Jordan Reed', 'Sam Carter', 'Taylor Brooks',
            'Morgan Lee', 'Drew Turner', 'Cameron Blake', 'Jamie Collins',
            'Robin Hayes', 'Casey Monroe', 'Devon Parker', 'Avery Stone',
        ]
        drivers = [
            {'CarIdx': i, 'CarNumber': str((i * 7 + 6) % 99).zfill(2),
             'UserName': name, 'CarClassID': 1, 'CarClassShortName': 'GT3'}
            for i, name in enumerate(names)
        ]
        self.data = {
            'DriverInfo': {'Drivers': drivers},
            'WeekendInfo': {'TrackDisplayName': 'Demo Circuit', 'SeriesName': 'Sample Race'},
            'SessionInfo': {'Sessions': [{'SessionType': 'Race', 'SessionLaps': '45'}]},
            'SessionNum': 0,
            'SessionFlags': GREEN,
            'CarIdxPosition': list(range(1, 13)),
            'CarIdxClassPosition': list(range(1, 13)),
            'CarIdxLap': [16] * 12,
            'CarIdxBestLapTime': [87.34 + i * .21 for i in range(12)],
            'CarIdxOnPitRoad': [False] * 12,
            'PlayerCarIdx': 3,
            'CamCarIdx': 2,
            'Lap': 16,
        }

    def __getitem__(self, key: str) -> Any:
        return self.data.get(key)
