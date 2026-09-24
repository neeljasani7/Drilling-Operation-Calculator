# DrillLab: Drilling Operation Calculator

An interactive Streamlit teaching app for Diploma in Mechanical Engineering, Semester 3. Explore drill speed, feed, point geometry, machine limits, and cycle-time estimates for through and blind holes.

## Features

- HSS and carbide tool choices with five workpiece material groups and editable speed/feed settings.
- RPM, feed rate, drill-point allowance, feed travel, feed-motion time, feed-per-flute estimate, and cylindrical material-removal-rate estimate.
- Optional spindle/feed caps and an extended cycle estimate with rapid travel, peck retracts and pauses, dwell, and tool-change allowances.
- Live drill preview plus a downloadable animated GIF that updates with diameter, RPM, feed, hole depth, hole type, and playback speed. Includes cycle-time chart, RPM/speed sensitivity plots, saved-run comparisons, and CSV downloads.
- Formula trace, labeled metric units, input validation, editable group/member placeholders, and reference links.
- Dark and light display themes: dark mode uses white text on dark surfaces; light mode uses dark text on light surfaces.

## Run locally

In PowerShell, open this folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks environment activation, run the app using the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

## GitHub and Streamlit Community Cloud

1. Create a public GitHub repository and upload **all five project files**: `app.py`, `drilling_calculations.py`, `drilling_visualization.py`, `requirements.txt`, and `README.md`.
2. Sign in to Streamlit Community Cloud with the GitHub account that owns the repository.
3. Choose **New app**, select the repository and branch, set the main file to `app.py`, and deploy.
4. Open the deployed link and confirm that the app loads and recalculates when inputs change.
5. Add the GitHub repository URL and deployed app URL to the college LMS submission.

The five-page report and seven-slide presentation are included beside the source files. Fill in group/member placeholders and replace the report's illustrative calculation with the group's textbook example before submission.

## Calculation model and assumptions

- Metric units; entered hole depth is the full-diameter section. The drill point is added as breakthrough allowance for through-holes or pointed-bottom allowance for blind holes.
- Point allowance: `Lp = (D / 2) / tan(point angle / 2)`. The default point angle is 118°.
- Spindle speed: `N = 1000 × Vc / (π × D)`; feed rate: `Vf = f × N`.
- Feed-motion time: `(approach + full-diameter depth + point allowance) / feed rate × 60` seconds.
- Approach clearance defaults to 2 mm and is editable. The optional extended estimate adds the displayed rapid, peck, dwell, and tool-change allowances.
- Machine caps apply to spindle speed and feed when enabled. The feed recommendation is an educational starting estimate, not manufacturer-specific data.
- The animation is illustrative. Estimates exclude loading, workholding, acceleration ramps, controller-specific motion profiles, setup time, and actual production variability.
- The dependency minimum is Streamlit 1.49 because the app uses the current `width="stretch"` layout option.

## References

- [Gühring drilling technical support](https://guhring.com/Support/Drilling)
- [Gühring speed and feed reference chart](https://guhring.com/media/speedfeed/4025.pdf)
- [Sandvik Coromant metric formulas](https://cdn.sandvik.coromant.com/files/sitecollectiondocuments/services/metal-cutting-e-learning/formulas-and-definitions/formulas-and-deinitions-for-turning-metric-enu.pdf)
