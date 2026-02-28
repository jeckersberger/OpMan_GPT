let map;
let lastClickedLatLng = null;

let teams = [];
let missions = [];
let assignments = [];

let selectedTeamId = null;
let selectedMissionId = null;

let teamMarkers = new Map();     // teamId -> L.CircleMarker
let missionMarkers = new Map();  // missionId -> L.Marker

let assignedTeamIds = new Set(); // Teams, die bereits irgendwo zugewiesen sind

// Exercise layer (Funkübung)
let exerciseGeodata = null;       // geodata from /api/exercise/geodata
let casedocData = [];             // from /api/casedocs
let exerciseMarkers = new Map();  // caseId (string) -> L.Marker
let connectionLines = [];         // L.Polyline[] team <-> case
let startpunktMarker = null;

const $ = (id) => document.getElementById(id);

// ---- Funkstatus (nur 0-9) ----
const RADIO_OPTIONS = [
  [1, "S1 – Frei auf Funk"],
  [2, "S2 – Frei auf Wache"],
  [3, "S3 – Einsatz übernommen"],
  [4, "S4 – Am Einsatzort"],
  [5, "S5 – Sprechwunsch"],
  [6, "S6 – nicht Einsatzbereit"],
  [7, "S7 – Patient aufgenommen"],
  [8, "S8 – Am Transportziel"],
  [9, "S9 – Sonderfunktion"],
  [0, "S0 – prio. Sprechwunsch"],
];

const RADIO_LABELS = new Map(RADIO_OPTIONS.map(([c, t]) => [c, t.replace(/^S\d+\s–\s/, "")]));
const DISPATCHABLE_CODES = new Set([1, 2]); // "frei" = nur S1/S2

// Statusfarben (einheitlich für Marker, Badges, etc.)
const STATUS_COLORS = new Map([
  [1, "#22cc66"],   // grün
  [2, "#0d7a3a"],   // dunkelgrün
  [3, "#f5c842"],   // gelb
  [4, "#2299ff"],   // blau
  [5, "#888888"],   // grau
  [6, "#888888"],   // grau
  [7, "#ff8800"],   // orange
  [8, "#9b59b6"],   // lila
  [9, "#888888"],   // grau
  [0, "#ff3333"],   // rot
]);

function esc(s){
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function badge(text){ return `<span class="badge">${esc(text)}</span>`; }
function priorityBadge(p){ return `<span class="badge">P${esc(p)}</span>`; }

function radioText(code, label, pending=false){
  const l = label || RADIO_LABELS.get(code) || "";
  return `S${code}${l ? " – " + l : ""}${pending ? " ·P" : ""}`;
}

function radioBadge(code, label, pending=false){
  const col = STATUS_COLORS.get(code) || "#888";
  const extra = pending
    ? ` style="background:#3a2800;color:#f5c842;border:1px solid #f5c842;font-weight:700;"`
    : ` style="background:${col}22;color:${col};border:1px solid ${col};"`;
  return `<span class="badge"${extra}>${esc(radioText(code, label, pending))}</span>`;
}

function colorDot(hex){
  const safe = hex || "#4ea1ff";
  return `<span class="colorDot" style="background:${safe}"></span>`;
}

function setSelectionLabel(){
  const t = teams.find(x => x.id === selectedTeamId);
  const m = missions.find(x => x.id === selectedMissionId);
  const parts = [];
  if (t) parts.push(`Trupp: ${t.name}`);
  if (m) parts.push(`Einsatz: ${m.title}`);
  $("selectionLabel").textContent = parts.length ? parts.join(" | ") : "—";
}

async function api(url, options){
  const res = await fetch(url, options);
  if (!res.ok){
    let msg = `${res.status} ${res.statusText}`;
    try{
      const data = await res.json();
      if (data?.error) msg += `: ${data.error}`;
    }catch(_){}
    alert(msg);
    throw new Error(msg);
  }
  return res.json();
}

// ---------------- Map ----------------
function initMap(){
  map = L.map("map").setView([49.3783, 11.2134], 15); // Default: Feucht

  const layers = {
    "🗺 OpenStreetMap": L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap"
    }),
    "🛰 Satellite": L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, attribution: "&copy; Esri World Imagery"
    }),
    "🏔 Topo": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17, attribution: "&copy; OpenTopoMap"
    }),
  };

  layers["🗺 OpenStreetMap"].addTo(map);
  L.control.layers(layers, {}, { position: "topright", collapsed: false }).addTo(map);

  map.on("click", (e) => {
    lastClickedLatLng = e.latlng;
    $("lastClick").textContent = `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;

    // quick-fill create forms
    $("missionLat").value = e.latlng.lat.toFixed(6);
    $("missionLng").value = e.latlng.lng.toFixed(6);
  });
}

// ---------------- Marker styles ----------------

// GPS-Alter in Sekunden (null wenn kein GPS)
function gpsAgeSec(t) {
  if (!t.gps_updated_at) return null;
  return (Date.now() - new Date(t.gps_updated_at).getTime()) / 1000;
}

// Teams: Kreis + permanentes Label "Name | Aktueller Status"
function upsertTeamMarker(t){
  // Wenn kein GPS / keine Position: am Startpunkt anzeigen (grau, halbtransparent)
  const hasPosition = t.lat != null && t.lng != null;
  const sp = exerciseGeodata?.startpunkt;
  if (!hasPosition && !sp) return;  // kein Startpunkt bekannt → kein Marker

  const atStart = !hasPosition;

  const key = t.id;
  const ll = atStart ? [sp.lat, sp.lng] : [t.lat, t.lng];

  const statusText = radioText(t.radio_status, t.radio_status_label);
  const statusCol = STATUS_COLORS.get(t.radio_status) || "#888";
  const age = gpsAgeSec(t);
  const isLiveGps = !atStart && age !== null && age < 120;  // live = GPS-Update vor < 2 Min
  const gpsInfo = atStart
    ? " | wartet auf GPS"
    : (t.gps_updated_at
        ? ` | GPS ${new Date(t.gps_updated_at).toLocaleTimeString("de-DE", {hour:"2-digit", minute:"2-digit", second:"2-digit"})}`
        : " | manuell");
  const tooltipText = `${t.name} | ${statusText}${gpsInfo}`;
  const tooltipHtml = `<span style="background:${statusCol};color:#fff;padding:1px 5px;border-radius:3px;font-size:11px;font-weight:600;white-space:nowrap;">${esc(t.name)} | ${esc(statusText)}</span>`;
  const popupHtml =
    `${esc(t.name)}${t.callsign ? " (" + esc(t.callsign) + ")" : ""}<br>` +
    `${esc(statusText)}<br>` +
    (atStart
      ? `<span style="color:#888">⏳ Wartet auf GPS – am Startpunkt</span>`
      : isLiveGps
        ? `<span style="color:#3ddc84">● Live-GPS (${Math.round(age)}s)</span>`
        : `<span style="color:#a6b3d1">○ ${t.gps_updated_at ? "GPS " + new Date(t.gps_updated_at).toLocaleTimeString("de-DE") : "Manuell"}</span>`);
  // Punkt: GPS-Status (grau = kein GPS, blau = GPS aktiv/live)
  const gpsCol = atStart ? "#888" : (isLiveGps ? "#2299ff" : "#888");
  const style = {
    radius: atStart ? 5 : 7,
    color: atStart ? "#666" : (isLiveGps ? "#2299ff" : "#666"),
    weight: 3,
    fillColor: gpsCol,
    fillOpacity: atStart ? 0.45 : 0.95,
  };

  if (teamMarkers.has(key)){
    const marker = teamMarkers.get(key);
    marker.setLatLng(ll);
    marker.setStyle(style);
    marker.setPopupContent(popupHtml);

    // Puls-Klasse setzen/entfernen je nach Live-GPS-Status
    const el = marker.getElement();
    if (el) el.classList.toggle("gps-live", isLiveGps);

    // Tooltip aktualisieren (Leaflet: tooltip exists after bindTooltip)
    if (marker.getTooltip()){
      marker.unbindTooltip();
    }
    marker.bindTooltip(tooltipHtml, {
      permanent: true,
      direction: "right",
      offset: [10, 0],
      opacity: 0.95,
      className: "team-tt",
    });
  } else {
    const marker = L.circleMarker(ll, style).addTo(map).bindPopup(popupHtml);
    marker.bindTooltip(tooltipHtml, {
      permanent: true,
      direction: "right",
      offset: [10, 0],
      opacity: 0.95,
      className: "team-tt",
    });

    marker.on("click", () => {
      selectedTeamId = t.id;
      renderTeams();
      setSelectionLabel();
    });

    // Puls-Klasse direkt nach Erstellen setzen
    marker.on("add", () => {
      const el = marker.getElement();
      if (el && isLiveGps) el.classList.add("gps-live");
    });

    teamMarkers.set(key, marker);
  }
}

// Einsätze: Stecknadel (SVG) + permanentes Label "Einsatzname"
function makeMissionIcon(color){
  const c = color || "red";
  const svg = `
    <svg width="26" height="42" viewBox="0 0 26 42" xmlns="http://www.w3.org/2000/svg">
      <path d="M13 41 C13 41 2 26 2 16 C2 8.268 7.82 2 13 2 C18.18 2 24 8.268 24 16 C24 26 13 41 13 41 Z"
            fill="${c}" stroke="rgba(0,0,0,0.35)" stroke-width="1.5"/>
      <circle cx="13" cy="16" r="5.5" fill="rgba(255,255,255,0.9)" stroke="rgba(0,0,0,0.25)" stroke-width="1"/>
    </svg>
  `.trim();

  return L.divIcon({
    className: "",
    html: svg,
    iconSize: [26, 42],
    iconAnchor: [13, 40],
    popupAnchor: [0, -36],
  });
}

// Mission-Farbe:
// - Rot: kein Trupp zugewiesen
// - Gelb: Trupp(e) zugewiesen, aber keiner Status 4/7/8
// - Grün: mind. ein zugewiesener Trupp hat Status 4 oder 7 oder 8
function missionColor(m){
  const assignedTeams = m.teams || [];
  if (!assignedTeams.length) return "red";
  const greenCodes = new Set([4, 7, 8]);
  const anyGreen = assignedTeams.some(t => greenCodes.has(Number(t.radio_status)));
  return anyGreen ? "green" : "yellow";
}

// ---------------- Exercise Layer helpers ----------------

// Color by CaseDoc status: grey → yellow → orange → blue → green → dark (done)
function exerciseCaseColor(doc) {
  if (doc?.completed) return "#444444";                    // dark: station done, don't dispatch
  if (!doc || !doc.alarm_time) return "#777777";           // grey: not alarmed
  if (doc.status8_time || doc.status7_time) return "#22cc66"; // green: S7/S8
  if (doc.status4_time) return "#2299ff";                  // blue: S4 on scene
  if (doc.status3_time) return "#ff8800";                  // orange: S3 en route
  return "#ffcc00";                                        // yellow: alarmed, pre-S3
}

// Straight-line distance (Haversine) in km
function haversine(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const toRad = d => d * Math.PI / 180;
  const dLat = toRad(lat2 - lat1);
  const dLng = toRad(lng2 - lng1);
  const a = Math.sin(dLat / 2) ** 2
    + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function walkingTimeStr(km) {
  const mins = Math.round(km / 4.5 * 60);
  if (mins < 60) return `${mins} min`;
  return `${Math.floor(mins / 60)}h ${mins % 60}min`;
}

function makeExerciseIcon(color, label, completed) {
  const bg = color || "#777777";
  const border = completed ? "2px dashed #3ddc84" : "2px solid rgba(0,0,0,0.55)";
  const strike = completed ? "text-decoration:line-through;opacity:0.85;" : "";
  const check = completed
    ? `<div style="position:absolute;top:-5px;right:-5px;background:#3ddc84;color:#000;` +
      `border-radius:50%;width:14px;height:14px;display:flex;align-items:center;` +
      `justify-content:center;font-size:8px;font-weight:bold;line-height:1;">✓</div>`
    : "";
  const html = `<div style="position:relative;width:30px;height:30px;">` +
    `<div style="background:${bg};color:#fff;width:30px;height:30px;border-radius:50%;` +
    `border:${border};display:flex;align-items:center;justify-content:center;` +
    `font-weight:bold;font-size:11px;box-shadow:0 2px 5px rgba(0,0,0,0.5);font-family:monospace;${strike}">${label}</div>` +
    `${check}</div>`;
  return L.divIcon({ className: "", html, iconSize: [30, 30], iconAnchor: [15, 15], popupAnchor: [0, -17] });
}

function makeStartpunktIcon() {
  const html = `<div style="background:#9933cc;color:#fff;width:40px;height:20px;border-radius:4px;` +
    `border:2px solid rgba(0,0,0,0.55);display:flex;align-items:center;justify-content:center;` +
    `font-weight:bold;font-size:10px;box-shadow:0 2px 5px rgba(0,0,0,0.5);">START</div>`;
  return L.divIcon({ className: "", html, iconSize: [40, 20], iconAnchor: [20, 10], popupAnchor: [0, -12] });
}

function refreshExerciseLayer() {
  if (!exerciseGeodata) return;

  // Remove old connection lines
  for (const line of connectionLines) line.remove();
  connectionLines = [];

  const cases = exerciseGeodata.cases || {};

  for (const [id, data] of Object.entries(cases)) {
    if (data.lat == null || data.lng == null) continue;

    const doc = casedocData.find(d => d.id === id);
    const color = exerciseCaseColor(doc);
    const completed = !!doc?.completed;
    const ll = [data.lat, data.lng];

    // Draw dashed line from assigned EVT team to this case (skip if completed)
    let walkExtra = "";
    if (doc?.assigned_evt && !completed) {
      const team = teams.find(t => t.name === doc.assigned_evt || t.callsign === doc.assigned_evt);
      if (team?.lat != null) {
        const km = haversine(team.lat, team.lng, data.lat, data.lng);
        walkExtra = ` | ~${walkingTimeStr(km)} Fußweg`;
        const line = L.polyline([[team.lat, team.lng], ll], {
          color, weight: 2, dashArray: "6 4", opacity: 0.75,
        }).addTo(map);
        connectionLines.push(line);
      }
    }

    const tooltipText = `${completed ? "✓ FERTIG | " : ""}${id}: ${data.schlagwort}${walkExtra}`;
    const popupHtml = `<b>${esc(id)}</b>: ${esc(data.schlagwort)}<br>Patient: ${esc(data.patient)}` +
      (completed ? `<br><b style="color:#3ddc84">✓ Station abgeschlossen</b>` : "");

    if (exerciseMarkers.has(id)) {
      const marker = exerciseMarkers.get(id);
      marker.setLatLng(ll);
      marker.setIcon(makeExerciseIcon(color, id, completed));
      if (marker.getTooltip()) {
        marker.setTooltipContent(tooltipText);
      } else {
        marker.bindTooltip(tooltipText, { permanent: true, direction: "right", offset: [18, 0], opacity: 0.9 });
      }
      marker.setPopupContent(popupHtml);
    } else {
      const marker = L.marker(ll, { icon: makeExerciseIcon(color, id, completed) })
        .addTo(map)
        .bindTooltip(tooltipText, { permanent: true, direction: "right", offset: [18, 0], opacity: 0.9 })
        .bindPopup(popupHtml);
      exerciseMarkers.set(id, marker);
    }
  }

  // Startpunkt marker
  const sp = exerciseGeodata.startpunkt;
  if (sp?.lat != null) {
    if (!startpunktMarker) {
      startpunktMarker = L.marker([sp.lat, sp.lng], { icon: makeStartpunktIcon() })
        .addTo(map)
        .bindTooltip("Startpunkt", { permanent: true, direction: "right", offset: [22, 0], opacity: 0.9 })
        .bindPopup("Startpunkt der Funkübung");
    } else {
      startpunktMarker.setLatLng([sp.lat, sp.lng]);
    }
  }
}

async function loadExerciseLayer() {
  try {
    [exerciseGeodata, casedocData] = await Promise.all([
      api("/api/exercise/geodata"),
      api("/api/casedocs"),
    ]);
  } catch (e) {
    console.warn("Exercise layer konnte nicht geladen werden:", e);
    return;
  }

  refreshExerciseLayer();

  // Auto-fit map bounds to all exercise locations
  const pts = [];
  for (const data of Object.values(exerciseGeodata.cases || {})) {
    if (data.lat != null) pts.push([data.lat, data.lng]);
  }
  const sp = exerciseGeodata.startpunkt;
  if (sp?.lat != null) pts.push([sp.lat, sp.lng]);
  if (pts.length > 0) {
    map.fitBounds(L.latLngBounds(pts).pad(0.15));
  }
}

function upsertMissionMarker(m){
  if (m.lat == null || m.lng == null) return;

  // Übungsfälle werden bereits als Exercise-Marker dargestellt → kein doppelter Pin
  if (exerciseGeodata) {
    const caseMatch = m.title.match(/^(P\d+):/);
    if (caseMatch && exerciseGeodata.cases && exerciseGeodata.cases[caseMatch[1]]) return;
  }

  const key = m.id;
  const ll = [m.lat, m.lng];
  const col = missionColor(m);
  const label = `${m.title} - ${m.status} (P${m.priority})`;

  if (missionMarkers.has(key)){
    const marker = missionMarkers.get(key);
    marker.setLatLng(ll);
    marker.setIcon(makeMissionIcon(col));
    marker.setPopupContent(label);

    if (marker.getTooltip()){
      marker.setTooltipContent(m.title);
    } else {
      marker.bindTooltip(m.title, {
        permanent: true,
        direction: "right",
        offset: [14, -10],
        opacity: 0.95,
      });
    }
  } else {
    const marker = L.marker(ll, { icon: makeMissionIcon(col) }).addTo(map).bindPopup(label);
    marker.bindTooltip(m.title, {
      permanent: true,
      direction: "right",
      offset: [14, -10],
      opacity: 0.95,
    });

    marker.on("click", () => {
      selectedMissionId = m.id;
      renderMissions();
      setSelectionLabel();
    });

    missionMarkers.set(key, marker);
  }
}

function cleanupMarkers(){
  const currentMissionIds = new Set(missions.map(m => m.id));
  for (const [id, marker] of missionMarkers.entries()) {
    if (!currentMissionIds.has(id)) {
      marker.remove();
      missionMarkers.delete(id);
    }
  }
  // Mission-Marker entfernen die jetzt als Exercise-Marker dargestellt werden
  if (exerciseGeodata) {
    for (const [id, marker] of missionMarkers.entries()) {
      const m = missions.find(x => x.id === id);
      if (!m) continue;
      const caseMatch = m.title.match(/^(P\d+):/);
      if (caseMatch && exerciseGeodata.cases && exerciseGeodata.cases[caseMatch[1]]) {
        marker.remove();
        missionMarkers.delete(id);
      }
    }
  }
  const currentTeamIds = new Set(teams.map(t => t.id));
  for (const [id, marker] of teamMarkers.entries()) {
    if (!currentTeamIds.has(id)) {
      marker.remove();
      teamMarkers.delete(id);
    }
  }
}

function rebuildMarkers(){
  cleanupMarkers();
  for (const t of teams) upsertTeamMarker(t);
  for (const m of missions) upsertMissionMarker(m);
}

// ---------------- Render: Teams ----------------
function renderTeams(){
  const root = $("teamsList");
  root.innerHTML = "";

  teams.forEach(t => {
    const sel = (t.id === selectedTeamId);
    const assigned = (t.missions || []);
    const latVal = (t.lat == null ? "" : String(t.lat));
    const lngVal = (t.lng == null ? "" : String(t.lng));

    const assignedHtml = assigned.length
      ? `<div class="mini"><b>Zugewiesene Einsätze:</b><br/>${assigned
          .map(mi => `• ${esc(mi.title)} (${esc(mi.status)}, P${esc(mi.priority)})`)
          .join("<br/>")}</div>`
      : `<div class="mini">Keine zugewiesenen Einsätze</div>`;

    const el = document.createElement("div");
    el.className = "item";

    el.innerHTML = `
      <div class="row">
        <div>
          <div><b>${colorDot(t.color)}${esc(t.name)}</b>
            ${t.callsign ? `<span class="badge">${esc(t.callsign)}</span>` : ""}
          </div>
          <div style="margin-top:4px;">
            ${radioBadge(t.radio_status, t.radio_status_label, !!t.pending_alarm)}
            ${(t.radio_group||"regelfunk")==="bettenkanal"
              ? `<span class="badge" style="color:#c084fc;border-color:#c084fc;">🏥 Betten</span>`
              : `<span class="badge" style="color:#4ea1ff;border-color:#4ea1ff;">📻 Regel</span>`}
            ${(()=>{
              if (t.lat == null) return `<span class="badge">ohne Position</span>`;
              const age = gpsAgeSec(t);
              const live = age !== null && age < 120;
              const gpsLabel = live
                ? `<span class="badge" style="color:#3ddc84;border-color:#3ddc84;">● GPS live</span>`
                : (t.gps_updated_at
                    ? `<span class="badge" style="color:#f5c842;border-color:#f5c842;" title="GPS ${new Date(t.gps_updated_at).toLocaleTimeString('de-DE')}">○ GPS ${new Date(t.gps_updated_at).toLocaleTimeString('de-DE',{hour:'2-digit',minute:'2-digit'})}</span>`
                    : `<span class="badge">manuell</span>`);
              return `<span class="badge">${Number(t.lat).toFixed(4)}, ${Number(t.lng).toFixed(4)}</span> ${gpsLabel}`;
            })()}
            ${assignedTeamIds.has(t.id) ? `<span class="badge">zugewiesen</span>` : ""}
          </div>
        </div>
        <div class="badge ${sel ? "sel" : ""}">ID ${esc(t.id)}</div>
      </div>

      <div class="row">
        <select data-team-radio="${esc(t.id)}" title="Funkstatus">
          ${RADIO_OPTIONS.map(([v, txt]) => `<option value="${v}" ${v===t.radio_status?"selected":""}>${esc(txt)}</option>`).join("")}
        </select>
      </div>

      <div class="row">
        <input data-team-color="${esc(t.id)}" type="color" value="${esc(t.color || "#4ea1ff")}" title="Trupp-Farbe" />
        <button data-team-select="${esc(t.id)}">${sel ? "Ausgewählt" : "Wählen"}</button>
        <button data-team-pan="${esc(t.id)}">Karte</button>
        <button data-team-del="${esc(t.id)}">Löschen</button>
      </div>

      <div class="mini"><b>Position ändern:</b></div>
      <div class="row">
        <input data-team-lat="${esc(t.id)}" placeholder="lat" value="${esc(latVal)}" />
        <input data-team-lng="${esc(t.id)}" placeholder="lng" value="${esc(lngVal)}" />
      </div>
      <div class="row">
        <button data-team-useclick="${esc(t.id)}">Kartenklick übernehmen</button>
        <button data-team-savepos="${esc(t.id)}">Position speichern</button>
      </div>

      ${assignedHtml}
    `;
    root.appendChild(el);
  });

  // ---- events ----
  root.querySelectorAll("[data-team-select]").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedTeamId = parseInt(btn.getAttribute("data-team-select"), 10);
      setSelectionLabel();
      renderTeams();
    });
  });

  root.querySelectorAll("[data-team-pan]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.getAttribute("data-team-pan"), 10);
      const t = teams.find(x => x.id === id);
      if (t?.lat != null) map.setView([t.lat, t.lng], map.getZoom());
      if (teamMarkers.has(id)) teamMarkers.get(id).openPopup();
    });
  });

  root.querySelectorAll("[data-team-del]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.getAttribute("data-team-del"), 10);
      await api(`/api/teams/${id}`, { method: "DELETE" });
      if (selectedTeamId === id) selectedTeamId = null;
      await refreshAll();
    });
  });

  root.querySelectorAll("[data-team-radio]").forEach(sel => {
    sel.addEventListener("change", async () => {
      const id = parseInt(sel.getAttribute("data-team-radio"), 10);
      await api(`/api/teams/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ radio_status: parseInt(sel.value, 10) })
      });
      await refreshAll(false);
    });
  });

  root.querySelectorAll("[data-team-color]").forEach(inp => {
    inp.addEventListener("change", async () => {
      const id = parseInt(inp.getAttribute("data-team-color"), 10);
      await api(`/api/teams/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ color: inp.value })
      });
      await refreshAll(false);
    });
  });

  // Kartenklick übernehmen
  root.querySelectorAll("[data-team-useclick]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.getAttribute("data-team-useclick"), 10);
      if (!lastClickedLatLng){
        alert("Bitte zuerst auf die Karte klicken, um Koordinaten zu übernehmen.");
        return;
      }
      const latInput = root.querySelector(`[data-team-lat="${id}"]`);
      const lngInput = root.querySelector(`[data-team-lng="${id}"]`);
      latInput.value = lastClickedLatLng.lat.toFixed(6);
      lngInput.value = lastClickedLatLng.lng.toFixed(6);
    });
  });

  // Position speichern
  root.querySelectorAll("[data-team-savepos]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.getAttribute("data-team-savepos"), 10);
      const latInput = root.querySelector(`[data-team-lat="${id}"]`);
      const lngInput = root.querySelector(`[data-team-lng="${id}"]`);
      const lat = latInput.value ? parseFloat(latInput.value) : null;
      const lng = lngInput.value ? parseFloat(lngInput.value) : null;

      if (lat == null || lng == null || Number.isNaN(lat) || Number.isNaN(lng)){
        alert("Bitte gültige lat/lng Werte eingeben.");
        return;
      }

      await api(`/api/teams/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat, lng })
      });
      await refreshAll(false);
    });
  });
}

// ---------------- Render: Missions ----------------
function renderMissions(){
  const root = $("missionsList");
  root.innerHTML = "";

  missions.forEach(m => {
    const sel = (m.id === selectedMissionId);
    const assignedTeams = (m.teams || []);
    const col = missionColor(m);

    const assignedHtml = assignedTeams.length
      ? `<div class="mini"><b>Zugewiesene Trupps:</b><br/>${assignedTeams
          .map(t => `${colorDot(t.color)}${esc(t.name)} (${esc(radioText(t.radio_status, t.radio_status_label))})`)
          .join("<br/>")}</div>`
      : `<div class="mini">Keine Trupps zugewiesen</div>`;

    // Verfügbare Trupps: Funkstatus 1/2 UND NICHT bereits zugewiesen
    const dispatchableTeams = teams.filter(t =>
      DISPATCHABLE_CODES.has(Number(t.radio_status)) && !assignedTeamIds.has(t.id)
    );

    const options = dispatchableTeams.length
      ? dispatchableTeams
          .map(t => `<option value="${esc(t.id)}">${esc(t.name)} (${esc(radioText(t.radio_status, t.radio_status_label))})</option>`)
          .join("")
      : `<option value="">Keine freien Trupps (Funk 1/2) verfügbar</option>`;

    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><b>${esc(m.title)}</b></div>
          <div style="margin-top:4px;">
            ${badge(m.status)}
            ${priorityBadge(m.priority)}
            ${badge("Marker: " + col.toUpperCase())}
            ${m.lat!=null ? `<span class="badge">${Number(m.lat).toFixed(4)}, ${Number(m.lng).toFixed(4)}</span>` : `<span class="badge">ohne Position</span>`}
          </div>
        </div>
        <div class="badge ${sel ? "sel" : ""}">ID ${esc(m.id)}</div>
      </div>

      <div class="row">
        <select data-mission-status="${esc(m.id)}">
          ${["offen","zugewiesen","in_arbeit","abgeschlossen","abgebrochen"].map(s => `<option value="${s}" ${s===m.status?"selected":""}>${esc(s)}</option>`).join("")}
        </select>
        <select data-mission-prio="${esc(m.id)}">
          ${[1,2,3,4,5].map(p => `<option value="${p}" ${p===m.priority?"selected":""}>P${esc(p)}</option>`).join("")}
        </select>
      </div>

      <div class="row">
        <select data-mission-assign-team="${esc(m.id)}">
          <option value="">Trupp wählen…</option>
          ${options}
        </select>
        <button data-mission-assign-btn="${esc(m.id)}">Zuweisen</button>
      </div>

      <div class="row actions">
        <button data-mission-select="${esc(m.id)}">${sel ? "Ausgewählt" : "Wählen"}</button>
        <button data-mission-pan="${esc(m.id)}">Karte</button>
        <button data-mission-del="${esc(m.id)}">Löschen</button>
      </div>

      ${m.description ? `<div class="tiny">${esc(m.description)}</div>` : ""}
      ${assignedHtml}
    `;
    root.appendChild(el);
  });

  root.querySelectorAll("[data-mission-select]").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedMissionId = parseInt(btn.getAttribute("data-mission-select"), 10);
      setSelectionLabel();
      renderMissions();
    });
  });

  root.querySelectorAll("[data-mission-pan]").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = parseInt(btn.getAttribute("data-mission-pan"), 10);
      const m = missions.find(x => x.id === id);
      if (!m) return;

      // Übungsfall? → zum Exercise-Marker springen
      const caseMatch = m.title.match(/^(P\d+):/);
      if (caseMatch && exerciseMarkers.has(caseMatch[1])) {
        const exMarker = exerciseMarkers.get(caseMatch[1]);
        map.setView(exMarker.getLatLng(), map.getZoom());
        exMarker.openPopup();
        return;
      }

      if (m.lat != null) map.setView([m.lat, m.lng], map.getZoom());
      if (missionMarkers.has(id)) missionMarkers.get(id).openPopup();
    });
  });

  root.querySelectorAll("[data-mission-del]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.getAttribute("data-mission-del"), 10);
      await api(`/api/missions/${id}`, { method: "DELETE" });
      if (selectedMissionId === id) selectedMissionId = null;
      await refreshAll();
    });
  });

  root.querySelectorAll("[data-mission-status]").forEach(sel => {
    sel.addEventListener("change", async () => {
      const id = parseInt(sel.getAttribute("data-mission-status"), 10);
      await api(`/api/missions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: sel.value })
      });
      await refreshAll(false);
    });
  });

  root.querySelectorAll("[data-mission-prio]").forEach(sel => {
    sel.addEventListener("change", async () => {
      const id = parseInt(sel.getAttribute("data-mission-prio"), 10);
      await api(`/api/missions/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ priority: parseInt(sel.value, 10) })
      });
      await refreshAll(false);
    });
  });

  root.querySelectorAll("[data-mission-assign-btn]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const missionId = parseInt(btn.getAttribute("data-mission-assign-btn"), 10);
      const sel = root.querySelector(`[data-mission-assign-team="${missionId}"]`);
      const teamId = sel.value ? parseInt(sel.value, 10) : null;

      if (!teamId){
        alert("Bitte einen freien Trupp auswählen (Funk 1/2).");
        return;
      }

      await api("/api/assignments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: teamId, mission_id: missionId })
      });

      await refreshAll(false);
    });
  });
}

// ---------------- Render: Assignments ----------------
function renderAssignments(){
  const root = $("assignmentsList");
  root.innerHTML = "";

  assignments.forEach(a => {
    const el = document.createElement("div");
    el.className = "item";
    el.innerHTML = `
      <div class="row">
        <div>
          <div><b>${colorDot(a.team.color)}${esc(a.team.name)}</b> → ${esc(a.mission.title)}</div>
          <div class="tiny">${esc(radioText(a.team.radio_status, a.team.radio_status_label))} | ${esc(a.mission.status)}</div>
        </div>
        <button data-as-del="${esc(a.id)}">✕</button>
      </div>
    `;
    root.appendChild(el);
  });

  root.querySelectorAll("[data-as-del]").forEach(btn => {
    btn.addEventListener("click", async () => {
      const id = parseInt(btn.getAttribute("data-as-del"), 10);
      await api(`/api/assignments/${id}`, { method: "DELETE" });
      await refreshAll(false);
    });
  });
}

// ---------------- Refresh ----------------
function computeAssignedTeamIds(){
  assignedTeamIds = new Set(assignments.map(a => a.team_id));
}

function normalizeRadioLabels(){
  teams = teams.map(t => ({
    ...t,
    radio_status: Number(t.radio_status),
    radio_status_label: t.radio_status_label || RADIO_LABELS.get(Number(t.radio_status)) || ""
  }));

  missions = missions.map(m => ({
    ...m,
    teams: (m.teams || []).map(t => ({
      ...t,
      radio_status: Number(t.radio_status),
      radio_status_label: t.radio_status_label || RADIO_LABELS.get(Number(t.radio_status)) || ""
    }))
  }));
}

async function refreshAll(rebuild = true){
  // Beim ersten Laden: eingebettete Daten nutzen (kein Request nötig)
  let data;
  if (window.__INITIAL_DATA__) {
    data = window.__INITIAL_DATA__;
    delete window.__INITIAL_DATA__;
  } else {
    data = await api("/api/dashboard");
  }
  teams = data.teams;
  missions = data.missions;
  assignments = data.assignments;
  casedocData = data.casedocs;

  normalizeRadioLabels();
  computeAssignedTeamIds();

  renderTeams();
  renderMissions();
  renderAssignments();
  setSelectionLabel();

  if (rebuild){
    rebuildMarkers();
  } else {
    cleanupMarkers();
    for (const t of teams) upsertTeamMarker(t);
    for (const m of missions) upsertMissionMarker(m);
  }

  if (exerciseGeodata) refreshExerciseLayer();
  renderSprechwunschPanel();
}

// ---------------- Sprechwunsch-Panel ----------------
// Web Audio API – Benachrichtigungston erzeugen (kein Audio-Datei-Download nötig)
function _playSWTone(prio) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const schedule = prio
      ? [[440, 0.00, 0.12], [550, 0.13, 0.12], [660, 0.26, 0.18]]   // S0: 3 aufsteigende Töne
      : [[520, 0.00, 0.10], [520, 0.12, 0.10]];                       // S5: 2 kurze gleiche Töne
    schedule.forEach(([freq, start, dur]) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.frequency.value = freq;
      osc.type = "sine";
      gain.gain.setValueAtTime(0.35, ctx.currentTime + start);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + start + dur);
      osc.start(ctx.currentTime + start);
      osc.stop(ctx.currentTime + start + dur + 0.05);
    });
  } catch (_) { /* AudioContext nicht verfügbar */ }
}

const _swKnownIds = new Set();  // IDs der bereits bekannten Sprechwunsch-Teams

function _swRows(teamList) {
  const byTime = (a, b) => new Date(a.updated_at) - new Date(b.updated_at);
  const s0 = teamList.filter(t => t.radio_status === 0).sort(byTime);
  const s5 = teamList.filter(t => t.radio_status === 5).sort(byTime);
  return [...s0, ...s5].map(t => {
    const cls   = t.radio_status === 0 ? "s0" : "s5";
    const badge = t.radio_status === 0 ? "S0 PRIO" : "S5";
    const time  = new Date(t.updated_at).toLocaleTimeString("de-DE",
                    {hour:"2-digit", minute:"2-digit"});
    // Show both name and callsign when they differ
    const hasCallsign = t.callsign && t.callsign !== t.name;
    const mainLine  = hasCallsign ? t.callsign : t.name;
    const subLine   = hasCallsign ? t.name : null;
    return `<li class="sw-item ${cls}">
      <div class="sw-names">
        <span class="sw-callsign">${esc(mainLine)}</span>
        ${subLine ? `<span class="sw-subname">${esc(subLine)}</span>` : ""}
      </div>
      <div class="sw-meta">
        <span class="sw-badge ${cls}">${badge}</span>
        <span class="sw-time">${time}</span>
        <button class="sw-quit" onclick="quittieren(${t.id})">✓</button>
      </div>
    </li>`;
  }).join("") || `<li style="padding:.6rem 1rem;font-size:.8rem;color:var(--muted);">–</li>`;
}

function renderSprechwunschPanel() {
  const panel = document.getElementById("swPanel");
  if (!panel) return;

  const sw = teams.filter(t => t.radio_status === 0 || t.radio_status === 5);

  if (sw.length === 0) {
    panel.classList.remove("sw-visible");
    _swKnownIds.clear();
    return;
  }

  // Ton abspielen für neu hinzugekommene Einträge
  sw.forEach(t => {
    if (!_swKnownIds.has(t.id)) {
      _swKnownIds.add(t.id);
      _playSWTone(t.radio_status === 0);
    }
  });
  // Quittierte entfernen
  const swIds = new Set(sw.map(t => t.id));
  for (const id of _swKnownIds) { if (!swIds.has(id)) _swKnownIds.delete(id); }

  const regel  = sw.filter(t => (t.radio_group || "regelfunk") === "regelfunk");
  const betten = sw.filter(t => (t.radio_group || "regelfunk") === "bettenkanal");
  const hasS0  = sw.some(t => t.radio_status === 0);
  const label  = hasS0 ? "🚨 Sprechwunsch" : "📻 Sprechwunsch";

  panel.className = "sw-panel sw-visible";
  panel.innerHTML = `
    <div class="sw-header">${label}&nbsp;<span style="opacity:.7;font-weight:400">${sw.length}</span></div>
    <div class="sw-cols">
      <div class="sw-col">
        <div class="sw-col-header c-regel">📻 Regelfunk&nbsp;<span style="opacity:.6">${regel.length}</span></div>
        <ul class="sw-list">${_swRows(regel)}</ul>
      </div>
      <div class="sw-col">
        <div class="sw-col-header c-betten">🏥 Bettenkanal&nbsp;<span style="opacity:.6">${betten.length}</span></div>
        <ul class="sw-list">${_swRows(betten)}</ul>
      </div>
    </div>`;
}

async function quittieren(teamId) {
  await api(`/api/teams/${teamId}/quittieren`, { method: "POST" });
  await refreshAll(false);
}

// ---------------- UI Wiring ----------------
function wireUI(){
  $("btnRefresh").addEventListener("click", () => refreshAll(false));

  $("btnLocate").addEventListener("click", () => {
    if (!navigator.geolocation){
      alert("Geolocation wird vom Browser nicht unterstützt.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const lat = pos.coords.latitude;
        const lng = pos.coords.longitude;
        map.setView([lat, lng], 14);
      },
      () => alert("Position konnte nicht ermittelt werden.")
    );
  });

  $("btnCreateTeam").addEventListener("click", async () => {
    const payload = {
      callsign: $("teamCallsign").value.trim() || undefined,
      color: $("teamColor").value,
    };

    const t = await api("/api/teams", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    selectedTeamId = t.id;
    $("teamCallsign").value = "";
    await refreshAll();
  });

  $("btnCreateMission").addEventListener("click", async () => {
    const payload = {
      title: $("missionTitle").value.trim(),
      description: $("missionDesc").value.trim(),
      status: $("missionStatus").value,
      priority: parseInt($("missionPriority").value, 10),
      lat: $("missionLat").value ? parseFloat($("missionLat").value) : null,
      lng: $("missionLng").value ? parseFloat($("missionLng").value) : null,
    };

    const m = await api("/api/missions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    selectedMissionId = m.id;
    $("missionTitle").value = "";
    $("missionDesc").value = "";
    await refreshAll();
  });

  const btnImport = $("btnImportExercise");
  if (btnImport) {
    btnImport.addEventListener("click", async () => {
      btnImport.disabled = true;
      btnImport.textContent = "Importiere…";
      try {
        const result = await api("/api/exercise/import-missions", { method: "POST" });
        const created = result.created || [];
        const newOnes = created.filter(c => !c.skipped).length;
        const skipped = created.filter(c => c.skipped).length;
        alert(`Import: ${newOnes} neu angelegt, ${skipped} übersprungen (bereits vorhanden).`);
        await refreshAll(true);
        if (typeof loadExerciseLayer === "function") await loadExerciseLayer();
      } catch (e) {
        // error already shown by api()
      } finally {
        btnImport.disabled = false;
        btnImport.textContent = "📥 Übungsfälle als Einsätze importieren";
      }
    });
  }

  // global Assign (links+rechts auswählen)
  const btnAssign = $("btnAssign");
  if (btnAssign){
    btnAssign.addEventListener("click", async () => {
      if (!selectedTeamId || !selectedMissionId){
        alert("Bitte einen Trupp (links) und einen Einsatz (rechts) auswählen.");
        return;
      }

      // Frontend-Schutz: bereits zugewiesene Teams nicht erneut anbieten
      if (assignedTeamIds.has(selectedTeamId)){
        alert("Dieser Trupp ist bereits einem Einsatz zugewiesen und kann nicht erneut zugewiesen werden.");
        return;
      }

      // Frontend-Schutz: nur Funk 1/2
      const t = teams.find(x => x.id === selectedTeamId);
      if (!t || !DISPATCHABLE_CODES.has(Number(t.radio_status))){
        alert("Dieser Trupp ist nicht frei (nur Funk 1/2 sind disponierbar).");
        return;
      }

      await api("/api/assignments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ team_id: selectedTeamId, mission_id: selectedMissionId })
      });

      await refreshAll(false);
    });
  }
}

// ---------------- Connection-Status + Auto-Refresh ----------------
let _connOk = true;
let _connFailCount = 0;

function _showConnBanner(ok) {
  let banner = document.getElementById("connBanner");
  if (!banner) {
    banner = document.createElement("div");
    banner.id = "connBanner";
    banner.style.cssText = "position:fixed;top:0;left:0;right:0;z-index:9999;padding:6px 12px;" +
      "text-align:center;font-size:.85rem;font-weight:600;transition:transform .3s;transform:translateY(-100%);";
    document.body.appendChild(banner);
  }
  if (!ok) {
    _connFailCount++;
    banner.style.background = "#b91c1c";
    banner.style.color = "#fff";
    banner.textContent = `⚠ Verbindung zum Server verloren (${_connFailCount}x)`;
    banner.style.transform = "translateY(0)";
  } else if (_connOk !== ok && _connFailCount > 0) {
    banner.style.background = "#15803d";
    banner.style.color = "#fff";
    banner.textContent = "✓ Verbindung wiederhergestellt";
    banner.style.transform = "translateY(0)";
    _connFailCount = 0;
    setTimeout(() => { banner.style.transform = "translateY(-100%)"; }, 3000);
  } else {
    banner.style.transform = "translateY(-100%)";
  }
  _connOk = ok;
}

async function _silentRefreshAll() {
  // Fetch mit 15s Timeout (Flask dev-server + HTTPS kann langsam sein)
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const res = await fetch("/api/dashboard", { signal: ctrl.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error("API error");
    const data = await res.json();
    teams = data.teams;
    missions = data.missions;
    assignments = data.assignments;
    casedocData = data.casedocs;
    normalizeRadioLabels();
    computeAssignedTeamIds();
    renderTeams(); renderMissions(); renderAssignments(); setSelectionLabel();
    cleanupMarkers();
    for (const t of teams) upsertTeamMarker(t);
    for (const m of missions) upsertMissionMarker(m);
    if (exerciseGeodata) refreshExerciseLayer();
    renderSprechwunschPanel();
  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

// Polling: Banner erst nach 5 aufeinanderfolgenden Fehlern anzeigen
let _pollFailStreak = 0;
let _pollBusy = false;
setInterval(async () => {
  if (_pollBusy) return;  // vorheriger Poll noch nicht fertig
  _pollBusy = true;
  try {
    await _silentRefreshAll();
    _pollFailStreak = 0;
    _showConnBanner(true);
  } catch (_) {
    _pollFailStreak++;
    if (_pollFailStreak >= 8) _showConnBanner(false);
  } finally {
    _pollBusy = false;
  }
}, 15000);

// ---------------- LAN-Info (Handy-Zugang) ----------------
let _lanInfo = null;

async function loadLanInfo() {
  try {
    const res = await fetch("/api/server-info");
    if (!res.ok) return;
    _lanInfo = await res.json();
    const el = document.getElementById("lanInfo");
    if (el) el.textContent = `📡 ${_lanInfo.ip}:${_lanInfo.port}`;
  } catch (_) { /* silent */ }
}

function showLanModal() {
  if (!_lanInfo) return;
  document.getElementById("lanUrl").textContent = _lanInfo.evt_url;
  document.getElementById("lanQr").src =
    `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(_lanInfo.evt_url)}`;
  const certLink = document.getElementById("certDownloadLink");
  if (certLink) certLink.href = `${_lanInfo.base_url}/cert`;
  document.getElementById("lanModal").style.display = "flex";
}

async function showQrSetup() {
  document.getElementById("lanModal").style.display = "none";
  const qrModal = document.getElementById("qrSetupModal");
  const grid = document.getElementById("qrGrid");
  grid.innerHTML = '<div style="text-align:center;color:#a6b3d1;padding:2rem;">Lade QR-Codes…</div>';
  qrModal.style.display = "flex";
  try {
    const res = await fetch("/api/qrcodes");
    if (!res.ok) throw new Error("Fehler beim Laden");
    const data = await res.json();
    grid.innerHTML = data.codes.map(c => `
      <div style="text-align:center;background:#0b1220;border:1px solid #223152;border-radius:10px;padding:1rem;">
        <div style="font-weight:700;font-size:1.1rem;margin-bottom:.5rem;color:#4ea1ff;">${esc(c.name)}</div>
        <img src="data:image/svg+xml;base64,${c.img_b64}" alt="${esc(c.name)}" style="width:160px;height:160px;border-radius:6px;background:#fff;"/>
        <div style="font-size:.65rem;color:#a6b3d1;margin-top:.4rem;word-break:break-all;">${esc(c.url)}</div>
      </div>
    `).join('');
  } catch (e) {
    grid.innerHTML = `<div style="color:#ff6b6b;text-align:center;padding:1rem;">Fehler: ${esc(e.message)}</div>`;
  }
}

function printQrCodes() {
  const w = window.open('', '_blank');
  // Alle QR-Karten extrahieren, aber für Druck-Layout vereinfachen
  const cards = document.querySelectorAll('#qrGrid > div');
  let html = '';
  cards.forEach(card => {
    const name = card.querySelector('div')?.textContent || '';
    const img = card.querySelector('img');
    const url = card.querySelectorAll('div')[2]?.textContent || '';
    html += `<div class="card"><h3>${esc(name)}</h3>${img ? `<img src="${img.src}" style="width:160px;height:160px;"/>` : ''}<div class="url">${esc(url)}</div></div>`;
  });
  w.document.write(`<!doctype html><html><head><title>QR-Codes – EVT Setup</title>
    <style>body{font-family:sans-serif;margin:1rem;text-align:center;color:#000}
    .grid{display:flex;flex-wrap:wrap;gap:1.5rem;justify-content:center}
    .card{border:1px solid #ccc;border-radius:8px;padding:1rem;width:200px;page-break-inside:avoid}
    .card img{width:160px;height:160px} .card h3{margin:.5rem 0 .3rem}
    .url{font-size:.6rem;color:#666;word-break:break-all}
    @media print{body{margin:0}}</style></head><body>
    <h1>EVT Setup – QR-Codes</h1>
    <p>Scannen = EVT-App mit richtigem Team vorausgewählt</p>
    <div class="grid">${html}</div>
    </body></html>`);
  w.document.close();
  w.onload = () => { w.print(); };
}

// ---------------- Übungs-Timer ----------------
let _timerStart   = null;   // Date when timer was started
let _timerElapsed = 0;      // ms accumulated before last pause
let _timerHandle  = null;

function _timerFmt(ms) {
  const s = Math.floor(ms / 1000);
  const m = Math.floor(s / 60);
  const h = Math.floor(m / 60);
  if (h > 0) return `${String(h).padStart(2,"0")}:${String(m%60).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;
  return `${String(m).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;
}

function _timerTick() {
  const el = $("timerDisplay");
  if (!el) return;
  const ms = _timerElapsed + (Date.now() - _timerStart);
  el.textContent = _timerFmt(ms);
}

function timerToggle() {
  if (_timerHandle) {
    // Pause
    _timerElapsed += Date.now() - _timerStart;
    _timerStart = null;
    clearInterval(_timerHandle);
    _timerHandle = null;
    $("timerDisplay").style.color = "#f5c842";
  } else {
    // Start / Resume
    _timerStart = Date.now();
    _timerHandle = setInterval(_timerTick, 500);
    $("timerDisplay").style.color = "#3ddc84";
  }
}

function timerReset() {
  clearInterval(_timerHandle);
  _timerHandle  = null;
  _timerStart   = null;
  _timerElapsed = 0;
  const el = $("timerDisplay");
  if (el) { el.textContent = "00:00"; el.style.color = "#3ddc84"; }
}

// ---------------- Übungs-Reset ----------------
function showResetModal() {
  $("resetModal").style.display = "flex";
}

async function doReset() {
  const include_log  = $("rsLog").checked;
  const delete_teams = $("rsDeleteTeams").checked;
  const reset_teams  = $("rsTeams").checked && !delete_teams;

  const warn = delete_teams
    ? "ACHTUNG: Alle Trupps und Einsätze werden gelöscht!\n\nTrotzdem zurücksetzen?"
    : "Übung zurücksetzen? Alle Falldokumentationen und Zuweisungen werden geleert.";
  if (!confirm(warn)) return;

  await api("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ include_log, reset_teams, delete_teams }),
  });
  $("resetModal").style.display = "none";
  await refreshAll(true);
  if (exerciseGeodata) refreshExerciseLayer();
}

// ---------------- Testalarm ----------------
function showTestAlarmModal() {
  const list = $("taTeamList");
  list.innerHTML = "";
  teams.forEach(t => {
    const row = document.createElement("label");
    row.style.cssText = "display:flex;align-items:center;gap:.5rem;cursor:pointer;font-size:.85rem;padding:.2rem .3rem;border-radius:4px;";
    row.innerHTML = `<input type="checkbox" value="${esc(t.id)}" checked style="accent-color:#f5c842;" />`
      + `${colorDot(t.color)}${esc(t.name)}`
      + (t.callsign ? ` <span style="color:#aaa;font-size:.8rem;">(${esc(t.callsign)})</span>` : "");
    list.appendChild(row);
  });
  $("testAlarmModal").style.display = "flex";
}

function taSelectAll()  { $("taTeamList").querySelectorAll("input[type=checkbox]").forEach(c => c.checked = true); }
function taSelectNone() { $("taTeamList").querySelectorAll("input[type=checkbox]").forEach(c => c.checked = false); }

async function sendTestAlarm() {
  const text = $("taText").value.trim() || "Testalarm";
  const checked = [...$("taTeamList").querySelectorAll("input[type=checkbox]:checked")];
  const team_ids = checked.map(c => parseInt(c.value, 10));
  if (!team_ids.length) { alert("Bitte mindestens ein Team auswählen."); return; }
  const btn = $("taSendBtn");
  btn.disabled = true;
  btn.textContent = "Sende…";
  try {
    await api("/api/testalarm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team_ids, text }),
    });
    $("testAlarmModal").style.display = "none";
  } finally {
    btn.disabled = false;
    btn.textContent = "🔔 Senden";
  }
}

// ---------------- Boot ----------------
window.addEventListener("DOMContentLoaded", async () => {
  initMap();
  wireUI();
  // Exercise-Geodaten VOR dem ersten Marker-Aufbau laden,
  // damit upsertMissionMarker() doppelte Pins sofort erkennt.
  try {
    [exerciseGeodata, casedocData] = await Promise.all([
      api("/api/exercise/geodata"),
      api("/api/casedocs"),
    ]);
  } catch (_) { /* kein Übungsbetrieb aktiv */ }
  await refreshAll(true);
  if (exerciseGeodata) refreshExerciseLayer();
  // Auto-fit map bounds to exercise locations
  if (exerciseGeodata) {
    const pts = [];
    for (const data of Object.values(exerciseGeodata.cases || {})) {
      if (data.lat != null) pts.push([data.lat, data.lng]);
    }
    const sp = exerciseGeodata.startpunkt;
    if (sp?.lat != null) pts.push([sp.lat, sp.lng]);
    if (pts.length > 0) map.fitBounds(L.latLngBounds(pts).pad(0.15));
  }
  loadLanInfo();
});