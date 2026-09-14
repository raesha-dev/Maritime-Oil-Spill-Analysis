# Maritime Insight

## Backend API

The repository now includes a standalone FastAPI service in [backend](backend/README.md). It is intentionally separate from the TanStack frontend so the dashboard can call a stable API now and the deterministic development adapters can later be replaced with AI, OpenDrift, Copernicus, and AIS providers without changing the UI contracts.

Copy `.env.example` to `.env` and set `VITE_FORENSICS_API_URL` to connect the dashboard to the FastAPI service. The UI falls back safely to clearly marked demonstration data only when the API is unavailable or the selected incident has no complete analysis snapshot.

Design a high-fidelity desktop mission-control interface for an oil-spill forensic investigation and vessel-attribution platform. The interface is designed for a trained maritime intelligence analyst, not a consumer application. It should feel like a real operational geospatial workstation used for satellite analysis, maritime surveillance, and forensic investigation.

IMPORTANT: Do not use any NTRO, ISRO, NASA, military, government, corporate, or organization logo. The interface must be completely unbranded. Do not invent seals, emblems, flags, agency insignia, or institutional symbols.

Use the supplied reference dashboard image as the primary visual reference for composition, density, hierarchy, spacing, panel proportions, map dominance, typography, and information architecture. Reproduce the visual character closely while making the interface cleaner, more polished, and more realistic.

Overall visual direction

Dark maritime command-center aesthetic.

Background: near-black navy / blue-black.

Panels: slightly lighter navy surfaces with thin technical borders.

Primary interface accent: cool cyan / teal.

Secondary data colors: restrained blue, green, amber and red.

Typography: technical sans-serif for labels and navigation; monospace for coordinates, timestamps, scores, MMSI, measurements and model outputs.

Dense information hierarchy, but extremely clean.

No glassmorphism.

No excessive blur.

No large decorative gradients.

No excessive rounded cards.

No playful illustrations.

No emoji.

No bright consumer-app styling.

No marketing-page appearance.

The result should look like a real analyst console, not a concept landing page.

GLOBAL LAYOUT

Use a 16:9 desktop workstation layout.

Maintain a dense multi-panel arrangement similar to the reference image.

Top Header

A narrow professional header spanning the full width.

Left:

MARITIME OIL-SPILL FORENSIC ANALYSIS

Small subtitle:

Satellite intelligence for evidence-based vessel attribution

Center:

compact workflow indicator:

DETECT → TRACE → ATTRIBUTE → TEST → INVESTIGATE

Active stage highlighted in cyan.

Right:

search field:

Search vessel, location, incident ID...

UTC clock.

system status indicator:

SYSTEM OPERATIONAL

Do not place any logo anywhere.

LEFT NAVIGATION

A slim vertical navigation rail on the far left.

Navigation items:

Dashboard

Detection

Trace

Vessels

Simulation

Evidence

Reports

Settings

Use extremely restrained technical line icons.

Selected navigation item has a cyan edge highlight.

Keep this rail narrow and subordinate to the map.

TOP METRIC STRIP

Directly below the header, show a compact row of operational metrics:

INCIDENT ID

SIH26143-2025-001

SATELLITE

Sentinel-1 SAR

DETECTED SLICK

12.4 km²

Confidence 0.91

RELEASE WINDOW

08 Sep 14:00–18:00 UTC

SEARCH AREA

2,850 km²

AIS CANDIDATES

18

5 simulated

Keep these compact. They are mission telemetry, not decorative cards.

CENTRAL WORKSPACE

The central area is dominated by a large geospatial maritime map.

The map should occupy approximately 55–60% of the main workspace.

Use a realistic satellite / nautical-chart basemap showing:

Indian coastline

Bay of Bengal / Arabian Sea maritime region as appropriate

muted land colors

realistic coastlines

subtle bathymetry

dark ocean

faint geographic grid

The map must look geographically real, not abstract.

MAP DATA LAYERS

The map must simultaneously visualize:

Observed slick

Show the actual observed slick as a solid sharply defined dark/outlined region.

It represents observed satellite evidence.

Give it a clear visual identity distinct from simulations.

Simulated slicks

Show hypothetical counterfactual spills as semi-transparent colored envelopes/clouds.

They must look less certain than the observed slick.

Show several candidate simulations using restrained colors.

Never make simulated predictions look identical to observed evidence.

Hindcast origin probability

Show a probability field, not a single point.

Use multiple soft concentric/dashed contours and heat-density regions.

Clearly indicate:

PROBABLE ORIGIN

and

RELEASE WINDOW

Do not represent the origin as one precise pin.

AIS vessel tracks

Display multiple vessel trajectories.

Every vessel appears as a small directional triangle/chevron rotated according to heading.

Each vessel has a fading historical trail.

AIS status colors:

green = consistent

amber = gap / uncertain

red = inconsistent

grey dashed = insufficient evidence / unknown

Cyan is reserved for general telemetry and tracking, not AIS integrity status.

MAP LEGEND

Place a compact technical legend inside the map:

Observed Oil Slick

Simulated Spill

Hindcast Origin Probability

AIS Vessel Track

Vessel Position

AIS Integrity

Keep it visually minimal.

RIGHT INTELLIGENCE COLUMN

The right side of the interface contains the forensic evidence panels.

PANEL 1: DETECTED OIL SLICK

Header:

DETECTED OIL SLICK

Include a realistic Sentinel-1 SAR thumbnail.

Show:

Satellite: Sentinel-1 (SAR)

Acquisition: 09 Sep 2025 08:17 UTC

Area: 12.4 km²

Confidence: 0.91 HIGH

Classification: Oil Spill

Button:

VIEW FULL IMAGE

PANEL 2: HINDCAST ANALYSIS

Header:

HINDCAST ANALYSIS

Display a compact probability heatmap.

Show:

Probable Origin

Release Window

Uncertainty Radius

Model: OpenDrift Ensemble

Currents: CMEMS

Wind: ERA5

Add a small probability color scale.

Do not display false precision.

CANDIDATE VESSEL PANEL

Header:

VESSEL CANDIDATES

Show a ranked table:

Rank

Vessel Name

Type

Proximity

Source Consistency

AIS Integrity

Example:

1 Ocean Pride — Tanker — 12 km — 0.82 — Consistent

2 Eastern Star — Cargo — 18 km — 0.74 — Gap

3 Sea Voyager — Tanker — 25 km — 0.61 — Consistent

4 Al Zubara — Cargo — 28 km — 0.48 — Gap

5 Blue Horizon — Tanker — 31 km — 0.42 — Inconsistent

Include:

EXPAND SEARCH

This must communicate that the candidates are ranked hypotheses, not accusations.

SELECTED VESSEL

Under the candidate list, show a compact selected-vessel dossier:

Vessel image

Vessel name

MMSI

IMO

Type

Flag as ISO code only

Dimensions

Latest AIS timestamp

Button:

VIEW AIS TRACK

COUNTERFACTUAL SIMULATION PANEL

This is the hero analytical component of the interface.

Header:

COUNTERFACTUAL SIMULATION — OCEAN PRIDE

Subtitle:

Observed vs simulated spill evolution

Show four temporal frames:

T + 0 h

T + 6 h

T + 12 h

T + 24 h

Each frame compares the predicted spill against observed evidence where available.

The progression should visually demonstrate the spill spreading and moving through the ocean.

Show:

Observed Slick

Simulated Slick

Keep observed evidence visually solid and simulated evidence translucent.

SOURCE CONSISTENCY

Beside or directly below the simulation panel:

SOURCE CONSISTENCY METRICS

Show four independent components:

Spatial Overlap (IoU)

Trajectory Match

Area Evolution

Shape Similarity

Use compact horizontal metric bars plus exact values and uncertainty.

Example:

Spatial Overlap 0.89 ± 0.04

Trajectory Match 0.84 ± 0.05

Area Evolution 0.78 ± 0.07

Shape Similarity 0.72 ± 0.09

OVERALL SOURCE CONSISTENCY

Show a prominent circular/radial gauge:

0.82

HIGH CONFIDENCE

Beneath it, permanently display:

SOURCE CONSISTENCY — NOT A PROBABILITY OF GUILT

Do not phrase this as probability of responsibility.

WHY THIS CANDIDATE COULD BE THE CAUSE

This panel must remain persistently visible, never hidden behind a modal.

Header:

WHY THIS CANDIDATE COULD BE THE CAUSE

Show concise evidence statements:

✓ Passes through high-probability origin region

✓ Speed profile consistent with release window

✓ Simulated slick closely matches observed evolution

⚠ AIS gap overlaps estimated release window

ℹ Vessel context shown separately as supporting background

Then a concise system assessment:

Strong physical consistency. Further investigation recommended.

Never use:

caused

responsible

guilty

identified as the source

proven

Instead use:

ranked candidate

is consistent with

could explain

raises the possibility

supports further investigation

does not rule out

EVIDENCE CHAIN

Add a compact chronological investigation timeline:

08 Sep 14:20 — Vessel enters probable origin region — OBSERVED

08 Sep 14:45 — Estimated release window — INFERRED

08 Sep 15:00 — Hypothetical release — SIMULATED

T+6h — Simulated spill movement — SIMULATED

09 Sep 08:17 — Sentinel-1 detects slick — OBSERVED

09 Sep 08:30 — Real vs simulated comparison — SYSTEM

Each evidence type must have a distinct visual marker.

Satellite revisit gaps should appear as explicit hollow/dashed nodes instead of disappearing from the timeline.

NULL / FAILURE STATE

Include an alternate interface state that can replace the final candidate result:

NO SUFFICIENTLY CONSISTENT VESSEL IDENTIFIED

Supporting line:

Origin estimate may be unreliable — recommend re-examining detection and hindcast inputs.

This state must look intentional and professional, not like an application error.

INTERACTION DESIGN

The interface should feel operational even as a static mockup.

Use subtle:

150–250 ms transitions

map layer toggling

vessel selection

candidate highlighting

simulation playback

timeline scrubbing

hover states

probability-layer controls

no bouncing

no exaggerated animation.

When a simulation is running, show a restrained scan / propagation animation over the simulated spill.

VISUAL PRIORITIES

The visual hierarchy must be:

1. Map and physical evidence

2. Counterfactual simulation

3. Candidate ranking

4. Source Consistency

5. Why This Candidate

6. Supporting metadata

The viewer should understand the complete forensic story without opening another page.

CRITICAL DESIGN RULE

The UI is not a generic AI dashboard.

It must visually communicate:

OBSERVED → INFERRED → HYPOTHESIS → SIMULATED → COMPARED → INVESTIGATED

The central visual question should always be:

“If this vessel released the oil here and now, would physics produce what the satellite actually observed?”

The interface should make that question obvious within a few seconds of viewing.

OUTPUT REQUIREMENTS

Generate one polished 16:9 desktop dashboard screenshot.

No logo.

No branding.

No organization seal.

No emoji.

No people.

No marketing illustrations.

No unnecessary empty space.

Dense but readable.

Professional geospatial command-center aesthetic.

High information density with strong hierarchy.

Make it look like a real operational forensic workstation that could plausibly be demonstrated to SIH judges.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/775b0b05-7fc5-4eb4-8d21-3df705e0c9e5).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
