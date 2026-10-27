const API_BASE = "http://localhost:8004";

const state = { roomId: null };

async function apiGet(path, fallback = []) {
  try {
    const resp = await fetch(API_BASE + path);
    if (!resp.ok) throw new Error(resp.status + " " + resp.statusText);
    return await resp.json();
  } catch (e) {
    showError("Could not reach API: " + e.message);
    return fallback;
  }
}

async function apiPost(path, body) {
  try {
    const resp = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!resp.ok) {
      let detail = "";
      try { detail = (await resp.json()).detail; } catch (_) {}
      showError(detail || "Request failed: " + resp.status);
      return false;
    }
    clearError();
    return true;
  } catch (e) {
    showError("Could not reach API: " + e.message);
    return false;
  }
}

function showError(msg) { document.getElementById("error").textContent = msg; }
function clearError() { document.getElementById("error").textContent = ""; }

function el(tag, text) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  return node;
}

async function bookSlot(roomId, slot) {
  if (await apiPost("/reservations/book", { room_id: roomId, slot })) {
    renderContent();
  }
}

async function cancelReservation(reservationId) {
  if (await apiPost("/reservations/cancel", { reservation_id: reservationId })) {
    renderContent();
  }
}

function selectRoom(roomId) {
  state.roomId = roomId;
  renderContent();
}

async function renderSidebar() {
  const container = document.getElementById("room-list");
  const rooms = await apiGet("/rooms");
  container.replaceChildren();

  if (rooms.length && state.roomId === null) {
    state.roomId = rooms[0].id;
  }

  for (const room of rooms) {
    const link = el("a", `${room.name} (${room.building})`);
    link.href = "#";
    link.onclick = (e) => {
      e.preventDefault();
      selectRoom(room.id);
    };
    container.appendChild(link);
  }
}

async function renderContent() {
  if (state.roomId === null) return;

  await Promise.all([
    renderRoomHeader(),
    renderSlots(),
    renderMyReservations(),
    renderAnnouncements(),
  ]);
}

async function renderRoomHeader() {
  const room = await apiGet(`/rooms/${state.roomId}`, {});
  const header = document.getElementById("room-header");
  header.replaceChildren();
  header.appendChild(el("h1", room.name || ""));
  header.appendChild(el("h1",
    `${room.building || ""} - capacity ${room.capacity || ""} - ${room.equipment || ""}`));
}

async function renderSlots() {
  const container = document.getElementById("slots");
  const slots = await apiGet(`/rooms/${state.roomId}/slots`);
  container.replaceChildren();

  for (const s of slots) {
    const row = el("div");
    row.className = "row";

    let label = `${s.slot} - ${s.status}`;
    if (s.reserved_by) label += ` (${s.reserved_by})`;
    row.appendChild(el("span", label));

    if (s.status === "available") {
      const btn = el("button", "Book");
      btn.onclick = () => bookSlot(state.roomId, s.slot);
      row.appendChild(btn);
    } else if (s.reserved_by === "you") {
      const btn = el("button", "Cancel");
      btn.onclick = () => cancelReservation(s.reservation_id);
      row.appendChild(btn);
    }
    container.appendChild(row);
  }
}

async function renderMyReservations() {
  const container = document.getElementById("my-reservations");
  const reservations = await apiGet("/my-reservations");
  container.replaceChildren();

  if (!reservations.length) {
    container.appendChild(el("div", "You don't have any reservations yet."));
    return;
  }

  for (const r of reservations) {
    const row = el("div");
    row.className = "row";
    row.appendChild(el("span", `${r.room_name} (${r.building}) - ${r.date} ${r.slot}`));

    const btn = el("button", "Cancel");
    btn.onclick = () => cancelReservation(r.id);
    row.appendChild(btn);

    container.appendChild(row);
  }
}

async function renderAnnouncements() {
  const container = document.getElementById("announcements");
  const announcements = await apiGet("/announcements");
  container.replaceChildren();

  for (const a of announcements) {
    container.appendChild(el("div", a.title));
    container.appendChild(el("div", a.body));
    container.appendChild(document.createElement("hr"));
  }
}

async function init() {
  await renderSidebar();
  await renderContent();
}

init();
