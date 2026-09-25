"""Advanced educational Streamlit app for drilling-operation planning.

The app is a classroom simulator. It does not control a machine and its
starting cutting data is not a substitute for a tool-maker's catalog.
"""

from __future__ import annotations

import csv
import base64
import io
import math
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from drilling_calculations import (
    CUTTING_SPEED_DATA,
    MATERIAL_FEED_FACTORS,
    MATERIAL_LABELS,
    calculate_drilling,
    format_duration,
    recommended_feed_per_rev,
)
from drilling_visualization import make_drill_animation_gif


st.set_page_config(
    page_title="DrillLab | Drilling Operation Simulator",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

PALETTE = {
    "navy": "#071827",
    "navy_light": "#102A3D",
    "teal": "#19D3C5",
    "blue": "#36A3FF",
    "orange": "#FFB15C",
    "ink": "#E8F2FA",
    "muted": "#F4F8FB",
    "surface": "#0C2233",
}


def _install_styles(theme: str = "Dark") -> None:
    st.markdown(
        """
        <style>
          :root { color-scheme: dark; }
          .stApp {
            color: #f4f8fb;
            background:
              radial-gradient(ellipse at 80% 3%, rgba(25,211,197,.11), transparent 27%),
              radial-gradient(ellipse at 4% 25%, rgba(54,163,255,.08), transparent 26%),
              #071827;
          }
          [data-testid="stHeader"] { background: rgba(7,24,39,.76); }
          [data-testid="stSidebar"] {
            background: linear-gradient(180deg,#0a2032 0%,#071827 100%);
            border-right: 1px solid rgba(77,156,190,.18);
          }
          .stApp,
          .stApp p,
          .stApp label,
          .stApp [data-testid="stWidgetLabel"],
          .stApp [data-testid="stWidgetLabel"] p,
          .stApp [data-testid="stCaptionContainer"],
          .stApp [data-testid="stCaptionContainer"] p,
          .stApp [data-testid="stSidebar"] p,
          .stApp [data-testid="stSidebar"] label,
          .stApp [data-testid="stSidebar"] small,
          .stApp [data-testid="stRadio"] label,
          .stApp [data-testid="stToggle"] label,
          .stApp [data-testid="stCheckbox"] label {
            color: #F4F8FB !important;
          }
          .stApp [data-testid="stNumberInput"] input,
          .stApp [data-testid="stTextInput"] input,
          .stApp [data-testid="stTextArea"] textarea,
          .stApp [data-baseweb="select"] [role="combobox"] {
            color: #111827 !important;
            background-color: #ffffff !important;
          }
          .stApp [data-baseweb="popover"] [role="option"] {
            color: #111827 !important;
          }
          [data-testid="stMetric"] {
            min-height: 122px;
            background: linear-gradient(145deg,rgba(15,43,62,.96),rgba(8,29,45,.96));
            border: 1px solid rgba(90,174,199,.23);
            border-radius: 16px;
            padding: 1rem 1.05rem;
            box-shadow: 0 10px 35px rgba(0,0,0,.16);
            transition: transform .22s ease, border-color .22s ease, box-shadow .22s ease;
          }
          [data-testid="stMetric"]:hover {
            transform: translateY(-3px);
            border-color: rgba(25,211,197,.62);
            box-shadow: 0 12px 34px rgba(25,211,197,.12);
          }
          [data-testid="stMetricLabel"] { color: #F4F8FB !important; }
          [data-testid="stMetricValue"] { color: #effaff !important; }
          .hero-shell {
            position: relative; overflow: hidden;
            border: 1px solid rgba(68,207,211,.28);
            border-radius: 22px; padding: 1.55rem 1.8rem 1.45rem;
            margin: .2rem 0 1.2rem;
            background: linear-gradient(110deg,rgba(11,39,58,.98),rgba(13,70,81,.91));
            box-shadow: 0 18px 50px rgba(0,0,0,.22);
          }
          .hero-shell:after {
            content: ""; position: absolute; top: 0; right: -10%; width: 48%; height: 100%;
            background: repeating-linear-gradient(115deg,transparent 0 23px,rgba(83,224,217,.06) 24px 25px);
            transform: skewX(-10deg); pointer-events: none;
          }
          .hero-kicker { color:#74e4dc; font-size:.77rem; font-weight:750; letter-spacing:.19em; text-transform:uppercase; }
          .hero-title { color:#f2fbff; font-size:2.1rem; font-weight:780; line-height:1.12; margin:.5rem 0 .35rem; }
          .hero-copy { color:#F4F8FB; font-size:1rem; margin:0; max-width:800px; }
          .live-indicator { display:inline-flex; gap:.55rem; align-items:center; color:#F4F8FB; font-size:.82rem; letter-spacing:.08em; text-transform:uppercase; }
          .cycle-model { color:#F4F8FB; font-size:.84rem; }
          .live-indicator:before {
            content:""; width:9px; height:9px; border-radius:50%; background:#19d3c5;
            box-shadow:0 0 0 0 rgba(25,211,197,.68); animation:beacon 1.8s ease-out infinite;
          }
          @keyframes beacon { 70% { box-shadow:0 0 0 10px rgba(25,211,197,0); } 100% { box-shadow:0 0 0 0 rgba(25,211,197,0); } }
          @keyframes scan { 0% { transform:translateX(-110%); opacity:0; } 25% { opacity:.75; } 100% { transform:translateX(250%); opacity:0; } }
          .scan-line { height:1px; overflow:hidden; margin-top:1.2rem; background:rgba(100,192,199,.12); }
          .scan-line:after { content:""; display:block; width:30%; height:1px; background:#19d3c5; animation:scan 4.8s ease-in-out infinite; }
          .section-eyebrow { color:#19d3c5; font-size:.75rem; font-weight:750; letter-spacing:.16em; text-transform:uppercase; margin-bottom:.2rem; }
          .muted-copy { color:#F4F8FB; }
          .formula-box {
            border-left:3px solid #19d3c5; border-radius:0 10px 10px 0;
            background:rgba(15,43,62,.78); padding:.8rem 1rem; margin:.4rem 0;
          }
          .sim-frame {
            border:1px solid rgba(82,167,190,.3); border-radius:18px; overflow:hidden;
            background:linear-gradient(160deg,#0c2639,#071827); padding:.5rem;
          }
          .sim-frame svg { display:block; width:100%; height:auto; }
          .drill-drop { transform-box:fill-box; transform-origin:center top; animation:drill-cycle var(--cycle-duration) cubic-bezier(.42,0,.2,1) infinite; }
          .rotor { transform-box:fill-box; transform-origin:center; animation:rotor-spin var(--spin-duration) linear infinite; }
          .tip-glow { animation:tip-glow 1.5s ease-in-out infinite; }
          @keyframes drill-cycle { 0%,12% { transform:translateY(var(--start-offset)); } 57%,68% { transform:translateY(calc(var(--start-offset) + var(--travel))); } 100% { transform:translateY(var(--start-offset)); } }
          @keyframes rotor-spin { to { transform:rotate(360deg); } }
          @keyframes tip-glow { 0%,100% { opacity:.38; } 50% { opacity:1; } }
          .motion-off .drill-drop,.motion-off .rotor,.motion-off .tip-glow,.motion-off .live-indicator:before,.motion-off .scan-line:after { animation:none !important; }
          .sim-caption { color:#F4F8FB; font-size:.8rem; margin:.35rem .15rem 0; }
          .small-note { color:#F4F8FB; font-size:.84rem; }
          [data-testid="stMainBlockContainer"] { max-width: 1560px; padding-top: 1.25rem; }
          [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 { letter-spacing: .01em; }
          div[data-testid="stTabs"] { border-bottom: 1px solid rgba(110,160,182,.2); }
          div[data-testid="stTabs"] button[role="tab"] { min-height: 3rem; }
          .hero-shell { padding: 1.8rem 2rem 1.55rem; }
          .hero-title { letter-spacing: -.035em; }
          .hero-meta { display:flex; gap:.55rem; align-items:center; flex-wrap:wrap; margin-top:1rem; }
          .hero-pill { display:inline-flex; align-items:center; gap:.4rem; border:1px solid rgba(134,225,222,.28); border-radius:999px; padding:.38rem .72rem; color:#e9fbfb; background:rgba(4,24,36,.32); font-size:.77rem; }
          .preview-toolbar { display:flex; align-items:center; justify-content:space-between; gap:1rem; flex-wrap:wrap; margin:.1rem 0 .7rem; }
          .preview-title { color:#eaf7fc; font-size:1.06rem; font-weight:730; }
          .preview-subtitle { color:#a8c0cd; font-size:.82rem; margin-top:.16rem; }
          .telemetry-card { border:1px solid rgba(90,174,199,.23); border-radius:16px; padding:1rem 1.1rem; background:linear-gradient(145deg,rgba(15,43,62,.96),rgba(8,29,45,.96)); margin:.25rem 0 .8rem; }
          .telemetry-label { color:#8caebe; text-transform:uppercase; letter-spacing:.11em; font-size:.68rem; font-weight:750; }
          .telemetry-value { color:#f0fbff; font-size:1.3rem; line-height:1.25; font-weight:760; margin-top:.28rem; }
          .telemetry-detail { color:#c2d4de; font-size:.78rem; margin-top:.22rem; }
          .motion-legend { display:flex; flex-wrap:wrap; gap:.45rem; margin:.5rem 0 .1rem; }
          .motion-chip { border:1px solid rgba(90,174,199,.25); border-radius:9px; padding:.35rem .55rem; color:#d5e6ee; background:rgba(9,31,46,.62); font-size:.74rem; }
          div[data-testid="stTabs"] button[role="tab"] { color:#F4F8FB; font-weight:650; }
          div[data-testid="stTabs"] button[aria-selected="true"] { color:#5AF0E4; }
          div[data-testid="stAlert"] { border-radius:12px; }
          @media (prefers-reduced-motion: reduce) {
            *, *:before, *:after { animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; scroll-behavior:auto !important; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if theme == "Light":
        st.markdown(
            """
            <style>
              :root { color-scheme: light; }
              .stApp {
                color: #17212b !important;
                background: #f4f7fa !important;
              }
              [data-testid="stHeader"] { background: rgba(244,247,250,.94) !important; }
              [data-testid="stSidebar"] {
                color: #17212b !important;
                background: linear-gradient(180deg,#ffffff 0%,#edf2f7 100%) !important;
                border-right: 1px solid #d2dbe4 !important;
              }
              .stApp,
              .stApp p,
              .stApp label,
              .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
              .stApp [data-testid="stWidgetLabel"],
              .stApp [data-testid="stWidgetLabel"] p,
              .stApp [data-testid="stCaptionContainer"],
              .stApp [data-testid="stCaptionContainer"] p,
              .stApp [data-testid="stSidebar"] p,
              .stApp [data-testid="stSidebar"] label,
              .stApp [data-testid="stSidebar"] small,
              .stApp [data-testid="stRadio"] label,
              .stApp [data-testid="stToggle"] label,
              .stApp [data-testid="stCheckbox"] label {
                color: #17212b !important;
              }
              .stApp [data-testid="stNumberInput"] input,
              .stApp [data-testid="stTextInput"] input,
              .stApp [data-testid="stTextArea"] textarea,
              .stApp [data-baseweb="select"] [role="combobox"],
              .stApp [data-baseweb="popover"] [role="option"] {
                color: #17212b !important;
                background-color: #ffffff !important;
              }
              .stApp [data-testid="stMetric"] {
                color: #17212b !important;
                background: linear-gradient(145deg,#ffffff,#f2f6f9) !important;
                border-color: #d1dce5 !important;
                box-shadow: 0 8px 24px rgba(25,48,68,.08) !important;
              }
              .stApp [data-testid="stMetricLabel"] { color: #253441 !important; }
              .stApp [data-testid="stMetricValue"] { color: #101820 !important; }
              .hero-shell {
                background: linear-gradient(110deg,#ffffff,#e7f5f3) !important;
                border-color: #a9d8d3 !important;
                box-shadow: 0 12px 34px rgba(25,48,68,.09) !important;
              }
              .hero-title, .hero-copy, .live-indicator, .cycle-model { color: #17212b !important; }
              .hero-kicker, .section-eyebrow { color: #08796e !important; }
              .muted-copy, .small-note, .sim-caption { color: #263746 !important; }
              .preview-title, .telemetry-value { color: #142630 !important; }
              .preview-subtitle, .telemetry-detail { color: #405765 !important; }
              .telemetry-card { background:linear-gradient(145deg,#ffffff,#f2f6f9) !important; border-color:#d1dce5 !important; }
              .telemetry-label { color:#45616f !important; }
              .hero-pill { color:#17323c !important; background:rgba(255,255,255,.62) !important; border-color:#9fcac7 !important; }
              .motion-chip { color:#203743 !important; background:#ffffff !important; border-color:#d1dce5 !important; }
              .formula-box {
                color: #17212b !important;
                background: #ffffff !important;
                border-color: #08796e !important;
              }
              div[data-testid="stTabs"] button[role="tab"] { color: #263746 !important; }
              div[data-testid="stTabs"] button[aria-selected="true"] { color: #08796e !important; }
              .stApp [data-testid="stButton"] button,
              .stApp [data-testid="stDownloadButton"] button {
                color: #17212b !important;
                border-color: #c7d2dc !important;
              }
              .stApp [data-testid="stAlert"] { color: #17212b !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def _hero(motion_enabled: bool, cycle_mode: str) -> None:
    motion_class = "" if motion_enabled else " motion-off"
    st.markdown(
        f"""
        <div class="hero-shell{motion_class}">
          <div class="hero-kicker">DIPLOMA MECHANICAL ENGINEERING · SEMESTER 3</div>
          <div class="hero-title">DrillLab <span style="color:#19d3c5">/</span> Drilling Process Simulator</div>
          <p class="hero-copy">Explore cutting data, spindle limits, drill-point geometry and cycle time through a live, input-responsive engineering model.</p>
          <div class="hero-meta">
            <span class="hero-pill">PAPER X</span>
            <span class="hero-pill">NEEL JASANI · MANVIR PANCHAL · REHANT PATIL</span>
            <span class="hero-pill live-indicator">{('Simulation running' if motion_enabled else 'Simulation paused')}</span>
            <span class="hero-pill cycle-model">{cycle_mode}</span>
          </div>
          <div class="scan-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def plot_time_breakdown(result: dict[str, Any], cycle_mode: str) -> plt.Figure:
    labels = ["Approach feed", "Full-diameter drilling", result["point_allowance_label"]]
    values = [result["approach_time_sec"], result["hole_time_sec"], result["point_time_sec"]]
    colors = ["#48B8D5", "#19D3C5", "#FFB15C"]
    if cycle_mode == "Extended machine cycle":
        extra_rows = [
            ("Rapid approach", result["rapid_in_time_sec"], "#4284C6"),
            ("Final rapid retract", result["rapid_out_time_sec"], "#5576B8"),
            ("Peck retracts", result["peck_retract_time_sec"], "#A17FE0"),
            ("Peck pauses", result["peck_pause_time_sec"], "#CA86C8"),
            ("Bottom dwell", result["dwell_seconds"], "#E0A84D"),
            ("Tool change", result["tool_change_seconds"], "#73889A"),
        ]
        for label, value, color in extra_rows:
            if value > 0:
                labels.append(label)
                values.append(value)
                colors.append(color)
    fig_height = max(3.1, 0.44 * len(labels) + 1.2)
    fig, ax = plt.subplots(figsize=(9, fig_height), facecolor="#0B2031")
    ax.set_facecolor("#0B2031")
    positions = np.arange(len(labels))
    bars = ax.barh(positions, values, color=colors, height=.58, edgecolor="none")
    ax.set_yticks(positions, labels, color="#F4F8FB")
    ax.invert_yaxis()
    ax.set_xlabel("Estimated time (seconds)", color="#F4F8FB", labelpad=9)
    ax.set_title("Cycle-time decomposition", loc="left", fontsize=14, weight="bold", color="#EAF7FC", pad=14)
    ax.xaxis.grid(True, linestyle="--", linewidth=.7, alpha=.27, color="#9BB6C6")
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#597285")
    ax.tick_params(axis="y", length=0, pad=9, labelsize=9, colors="#F4F8FB")
    ax.tick_params(axis="x", labelsize=8, colors="#F4F8FB")
    max_value = max(max(values, default=0.0), 1.0)
    ax.set_xlim(0, max_value * 1.22)
    for bar, value in zip(bars, values):
        ax.text(bar.get_width() + max_value * .018, bar.get_y() + bar.get_height() / 2,
                f"{value:.2f} s", va="center", fontsize=8, color="#E8F2FA")
    fig.tight_layout()
    return fig


def plot_rpm_sensitivity(cutting_speed_m_min: float, max_rpm: float | None) -> plt.Figure:
    diameters = np.linspace(2.0, 50.0, 160)
    theoretical = 1000.0 * cutting_speed_m_min / (math.pi * diameters)
    fig, ax = plt.subplots(figsize=(8.3, 3.8), facecolor="#0B2031")
    ax.set_facecolor("#0B2031")
    ax.plot(diameters, theoretical, color="#19D3C5", linewidth=2.6, label="Theoretical RPM")
    if max_rpm is not None:
        ax.axhline(max_rpm, color="#FFB15C", linestyle="--", linewidth=1.6, label=f"Machine cap: {max_rpm:,.0f} rpm")
        ax.fill_between(diameters, max_rpm, theoretical, where=theoretical > max_rpm,
                        color="#FFB15C", alpha=.12, interpolate=True)
    ax.set_xlabel("Drill diameter (mm)", color="#F4F8FB")
    ax.set_ylabel("Spindle speed (rpm)", color="#F4F8FB")
    ax.set_title("Spindle speed changes inversely with diameter", loc="left", color="#EAF7FC", fontsize=13, weight="bold")
    ax.grid(True, linestyle="--", alpha=.23, color="#9BB6C6")
    ax.tick_params(colors="#F4F8FB", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#597285")
    ax.legend(frameon=False, labelcolor="#F4F8FB", fontsize=8)
    fig.tight_layout()
    return fig


def plot_speed_sweep(
    speed_band: tuple[float, float],
    diameter_mm: float,
    depth_mm: float,
    feed_per_rev_mm: float,
    approach_mm: float,
    point_angle: float,
    max_rpm: float,
    max_feed: float,
    apply_limits: bool,
) -> plt.Figure:
    speeds = np.linspace(speed_band[0], speed_band[1], 80)
    times = []
    for speed in speeds:
        sample = calculate_drilling(
            diameter_mm, depth_mm, float(speed), feed_per_rev_mm, approach_mm,
            "Through hole", point_angle_deg=point_angle, apply_machine_limits=apply_limits,
            max_spindle_rpm=max_rpm, max_feed_rate_mm_min=max_feed,
        )
        times.append(sample["cycle_time_sec"])
    fig, ax = plt.subplots(figsize=(8.3, 3.8), facecolor="#0B2031")
    ax.set_facecolor("#0B2031")
    ax.plot(speeds, times, color="#36A3FF", linewidth=2.5)
    ax.fill_between(speeds, times, min(times), color="#36A3FF", alpha=.12)
    ax.scatter([speeds[len(speeds) // 2]], [times[len(times) // 2]], color="#FFB15C", s=38, zorder=3)
    ax.set_xlabel("Selected cutting speed (m/min)", color="#F4F8FB")
    ax.set_ylabel("Feed-motion cycle (seconds)", color="#F4F8FB")
    ax.set_title("Speed sweep at constant feed per revolution", loc="left", color="#EAF7FC", fontsize=13, weight="bold")
    ax.grid(True, linestyle="--", alpha=.23, color="#9BB6C6")
    ax.tick_params(colors="#F4F8FB", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color("#597285")
    fig.tight_layout()
    return fig


def drilling_animation(
    diameter_mm: float,
    depth_mm: float,
    tip_mm: float,
    spindle_rpm: float,
    feed_rate_mm_min: float,
    feed_time_sec: float,
    hole_type: str,
    motion_enabled: bool,
    playback_rate: float,
    approach_mm: float,
    point_angle_deg: float,
    tool_material: str,
    preview_phase: str,
) -> str:
    """Build an input-responsive SVG cutaway; this is not machine-control output."""
    center_x, surface_y = 380.0, 252.0
    drill_width = min(38.0, max(12.0, diameter_mm * 1.55))
    hole_width = min(90.0, max(drill_width + 12.0, diameter_mm * 2.35))
    hole_left, hole_right = center_x - hole_width / 2.0, center_x + hole_width / 2.0
    drill_left, drill_right = center_x - drill_width / 2.0, center_x + drill_width / 2.0
    depth_px = min(112.0, max(28.0, depth_mm * 3.3))
    point_px = min(44.0, max(5.0, tip_mm * 3.3))
    point_angle_visual = min(42.0, max(18.0, point_px))
    initial_tip_y = 169.0 + point_angle_visual
    px_per_mm = depth_px / max(depth_mm, 0.1)
    approach_px = min(32.0, max(4.0, approach_mm * px_per_mm)) if approach_mm else 0.0
    start_offset = surface_y - approach_px - initial_tip_y
    bottom_offset = surface_y + depth_px + point_px - initial_tip_y
    travel_px = max(0.0, bottom_offset - start_offset)
    blind_hole = hole_type == "Blind hole"
    stage_offsets = {
        "Approach": start_offset,
        "Cutting": start_offset + travel_px * 0.54,
        "Bottom": bottom_offset,
        "Retract": start_offset,
    }
    stage_text = "AUTOMATIC CYCLE" if preview_phase == "Auto cycle" else preview_phase.upper()
    fixed_offset = stage_offsets.get(preview_phase, start_offset)
    auto_motion = motion_enabled and preview_phase == "Auto cycle"
    stage_style = "" if auto_motion else f"animation:none;transform:translateY({fixed_offset:.1f}px)"
    stage_kicker = {
        "Auto cycle": "AUTO CYCLE · FEED / RETRACT",
        "Approach": "STAGE 01 · APPROACH CLEARANCE",
        "Cutting": "STAGE 02 · AXIAL FEED",
        "Bottom": "STAGE 03 · FULL DEPTH / POINT",
        "Retract": "STAGE 04 · RETURN TO SAFE POSITION",
    }.get(preview_phase, "AUTO CYCLE · FEED / RETRACT")
    tool_color_a, tool_color_b, tool_color_c = (
        ("#FFD18A", "#F2A640", "#A85F12") if tool_material == "Carbide"
        else ("#7CF6EA", "#19D3C5", "#16859C")
    )
    stock_gradient = "url(#stock)"
    if blind_hole:
        stock_shapes = f"""
          <rect x="100" y="{surface_y}" width="{hole_left - 100:.1f}" height="148" rx="3" fill="{stock_gradient}" stroke="#50748B"/>
          <rect x="{hole_right:.1f}" y="{surface_y}" width="{660 - hole_right:.1f}" height="148" rx="3" fill="{stock_gradient}" stroke="#50748B"/>
          <rect x="{hole_left:.1f}" y="{surface_y}" width="{hole_width:.1f}" height="{depth_px:.1f}" fill="#061725"/>
          <path d="M{hole_left:.1f} {surface_y + depth_px:.1f} L{center_x:.1f} {surface_y + depth_px + point_px:.1f} L{hole_right:.1f} {surface_y + depth_px:.1f} Z" fill="#061725" stroke="#19D3C5" stroke-opacity=".65"/>
          <rect x="100" y="{surface_y + 148}" width="560" height="18" rx="2" fill="url(#stock)" stroke="#50748B"/>
        """
    else:
        stock_shapes = f"""
          <rect x="100" y="{surface_y}" width="{hole_left - 100:.1f}" height="166" rx="3" fill="{stock_gradient}" stroke="#50748B"/>
          <rect x="{hole_right:.1f}" y="{surface_y}" width="{660 - hole_right:.1f}" height="166" rx="3" fill="{stock_gradient}" stroke="#50748B"/>
        """
    cycle_duration = min(18.0, max(4.0, feed_time_sec / max(playback_rate, 0.25)))
    spin_duration = min(2.5, max(0.12, 800.0 / max(spindle_rpm, 1.0)))
    wrapper_class = "sim-frame" if motion_enabled else "sim-frame motion-off"
    return f"""
    <div class="{wrapper_class}" style="--travel:{travel_px:.1f}px;--start-offset:{start_offset:.1f}px;--cycle-duration:{cycle_duration:.2f}s;--spin-duration:{spin_duration:.2f}s">
      <svg viewBox="0 0 760 450" role="img" aria-label="Animated {tool_material} drill, diameter {diameter_mm:g} millimetres, {spindle_rpm:.0f} rpm, cutting a {hole_type.lower()} to {depth_mm:g} millimetres">
        <defs>
          <linearGradient id="stock" x1="0" x2="1"><stop offset="0" stop-color="#203C52"/><stop offset="1" stop-color="#132D43"/></linearGradient>
          <linearGradient id="tool" x1="0" x2="1"><stop offset="0" stop-color="{tool_color_a}"/><stop offset=".48" stop-color="{tool_color_b}"/><stop offset="1" stop-color="{tool_color_c}"/></linearGradient>
          <radialGradient id="glow"><stop offset="0" stop-color="#19D3C5" stop-opacity=".55"/><stop offset="1" stop-color="#19D3C5" stop-opacity="0"/></radialGradient>
          <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#5A8199" stroke-opacity=".12" stroke-width="1"/></pattern>
          <pattern id="flutes" width="16" height="18" patternUnits="userSpaceOnUse"><path d="M-3 18 Q8 9 19 0" fill="none" stroke="#052B3A" stroke-opacity=".52" stroke-width="3"/><path d="M4 20 Q13 11 21 4" fill="none" stroke="#E7FFFC" stroke-opacity=".42" stroke-width="1.3"/></pattern>
        </defs>
        <rect x="0" y="0" width="760" height="450" rx="13" fill="url(#grid)"/>
        <text x="28" y="33" fill="#75DCD7" font-size="12" font-family="Arial" letter-spacing="1.8">MOTION SIMULATOR  /  AXIAL CUTAWAY</text>
        <text x="665" y="33" fill="#9DB6C4" font-size="10" font-family="Arial">SCHEMATIC</text>
        <text x="28" y="57" fill="#F4F8FB" font-size="12" font-family="Arial">{tool_material.upper()}  ·  D {diameter_mm:.1f} mm  ·  N {spindle_rpm:,.0f} rpm  ·  f {feed_rate_mm_min:,.0f} mm/min</text>
        <rect x="24" y="74" width="240" height="27" rx="13" fill="#12394B" stroke="#267486"/>
        <text x="38" y="92" fill="#B8F8F1" font-size="10" font-family="Arial" letter-spacing="1.1">{stage_kicker}</text>
        <text x="606" y="92" fill="#A8C0CD" font-size="10" font-family="Arial">{stage_text}</text>
        <line x1="75" y1="{surface_y}" x2="685" y2="{surface_y}" stroke="#FFB15C" stroke-dasharray="7 6" stroke-width="1.5"/>
        {stock_shapes}
        <line x1="{hole_left:.1f}" y1="{surface_y}" x2="{hole_left:.1f}" y2="{surface_y + depth_px:.1f}" stroke="#56D9CF" stroke-opacity=".7" stroke-width="1"/>
        <line x1="{hole_right:.1f}" y1="{surface_y}" x2="{hole_right:.1f}" y2="{surface_y + depth_px:.1f}" stroke="#56D9CF" stroke-opacity=".7" stroke-width="1"/>
        <text x="104" y="{surface_y - 11}" fill="#FFC27F" font-size="11" font-family="Arial">WORK SURFACE</text>
        <line x1="{center_x}" y1="{surface_y}" x2="{center_x}" y2="410" stroke="#5A879D" stroke-dasharray="4 5" stroke-width="1" opacity=".7"/>
        <line x1="{hole_right + 35:.1f}" y1="{surface_y + 2:.1f}" x2="{hole_right + 35:.1f}" y2="{surface_y + depth_px:.1f}" stroke="#19D3C5" stroke-width="1.4"/>
        <path d="M{hole_right + 31:.1f} {surface_y + 8:.1f} L{hole_right + 35:.1f} {surface_y + 1:.1f} L{hole_right + 39:.1f} {surface_y + 8:.1f} M{hole_right + 31:.1f} {surface_y + depth_px - 7:.1f} L{hole_right + 35:.1f} {surface_y + depth_px + 1:.1f} L{hole_right + 39:.1f} {surface_y + depth_px - 7:.1f}" fill="none" stroke="#19D3C5" stroke-width="1.3"/>
        <text x="{hole_right + 45:.1f}" y="{surface_y + depth_px / 2:.1f}" fill="#BDEDEA" font-size="11" font-family="Arial">FULL Ø</text>
        <text x="{hole_right + 45:.1f}" y="{surface_y + depth_px / 2 + 15:.1f}" fill="#E8F2FA" font-size="12" font-family="Arial">{depth_mm:.1f} mm</text>
        <g class="drill-drop" style="{stage_style}">
          <rect x="351" y="48" width="58" height="39" rx="7" fill="#17384C" stroke="#4D93A4" stroke-width="2"/>
          <rect x="359" y="85" width="42" height="32" fill="#27526A" stroke="#4D93A4" stroke-width="1.5"/>
          <g class="rotor"><circle cx="380" cy="67" r="12" fill="none" stroke="{tool_color_b}" stroke-opacity=".82" stroke-width="1.5"/><path d="M380 55V79M368 67H392" stroke="{tool_color_b}" stroke-opacity=".9" stroke-width="1.2"/></g>
          <rect x="{drill_left:.1f}" y="114" width="{drill_width:.1f}" height="57" fill="url(#tool)"/>
          <rect x="{drill_left:.1f}" y="114" width="{drill_width:.1f}" height="57" fill="url(#flutes)"/>
          <path d="M{drill_left:.1f} 169 L{center_x} {169 + point_angle_visual:.1f} L{drill_right:.1f} 169 Z" fill="url(#tool)" stroke="{tool_color_a}" stroke-width="1"/>
          <ellipse class="tip-glow" cx="{center_x}" cy="{169 + point_angle_visual:.1f}" rx="25" ry="9" fill="url(#glow)"/>
        </g>
        <line x1="{hole_left:.1f}" y1="432" x2="{hole_right:.1f}" y2="432" stroke="#8DDDD7" stroke-width="1.1"/>
        <path d="M{hole_left:.1f} 427 L{hole_left:.1f} 437 M{hole_right:.1f} 427 L{hole_right:.1f} 437" stroke="#8DDDD7"/>
        <text x="380" y="447" text-anchor="middle" fill="#BDEDEA" font-size="10" font-family="Arial">HOLE Ø {diameter_mm:.1f} mm</text>
        <text x="28" y="425" fill="#F4F8FB" font-size="10" font-family="Arial">{hole_type.upper()}  ·  {point_angle_deg:g}° POINT  ·  {tip_mm:.2f} mm {('POINT ALLOWANCE' if blind_hole else 'BREAKTHROUGH ALLOWANCE')}</text>
      </svg>
    </div>
    """


@st.cache_data(show_spinner=False, max_entries=16)
def _cached_drill_gif(
    diameter_mm: float,
    depth_mm: float,
    tip_mm: float,
    spindle_rpm: float,
    feed_rate_mm_min: float,
    feed_time_sec: float,
    hole_type: str,
    tool_material: str,
    playback_rate: float,
) -> bytes:
    return make_drill_animation_gif(
        diameter_mm, depth_mm, tip_mm, spindle_rpm, feed_rate_mm_min, feed_time_sec,
        hole_type, tool_material, playback_rate,
    )


def _csv_bytes(record: dict[str, Any]) -> bytes:
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(["Quantity", "Value", "Unit"])
    for key, value, unit in record["rows"]:
        writer.writerow([key, value, unit])
    return stream.getvalue().encode("utf-8")


def _snapshot(
    diameter: float,
    depth: float,
    tool: str,
    material: str,
    hole_type: str,
    speed: float,
    result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "Saved at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Diameter (mm)": round(diameter, 2),
        "Depth (mm)": round(depth, 2),
        "Tool": tool,
        "Material": MATERIAL_LABELS[material],
        "Hole type": hole_type,
        "Cutting speed (m/min)": round(speed, 2),
        "RPM setpoint": round(result["spindle_rpm"], 1),
        "Feed rate (mm/min)": round(result["feed_rate_mm_min"], 2),
        "Feed motion (s)": round(result["cycle_time_sec"], 3),
        "Machine cycle (s)": round(result["estimated_machine_cycle_sec"], 3),
    }


display_theme = st.sidebar.selectbox("Display theme", ["Dark", "Light"], index=0)
_install_styles(display_theme)

if "saved_runs" not in st.session_state:
    st.session_state.saved_runs = []

with st.sidebar:
    st.markdown("### ⚙️ Operation setup")
    st.caption("Set the tool, workpiece and hole geometry.")
    diameter_mm = st.number_input(
        "Drill diameter, D (mm)", min_value=0.0, max_value=50.0, value=10.0, step=0.5,
        help="Positive drill diameter. Zero is rejected by the calculator.",
    )
    depth_mm = st.number_input(
        "Full-diameter depth (mm)", min_value=0.0, max_value=500.0, value=25.0, step=1.0,
        help="Enter the cylindrical full-diameter portion. Drill-point length is added separately.",
    )
    tool_material = st.selectbox("Drill tool material", ["HSS", "Carbide"])
    material_key = st.selectbox(
        "Workpiece material group", list(MATERIAL_LABELS),
        format_func=lambda key: MATERIAL_LABELS[key],
    )
    hole_type = st.radio("Hole type", ["Through hole", "Blind hole"], horizontal=True)
    point_angle = st.selectbox("Included drill point angle", [118, 135, 140], index=0)
    flutes = st.selectbox("Drill flute count", [2, 3, 4], index=0)
    approach_mm = st.number_input(
        "Feed approach clearance (mm)", min_value=0.0, max_value=25.0,
        value=2.0, step=0.5, help="Default classroom allowance: 2 mm.",
    )

    speed_low, recommended_speed, speed_high = CUTTING_SPEED_DATA[tool_material][material_key]
    st.markdown("---")
    st.markdown("### 🎚️ Cutting data")
    st.caption(f"Teaching band: {speed_low:g}–{speed_high:g} m/min · Suggested start: {recommended_speed:g} m/min")
    cutting_speed = st.slider(
        "Selected cutting speed, Vc (m/min)",
        min_value=float(speed_low), max_value=float(speed_high), value=float(recommended_speed),
        step=max((speed_high - speed_low) / 100.0, 0.1),
        help="Choose a value inside the classroom band. Use exact catalog data for real machining.",
        key=f"speed_{tool_material}_{material_key}",
    )
    suggested_feed = recommended_feed_per_rev(diameter_mm, tool_material, material_key)
    feed_mode = st.radio("Feed source", ["Starting recommendation", "Manual override"], horizontal=False)
    if feed_mode == "Manual override":
        feed_per_rev = st.number_input(
            "Programmed feed, f (mm/rev)", min_value=0.0, max_value=2.0,
            value=round(max(suggested_feed, 0.005), 3), step=0.005, format="%.3f",
            key=f"manual-feed-{tool_material}-{material_key}",
        )
    else:
        feed_per_rev = suggested_feed
        st.metric("Starting feed", f"{feed_per_rev:.3f} mm/rev")

    with st.expander("Machine limits", expanded=True):
        apply_machine_limits = st.toggle("Apply spindle and feed caps", value=True)
        max_spindle_rpm = st.number_input("Maximum spindle speed (rpm)", min_value=0.0, max_value=30000.0, value=3000.0, step=100.0)
        max_feed_rate = st.number_input("Maximum feed rate (mm/min)", min_value=0.0, max_value=20000.0, value=1500.0, step=50.0)
        st.caption("Caps adjust the calculated setpoint and effective feed. Toggle off to inspect the theoretical result.")

    cycle_mode = st.selectbox("Cycle-time model", ["Feed motion only", "Extended machine cycle"], index=0)
    if cycle_mode == "Extended machine cycle":
        with st.expander("Extended cycle allowances", expanded=True):
            rapid_feed_rate = st.number_input("Rapid traverse rate (mm/min)", min_value=0.0, max_value=50000.0, value=5000.0, step=250.0)
            rapid_approach = st.number_input("Safe rapid approach distance (mm)", min_value=0.0, max_value=1000.0, value=50.0, step=5.0)
            dwell_seconds = st.number_input("Bottom dwell (s)", min_value=0.0, max_value=300.0, value=0.0, step=0.5)
            tool_change_seconds = st.number_input("Tool-change allowance (s)", min_value=0.0, max_value=600.0, value=0.0, step=1.0)
            peck_drilling = st.toggle("Include peck drilling allowances", value=(diameter_mm > 0 and depth_mm / diameter_mm > 5))
            peck_factor = st.slider("Peck depth (multiples of D)", 1.0, 5.0, 2.5, 0.5, disabled=not peck_drilling)
            peck_retract = st.number_input("Short retract per peck (mm)", min_value=0.0, max_value=25.0, value=2.0, step=0.5, disabled=not peck_drilling)
            peck_pause = st.number_input("Pause per peck (s)", min_value=0.0, max_value=60.0, value=0.25, step=0.05, disabled=not peck_drilling)
    else:
        rapid_feed_rate = 5000.0
        rapid_approach = 50.0
        dwell_seconds = 0.0
        tool_change_seconds = 0.0
        peck_drilling = False
        peck_factor = 2.5
        peck_retract = 2.0
        peck_pause = 0.25

    motion_enabled = st.toggle("Animate drill preview", value=True)

    team_members = "NEEL JASANI, MANVIR PANCHAL, REHANT PATIL"
    with st.expander("Team details"):
        st.caption("Group: PAPER X")
        st.caption(f"Members: {team_members}")
    with st.expander("Reference data and limits"):
        st.markdown(
            "Classroom starting values only. Exact speed/feed depends on material grade and hardness, "
            "drill geometry and coating, coolant, chip evacuation, and machine rigidity.\n\n"
            "- [Gühring drilling support](https://guhring.com/Support/Drilling)\n"
            "- [Gühring speed/feed chart](https://guhring.com/media/speedfeed/4025.pdf)\n"
            "- [Sandvik Coromant metric formulas](https://cdn.sandvik.coromant.com/files/sitecollectiondocuments/services/metal-cutting-e-learning/formulas-and-definitions/formulas-and-deinitions-for-turning-metric-enu.pdf)"
        )

_hero(motion_enabled, cycle_mode)
st.caption("Educational simulator · metric units · use the machine/tool manufacturer's data for production work")

validation_errors = []
if diameter_mm <= 0:
    validation_errors.append("Drill diameter must be greater than zero.")
if depth_mm <= 0:
    validation_errors.append("Full-diameter depth must be greater than zero.")
if feed_per_rev <= 0:
    validation_errors.append("Feed per revolution must be greater than zero.")
if apply_machine_limits and max_spindle_rpm <= 0:
    validation_errors.append("Maximum spindle speed must be greater than zero when machine caps are enabled.")
if apply_machine_limits and max_feed_rate <= 0:
    validation_errors.append("Maximum feed rate must be greater than zero when machine caps are enabled.")
if cycle_mode == "Extended machine cycle" and rapid_feed_rate <= 0:
    validation_errors.append("Rapid traverse rate must be greater than zero in the extended cycle model.")

result = None
if not validation_errors:
    try:
        current_peck_depth = max(diameter_mm * peck_factor, 0.1) if peck_drilling else None
        result = calculate_drilling(
            diameter_mm=diameter_mm,
            full_diameter_depth_mm=depth_mm,
            cutting_speed_m_min=cutting_speed,
            feed_per_rev_mm=feed_per_rev,
            approach_clearance_mm=approach_mm,
            hole_type=hole_type,
            point_angle_deg=float(point_angle),
            flutes=int(flutes),
            apply_machine_limits=apply_machine_limits,
            max_spindle_rpm=max_spindle_rpm,
            max_feed_rate_mm_min=max_feed_rate,
            cycle_mode=cycle_mode,
            rapid_feed_rate_mm_min=rapid_feed_rate,
            rapid_approach_distance_mm=rapid_approach,
            dwell_seconds=dwell_seconds,
            tool_change_seconds=tool_change_seconds,
            peck_drilling=peck_drilling,
            peck_depth_mm=current_peck_depth,
            peck_retract_mm=peck_retract,
            peck_pause_seconds=peck_pause,
        )
    except ValueError as exc:
        validation_errors.append(str(exc))

if validation_errors:
    for message in validation_errors:
        st.error(message)
    st.info("Enter positive geometry and valid machine limits to calculate this operation.")
else:
    assert result is not None
    for warning in result["limit_warnings"]:
        st.warning(warning)
    if result["depth_ratio"] > 5 and not peck_drilling:
        st.warning("Depth exceeds 5× diameter. Consider peck drilling and confirm chip evacuation with the tool maker.")
    if result["depth_ratio"] > 5 and peck_drilling:
        st.info(f"Deep-hole flag: L/D = {result['depth_ratio']:.1f}. The extended estimate includes {result['peck_count']} peck events.")

    allowance_type = result["point_allowance_label"]
    st.info(
        f"**{hole_type}:** depth is measured to the full-diameter section. The {point_angle}° point adds "
        f"{result['point_allowance_mm']:.2f} mm as the {allowance_type.lower()}."
    )

    overview_tab, simulation_tab, lab_tab, compare_tab = st.tabs(
        ["◈  Live dashboard", "⟲  Motion preview", "⌁  Engineering lab", "▤  Compare runs"]
    )

    with overview_tab:
        st.markdown('<div class="section-eyebrow">Live operation telemetry</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Selected cutting speed", f"{cutting_speed:.1f} m/min", f"{speed_low:g}–{speed_high:g} band")
        c2.metric("Spindle setpoint", f"{result['spindle_rpm']:,.0f} rpm", f"Theory {result['theoretical_spindle_rpm']:,.0f} rpm")
        c3.metric("Effective feed rate (mm/min)", f"{result['feed_rate_mm_min']:,.1f}", f"{result['effective_feed_per_rev_mm']:.3f} mm/rev")
        selected_cycle_sec = result["estimated_machine_cycle_sec"] if cycle_mode == "Extended machine cycle" else result["cycle_time_sec"]
        c4.metric("Estimated cycle", format_duration(selected_cycle_sec), cycle_mode)

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Point allowance", f"{result['point_allowance_mm']:.2f} mm", allowance_type)
        c6.metric("Total feed travel", f"{result['total_feed_travel_mm']:.2f} mm", f"Depth ratio {result['depth_ratio']:.1f}×D")
        c7.metric("MRR (mm³/min)", f"{result['material_removal_rate_mm3_min']:,.0f}", "Cylindrical section estimate")
        c8.metric("Feed per flute", f"{result['feed_per_flute_mm']:.3f} mm", f"Assumes {flutes}-flute drill")

        chart_col, summary_col = st.columns([1.6, 1])
        with chart_col:
            fig = plot_time_breakdown(result, cycle_mode)
            st.pyplot(fig, width="stretch")
            plt.close(fig)
        with summary_col:
            st.markdown("### Operation status")
            st.write(f"**Tool / material:** {tool_material} · {MATERIAL_LABELS[material_key]}")
            st.write(f"**Hole geometry:** {hole_type.lower()} · {point_angle}° point · {flutes} flutes")
            st.write(f"**Actual cutting speed:** {result['actual_cutting_speed_m_min']:.2f} m/min")
            st.write(f"**Feed-motion baseline:** {format_duration(result['cycle_time_sec'])}")
            if cycle_mode == "Extended machine cycle":
                st.write(f"**Added non-cut time:** {format_duration(result['estimated_machine_cycle_sec'] - result['cycle_time_sec'])}")
                st.caption("Extended model assumptions appear in the sidebar and formula details below.")
            else:
                st.caption("Baseline time excludes rapid moves, dwell, peck retracts, and tool changes.")
            st.progress(min(result["spindle_rpm"] / max(max_spindle_rpm, 1), 1.0), text="Spindle setpoint / configured RPM cap")

        left_action, right_action = st.columns([1, 2])
        with left_action:
            if st.button("＋ Save setup for comparison", type="primary", width="stretch"):
                st.session_state.saved_runs.append(_snapshot(diameter_mm, depth_mm, tool_material, material_key, hole_type, cutting_speed, result))
                st.session_state.saved_runs = st.session_state.saved_runs[-12:]
                st.toast("Setup saved to Compare runs", icon="✅")
        with right_action:
            csv_record = {
                "rows": [
                    ("Tool material", tool_material, ""),
                    ("Workpiece material", MATERIAL_LABELS[material_key], ""),
                    ("Hole type", hole_type, ""),
                    ("Diameter", diameter_mm, "mm"),
                    ("Full-diameter depth", depth_mm, "mm"),
                    ("Point angle", point_angle, "degrees"),
                    ("Cutting speed selected", cutting_speed, "m/min"),
                    ("Theoretical spindle speed", result["theoretical_spindle_rpm"], "rpm"),
                    ("Spindle setpoint", result["spindle_rpm"], "rpm"),
                    ("Effective feed rate", result["feed_rate_mm_min"], "mm/min"),
                    ("Point allowance", result["point_allowance_mm"], "mm"),
                    ("Total feed travel", result["total_feed_travel_mm"], "mm"),
                    ("Feed-motion time", result["cycle_time_sec"], "s"),
                    ("Estimated machine cycle", result["estimated_machine_cycle_sec"], "s"),
                    ("Cycle-time model", cycle_mode, ""),
                ]
            }
            st.download_button("⇩ Download calculation CSV", data=_csv_bytes(csv_record), file_name="drilllab_calculation.csv", mime="text/csv", width="stretch")

        with st.expander("Formula trace and assumptions", expanded=False):
            st.markdown(
                f"""
                <div class="formula-box"><b>Spindle speed:</b> N = (1000 × Vc) / (π × D) =
                (1000 × {cutting_speed:.2f}) / (π × {diameter_mm:.2f}) = {result['theoretical_spindle_rpm']:.2f} rpm theoretical.</div>
                <div class="formula-box"><b>Feed rate:</b> Vf = f × N. Programmed f = {feed_per_rev:.3f} mm/rev;
                effective Vf = {result['feed_rate_mm_min']:.2f} mm/min after configured machine caps.</div>
                <div class="formula-box"><b>Point length:</b> Lp = (D / 2) / tan(point angle / 2) = {result['point_allowance_mm']:.3f} mm.</div>
                <div class="formula-box"><b>Feed travel:</b> L = approach + full-diameter depth + Lp =
                {approach_mm:.2f} + {depth_mm:.2f} + {result['point_allowance_mm']:.2f} = {result['total_feed_travel_mm']:.2f} mm.</div>
                <div class="formula-box"><b>Feed-motion time:</b> T = L / Vf × 60 = {result['cycle_time_sec']:.3f} s.</div>
                """,
                unsafe_allow_html=True,
            )
            if cycle_mode == "Extended machine cycle":
                st.write(
                    "Extended estimate = feed-motion time + rapid approach + final rapid retract + optional peck retracts/pauses + bottom dwell + tool-change allowance. "
                    "It remains a simplified estimate and excludes loading, workholding, acceleration, and controller-specific motion profiles."
                )

    with simulation_tab:
        playback_controls, motion_controls = st.columns([1, 1.8])
        with playback_controls:
            playback_rate = st.slider(
                "Playback speed",
                min_value=0.25,
                max_value=8.0,
                value=2.0,
                step=0.25,
                help="Changes the visual feed cycle and exported GIF speed. The displayed machine estimate is unchanged.",
            )
        with motion_controls:
            preview_phase = st.radio(
                "Motion stage",
                ["Auto cycle", "Approach", "Cutting", "Bottom", "Retract"],
                horizontal=True,
                help="Auto cycle animates the feed and retract. Choose a stage to inspect the drill position frame by frame.",
            )
        st.markdown(
            '<div class="preview-toolbar"><div><div class="preview-title">Live toolpath cutaway</div><div class="preview-subtitle">The schematic responds to drill size, point angle, hole type, feed and spindle setpoint.</div></div></div>',
            unsafe_allow_html=True,
        )
        sim_left, sim_right = st.columns([1.9, 0.78], gap="large")
        with sim_left:
            st.markdown(
                drilling_animation(
                    diameter_mm,
                    depth_mm,
                    result["point_allowance_mm"],
                    result["spindle_rpm"],
                    result["feed_rate_mm_min"],
                    result["cycle_time_sec"],
                    hole_type,
                    motion_enabled,
                    playback_rate,
                    approach_mm,
                    float(point_angle),
                    tool_material,
                    preview_phase,
                ),
                unsafe_allow_html=True,
            )
            if preview_phase == "Auto cycle" and not motion_enabled:
                st.info("The motion is paused at the approach position. Turn on **Animate drill preview** in the sidebar or select a motion stage.")
            st.caption("Schematic cross-section · geometry is illustrative and not to scale. Point allowance is added after the full-diameter depth.")
            show_gif = st.toggle(
                "Render video-style playback and export GIF",
                value=False,
                help="Generates a downloadable animated GIF from the current drill, material, hole and motion settings.",
            )
            if show_gif:
                animation_gif = _cached_drill_gif(
                    diameter_mm,
                    depth_mm,
                    result["point_allowance_mm"],
                    result["spindle_rpm"],
                    result["feed_rate_mm_min"],
                    result["cycle_time_sec"],
                    hole_type,
                    tool_material,
                    playback_rate,
                )
                encoded_gif = base64.b64encode(animation_gif).decode("ascii")
                st.markdown(
                    f'<div class="sim-frame"><img src="data:image/gif;base64,{encoded_gif}" alt="GIF playback matching the current drill setup" style="display:block;width:100%;height:auto;border-radius:12px"></div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    "Download current motion as GIF",
                    data=animation_gif,
                    file_name="drilllab_current_setup.gif",
                    mime="image/gif",
                    width="stretch",
                )
        with sim_right:
            st.markdown("### Process telemetry")
            st.markdown(
                f'<div class="telemetry-card"><div class="telemetry-label">Spindle setpoint</div><div class="telemetry-value">{result["spindle_rpm"]:,.0f} <span style="font-size:.76rem;font-weight:550">rpm</span></div><div class="telemetry-detail">Actual cutting speed {result["actual_cutting_speed_m_min"]:.1f} m/min</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="telemetry-card"><div class="telemetry-label">Axial feed</div><div class="telemetry-value">{result["feed_rate_mm_min"]:,.0f} <span style="font-size:.76rem;font-weight:550">mm/min</span></div><div class="telemetry-detail">{result["effective_feed_per_rev_mm"]:.3f} mm/rev · {flutes} flutes</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="telemetry-card"><div class="telemetry-label">Estimated {"machine cycle" if cycle_mode == "Extended machine cycle" else "feed-motion time"}</div><div class="telemetry-value">{format_duration(selected_cycle_sec)}</div><div class="telemetry-detail">Feed travel {result["total_feed_travel_mm"]:.2f} mm</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="motion-legend"><span class="motion-chip">{tool_material}</span><span class="motion-chip">{MATERIAL_LABELS[material_key]}</span><span class="motion-chip">{hole_type}</span><span class="motion-chip">{point_angle}° point</span></div>',
                unsafe_allow_html=True,
            )
            with st.expander("Operation sequence", expanded=False):
                st.markdown(
                    "1. **Approach** to the configured feed clearance.\n\n"
                    "2. **Feed** through the clearance and full-diameter hole depth.\n\n"
                    f"3. **Finish the point travel** by {result['point_allowance_mm']:.2f} mm ({allowance_type.lower()}).\n\n"
                    "4. **Retract** to the safe position."
                )
        with st.expander("Motion model and assumptions", expanded=False):
            st.write(
                "The spindle icon rotates in relation to the calculated RPM and the feed loop follows the estimated feed-motion time. "
                "The stage selector provides a manual position preview. The GIF export is a visual teaching aid. Neither preview models chip formation, coolant, forces, machine acceleration, controller timing, or real machine motion."
            )

    with lab_tab:
        data_tab, sensitivity_tab, formulas_tab = st.tabs(["Cutting-data matrix", "Sensitivity analysis", "Engineering notes"])
        with data_tab:
            st.markdown("### Classroom cutting-speed starting bands")
            rows = []
            for key, label in MATERIAL_LABELS.items():
                hss_band = CUTTING_SPEED_DATA["HSS"][key]
                carbide_band = CUTTING_SPEED_DATA["Carbide"][key]
                rows.append({
                    "Workpiece group": label,
                    "HSS band (m/min)": f"{hss_band[0]:g}–{hss_band[2]:g}",
                    "HSS start": f"{hss_band[1]:g}",
                    "Carbide band (m/min)": f"{carbide_band[0]:g}–{carbide_band[2]:g}",
                    "Carbide start": f"{carbide_band[1]:g}",
                    "Feed factor": f"{MATERIAL_FEED_FACTORS[key]:.2f}",
                })
            st.dataframe(rows, hide_index=True, width="stretch")
            st.warning("These broad ranges are this project's teaching reference values. Confirm exact alloy and drill catalog data before any production use.")
            st.markdown("**Feed starting estimate:** HSS = 0.012 × D × material factor; carbide = 0.015 × D × material factor. You can replace this estimate with a manual feed in the sidebar.")
        with sensitivity_tab:
            sens_a, sens_b = st.tabs(["RPM vs diameter", "Cycle-time vs speed"])
            with sens_a:
                fig = plot_rpm_sensitivity(cutting_speed, max_spindle_rpm if apply_machine_limits else None)
                st.pyplot(fig, width="stretch")
                plt.close(fig)
                st.caption("At constant surface speed, theoretical RPM falls as drill diameter increases. The dashed line is the configured spindle cap.")
            with sens_b:
                fig = plot_speed_sweep(
                    (speed_low, speed_high), diameter_mm, depth_mm, feed_per_rev, approach_mm,
                    float(point_angle), max_spindle_rpm, max_feed_rate, apply_machine_limits,
                )
                st.pyplot(fig, width="stretch")
                plt.close(fig)
                st.caption("Sweep holds feed per revolution and geometry constant. Machine caps may flatten the response at higher selected speeds.")
        with formulas_tab:
            st.markdown("### Symbols and unit checks")
            st.markdown(
                "| Symbol | Meaning | Unit |\n|---|---|---|\n"
                "| Vc | Cutting speed | m/min |\n| D | Drill diameter | mm |\n| N | Spindle speed | rev/min |\n"
                "| f | Feed per revolution | mm/rev |\n| Vf | Linear feed rate | mm/min |\n| Lp | Drill-point length | mm |\n| T | Time | min or s |"
            )
            st.markdown("### Modeling limits")
            st.markdown(
                "- Standard selected point angles use straight-flank geometry: `Lp = (D / 2) / tan(angle / 2)`.\n"
                "- Full-diameter depth is entered separately; point travel is added to it for both hole types.\n"
                "- Cylindrical material-removal rate is `Q = (πD² / 4) × Vf`; it does not model the conical point volume.\n"
                "- Feed recommendations are classroom estimates and do not account for exact alloy grade, coating, coolant, rigidity, or chip evacuation.\n"
                "- Cycle estimates exclude acceleration ramps, loading, workholding, controller-specific delays, and setup time."
            )
            st.markdown("### References")
            st.markdown(
                "- [Sandvik Coromant metric machining formulas](https://cdn.sandvik.coromant.com/files/sitecollectiondocuments/services/metal-cutting-e-learning/formulas-and-definitions/formulas-and-deinitions-for-turning-metric-enu.pdf)\n"
                "- [Gühring drilling technical support](https://guhring.com/Support/Drilling)\n"
                "- [Gühring speed and feed chart](https://guhring.com/media/speedfeed/4025.pdf)"
            )

    with compare_tab:
        st.markdown("### Saved setup comparison")
        st.caption("Save several operating setups from the dashboard, then compare their setpoints and cycle estimates.")
        if st.session_state.saved_runs:
            st.dataframe(st.session_state.saved_runs, hide_index=True, width="stretch")
            compare_left, compare_right = st.columns([1, 3])
            with compare_left:
                if st.button("Clear saved runs", type="secondary"):
                    st.session_state.saved_runs = []
                    st.rerun()
            with compare_right:
                comparison_stream = io.StringIO()
                comparison_writer = csv.DictWriter(
                    comparison_stream,
                    fieldnames=list(st.session_state.saved_runs[0]),
                )
                comparison_writer.writeheader()
                comparison_writer.writerows(st.session_state.saved_runs)
                st.download_button(
                    "Download comparison CSV",
                    data=comparison_stream.getvalue().encode("utf-8"),
                    file_name="drilllab_saved_runs.csv",
                    mime="text/csv",
                )
            if len(st.session_state.saved_runs) >= 2:
                saved = st.session_state.saved_runs
                fig, ax = plt.subplots(figsize=(8.5, 3.4), facecolor="#0B2031")
                ax.set_facecolor("#0B2031")
                labels = [f"{r['Tool']} · {r['Diameter (mm)']:g} mm" for r in saved]
                vals = [r["Machine cycle (s)"] for r in saved]
                bars = ax.barh(labels, vals, color=["#19D3C5" if i == len(vals)-1 else "#3A88A8" for i in range(len(vals))])
                ax.invert_yaxis()
                ax.set_xlabel("Estimated machine cycle (seconds)", color="#F4F8FB")
                ax.grid(axis="x", linestyle="--", alpha=.22, color="#9BB6C6")
                ax.set_axisbelow(True)
                ax.tick_params(colors="#F4F8FB", labelsize=8)
                ax.spines[["top", "right", "left"]].set_visible(False)
                ax.spines["bottom"].set_color("#597285")
                for bar, val in zip(bars, vals):
                    ax.text(val + max(vals) * .02, bar.get_y()+bar.get_height()/2, f"{val:.2f} s", va="center", color="#E8F2FA", fontsize=8)
                ax.set_xlim(0, max(vals) * 1.25)
                fig.tight_layout()
                st.pyplot(fig, width="stretch")
                plt.close(fig)
        else:
            st.info("No saved runs yet. Open Live dashboard and choose **Save setup for comparison**.")

with st.expander("Group details", expanded=False):
    st.write("**Group:** PAPER X")
    st.write(f"**Members:** {team_members}")

st.markdown("---")
st.markdown(
    "<div class='small-note'>DrillLab is an educational estimate, not machine-control software. Confirm tool-maker cutting data, "
    "machine limits, workholding and safety procedures before machining. Feed-motion time and extended machine-cycle time are estimates.</div>",
    unsafe_allow_html=True,
)
