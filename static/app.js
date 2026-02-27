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
  [1, "1 – Frei auf Funk"],
  [2, "2 – Frei auf Wache"],
  [3, "3 – Auf Anfahrt"],
  [4, "4 – Am Einsatzort"],
  [5, "5 – Sprechwunsch"],
  [6, "6 – nicht Einsatzbereit"],
  [7, "7 – gebunden"],
  [8, "8 – Bedingt Einsatzbereit"],
  [9, "9 – Sonderfunktion"],
  [0, "0 – prio. Sprechwunsch"],
];

const RADIO_LABELS = new Map(RADIO_OPTIONS.map(([c, t]) => [c, t.replace(/^\d+\s–\s/, "")]));
const DISPATCHABLE_CODES = new Set([1, 2]); // "frei" = nur Funk 1/2

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
  return `Funk ${code}${l ? " – " + l : ""}${pending ? " ·P" : ""}`;
}

function radioBadge(code, label, pending=false){
  const extra = pending
    ? ' style="background:#3a2800;color:#f5c842;border:1px solid #f5c842;font-weight:700;"'
    : '';
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
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap"
  }).addTo(map);

  map.on("click", (e) => {
    lastClickedLatLng = e.latlng;
    $("lastClick").textContent = `${e.latlng.lat.toFixed(6)}, ${e.latlng.lng.toFixed(6)}`;

    // quick-fill create forms
    $("teamLat").value = e.latlng.lat.toFixed(6);
    $("teamLng").value = e.latlng.lng.toFixed(6);
    $("missionLat").value = e.latlng.lat.toFixed(6);
    $("missionLng").value = e.latlng.lng.toFixed(6);
  });
}

// ---------------- Marker styles ----------------

// Teams: Kreis + permanentes Label "Name | Aktueller Status"
function upsertTeamMarker(t){
  if (t.lat == null || t.lng == null) return;

  const key = t.id;
  const ll = [t.lat, t.lng];

  const statusText = radioText(t.radio_status, t.radio_status_label);
  const tooltipText = `${t.name} | ${statusText}`;
  const popupHtml =
    `${esc(t.name)}${t.callsign ? " (" + esc(t.callsign) + ")" : ""}<br>` +
    `${esc(statusText)}`;

  const style = {
    radius: 7,
    color: t.color || "#4ea1ff",
    weight: 3,
    fillColor: t.color || "#4ea1ff",
    fillOpacity: 0.95,
  };

  if (teamMarkers.has(key)){
    const marker = teamMarkers.get(key);
    marker.setLatLng(ll);
    marker.setStyle(style);
    marker.setPopupContent(popupHtml);

    // Tooltip-Text aktualisieren (Leaflet: tooltip exists after bindTooltip)
    if (marker.getTooltip()){
      marker.setTooltipContent(tooltipText);
    } else {
      marker.bindTooltip(tooltipText, {
        permanent: true,
        direction: "right",
        offset: [10, 0],
        opacity: 0.95,
      });
    }
  } else {
    const marker = L.circleMarker(ll, style).addTo(map).bindPopup(popupHtml);
    marker.bindTooltip(tooltipText, {
      permanent: true,
      direction: "right",
      offset: [10, 0],
      opacity: 0.95,
    });

    marker.on("click", () => {
      selectedTeamId = t.id;
      renderTeams();
      setSelectionLabel();
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
            ${t.lat!=null ? `<span class="badge">${Number(t.lat).toFixed(4)}, ${Number(t.lng).toFixed(4)}</span>` : `<span class="badge">ohne Position</span>`}
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
      if (t?.lat != null) map.setView([t.lat, t.lng], 15);
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
      if (m?.lat != null) map.setView([m.lat, m.lng], 15);
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
  [teams, missions, assignments, casedocData] = await Promise.all([
    api("/api/teams"),
    api("/api/missions"),
    api("/api/assignments"),
    api("/api/casedocs"),
  ]);

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
                    {hour:"2-digit", minute:"2-digit", second:"2-digit"});
    const primary   = t.callsign || t.name;
    const secondary = t.callsign && t.callsign !== t.name ? t.name : null;
    return `<li class="sw-item ${cls}">
      <span class="sw-badge ${cls}">${badge}</span>
      <span class="sw-name">
        <span class="sw-callsign">${esc(primary)}</span>${secondary
          ? `<br><span class="sw-subname">${esc(secondary)}</span>`
          : ""}
      </span>
      <span class="sw-time">${time}</span>
      <button class="sw-quit" onclick="quittieren(${t.id})">✓</button>
    </li>`;
  }).join("") || `<li style="padding:.5rem .8rem;font-size:.75rem;color:var(--muted);">–</li>`;
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

  const regel   = sw.filter(t => (t.radio_group || "regelfunk") === "regelfunk");
  const betten  = sw.filter(t => (t.radio_group || "regelfunk") === "bettenkanal");
  const hasS0   = sw.some(t => t.radio_status === 0);
  const label   = hasS0 ? "🚨 Sprechwunsch" : "📻 Sprechwunsch";

  panel.className = "sw-panel sw-visible";
  panel.innerHTML = `
    <div class="sw-header">${label}&nbsp;<span style="opacity:.7">${sw.length}</span></div>
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
      name: $("teamName").value.trim(),
      callsign: $("teamCallsign").value.trim(),
      radio_status: parseInt($("teamRadioStatus").value, 10),
      color: $("teamColor").value,
      lat: $("teamLat").value ? parseFloat($("teamLat").value) : null,
      lng: $("teamLng").value ? parseFloat($("teamLng").value) : null,
    };

    const t = await api("/api/teams", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    selectedTeamId = t.id;
    $("teamName").value = "";
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
      btnImport.textContent = "Lade Koordinaten…";
      try {
        // Erst Cache prüfen; nur wenn keine Koordinaten im Cache → API (refresh=1)
        let geo = await api("/api/exercise/geodata");
        const cachedWithCoords = Object.values(geo.cases || {}).filter(c => c.lat != null).length;
        if (cachedWithCoords === 0) {
          btnImport.textContent = "Löse w3w-Adressen auf…";
          geo = await api("/api/exercise/geodata?refresh=1");
        }
        const cases = geo.cases || {};
        const withCoords = Object.values(cases).filter(c => c.lat != null).length;
        const total = Object.keys(cases).length;
        if (withCoords === 0) {
          const proceed = confirm(
            `⚠ Keine Koordinaten vorhanden (${total} Fälle).\n\n` +
            `Möglicherweise ist die w3w-API nicht erreichbar.\n` +
            `Koordinaten können manuell über „📍 Koordinaten manuell eingeben" gesetzt werden.\n\n` +
            `Trotzdem importieren (ohne Kartenposition)?`
          );
          if (!proceed) return;
        }
        btnImport.textContent = "Importiere…";
        const result = await api("/api/exercise/import-missions", { method: "POST" });
        const created = result.created || [];
        const newOnes = created.filter(c => !c.skipped).length;
        const skipped = created.filter(c => c.skipped).length;
        const noCoord = created.filter(c => {
          const caseData = cases[c.title?.split(":")[0]?.trim()];
          return caseData && caseData.lat == null;
        }).length;
        let msg = `Import: ${newOnes} neu angelegt, ${skipped} übersprungen (bereits vorhanden).`;
        if (withCoords < total) msg += `\n⚠ ${total - withCoords} Fälle ohne Koordinaten (w3w fehlgeschlagen).`;
        alert(msg);
        await refreshAll(true);
        if (typeof loadExerciseLayer === "function") await loadExerciseLayer();
      } catch (e) {
        // error already shown by api()
      } finally {
        btnImport.disabled = false;
        btnImport.textContent = "📥 Übungsfälle als Einsätze importieren (P1–P6)";
      }
    });
  }

  const btnRefreshGeo = $("btnRefreshGeodata");
  if (btnRefreshGeo) {
    btnRefreshGeo.addEventListener("click", async () => {
      btnRefreshGeo.disabled = true;
      btnRefreshGeo.textContent = "Löse auf…";
      try {
        await api("/api/exercise/geodata?refresh=1");
        if (typeof loadExerciseLayer === "function") await loadExerciseLayer();
      } catch (e) { /* shown by api() */ } finally {
        btnRefreshGeo.disabled = false;
        btnRefreshGeo.textContent = "🗺 w3w-Koordinaten neu auflösen";
      }
    });
  }

  // Manual coordinate entry modal
  const btnEditCoords = $("btnEditCoords");
  if (btnEditCoords) {
    btnEditCoords.addEventListener("click", async () => {
      // Load current geodata (cached or null coords)
      let geo = { cases: {}, startpunkt: null };
      try { geo = await api("/api/exercise/geodata"); } catch (e) { /* use empty */ }

      const cases = geo.cases || {};
      const sp = geo.startpunkt || {};
      const rowsDiv = $("coordRows");

      // Build table rows
      const rowStyle = "display:grid;grid-template-columns:3.5rem 1fr 5.5rem 5.5rem;gap:.35rem;align-items:center;margin-bottom:.4rem;";
      const inputStyle = "background:#0b1220;border:1px solid #334;border-radius:4px;color:#e8edf8;padding:.25rem .4rem;font-size:.78rem;font-family:inherit;width:100%;";
      const labelStyle = "font-size:.78rem;color:#a6b3d1;";
      const linkStyle = "font-size:.75rem;color:#4ea1ff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;";

      let html = `<div style="${rowStyle}font-weight:700;">
        <span style="${labelStyle}">Fall</span>
        <span style="${labelStyle}">w3w-Adresse</span>
        <span style="${labelStyle}">Latitude</span>
        <span style="${labelStyle}">Longitude</span>
      </div>`;

      const caseOrder = ["P1","P2","P3","P4","P5","P6"];
      for (const cid of caseOrder) {
        const c = cases[cid] || {};
        const w3w = (c.w3w || "").replace(/^\/+/, "");
        const w3wUrl = w3w ? `https://what3words.com/${encodeURIComponent(w3w)}` : "#";
        const lat = c.lat != null ? c.lat : "";
        const lng = c.lng != null ? c.lng : "";
        html += `<div style="${rowStyle}">
          <span style="${labelStyle};font-weight:700;">${esc(cid)}</span>
          <a href="${w3wUrl}" target="_blank" rel="noopener" style="${linkStyle}" title="${esc(w3w)}">${esc(w3w) || "–"}</a>
          <input class="coord-lat" data-case="${esc(cid)}" data-w3w="${esc(w3w)}" value="${lat}" placeholder="48.1234" style="${inputStyle}">
          <input class="coord-lng" data-case="${esc(cid)}" value="${lng}" placeholder="11.5678" style="${inputStyle}">
        </div>`;
      }
      // Startpunkt row
      const spW3w = (sp.w3w || "").replace(/^\/+/, "");
      const spUrl = spW3w ? `https://what3words.com/${encodeURIComponent(spW3w)}` : "#";
      html += `<div style="${rowStyle}">
        <span style="${labelStyle};font-weight:700;">Start</span>
        <a href="${spUrl}" target="_blank" rel="noopener" style="${linkStyle}" title="${esc(spW3w)}">${esc(spW3w) || "–"}</a>
        <input id="spLat" data-w3w="${esc(spW3w)}" value="${sp.lat != null ? sp.lat : ""}" placeholder="48.1234" style="${inputStyle}">
        <input id="spLng" value="${sp.lng != null ? sp.lng : ""}" placeholder="11.5678" style="${inputStyle}">
      </div>`;

      rowsDiv.innerHTML = html;
      const modal = $("coordModal");
      modal.style.display = "block";
    });
  }

  const btnSaveCoords = $("btnSaveCoords");
  if (btnSaveCoords) {
    btnSaveCoords.addEventListener("click", async () => {
      const payload = { cases: {}, startpunkt: {} };
      document.querySelectorAll(".coord-lat").forEach(inp => {
        const cid = inp.dataset.case;
        const lat = parseFloat(inp.value);
        const lngInp = document.querySelector(`.coord-lng[data-case="${cid}"]`);
        const lng = parseFloat(lngInp ? lngInp.value : "");
        payload.cases[cid] = {
          lat: isNaN(lat) ? null : lat,
          lng: isNaN(lng) ? null : lng,
        };
      });
      const spLat = parseFloat(($("spLat") || {}).value);
      const spLng = parseFloat(($("spLng") || {}).value);
      payload.startpunkt = {
        lat: isNaN(spLat) ? null : spLat,
        lng: isNaN(spLng) ? null : spLng,
      };

      btnSaveCoords.disabled = true;
      btnSaveCoords.textContent = "Speichern…";
      try {
        await api("/api/exercise/geodata", { method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload) });
        $("coordModal").style.display = "none";
        if (typeof loadExerciseLayer === "function") await loadExerciseLayer();
        alert("Koordinaten gespeichert. Jetzt ggf. Einsätze neu importieren.");
      } catch (e) { /* shown */ } finally {
        btnSaveCoords.disabled = false;
        btnSaveCoords.textContent = "Speichern";
      }
    });
  }

  // Auto-resolve w3w via browser (CORS-capable direct API call)
  const btnAutoResolve = $("btnAutoResolve");
  if (btnAutoResolve) {
    btnAutoResolve.addEventListener("click", async () => {
      const statusEl = $("coordResolveStatus");
      btnAutoResolve.disabled = true;
      btnAutoResolve.textContent = "Auflösen…";
      if (statusEl) statusEl.textContent = "Rufe w3w API auf…";

      // Collect all w3w addresses from current input rows
      const latInputs = document.querySelectorAll(".coord-lat");
      const allW3w = [];
      latInputs.forEach(inp => {
        const cid = inp.dataset.case;
        const w3wAddr = inp.dataset.w3w || "";
        allW3w.push({ cid, w3wAddr, latInp: inp,
          lngInp: document.querySelector(`.coord-lng[data-case="${cid}"]`) });
      });
      // Also startpunkt
      const spLat = $("spLat"), spLng = $("spLng");

      let ok = 0, fail = 0;
      const W3W_KEY = "2ZJ55EYB";

      const resolveOne = async (words) => {
        const clean = words.replace(/^\/+/, "");
        const url = `https://api.what3words.com/v3/convert-to-coordinates` +
          `?words=${encodeURIComponent(clean)}&key=${W3W_KEY}`;
        const r = await fetch(url, { signal: AbortSignal.timeout(8000) });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const d = await r.json();
        if (!d.coordinates) throw new Error(d.error?.message || "no coords");
        return { lat: d.coordinates.lat, lng: d.coordinates.lng };
      };

      for (const { cid, w3wAddr, latInp, lngInp } of allW3w) {
        if (!w3wAddr) continue;
        try {
          const { lat, lng } = await resolveOne(w3wAddr);
          if (latInp) latInp.value = lat;
          if (lngInp) lngInp.value = lng;
          ok++;
          if (statusEl) statusEl.textContent = `${cid}: ${lat}, ${lng}`;
        } catch (e) {
          fail++;
          if (statusEl) statusEl.textContent = `${cid}: Fehler – ${e.message}`;
        }
      }

      // Startpunkt
      if (spLat && spLng) {
        const spW3w = spLat.dataset.w3w || "";
        if (spW3w) {
          try {
            const { lat, lng } = await resolveOne(spW3w);
            spLat.value = lat; spLng.value = lng;
            ok++;
          } catch (e) { fail++; }
        }
      }

      if (statusEl) {
        if (fail === 0)
          statusEl.style.color = "#7ddf8a", statusEl.textContent = `✓ Alle ${ok} Adressen aufgelöst. Speichern nicht vergessen!`;
        else if (ok > 0)
          statusEl.textContent = `${ok} aufgelöst, ${fail} fehlgeschlagen. Kein Internet?`;
        else
          statusEl.style.color = "#f87171", statusEl.textContent = `Fehlgeschlagen. Browser hat kein Internet oder API-Key ungültig.`;
      }
      btnAutoResolve.disabled = false;
      btnAutoResolve.textContent = "🌐 Automatisch auflösen";
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

// ---------------- Auto-Refresh (Live-Sync, alle 10 s) ----------------
// Vollständiger Refresh: Sidebar-Listen + Marker + Übungs-Layer
setInterval(() => refreshAll(false).catch(() => {}), 10000);

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

// ---------------- Boot ----------------
window.addEventListener("DOMContentLoaded", async () => {
  initMap();
  wireUI();
  await refreshAll(true);
  await loadExerciseLayer();
  loadLanInfo();
});