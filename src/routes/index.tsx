import { createFileRoute } from "@tanstack/react-router";
import {
  Activity,
  AlertTriangle,
  Anchor,
  Bell,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  Crosshair,
  Database,
  FileSearch,
  FileText,
  Layers3,
  MapPin,
  Pause,
  Play,
  Radar,
  RefreshCw,
  Search,
  Settings,
  Ship,
  Sun,
  Moon,
  Waves,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { demoDashboard } from "@/lib/demo-dashboard";
import { forensicsApi, type Candidate, type DashboardSnapshot } from "@/lib/forensics-api";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Maritime Oil-Spill Forensic Analysis" },
      {
        name: "description",
        content:
          "Operational geospatial workstation for satellite oil-spill analysis and evidence-based vessel attribution.",
      },
      { property: "og:title", content: "Maritime Oil-Spill Forensic Analysis" },
      {
        property: "og:description",
        content: "Operational satellite analysis and vessel-attribution workstation.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Workstation,
});

const nav = [
  [Activity, "Dashboard"],
  [Radar, "Detection"],
  [Crosshair, "Trace"],
  [Ship, "Vessels"],
  [Waves, "Simulation"],
  [FileSearch, "Evidence"],
  [FileText, "Reports"],
  [Settings, "Settings"],
] as const;

function Metric({
  label,
  children,
  sub,
  icon: Icon,
}: {
  label: string;
  children: React.ReactNode;
  sub?: string;
  icon?: typeof Activity;
}) {
  return (
    <div className="metric">
      {Icon && <Icon size={18} />}
      <div>
        <span>{label}</span>
        <strong>{children}</strong>
        {sub && <small>{sub}</small>}
      </div>
    </div>
  );
}

function Panel({
  title,
  children,
  className = "",
  action,
  onClick,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <section className={`panel ${className}`} onClick={onClick}>
      <header className="panel-header">
        <h2>{title}</h2>
        {action}
      </header>
      {children}
    </section>
  );
}

type LayerState = { observed: boolean; simulation: boolean; probability: boolean; tracks: boolean };

function MapWorkspace({
  layers,
  toggle,
  origin,
  candidates,
}: {
  layers: LayerState;
  toggle: (key: keyof LayerState) => void;
  origin: [number, number];
  candidates: Candidate[];
}) {
  const vesselNames = candidates.map((candidate) => candidate.vessel.name);
  return (
    <div className="map-wrap" aria-label="Bay of Bengal forensic map">
      <div className="map-toolbar">
        <button title="Zoom in">
          <ZoomIn />
        </button>
        <button title="Zoom out">
          <ZoomOut />
        </button>
        <button title="Map layers">
          <Layers3 />
        </button>
      </div>
      <svg
        className="map"
        viewBox="0 0 1000 640"
        role="img"
        aria-label="Bay of Bengal map showing spill evidence, probability field and vessel tracks"
      >
        <defs>
          <pattern id="grid" width="52" height="52" patternUnits="userSpaceOnUse">
            <path d="M52 0H0V52" fill="none" stroke="currentColor" strokeWidth=".7" />
          </pattern>
          <pattern id="micro" width="5" height="5" patternUnits="userSpaceOnUse">
            <circle cx="1" cy="1" r=".35" fill="currentColor" />
          </pattern>
          <radialGradient id="prob">
            <stop offset="0" stopColor="var(--prob-hot)" stopOpacity=".9" />
            <stop offset=".32" stopColor="var(--prob-mid)" stopOpacity=".55" />
            <stop offset="1" stopColor="var(--telemetry)" stopOpacity="0" />
          </radialGradient>
          <filter id="soft">
            <feGaussianBlur stdDeviation="12" />
          </filter>
        </defs>
        <rect width="1000" height="640" className="ocean" />
        <rect width="1000" height="640" fill="url(#grid)" className="grid" />
        <rect width="1000" height="640" fill="url(#micro)" className="micro" />
        <g className="bathymetry" fill="none">
          <path d="M130 470C280 435 430 438 610 475S840 575 1000 560" />
          <path d="M85 507C276 464 460 472 650 519S865 620 1000 600" />
          <path d="M480 88C595 105 764 60 934 116" />
        </g>
        <g className="land">
          <path d="M0 0H310C304 55 279 94 253 122C227 150 200 166 169 190C133 217 110 256 90 306C67 364 39 397 0 418Z" />
          <path d="M0 0H255C259 45 236 70 220 100C185 92 161 111 132 107C92 102 66 124 0 132Z" />
        </g>
        <g className="coast">
          <path d="M310 0C304 55 279 94 253 122C227 150 200 166 169 190C133 217 110 256 90 306C67 364 39 397 0 418" />
          <path d="M0 132C66 124 92 102 132 107C161 111 185 92 220 100" />
        </g>
        <g className="roads">
          <path d="M21 82C75 105 117 137 153 187S184 286 150 368" />
          <path d="M42 24C89 66 146 74 208 71" />
          <path d="M25 280C70 268 118 267 162 275" />
          <path d="M83 130C111 154 135 168 164 184" />
        </g>
        <g className="boundaries">
          <path d="M22 172C69 157 121 157 176 168" />
          <path d="M31 291C81 306 118 314 163 304" />
        </g>
        <text x="70" y="90" className="place major">
          INDIA
        </text>
        <text x="110" y="245" className="place city-label">
          Chennai
        </text>
        <circle cx="156" cy="237" r="2" className="city" />
        <text x="102" y="332" className="place city-label">
          Puducherry
        </text>
        <circle cx="168" cy="325" r="2" className="city" />
        <text x="194" y="182" className="place minor">
          Cuddalore
        </text>
        <text x="735" y="330" className="water-label">
          Bay of Bengal
        </text>
        {layers.probability && (
          <g className="probability">
            <ellipse cx="464" cy="257" rx="128" ry="92" fill="url(#prob)" filter="url(#soft)" />
            <ellipse cx="464" cy="257" rx="35" ry="27" />
            <ellipse cx="464" cy="257" rx="68" ry="52" />
            <ellipse cx="464" cy="257" rx="104" ry="77" />
            <circle cx="464" cy="257" r="5" />
            <text x="360" y="226">
              PROBABLE ORIGIN
            </text>
            <text x="360" y="239">
              {origin[1].toFixed(2)}°N, {origin[0].toFixed(2)}°E
            </text>
            <text x="483" y="276">
              RELEASE WINDOW FROM HINDCAST
            </text>
          </g>
        )}
        {layers.simulation && (
          <g className="sim-clouds">
            <path
              className="sim sim-a"
              d="M474 251C515 221 554 202 602 203C652 204 690 225 737 246C704 256 668 272 622 278C568 285 516 273 474 251Z"
            />
            <path
              className="sim sim-b"
              d="M474 251C520 236 571 230 625 245C675 259 719 288 764 316C707 305 660 303 609 293C552 282 508 269 474 251Z"
            />
            <path
              className="sim sim-c"
              d="M474 251C520 246 578 267 623 298C665 326 699 353 737 377C680 356 632 344 583 322C536 301 499 274 474 251Z"
            />
          </g>
        )}
        {layers.observed && (
          <g className="observed">
            <path d="M565 255C598 245 632 253 663 269C692 284 714 306 742 318C725 335 703 340 676 329C646 317 618 297 591 289C573 283 560 269 565 255Z" />
            <path
              d="M565 255C598 245 632 253 663 269C692 284 714 306 742 318"
              className="observed-edge"
            />
          </g>
        )}
        {layers.tracks && (
          <g className="tracks">
            <path className="track good" d="M463 257C510 290 573 322 649 349S761 391 838 421" />
            <path className="track warn" d="M463 257C431 207 421 161 428 112S438 73 421 51" />
            <path className="track good" d="M463 257C515 226 580 186 648 160S770 117 850 94" />
            <path className="track bad" d="M463 257C500 250 535 234 566 202" />
            <path className="track unknown" d="M463 257C419 293 387 335 361 389" />
            <g className="vessel good" transform="translate(838 421) rotate(116)">
              <path d="M0-9L6 7L0 4L-6 7Z" />
              <text transform="rotate(-116)" x="12" y="3">
                {vesselNames[0] ?? "VESSEL 1"}
              </text>
            </g>
            <g className="vessel warn" transform="translate(421 51) rotate(-8)">
              <path d="M0-9L6 7L0 4L-6 7Z" />
              <text transform="rotate(8)" x="12" y="3">
                {vesselNames[1] ?? "VESSEL 2"}
              </text>
            </g>
            <g className="vessel good" transform="translate(850 94) rotate(64)">
              <path d="M0-9L6 7L0 4L-6 7Z" />
              <text transform="rotate(-64)" x="12" y="3">
                {vesselNames[2] ?? "VESSEL 3"}
              </text>
            </g>
            <g className="vessel bad" transform="translate(566 202) rotate(50)">
              <path d="M0-9L6 7L0 4L-6 7Z" />
              <text transform="rotate(-50)" x="12" y="3">
                {vesselNames[3] ?? "VESSEL 4"}
              </text>
            </g>
            <g className="vessel unknown" transform="translate(361 389) rotate(222)">
              <path d="M0-9L6 7L0 4L-6 7Z" />
              <text transform="rotate(-222)" x="12" y="3">
                {vesselNames[4] ?? "RESERVE"}
              </text>
            </g>
          </g>
        )}
        <g className="scale">
          <path d="M770 590H920M770 585V595M820 585V595M870 585V595M920 585V595" />
          <text x="766" y="610">
            0
          </text>
          <text x="812" y="610">
            25
          </text>
          <text x="862" y="610">
            50
          </text>
          <text x="907" y="610">
            100 KM
          </text>
        </g>
        <g className="north" transform="translate(950 550)">
          <circle r="22" />
          <path d="M0-19V19M-19 0H19" />
          <text x="-4" y="-27">
            N
          </text>
        </g>
      </svg>
      <div className="map-coordinates">
        {origin[1].toFixed(3)}° N &nbsp; {origin[0].toFixed(3)}° E &nbsp; | &nbsp; HINDCAST ORIGIN
        &nbsp; | &nbsp; SCALE 1:950K
      </div>
      <div className="legend">
        <strong>MAP EVIDENCE</strong>
        <button onClick={() => toggle("observed")} className={!layers.observed ? "off" : ""}>
          <i className="key observed-key" />
          Observed oil slick
        </button>
        <button onClick={() => toggle("simulation")} className={!layers.simulation ? "off" : ""}>
          <i className="key simulated-key" />
          Simulated spill
        </button>
        <button onClick={() => toggle("probability")} className={!layers.probability ? "off" : ""}>
          <i className="key probability-key" />
          Hindcast probability
        </button>
        <button onClick={() => toggle("tracks")} className={!layers.tracks ? "off" : ""}>
          <i className="key track-key" />
          AIS vessel track
        </button>
        <span>
          <i className="triangle" />
          Vessel position / AIS integrity
        </span>
      </div>
    </div>
  );
}

function SarImage() {
  return (
    <div className="sar" aria-label="Sentinel-1 synthetic aperture radar thumbnail">
      <svg viewBox="0 0 240 122">
        <filter id="noise">
          <feTurbulence baseFrequency=".7" numOctaves="3" seed="9" />
          <feColorMatrix values=".8 0 0 0 .1 .8 0 0 0 .1 .8 0 0 0 .1 0 0 0 1 0" />
        </filter>
        <rect width="240" height="122" filter="url(#noise)" opacity=".6" />
        <path
          d="M38 75C55 55 71 47 93 50C113 53 119 43 137 34C154 25 176 27 188 38C172 48 168 62 156 72C139 87 121 93 96 91C75 89 59 82 38 75Z"
          className="sar-slick"
        />
      </svg>
      <span>S1A · VH POL · 10M</span>
    </div>
  );
}

function Heatmap() {
  return (
    <div className="heatmap">
      <svg viewBox="0 0 150 112">
        <defs>
          <radialGradient id="heat">
            <stop stopColor="var(--prob-hot)" />
            <stop offset=".25" stopColor="var(--prob-mid)" />
            <stop offset=".55" stopColor="var(--prob-cool)" />
            <stop offset="1" stopColor="var(--telemetry)" stopOpacity="0" />
          </radialGradient>
        </defs>
        <path
          d="M28 93C25 70 38 39 62 20C78 8 105 15 122 32C136 46 126 72 109 87C88 105 54 108 28 93Z"
          fill="url(#heat)"
        />
        <g fill="none" className="heat-contours">
          <ellipse cx="76" cy="61" rx="21" ry="36" transform="rotate(38 76 61)" />
          <ellipse cx="76" cy="61" rx="36" ry="52" transform="rotate(38 76 61)" />
        </g>
      </svg>
    </div>
  );
}

function SimFrame({ hour, index, active }: { hour: string; index: number; active: boolean }) {
  const d = [
    "M39 63C53 48 66 45 78 50C88 55 99 60 111 65C96 76 80 82 63 78C52 75 44 70 39 63Z",
    "M31 62C47 44 63 39 81 45C101 51 113 62 126 70C104 83 84 88 61 81C46 77 37 70 31 62Z",
    "M25 61C42 39 60 34 83 41C106 48 124 63 139 75C113 89 88 94 61 84C42 77 31 69 25 61Z",
    "M18 59C38 35 60 28 88 38C116 48 137 68 151 81C123 96 92 99 58 87C37 79 24 68 18 59Z",
  ][index];
  return (
    <div className={`sim-frame ${active ? "active" : ""}`}>
      <div className="frame-title">T + {hour}</div>
      <svg viewBox="0 0 170 105">
        <path className="frame-current" d="M5 83C43 70 70 81 103 65S142 32 169 29" />
        <path className="frame-sim" d={d} />
        <path
          className="frame-observed"
          d="M61 54C76 46 90 50 104 60C114 67 124 70 135 76C118 86 102 86 87 80C74 75 65 66 61 54Z"
        />
      </svg>
    </div>
  );
}

const integrityTone = (integrity: Candidate["vessel"]["ais_integrity"]) =>
  ({ consistent: "good", gap: "warn", inconsistent: "bad", insufficient_evidence: "unknown" })[
    integrity
  ];
const integrityLabel = (integrity: Candidate["vessel"]["ais_integrity"]) =>
  integrity.replaceAll("_", " ").toUpperCase();
const integrityColor = (integrity: Candidate["vessel"]["ais_integrity"]) =>
  ({ consistent: "text-ais-consistent", gap: "text-ais-gap", inconsistent: "text-ais-inconsistent", insufficient_evidence: "text-ais-unknown" })[
    integrity
  ];
const integrityBorder = (integrity: Candidate["vessel"]["ais_integrity"]) =>
  ({ consistent: "border-ais-consistent", gap: "border-ais-gap", inconsistent: "border-ais-inconsistent", insufficient_evidence: "border-ais-unknown" })[
    integrity
  ];
const displayUtc = (value: string) => new Date(value).toISOString().replace("T", " ").slice(0, 16);

function Workstation() {
  const [selected, setSelected] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [frame, setFrame] = useState(2);
  const [layers, setLayers] = useState({
    observed: true,
    simulation: true,
    probability: true,
    tracks: true,
  });
  const [clock, setClock] = useState("14:32:07");
  const [lightTheme, setLightTheme] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardSnapshot>(demoDashboard);
  const [dataMode, setDataMode] = useState<"loading" | "live" | "modelFallback" | "fallback">(
    "loading",
  );
  const [dataError, setDataError] = useState<string | null>(null);
  const [selectedCandidatePanel, setSelectedCandidatePanel] = useState(false);
  const [selectedSimulationPanel, setSelectedSimulationPanel] = useState(false);
  const [selectedDossierPanel, setSelectedDossierPanel] = useState(false);
  const [selectedConsistencyPanel, setSelectedConsistencyPanel] = useState(false);
  const [selectedDetectedOilPanel, setSelectedDetectedOilPanel] = useState(false);
  const [selectedHindcastPanel, setSelectedHindcastPanel] = useState(false);
  const [selectedWhyPanel, setSelectedWhyPanel] = useState(false);
  const [selectedEvidencePanel, setSelectedEvidencePanel] = useState(false);
  const reloadDashboard = useCallback(async () => {
    setDataMode("loading");
    try {
      const snapshot = await forensicsApi.getDashboard(demoDashboard.incident.incident_id);
      if (
        !snapshot.detection ||
        !snapshot.hindcast ||
        !snapshot.ranking ||
        !snapshot.simulations.length ||
        !snapshot.assessment
      ) {
        throw new Error("The live incident does not yet have a complete analysis snapshot.");
      }
      setDashboard(snapshot);
      setDataMode(snapshot.hindcast.is_fallback ? "modelFallback" : "live");
      setDataError(snapshot.hindcast.warnings.join(" ") || null);
    } catch (error) {
      setDashboard(demoDashboard);
      setDataMode("fallback");
      setDataError(error instanceof Error ? error.message : "Unable to load live analysis data.");
    }
  }, []);
  useEffect(() => {
    const tick = () => setClock(new Date().toISOString().slice(11, 19));
    tick();
    const id = window.setInterval(tick, 1000);
    return () => window.clearInterval(id);
  }, []);
  useEffect(() => {
    void reloadDashboard();
  }, [reloadDashboard]);
  useEffect(() => {
    const isLight = window.localStorage.getItem("forensic-theme") === "light";
    setLightTheme(isLight);
    document.documentElement.classList.toggle("light", isLight);
  }, []);
  const toggleTheme = () =>
    setLightTheme((current) => {
      const next = !current;
      document.documentElement.classList.toggle("light", next);
      window.localStorage.setItem("forensic-theme", next ? "light" : "dark");
      return next;
    });
  useEffect(() => {
    if (!playing) return;
    const id = window.setInterval(() => setFrame((v) => (v + 1) % 4), 900);
    return () => window.clearInterval(id);
  }, [playing]);

  // Close expanded panels on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (event.target instanceof HTMLElement && event.target.closest('.panel')) {
        return;
      }
      setSelectedCandidatePanel(false);
      setSelectedSimulationPanel(false);
      setSelectedDossierPanel(false);
      setSelectedConsistencyPanel(false);
      setSelectedDetectedOilPanel(false);
      setSelectedHindcastPanel(false);
      setSelectedWhyPanel(false);
      setSelectedEvidencePanel(false);
    };
    
    if (selectedCandidatePanel || selectedSimulationPanel || selectedDossierPanel || selectedConsistencyPanel || selectedDetectedOilPanel || selectedHindcastPanel || selectedWhyPanel || selectedEvidencePanel) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [selectedCandidatePanel, selectedSimulationPanel, selectedDossierPanel, selectedConsistencyPanel, selectedDetectedOilPanel, selectedHindcastPanel, selectedWhyPanel, selectedEvidencePanel]);
  const candidates = dashboard.ranking?.candidates ?? [];
  const candidate = candidates[selected] ?? candidates[0] ?? demoDashboard.ranking!.candidates[0]!;
  const detection = dashboard.detection ?? demoDashboard.detection!;
  const hindcast = dashboard.hindcast ?? demoDashboard.hindcast!;
  const simulation =
    dashboard.simulations.find((item) => item.candidate_id === candidate.vessel.vessel_id) ??
    dashboard.simulations[0] ??
    demoDashboard.simulations[0]!;
  const assessment = dashboard.assessment ?? demoDashboard.assessment!;
  const isNullResult = assessment.state === "no_sufficiently_consistent_vessel";
  if (!candidate) return null;
  const events = dashboard.evidence_events.length
    ? dashboard.evidence_events
    : demoDashboard.evidence_events;
  return (
    <main className="workstation">
      <header className="topbar">
        <div className="title-block">
          <h1>MARITIME OIL-SPILL FORENSIC ANALYSIS</h1>
          <p>Satellite intelligence for evidence-based vessel attribution</p>
        </div>
        <div className="workflow">
          {["DETECT", "TRACE", "ATTRIBUTE", "TEST", "INVESTIGATE"].map((x, i) => (
            <span className={i === 4 ? "active" : "done"} key={x}>
              {x}
              {i < 4 && <ChevronRight />}
            </span>
          ))}
        </div>
        <div className="top-actions">
          <label className="search">
            <Search />
            <input aria-label="Search" placeholder="Search vessel, location, incident ID..." />
          </label>
          <button
            className="icon-button"
            title="Refresh analysis data"
            onClick={() => void reloadDashboard()}
          >
            <RefreshCw />
          </button>
          <button
            className="icon-button theme-toggle"
            title={lightTheme ? "Switch to dark theme" : "Switch to light theme"}
            onClick={toggleTheme}
          >
            {lightTheme ? <Moon /> : <Sun />}
          </button>
          <button className="icon-button" title="Notifications">
            <Bell />
          </button>
          <div className="status" title={dataError ?? "Live API connection"}>
            <span>UTC {clock}</span>
            <b>
              <i />
              {dataMode === "live"
                ? "LIVE API"
                : dataMode === "modelFallback"
                  ? "MODEL FALLBACK"
                  : dataMode === "loading"
                    ? "CONNECTING"
                    : "DEMO FALLBACK"}
            </b>
          </div>
        </div>
      </header>
      <aside className="navrail">
        {nav.map(([Icon, label], i) => (
          <button key={label} className={i === 0 ? "selected" : ""} title={label}>
            <Icon />
            <span>{label}</span>
          </button>
        ))}
        <div className="nav-spacer" />
        <button title="Help">
          <CircleHelp />
          <span>Help</span>
        </button>
      </aside>
      <section className="metrics">
        <Metric label="INCIDENT ID" icon={Crosshair}>
          {dashboard.incident.incident_id}
        </Metric>
        <Metric label="SATELLITE" icon={Database}>
          {detection.satellite} SAR
        </Metric>
        <Metric
          label="DETECTED SLICK"
          icon={Waves}
          sub={`CONFIDENCE ${detection.oil_confidence.toFixed(2)} · ${detection.confidence_tier.toUpperCase()}`}
        >
          {detection.area_km2.toFixed(1)} km²
        </Metric>
        <Metric
          label="RELEASE WINDOW"
          icon={Activity}
          sub={`UNCERTAINTY ± ${hindcast.radius_km.toFixed(0)} KM`}
        >
          {displayUtc(hindcast.release_window_start).slice(5)}–
          {displayUtc(hindcast.release_window_end).slice(11)} UTC
        </Metric>
        <Metric label="SEARCH AREA" icon={MapPin}>
          2,850 km²
        </Metric>
        <Metric label="AIS CANDIDATES" icon={Ship} sub={`${candidates.length} SIMULATED`}>
          {dashboard.ranking?.raw_candidate_count ?? candidates.length}
        </Metric>
      </section>
      <div className="workspace">
        <div className="main-column">
          <MapWorkspace
            layers={layers}
            origin={hindcast.center}
            candidates={candidates}
            toggle={(key) => setLayers((v) => ({ ...v, [key]: !v[key] }))}
          />
          <div className="lower-grid">
            <Panel
              title="VESSEL CANDIDATES"
              className={`candidates ${selectedCandidatePanel ? 'expanded' : ''}`}
              action={
                <button className="utility" onClick={() => void reloadDashboard()}>
                  <RefreshCw /> REFRESH
                </button>
              }
              onClick={() => setSelectedCandidatePanel(!selectedCandidatePanel)}
            >
              {isNullResult ? (
                <div className="null-state">
                  <AlertTriangle />
                  <div>
                    <strong>NO SUFFICIENTLY CONSISTENT VESSEL IDENTIFIED</strong>
                    <p>{assessment.message}</p>
                  </div>
                </div>
              ) : (
                <>
                  <div className="table-head">
                    <span>#</span>
                    <span>VESSEL / TYPE</span>
                    <span>PROX.</span>
                    <span>SCORE</span>
                    <span>AIS INTEGRITY</span>
                  </div>
                  {candidates.map((c, i) => (
                    <button
                      key={c.vessel.vessel_id}
                      className={`candidate-row ${i === selected ? "active" : ""}`}
                      onClick={() => setSelected(i)}
                    >
                      <span>{c.rank}</span>
                      <span>
                        <b>{c.vessel.name}</b>
                        <small>{c.vessel.vessel_type}</small>
                      </span>
                      <span>{c.distance_to_origin_km.toFixed(0)} km</span>
                      <strong>{c.attribution_score.toFixed(2)}</strong>
                      <em className={integrityTone(c.vessel.ais_integrity)}>
                        {integrityLabel(c.vessel.ais_integrity)}
                      </em>
                    </button>
                  ))}
                </>
              )}
              <button className="expand" onClick={() => void reloadDashboard()}>
                <Search />
                REFRESH CANDIDATES
              </button>
            </Panel>
            <Panel
              title={`COUNTERFACTUAL SIMULATION — ${candidate.vessel.name}`}
              className={`simulation ${selectedSimulationPanel ? 'expanded' : ''}`}
              action={
                <div className="sim-actions">
                  <span>OBSERVED vs SIMULATED EVOLUTION</span>
                  <button
                    onClick={() => setPlaying((v) => !v)}
                    title={playing ? "Pause simulation" : "Play simulation"}
                  >
                    {playing ? <Pause /> : <Play />}
                  </button>
                </div>
              }
              onClick={() => setSelectedSimulationPanel(!selectedSimulationPanel)}
            >
              {selectedSimulationPanel && (
                <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setSelectedSimulationPanel(false)}
                    style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                  >
                    Close
                  </button>
                </div>
              )}
              <div className="frames">
                {["0 h", "6 h", "12 h", "24 h"].map((h, i) => (
                  <button
                    key={h}
                    onClick={() => {
                      setFrame(i);
                      setPlaying(false);
                    }}
                  >
                    <SimFrame hour={h} index={i} active={i === frame} />
                  </button>
                ))}
              </div>
              <div className="scrubber">
                <span>MODEL TIME</span>
                <input
                  type="range"
                  min="0"
                  max="3"
                  value={frame}
                  onChange={(e) => {
                    setFrame(Number(e.target.value));
                    setPlaying(false);
                  }}
                />
                <b>{["14:45", "20:45", "02:45", "14:45"][frame]} UTC</b>
              </div>
            </Panel>
            <Panel
              title="SELECTED VESSEL"
              className={`dossier ${selectedDossierPanel ? 'expanded' : ''}`}
              onClick={() => setSelectedDossierPanel(!selectedDossierPanel)}
            >
              {selectedDossierPanel && (
                <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setSelectedDossierPanel(false)}
                    style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                  >
                    Close
                  </button>
                </div>
              )}
              <div className="ship-image">
                <svg viewBox="0 0 180 90">
                  <path className="sea" d="M0 69Q25 62 45 69T90 69T135 69T180 69V90H0Z" />
                  <path className="hull" d="M24 50H141L126 69H45Z" />
                  <path className="deck" d="M45 39H126V50H45Z" />
                  <path className="bridge" d="M103 22H126V39H103Z" />
                  <path className="mast" d="M112 8V23M104 14H120" />
                </svg>
              </div>
              <div className="vessel-info">
                <h3>{candidate.vessel.name}</h3>
                <dl>
                  <dt>MMSI</dt>
                  <dd>{candidate.vessel.mmsi}</dd>
                  <dt>IMO</dt>
                  <dd>{candidate.vessel.imo ?? "—"}</dd>
                  <dt>TYPE</dt>
                  <dd>{candidate.vessel.vessel_type}</dd>
                  <dt>AIS</dt>
                  <dd>{integrityLabel(candidate.vessel.ais_integrity)}</dd>
                  <dt>PROXIMITY</dt>
                  <dd>{candidate.distance_to_origin_km.toFixed(1)} km</dd>
                  <dt>PRIORITY</dt>
                  <dd>{candidate.compute_priority.toFixed(2)}</dd>
                </dl>
              </div>
              <button className="primary-action">VIEW AIS TRACK</button>
            </Panel>
            <Panel
              title="SOURCE CONSISTENCY METRICS"
              className={`consistency ${selectedConsistencyPanel ? 'expanded' : ''}`}
              onClick={() => setSelectedConsistencyPanel(!selectedConsistencyPanel)}
            >
              <div className="bars">
                {[
                  ["Spatial Overlap (IoU)", simulation.components.spatial_iou, ""],
                  ["Centroid Match", simulation.components.centroid_match, ""],
                  ["Area Evolution", simulation.components.area_curve_dtw, ""],
                  ["Shape Similarity", simulation.components.shape_match, ""],
                ].map(([l, v, u]) => (
                  <div className="bar-row" key={String(l)}>
                    <span>{l}</span>
                    <div>
                      <i style={{ width: `${Number(v) * 100}%` }} />
                    </div>
                    <b>
                      {Number(v).toFixed(2)} <small>{u}</small>
                    </b>
                  </div>
                ))}
              </div>
              <div className="gauge">
                <svg viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="39" />
                  <circle className="value" cx="50" cy="50" r="39" pathLength="100" />
                  <text x="50" y="54">
                    {simulation.source_consistency_score.toFixed(2)}
                  </text>
                </svg>
                <strong>
                  {simulation.source_consistency_score >= 0.65
                    ? "HIGH CONSISTENCY"
                    : "LOW CONSISTENCY"}
                </strong>
                <small>
                  SOURCE CONSISTENCY
                  <br />
                  NOT A PROBABILITY OF GUILT
                </small>
              </div>
            </Panel>
          </div>
        </div>
        <aside className="intel-column">
          <Panel
            title="DETECTED OIL SLICK"
            className={`detected-oil ${selectedDetectedOilPanel ? 'expanded' : ''}`}
            action={<span className="evidence-tag observed-tag">OBSERVED</span>}
            onClick={() => setSelectedDetectedOilPanel(!selectedDetectedOilPanel)}
          >
            {selectedDetectedOilPanel && (
              <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setSelectedDetectedOilPanel(false)}
                  style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
            )}
            <div className="slick-data">
              <SarImage />
              <dl>
                <dt>SATELLITE</dt>
                <dd>{detection.satellite} (SAR)</dd>
                <dt>ACQUISITION</dt>
                <dd>{displayUtc(detection.acquired_at)} UTC</dd>
                <dt>AREA</dt>
                <dd>{detection.area_km2.toFixed(1)} km²</dd>
                <dt>CONFIDENCE</dt>
                <dd className="text-good">
                  {detection.oil_confidence.toFixed(2)} · {detection.confidence_tier.toUpperCase()}
                </dd>
                <dt>CLASSIFICATION</dt>
                <dd>{detection.classification.toUpperCase()}</dd>
              </dl>
            </div>
            <button className="secondary-action">
              VIEW FULL IMAGE <ChevronRight />
            </button>
          </Panel>
          <Panel
            title="HINDCAST ANALYSIS"
            className={`hindcast-panel ${selectedHindcastPanel ? 'expanded' : ''}`}
            action={<span className="evidence-tag inferred-tag">INFERRED</span>}
            onClick={() => setSelectedHindcastPanel(!selectedHindcastPanel)}
          >
            {selectedHindcastPanel && (
              <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setSelectedHindcastPanel(false)}
                  style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
            )}
            <div className="hindcast">
              <Heatmap />
              <dl>
                <dt>PROBABLE ORIGIN</dt>
                <dd>
                  {hindcast.center[1].toFixed(2)}° N, {hindcast.center[0].toFixed(2)}° E
                </dd>
                <dt>RELEASE WINDOW</dt>
                <dd>
                  {displayUtc(hindcast.release_window_start)}–
                  {displayUtc(hindcast.release_window_end).slice(11)} UTC
                </dd>
                <dt>UNCERTAINTY</dt>
                <dd>Approx. {hindcast.radius_km.toFixed(0)} km radius</dd>
                <dt>MODEL</dt>
                <dd>{hindcast.model}</dd>
                <dt>FORCING</dt>
                <dd>Provider supplied</dd>
              </dl>
            </div>
            <div className="color-scale">
              <span>HIGH PROBABILITY</span>
              <i />
              <span>LOW</span>
            </div>
          </Panel>
          <Panel
            title="WHY THIS CANDIDATE COULD BE THE CAUSE"
            className={`why-panel ${selectedWhyPanel ? 'expanded' : ''}`}
            action={<span className="evidence-tag compared-tag">COMPARED</span>}
            onClick={() => setSelectedWhyPanel(!selectedWhyPanel)}
          >
            {selectedWhyPanel && (
              <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setSelectedWhyPanel(false)}
                  style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
            )}
            <ul className="evidence-list">
              {assessment.dossier.map((item, index) => (
                <li className={index < 2 ? "pass" : index === 2 ? "caution" : "info"} key={item}>
                  {item}
                </li>
              ))}
            </ul>
            <div className="assessment">
              <strong>SYSTEM ASSESSMENT</strong>
              <p>{assessment.message}</p>
            </div>
          </Panel>
          <Panel
            title="EVIDENCE CHAIN"
            className={`timeline ${selectedEvidencePanel ? 'expanded' : ''}`}
            action={
              <button className="mini-select">
                ALL EVENTS <ChevronDown />
              </button>
            }
            onClick={() => setSelectedEvidencePanel(!selectedEvidencePanel)}
          >
            {selectedEvidencePanel && (
              <div className="close-expanded" onClick={(e) => e.stopPropagation()}>
                <button
                  onClick={() => setSelectedEvidencePanel(false)}
                  style={{ position: 'absolute', top: '8px', right: '8px', background: 'transparent', border: '1px solid var(--border)', color: 'var(--text-primary)', padding: '2px 8px', cursor: 'pointer' }}
                >
                  Close
                </button>
              </div>
            )}
            {events.map((event) => {
              const cls =
                (
                  { OBSERVED: "obs", INFERRED: "inf", SIMULATED: "sim", SYSTEM: "sys" } as Record<
                    string,
                    string
                  >
                )[event.kind] ?? "gap";
              return (
                <div className={`event ${cls}`} key={event.id}>
                  <i />
                  <time>{displayUtc(event.occurred_at)}</time>
                  <span>{event.description}</span>
                  <b>{event.kind}</b>
                </div>
              );
            })}
          </Panel>
        </aside>
      </div>
      <footer>
        <span>
          <i />
          {dataMode === "live"
            ? "LIVE DATA"
            : dataMode === "modelFallback"
              ? "MODEL FALLBACK"
              : "DEMO FALLBACK"}
        </span>
        <span>SATELLITE</span>
        <span>AIS</span>
        <span>METOCEAN</span>
        <span>FORENSIC SIMULATION</span>
        <div />
        <span>MODEL: {hindcast.model}</span>
        <span>UPDATED: {displayUtc(dashboard.updated_at)} UTC</span>
      </footer>
    </main>
  );
}
