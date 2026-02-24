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
  [9, "9 – Fremdanmeldung"],
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

function radioText(code, label){
  const l = label || RADIO_LABELS.get(code) || "";
  return `Funk ${code}${l ? " – " + l : ""}`;
}

function radioBadge(code, label){
  return `<span class="badge">${esc(radioText(code, label))}</span>`;
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
  map = L.map("map").setView([52.52, 13.405], 12); // Default: Berlin
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

function rebuildMarkers(){
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
            ${radioBadge(t.radio_status, t.radio_status_label)}
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
  teams = await api("/api/teams");
  missions = await api("/api/missions");
  assignments = await api("/api/assignments");

  normalizeRadioLabels();
  computeAssignedTeamIds();

  renderTeams();
  renderMissions();
  renderAssignments();
  setSelectionLabel();

  if (rebuild){
    rebuildMarkers();
  } else {
    for (const t of teams) upsertTeamMarker(t);
    for (const m of missions) upsertMissionMarker(m);
  }
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

// ---------------- Boot ----------------
window.addEventListener("DOMContentLoaded", async () => {
  initMap();
  wireUI();
  await refreshAll(true);
});