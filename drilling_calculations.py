"""Pure engineering calculations for the Streamlit drilling simulator.

The speed/feed values are broad teaching estimates, not manufacturer data.
Keep this module free of Streamlit imports so its calculations are easy to audit.
"""

from __future__ import annotations

import math
from typing import Any


MATERIAL_LABELS = {
    "mild_steel": "Mild steel (low carbon)",
    "stainless_steel": "Stainless steel",
    "grey_cast_iron": "Grey cast iron",
    "aluminium_alloy": "Aluminium alloy",
    "brass": "Brass",
}

# Broad classroom ranges in m/min. Values are not specific to an exact grade,
# coating, geometry, coolant condition, or machine.
CUTTING_SPEED_DATA = {
    "HSS": {
        "mild_steel": (20.0, 25.0, 30.0),
        "stainless_steel": (8.0, 10.0, 15.0),
        "grey_cast_iron": (20.0, 25.0, 30.0),
        "aluminium_alloy": (40.0, 50.0, 80.0),
        "brass": (30.0, 40.0, 60.0),
    },
    "Carbide": {
        "mild_steel": (60.0, 80.0, 100.0),
        "stainless_steel": (35.0, 45.0, 60.0),
        "grey_cast_iron": (70.0, 90.0, 120.0),
        "aluminium_alloy": (100.0, 150.0, 200.0),
        "brass": (80.0, 100.0, 140.0),
    },
}

MATERIAL_FEED_FACTORS = {
    "mild_steel": 1.00,
    "stainless_steel": 0.75,
    "grey_cast_iron": 0.90,
    "aluminium_alloy": 1.15,
    "brass": 1.05,
}

TOOL_FACTORS = {"HSS": 0.012, "Carbide": 0.015}
VALID_HOLE_TYPES = {"Through hole", "Blind hole"}
VALID_CYCLE_MODES = {"Feed motion only", "Extended machine cycle"}


def _finite_number(name: str, value: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def recommended_feed_per_rev(diameter_mm: float, tool_material: str, material_key: str) -> float:
    """Return the app's diameter-based starting feed estimate in mm/rev."""
    diameter_mm = _finite_number("Drill diameter", diameter_mm)
    if diameter_mm < 0:
        raise ValueError("Drill diameter cannot be negative.")
    if tool_material not in TOOL_FACTORS:
        raise ValueError("Choose HSS or Carbide.")
    if material_key not in MATERIAL_FEED_FACTORS:
        raise ValueError("Choose a supported workpiece material group.")
    return diameter_mm * TOOL_FACTORS[tool_material] * MATERIAL_FEED_FACTORS[material_key]


def calculate_drilling(
    diameter_mm: float,
    full_diameter_depth_mm: float,
    cutting_speed_m_min: float,
    feed_per_rev_mm: float,
    approach_clearance_mm: float,
    hole_type: str,
    point_angle_deg: float = 118.0,
    flutes: int = 2,
    apply_machine_limits: bool = True,
    max_spindle_rpm: float = 3000.0,
    max_feed_rate_mm_min: float = 1500.0,
    cycle_mode: str = "Feed motion only",
    rapid_feed_rate_mm_min: float = 5000.0,
    rapid_approach_distance_mm: float = 50.0,
    dwell_seconds: float = 0.0,
    tool_change_seconds: float = 0.0,
    peck_drilling: bool = False,
    peck_depth_mm: float | None = None,
    peck_retract_mm: float = 2.0,
    peck_pause_seconds: float = 0.25,
) -> dict[str, Any]:
    """Calculate drilling rates, geometry, feed time, and optional cycle extras.

    The baseline cycle is feed motion through approach, full-diameter depth,
    and point allowance. The extended model adds rapid approach/retract,
    optional peck retracts and pauses, bottom dwell, and tool-change time.
    """
    diameter_mm = _finite_number("Drill diameter", diameter_mm)
    full_diameter_depth_mm = _finite_number("Hole depth", full_diameter_depth_mm)
    cutting_speed_m_min = _finite_number("Cutting speed", cutting_speed_m_min)
    feed_per_rev_mm = _finite_number("Feed per revolution", feed_per_rev_mm)
    approach_clearance_mm = _finite_number("Approach clearance", approach_clearance_mm)
    point_angle_deg = _finite_number("Drill point angle", point_angle_deg)
    max_spindle_rpm = _finite_number("Maximum spindle speed", max_spindle_rpm)
    max_feed_rate_mm_min = _finite_number("Maximum feed rate", max_feed_rate_mm_min)
    rapid_feed_rate_mm_min = _finite_number("Rapid feed rate", rapid_feed_rate_mm_min)
    rapid_approach_distance_mm = _finite_number("Rapid approach distance", rapid_approach_distance_mm)
    dwell_seconds = _finite_number("Dwell time", dwell_seconds)
    tool_change_seconds = _finite_number("Tool-change time", tool_change_seconds)
    peck_retract_mm = _finite_number("Peck retract distance", peck_retract_mm)
    peck_pause_seconds = _finite_number("Peck pause", peck_pause_seconds)

    for name, value in (
        ("Drill diameter", diameter_mm),
        ("Hole depth", full_diameter_depth_mm),
        ("Cutting speed", cutting_speed_m_min),
        ("Feed per revolution", feed_per_rev_mm),
    ):
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero.")
    if approach_clearance_mm < 0:
        raise ValueError("Approach clearance cannot be negative.")
    if not 0 < point_angle_deg < 180:
        raise ValueError("Drill point angle must be between 0 and 180 degrees.")
    if flutes not in {2, 3, 4}:
        raise ValueError("Choose a drill with 2, 3, or 4 flutes.")
    if hole_type not in VALID_HOLE_TYPES:
        raise ValueError("Choose either a through hole or a blind hole.")
    if cycle_mode not in VALID_CYCLE_MODES:
        raise ValueError("Choose a supported cycle-time model.")
    if apply_machine_limits and (max_spindle_rpm <= 0 or max_feed_rate_mm_min <= 0):
        raise ValueError("Machine RPM and feed limits must be greater than zero.")
    if cycle_mode == "Extended machine cycle" and rapid_feed_rate_mm_min <= 0:
        raise ValueError("Rapid feed rate must be greater than zero for the extended cycle.")
    if min(rapid_approach_distance_mm, dwell_seconds, tool_change_seconds, peck_retract_mm, peck_pause_seconds) < 0:
        raise ValueError("Optional cycle allowances cannot be negative.")
    if peck_depth_mm is not None:
        peck_depth_mm = _finite_number("Peck depth", peck_depth_mm)
        if peck_depth_mm <= 0:
            raise ValueError("Peck depth must be greater than zero.")

    theoretical_rpm = (1000.0 * cutting_speed_m_min) / (math.pi * diameter_mm)
    spindle_rpm = min(theoretical_rpm, max_spindle_rpm) if apply_machine_limits else theoretical_rpm
    commanded_feed_rate = feed_per_rev_mm * spindle_rpm
    feed_rate_mm_min = min(commanded_feed_rate, max_feed_rate_mm_min) if apply_machine_limits else commanded_feed_rate
    effective_feed_per_rev = feed_rate_mm_min / spindle_rpm
    actual_cutting_speed_m_min = math.pi * diameter_mm * spindle_rpm / 1000.0

    half_angle_rad = math.radians(point_angle_deg / 2.0)
    point_allowance_mm = (diameter_mm / 2.0) / math.tan(half_angle_rad)
    total_feed_travel_mm = approach_clearance_mm + full_diameter_depth_mm + point_allowance_mm
    cycle_time_min = total_feed_travel_mm / feed_rate_mm_min
    cycle_time_sec = cycle_time_min * 60.0
    approach_time_sec = approach_clearance_mm / feed_rate_mm_min * 60.0
    hole_time_sec = full_diameter_depth_mm / feed_rate_mm_min * 60.0
    point_time_sec = point_allowance_mm / feed_rate_mm_min * 60.0

    depth_ratio = full_diameter_depth_mm / diameter_mm
    resolved_peck_depth = peck_depth_mm or max(diameter_mm * 2.5, 0.1)
    include_peck_allowances = cycle_mode == "Extended machine cycle" and peck_drilling
    peck_count = math.ceil(full_diameter_depth_mm / resolved_peck_depth) if include_peck_allowances else 0
    peck_retract_count = max(peck_count - 1, 0)
    peck_retract_time_sec = (
        peck_retract_count * peck_retract_mm / rapid_feed_rate_mm_min * 60.0
        if include_peck_allowances and rapid_feed_rate_mm_min > 0 else 0.0
    )
    peck_pause_time_sec = peck_count * peck_pause_seconds if include_peck_allowances else 0.0

    rapid_in_time_sec = 0.0
    rapid_out_time_sec = 0.0
    included_dwell_sec = 0.0
    included_tool_change_sec = 0.0
    if cycle_mode == "Extended machine cycle":
        rapid_in_time_sec = rapid_approach_distance_mm / rapid_feed_rate_mm_min * 60.0
        rapid_out_distance_mm = rapid_approach_distance_mm + total_feed_travel_mm
        rapid_out_time_sec = rapid_out_distance_mm / rapid_feed_rate_mm_min * 60.0
        included_dwell_sec = dwell_seconds
        included_tool_change_sec = tool_change_seconds

    extended_extra_sec = (
        rapid_in_time_sec + rapid_out_time_sec + peck_retract_time_sec
        + peck_pause_time_sec + included_dwell_sec + included_tool_change_sec
    )
    estimated_machine_cycle_sec = cycle_time_sec + extended_extra_sec
    point_label = "Breakthrough allowance" if hole_type == "Through hole" else "Pointed-bottom allowance"
    limit_warnings = []
    if apply_machine_limits and theoretical_rpm > max_spindle_rpm:
        limit_warnings.append("The requested spindle speed is above the machine RPM limit; the displayed setpoint is capped.")
    if apply_machine_limits and commanded_feed_rate > max_feed_rate_mm_min:
        limit_warnings.append("The feed rate is above the machine feed limit; the effective feed per revolution is reduced.")

    return {
        "theoretical_spindle_rpm": theoretical_rpm,
        "spindle_rpm": spindle_rpm,
        "commanded_feed_rate_mm_min": commanded_feed_rate,
        "feed_rate_mm_min": feed_rate_mm_min,
        "programmed_feed_per_rev_mm": feed_per_rev_mm,
        "effective_feed_per_rev_mm": effective_feed_per_rev,
        "feed_per_flute_mm": effective_feed_per_rev / flutes,
        "actual_cutting_speed_m_min": actual_cutting_speed_m_min,
        "point_allowance_mm": point_allowance_mm,
        "point_allowance_label": point_label,
        "approach_clearance_mm": approach_clearance_mm,
        "full_diameter_depth_mm": full_diameter_depth_mm,
        "total_feed_travel_mm": total_feed_travel_mm,
        "cycle_time_min": cycle_time_min,
        "cycle_time_sec": cycle_time_sec,
        "feed_motion_time_sec": cycle_time_sec,
        "estimated_machine_cycle_sec": estimated_machine_cycle_sec,
        "approach_time_sec": approach_time_sec,
        "hole_time_sec": hole_time_sec,
        "point_time_sec": point_time_sec,
        "rapid_in_time_sec": rapid_in_time_sec,
        "rapid_out_time_sec": rapid_out_time_sec,
        "peck_retract_time_sec": peck_retract_time_sec,
        "peck_pause_time_sec": peck_pause_time_sec,
        "dwell_seconds": included_dwell_sec,
        "tool_change_seconds": included_tool_change_sec,
        "depth_ratio": depth_ratio,
        "peck_count": peck_count,
        "peck_retract_count": peck_retract_count,
        "peck_depth_mm": resolved_peck_depth,
        "hole_type": hole_type,
        "cycle_mode": cycle_mode,
        "limit_warnings": limit_warnings,
        "material_removal_rate_mm3_min": math.pi * (diameter_mm**2) / 4.0 * feed_rate_mm_min,
    }


def format_duration(seconds: float) -> str:
    seconds = max(float(seconds), 0.0)
    minutes, remainder = divmod(seconds, 60.0)
    if minutes >= 1:
        return f"{int(minutes)} min {remainder:.1f} s"
    return f"{seconds:.2f} s"
