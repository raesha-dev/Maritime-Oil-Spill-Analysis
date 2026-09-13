# Maritime Forensic Workstation

## Goal
Build a single-screen, unbranded 16:9 desktop analyst console that closely follows the supplied dashboard references while improving clarity, realism, and evidentiary separation.

## What will be built
- A narrow command header, workflow stage indicator, search, UTC clock, and operational status.
- A slim left navigation rail and compact incident telemetry strip.
- A dominant realistic Bay of Bengal analytical map with coastline, bathymetry, grid, observed slick, simulated spill envelopes, probability contours, vessel tracks, positions, and legend.
- Dense forensic panels for the detected SAR slick, hindcast analysis, ranked vessel candidates, selected-vessel dossier, four-frame counterfactual simulation, source-consistency metrics, interpretation, and evidence chain.
- A professional alternate “no sufficiently consistent vessel” state available from the interface.
- Restrained interactions for vessel selection, map-layer toggles, simulation playback/scrubbing, and timeline inspection.

## Visual system
- Near-black navy workspace, slightly lifted panel surfaces, fine technical borders, cyan telemetry, and evidence-status green/amber/red/grey.
- Technical sans-serif labels with monospace coordinates, identifiers, times, and scores.
- Tight rectangular panel geometry, minimal radii, compact controls, and no glass, logos, decorative gradients, or consumer styling.

## Technical details
- Implement the workstation at `/` using the existing React/TanStack setup.
- Define all visual roles as semantic tokens in the global design system.
- Build map and analytical visuals as crisp custom vector/CSS graphics so they remain sharp and interactive without external map dependencies.
- Add route-specific title, description, Open Graph, and Twitter metadata.
- Verify the rendered screen at 16:9 and a narrower desktop width, checking readability, overlap, interactions, and console/build health.
