"""Visual-only drill animation helpers for the Streamlit classroom app."""

from __future__ import annotations

import io
import math

from PIL import Image, ImageDraw, ImageFont


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def make_drill_animation_gif(
    diameter_mm: float,
    depth_mm: float,
    point_allowance_mm: float,
    spindle_rpm: float,
    feed_rate_mm_min: float,
    feed_time_sec: float,
    hole_type: str,
    tool_material: str,
    playback_rate: float = 2.0,
    frame_count: int = 32,
) -> bytes:
    """Render a small looping GIF whose geometry and motion follow app inputs.

    This is a schematic for teaching. It does not model cutting forces, chips,
    coolant, machine acceleration, or real-time spindle behavior.
    """
    diameter_mm = float(diameter_mm)
    depth_mm = float(depth_mm)
    point_allowance_mm = float(point_allowance_mm)
    spindle_rpm = float(spindle_rpm)
    feed_rate_mm_min = float(feed_rate_mm_min)
    feed_time_sec = float(feed_time_sec)
    playback_rate = _clamp(float(playback_rate), 0.25, 8.0)
    frame_count = int(_clamp(int(frame_count), 12, 60))
    if not all(math.isfinite(v) for v in (diameter_mm, depth_mm, point_allowance_mm, spindle_rpm, feed_rate_mm_min, feed_time_sec)):
        raise ValueError("Animation values must be finite numbers.")
    if min(diameter_mm, depth_mm, spindle_rpm, feed_rate_mm_min, feed_time_sec) <= 0:
        raise ValueError("Diameter, depth, RPM, feed rate, and feed-motion time must be greater than zero.")

    width, height = 760, 375
    center_x = 380
    surface_y = 187
    tool_width = _clamp(diameter_mm * 1.5, 10, 38)
    hole_width = _clamp(diameter_mm * 2.2, tool_width + 6, 84)
    hole_left = center_x - hole_width / 2
    hole_right = center_x + hole_width / 2
    travel_px = min(92.0, max(26.0, 88.0 * min((depth_mm + point_allowance_mm) / 32.0, 1.0)))
    rotor_turns = _clamp(spindle_rpm / 220.0, 1.0, 10.0)
    frames: list[Image.Image] = []
    font = ImageFont.load_default()

    for index in range(frame_count):
        phase = index / frame_count
        if phase < 0.08:
            feed_progress = 0.0
        elif phase < 0.62:
            raw = (phase - 0.08) / 0.54
            feed_progress = raw * raw * (3.0 - 2.0 * raw)
        elif phase < 0.72:
            feed_progress = 1.0
        else:
            raw = (phase - 0.72) / 0.28
            feed_progress = 1.0 - raw * raw * (3.0 - 2.0 * raw)
        offset_y = travel_px * feed_progress
        frame = Image.new("RGB", (width, height), "#0B2031")
        draw = ImageDraw.Draw(frame)

        for x in range(0, width, 28):
            draw.line((x, 0, x, height), fill="#102A3D", width=1)
        for y in range(0, height, 28):
            draw.line((0, y, width, y), fill="#102A3D", width=1)

        draw.text((28, 22), "AXIAL CUTAWAY - LIVE DRILL PREVIEW", fill="#75DCD7", font=font)
        draw.text((28, 43), f"D {diameter_mm:g} mm   |   {spindle_rpm:,.0f} rpm   |   {feed_rate_mm_min:,.1f} mm/min", fill="#F4F8FB", font=font)
        draw.text((610, 22), "SCHEMATIC", fill="#F4F8FB", font=font)

        draw.rounded_rectangle((95, surface_y, hole_left, 340), radius=5, fill="#203C52", outline="#50748B", width=2)
        draw.rounded_rectangle((hole_right, surface_y, 665, 340), radius=5, fill="#203C52", outline="#50748B", width=2)
        draw.rectangle((78, surface_y - 1, 682, surface_y + 1), fill="#FFB15C")
        draw.text((99, surface_y - 20), "WORK SURFACE", fill="#FFC27F", font=font)

        housing_top = 48 + offset_y
        draw.rounded_rectangle((center_x - 30, housing_top, center_x + 30, housing_top + 43), radius=7, fill="#17384C", outline="#4D93A4", width=2)
        rotor_y = housing_top + 21
        draw.ellipse((center_x - 12, rotor_y - 12, center_x + 12, rotor_y + 12), outline="#19D3C5", width=2)
        angle = phase * math.tau * rotor_turns
        for offset_angle in (angle, angle + math.pi / 2):
            x1 = center_x + math.cos(offset_angle) * 9
            y1 = rotor_y + math.sin(offset_angle) * 9
            x2 = center_x - math.cos(offset_angle) * 9
            y2 = rotor_y - math.sin(offset_angle) * 9
            draw.line((x1, y1, x2, y2), fill="#19D3C5", width=2)

        shank_top = housing_top + 43
        tip_y = 181 + offset_y
        bit_left = center_x - tool_width / 2
        bit_right = center_x + tool_width / 2
        point_height = _clamp(point_allowance_mm * 7.0, 8, 28)
        draw.rectangle((bit_left, shank_top, bit_right, max(shank_top, tip_y - point_height)), fill="#19D3C5")
        draw.polygon(((bit_left, tip_y - point_height), (center_x, tip_y), (bit_right, tip_y - point_height)), fill="#6CFFF1", outline="#B7FFF8")
        if feed_progress > 0.35:
            draw.ellipse((center_x - 19, tip_y - 7, center_x + 19, tip_y + 7), outline="#19D3C5", width=2)

        depth_bottom = min(333, surface_y + max(28, depth_mm * 2.4))
        draw.line((450, surface_y + 12, 450, depth_bottom), fill="#19D3C5", width=2)
        draw.polygon(((445, surface_y + 20), (450, surface_y + 12), (455, surface_y + 20)), fill="#19D3C5")
        draw.polygon(((445, depth_bottom - 8), (450, depth_bottom), (455, depth_bottom - 8)), fill="#19D3C5")
        draw.text((466, surface_y + 48), f"{depth_mm:g} mm depth", fill="#F4F8FB", font=font)
        draw.text((466, surface_y + 66), f"{hole_type}", fill="#F4F8FB", font=font)
        draw.text((28, 358), f"{tool_material} drill - playback {playback_rate:g}x - animation is illustrative, not to scale", fill="#F4F8FB", font=font)
        frames.append(frame)

    cycle_duration_sec = _clamp(feed_time_sec / playback_rate, 4.0, 18.0)
    duration_ms = max(30, int(cycle_duration_sec * 1000 / frame_count))
    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=True,
    )
    return output.getvalue()
