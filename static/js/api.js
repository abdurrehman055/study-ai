/* ── Auth helpers ──────────────────────────────────── */
const TOKEN_KEY = 'sp_token';
const USER_KEY  = 'sp_user';

function getToken()  { return localStorage.getItem(TOKEN_KEY); }
function getUser()   { try { return JSON.parse(localStorage.getItem(USER_KEY)); } catch { return null; } }
function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
function clearAuth() { localStorage.removeItem(TOKEN_KEY); localStorage.removeItem(USER_KEY); }

function requireAuth() {
  if (!getToken()) { window.location.href = '/login'; return false; }
  return true;
}
function redirectIfAuthed() {
  if (getToken()) { window.location.href = '/app/dashboard'; }
}

/* ── Core fetch wrapper ────────────────────────────── */
async function apiFetch(path, options = {}) {
  const token = getToken();
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401) {
    clearAuth();
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }
  return res;
}

/* ── Auth endpoints ────────────────────────────────── */
async function apiLogin(email, password) {
  const res = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Login failed');
  setAuth(data.access_token, data.user);
  return data;
}

async function apiRegister(payload) {
  const res = await apiFetch('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Registration failed');
  setAuth(data.access_token, data.user);
  return data;
}

/* ── Dashboard ─────────────────────────────────────── */
async function apiDashboard() {
  const res = await apiFetch('/dashboard');
  if (!res.ok) throw new Error('Failed to load dashboard');
  return res.json();
}

/* ── Plans ─────────────────────────────────────────── */
async function apiListPlans() {
  const res = await apiFetch('/plans/');
  if (!res.ok) throw new Error('Failed to load plans');
  return res.json();
}

async function apiGetPlan(id) {
  const res = await apiFetch(`/plans/${id}`);
  if (!res.ok) throw new Error('Plan not found');
  return res.json();
}

async function apiGetPlanProgress(id) {
  const res = await apiFetch(`/plans/${id}/progress`);
  if (!res.ok) throw new Error('Failed to load progress');
  return res.json();
}

async function apiGeneratePlan(payload) {
  const res = await apiFetch('/plans/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to generate plan');
  return data;
}

async function apiDeletePlan(id) {
  const res = await apiFetch(`/plans/${id}`, { method: 'DELETE' });
  if (!res.ok) throw new Error('Failed to delete plan');
}

async function apiRegeneratePlan(id) {
  const res = await apiFetch(`/plans/${id}/regenerate`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to regenerate');
  return data;
}

/* ── Tasks ─────────────────────────────────────────── */
async function apiCompleteTask(id) {
  const res = await apiFetch(`/tasks/${id}/complete`, { method: 'PATCH' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to complete task');
  return data;
}

async function apiIncompleteTask(id) {
  const res = await apiFetch(`/tasks/${id}/incomplete`, { method: 'PATCH' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || 'Failed to undo task');
  return data;
}

/* ── Toast ─────────────────────────────────────────── */
function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const icons = { success: 'check-circle-fill', error: 'exclamation-circle-fill', info: 'info-circle-fill' };
  const t = document.createElement('div');
  t.className = `toast-sp toast-${type}`;
  t.innerHTML = `<i class="bi bi-${icons[type] || icons.info}"></i><span>${message}</span>`;
  container.appendChild(t);
  requestAnimationFrame(() => requestAnimationFrame(() => t.classList.add('show')));
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 350);
  }, 3800);
}

/* ── UI helpers ────────────────────────────────────── */
function showAlert(el, type, msg) {
  el.className = `alert-sp ${type}`;
  el.innerHTML = `<i class="bi bi-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i><span>${msg}</span>`;
}
function hideAlert(el) { el.className = 'alert-sp hidden'; }

function difficultyBadge(d) {
  const map = { Easy: 'badge-green', Medium: 'badge-amber', Hard: 'badge-red' };
  const icons = { Easy: 'bi-activity', Medium: 'bi-lightning', Hard: 'bi-fire' };
  return `<span class="badge-sp ${map[d] || 'badge-gray'}"><i class="bi ${icons[d] || 'bi-dash'}"></i>${d}</span>`;
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}
function formatDateShort(iso) {
  return new Date(iso).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}
function daysUntil(iso) {
  const diff = new Date(iso) - new Date();
  return Math.max(0, Math.ceil(diff / 86400000));
}

/* ── Sidebar active link ────────────────────────────── */
function initSidebar() {
  const user = getUser();
  if (user) {
    const nameEl  = document.getElementById('sidebar-user-name');
    const emailEl = document.getElementById('sidebar-user-email');
    const initEl  = document.getElementById('sidebar-user-init');
    if (nameEl)  nameEl.textContent  = user.name;
    if (emailEl) emailEl.textContent = user.email;
    if (initEl)  initEl.textContent  = user.name?.[0]?.toUpperCase() || '?';
  }

  // Active link
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(a => {
    const href = a.getAttribute('href');
    if (href && (path === href || (href !== '/app/dashboard' && path.startsWith(href)))) {
      a.classList.add('active');
    }
  });

  // Logout
  document.getElementById('btn-logout')?.addEventListener('click', () => {
    clearAuth();
    window.location.href = '/login';
  });

  // Mobile hamburger
  const hamburger = document.getElementById('btn-hamburger');
  const sidebar   = document.getElementById('sidebar');
  const overlay   = document.getElementById('sidebar-overlay');
  if (hamburger && sidebar && overlay) {
    hamburger.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('open');
    });
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('open');
    });
  }
}
