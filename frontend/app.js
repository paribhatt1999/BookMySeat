import { auth, googleProvider, signInWithPopup, RecaptchaVerifier, signInWithPhoneNumber, onAuthStateChanged, signOut } from './firebase.js';

// Same-origin API: FastAPI serves both the API and the frontend on Vercel.
const API = '';
function localDate() { const d = new Date(); return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Kolkata' }).format(d); }
let S = { movie: null, theatre: null, show: null, seats: [], expires: null, timer: null, userId: null, reservationId: null, bookingId: null };

const $ = id => document.getElementById(id);

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (auth.currentUser) headers.Authorization = `Bearer ${await auth.currentUser.getIdToken()}`;
  if (options.body && !headers['Content-Type']) headers['Content-Type'] = 'application/json';
  const res = await fetch(API + path, { ...options, headers });
  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try { message = (await res.json()).detail || message; } catch {}
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

function movieCard(m) {
  return `<article class="movie" onclick="openBook(${m.movie_id})">
    <img src="${m.poster_url}" alt="${m.title}">
    <div class="movie-info"><b>${m.title}</b><div class="meta">${m.genre} • ${m.language}</div><div>★ ${m.rating}</div></div>
  </article>`;
}

async function loadMovies(query = '', genre = 'all') {
  try {
    const params = new URLSearchParams();
    if (query) params.set('search', query);
    if (genre !== 'all') params.set('genre', genre);
    const data = await api('/movies' + (params.toString() ? '?' + params : ''));
    $('grid').innerHTML = data.map(movieCard).join('');
  } catch (e) { $('grid').innerHTML = `<p class="muted">Could not load movies: ${e.message}</p>`; }
}

async function openBook(movieId) {
  try {
    S.movie = await api('/movies/' + movieId);
    $('book').classList.remove('hidden'); $('pay').classList.add('hidden'); $('done').classList.add('hidden');
    $('bookTitle').textContent = 'Book ' + S.movie.title;
    const theatres = await api('/theatres?city=Jaipur');
    $('theatres').innerHTML = theatres.map(t => `<div class="item" onclick="selectTheatre(${t.theatre_id})"><b>${t.name}</b><div class="meta">${t.location}</div></div>`).join('');
    window.scrollTo({ top: $('book').offsetTop - 70, behavior: 'smooth' });
  } catch (e) { alert(e.message); }
}

async function selectTheatre(theatreId) {
  try {
    const all = await api('/theatres?city=Jaipur');
    S.theatre = all.find(t => t.theatre_id === theatreId);
    const date = localDate();
    const shows = await api(`/showtimes/${S.movie.movie_id}/${theatreId}/${date}`);
    $('shows').innerHTML = shows.length ? shows.map(s => `<div class="item" onclick="selectShow(${s.showtime_id})"><b>${s.time}</b><div class="meta">${s.format} • ${s.language}</div></div>`).join('') : '<p class="muted">No shows today.</p>';
  } catch (e) { alert(e.message); }
}

async function selectShow(showtimeId) {
  try {
    const shows = await api(`/showtimes/${S.movie.movie_id}/${S.theatre.theatre_id}/${localDate()}`);
    S.show = shows.find(s => s.showtime_id === showtimeId);
    const data = await api('/seats/' + showtimeId);
    S.seats = data.map(s => ({ ...s, selected: false, sold: s.is_booked }));
    renderSeats(); update(); connectSeatUpdates(showtimeId);
  } catch (e) { alert(e.message); }
}


function connectSeatUpdates(showtimeId) {
  if (!window.WebSocket || window.__seatSockets?.[showtimeId]) return;
  window.__seatSockets = window.__seatSockets || {};
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  try {
    const ws = new WebSocket(protocol + '//' + location.host + '/ws/seats/' + showtimeId);
    ws.onopen = () => ws.send('subscribe');
    ws.onmessage = () => selectShow(showtimeId);
    ws.onclose = () => delete window.__seatSockets[showtimeId];
    ws.onerror = () => ws.close();
    window.__seatSockets[showtimeId] = ws;
  } catch (_) {}
}

function renderSeats() {
  $('seats').innerHTML = S.seats.map(s => `<button class="seat ${s.sold ? 'sold' : ''}" ${s.sold ? 'disabled' : ''} onclick="toggle(${s.seat_id})" id="s${s.seat_id}">${s.seat_number}</button>`).join('');
}
function toggle(id) {
  const s = S.seats.find(x => x.seat_id === id);
  if (!s || s.sold) return;
  s.selected = !s.selected;
  $('s' + id).classList.toggle('selected', s.selected);
  update();
}
function chosen() { return S.seats.filter(s => s.selected); }
function update() { $('total').textContent = '₹' + chosen().reduce((a, s) => a + s.price, 0); }

async function checkout() {
  if (!auth.currentUser) return openAuth();
  if (!chosen().length) return alert('Select at least one seat.');
  try {
    const r = await api('/reserve-seats', { method: 'POST', body: JSON.stringify({ user_id: S.userId, showtime_id: S.show.showtime_id, seat_ids: chosen().map(s => s.seat_id) }) });
    S.reservationId = r.reservation_id; S.expires = new Date(r.expires_at).getTime();
    $('summary').innerHTML = `<p><b>${S.movie.title}</b><br>${S.theatre.name}<br>${S.show.date} • ${S.show.time}<br>Seats: ${chosen().map(s => s.seat_number).join(', ')}<br><b>Total: ₹${chosen().reduce((a,s) => a+s.price,0)}</b></p>`;
    $('pay').classList.remove('hidden'); $('book').classList.add('hidden');
    clearInterval(S.timer);
    S.timer = setInterval(() => {
      const left = Math.max(0, S.expires - Date.now());
      $('clock').textContent = `${String(Math.floor(left/60000)).padStart(2,'0')}:${String(Math.floor(left/1000)%60).padStart(2,'0')}`;
      if (!left) { clearInterval(S.timer); S.reservationId = null; alert('Reservation expired.'); hidePay(); selectShow(S.show.showtime_id); }
    }, 250);
  } catch (e) { alert(e.message); }
}

async function confirmPay() {
  if (!S.reservationId) return alert('Your reservation has expired.');
  try {
    clearInterval(S.timer);
    const b = await api('/book-tickets', { method: 'POST', body: JSON.stringify({ user_id: S.userId, showtime_id: S.show.showtime_id, reservation_id: S.reservationId }) });
    S.bookingId = b.booking_id;
    $('details').innerHTML = `<p><b>Booking ID:</b> BTS-${b.booking_id}</p><p>${S.movie.title} • ${S.theatre.name} • ${S.show.time}</p><p>Seats: ${chosen().map(s => s.seat_number).join(', ')} • ₹${b.total_price}</p>`;
    const qr = await api('/booking/' + b.booking_id + '/qr');
    $('qr').innerHTML = `<img width="190" alt="Booking QR" src="${qr.qr_data}">`;
    $('pay').classList.add('hidden'); $('done').classList.remove('hidden');
    S.reservationId = null;
    await loadMovies();
    await loadHistory();
    window.scrollTo({ top: $('done').offsetTop - 70, behavior: 'smooth' });
  } catch (e) { alert(e.message); }
}

function hideAll() { $('book').classList.add('hidden'); }
async function hidePay() { clearInterval(S.timer); if (S.reservationId && S.show) { try { await api('/release-reservation', { method: 'POST', body: JSON.stringify({ user_id: S.userId, showtime_id: S.show.showtime_id, reservation_id: S.reservationId }) }); } catch (_) {} } S.reservationId = null; $('pay').classList.add('hidden'); $('book').classList.remove('hidden'); if (S.show) await selectShow(S.show.showtime_id); }
function printPage() { window.print(); }

$('search').oninput = e => loadMovies(e.target.value);
document.querySelectorAll('.pill').forEach(b => b.onclick = () => {
  document.querySelectorAll('.pill').forEach(x => x.classList.remove('active'));
  b.classList.add('active'); loadMovies($('search').value, b.dataset.g);
});

async function loadHistory() {
  if (!auth.currentUser) {
    $('historyList').innerHTML = '<p class="muted">Sign in to view your bookings.</p>';
    return;
  }
  try {
    const rows = await api('/bookings/me');
    $('historyList').innerHTML = rows.length
      ? rows.map(b => '<div class="item"><b>BTS-' + b.booking_id + ' • ' + (b.movie || 'Movie') + '</b><div class="meta">' + (b.theatre || '') + ' • ' + (b.date || '') + ' • ' + (b.time || '') + '</div><div>Seats: ' + (b.seats || []).join(', ') + ' • ₹' + b.total_price + ' • ' + b.status + '</div></div>').join('')
      : '<p class="muted">No bookings yet.</p>';
  } catch (e) {
    $('historyList').innerHTML = '<p class="muted">Could not load history: ' + e.message + '</p>';
  }
}

let confirmationResult = null, recaptcha = null;
async function syncUser(user) {
  if (!user) { S.userId = null; $('userLabel').textContent = ''; $('signin').textContent = 'Sign in'; loadHistory(); return; }
  try {
    const r = await api('/auth/signup', { method: 'POST', body: JSON.stringify({ firebase_uid: user.uid, email: user.email || null, phone_number: user.phoneNumber || null }) });
    S.userId = r.user_id;
    await loadHistory();
    $('userLabel').textContent = user.displayName || user.email || user.phoneNumber || 'Signed in';
    $('signin').textContent = 'Sign out';
  } catch (e) { $('authError').textContent = e.message; }
}

function openAuth() { $('authModal').classList.remove('hidden'); $('authError').textContent = ''; }
function closeAuth() { $('authModal').classList.add('hidden'); }
$('signin').onclick = async () => auth.currentUser ? await signOut(auth) : openAuth();
$('googleBtn').onclick = async () => { try { await signInWithPopup(auth, googleProvider); closeAuth(); } catch (e) { $('authError').textContent = e.message; } };
$('phoneBtn').onclick = async () => { try {
  if (!recaptcha) recaptcha = new RecaptchaVerifier(auth, 'recaptcha-container', { size: 'invisible' });
  confirmationResult = await signInWithPhoneNumber(auth, $('phoneInput').value.trim(), recaptcha);
  $('otpArea').classList.remove('hidden'); $('phoneBtn').classList.add('hidden');
} catch (e) { $('authError').textContent = e.message; } };
$('verifyBtn').onclick = async () => { try { await confirmationResult.confirm($('otpInput').value.trim()); closeAuth(); } catch (e) { $('authError').textContent = 'Invalid OTP. Please try again.'; } };

onAuthStateChanged(auth, syncUser);
window.openBook = openBook; window.selectTheatre = selectTheatre; window.selectShow = selectShow; window.toggle = toggle;
window.checkout = checkout; window.confirmPay = confirmPay; window.hideAll = hideAll; window.hidePay = hidePay; window.print = printPage; window.closeAuth = closeAuth;

loadMovies();
