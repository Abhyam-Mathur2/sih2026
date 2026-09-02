import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, Link, useNavigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import {
  LayoutDashboard,
  Database,
  Upload,
  Sparkles,
  Landmark,
  LogOut,
  Shield,
  Plug,
  Zap,
  Terminal,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Info,
  X,
  RefreshCw,
  Play,
  Pause,
  Copy,
  Menu,
  Smartphone,
} from 'lucide-react';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip, PieChart, Pie, Cell, Legend } from 'recharts';
import logoImg from './assets/logo.png';
import './styles.css';
import { MobileApp, isNativeMobile } from './mobile';


// ---------------------------------------------------------------------------
// Toast Notification Context & Hook
// ---------------------------------------------------------------------------
type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: string;
  title: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (title: string, message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType>({ showToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  function showToast(title: string, message: string, type: ToastType = 'success') {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, message, type }]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4200);
  }

  function removeToast(id: string) {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toast-container">
        {toasts.map((t) => (
          <div key={t.id} className={`toast-card ${t.type}`}>
            <div className="toast-icon">
              {t.type === 'success' && <CheckCircle2 size={20} color="#138a72" />}
              {t.type === 'error' && <AlertCircle size={20} color="#ef4444" />}
              {t.type === 'info' && <Info size={20} color="#0284c7" />}
            </div>
            <div className="toast-content">
              <div className="toast-title">{t.title}</div>
              <div className="toast-message">{t.message}</div>
            </div>
            <button className="toast-close" onClick={() => removeToast(t.id)}>
              <X size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------
export function getWebApiBaseUrl(): string {
  const saved = localStorage.getItem('sangam_api_url');
  if (saved) return saved;
  return import.meta.env.VITE_API_BASE_URL || 'https://sih2026-e5wz.onrender.com/api/v1';
}

const api = axios.create({ baseURL: getWebApiBaseUrl(), timeout: 35000 });

api.interceptors.request.use((config) => {
  config.baseURL = getWebApiBaseUrl();
  const token = localStorage.getItem('sangam_token') || localStorage.getItem('bmim_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('sangam_token');
      localStorage.removeItem('bmim_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Shell / navigation
// ---------------------------------------------------------------------------
function Shell({ title, children }: { title: string; children: React.ReactNode }) {
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const nav = [
    { p: '/', icon: LayoutDashboard, n: 'Dashboard' },
    { p: '/materials', icon: Database, n: 'Materials' },
    { p: '/upload', icon: Upload, n: 'Upload Data' },
    { p: '/matches', icon: Sparkles, n: 'AI Match Center' },
    { p: '/national', icon: Landmark, n: 'National Master' },
    { p: '/audit', icon: Shield, n: 'Audit Trail' },
    { p: '/integration', icon: Plug, n: 'SAP/ERP Integration' },
    { p: '/terminal', icon: Terminal, n: 'Live AI Terminal' },
    { p: '/mobile/scan', icon: Smartphone, n: 'Mobile App View' },
  ];

  // Close drawer on route change
  useEffect(() => { setDrawerOpen(false); }, [location.pathname]);

  return (
    <div className="shell">
      {/* Hamburger button — visible only on mobile via CSS */}
      <button className="hamburger-btn" onClick={() => setDrawerOpen(!drawerOpen)} aria-label="Menu">
        {drawerOpen ? <X size={20} /> : <Menu size={20} />}
      </button>
      {/* Drawer overlay */}
      {drawerOpen && <div className="drawer-overlay open" onClick={() => setDrawerOpen(false)} />}
      <aside className={drawerOpen ? 'drawer-open' : ''}>
        <div className="brand">
          <img src={logoImg} alt="SANGAM" className="brand-logo" />
          <div>
            SANGAM
            <small>Standardized AI Gateway</small>
          </div>
        </div>
        {nav.map(({ p, icon: Icon, n }) => (
          <Link to={p} key={p} className={location.pathname === p ? 'active' : ''} onClick={() => setDrawerOpen(false)}>
            <Icon size={18} /> {n}
          </Link>
        ))}
        <button
          onClick={() => {
            localStorage.clear();
            window.location.href = '/login';
          }}
        >
          <LogOut size={18} /> Sign out
        </button>
      </aside>
      <main>
        <header>
          <div>
            <span className="eyebrow">SANGAM · NATIONAL UNIFIED MATERIAL PLATFORM</span>
            <h1>{title}</h1>
          </div>
          <span className="user">Secure CPSE data workspace</span>
        </header>
        {children}

        {/* Floating Quick Dock Terminal Bar */}
        {location.pathname !== '/terminal' && (
          <Link to="/terminal" className="floating-term-dock">
            <span className="terminal-status-dot" />
            <Terminal size={15} />
            <span>Live AI Console</span>
          </Link>
        )}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login page
// ---------------------------------------------------------------------------
function Login() {
  const nav = useNavigate();
  const { showToast } = useToast();
  const [email, setEmail] = useState('admin@sangam.gov.in');
  const [password, setPassword] = useState('admin_secure_password_2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [serverUrl, setServerUrl] = useState(getWebApiBaseUrl());
  const [showServerConfig, setShowServerConfig] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    const targetUrl = serverUrl.trim() || getWebApiBaseUrl();
    localStorage.setItem('sangam_api_url', targetUrl);
    api.defaults.baseURL = targetUrl;

    try {
      const body = new URLSearchParams({ username: email, password });
      const { data } = await api.post('/auth/login', body, {
        baseURL: targetUrl,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('sangam_token', data.access_token);
      localStorage.setItem('bmim_token', data.access_token);
      showToast('Welcome to SANGAM', 'Signed in successfully as Administrator.', 'success');
      nav('/');
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response) {
        setError(`Cannot reach API server at ${targetUrl}. Configure your live Render backend URL below.`);
        setShowServerConfig(true);
        showToast('Network Error', `Cannot connect to API server at ${targetUrl}`, 'error');
      } else {
        setError('Invalid email or password');
        showToast('Authentication Error', 'Invalid credentials. Please verify your email and password.', 'error');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login">
      <form onSubmit={submit}>
        <div className="login-logo-wrap">
          <img src={logoImg} alt="SANGAM Logo" className="login-logo" />
        </div>
        <span className="eyebrow">SANGAM SECURE ACCESS</span>
        <h1>SANGAM</h1>
        <p className="login-subtitle">Standardized AI-driven National Gateway for Aggregated Materials</p>
        <p>Sign in to harmonize material masters, review matches, and manage National Material Codes across CPSEs.</p>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className={`primary ${loading ? 'is-loading' : ''}`} disabled={loading}>
          {loading ? (
            <>
              <Loader2 size={16} className="spin" /> Verifying Credentials...
            </>
          ) : (
            'Sign in'
          )}
        </button>
        <small>Demo: admin@sangam.gov.in (or admin@example.com)</small>

        <div style={{ marginTop: '16px', borderTop: '1px solid #e0e9e6', paddingTop: '12px', textAlign: 'center' }}>
          <button
            type="button"
            onClick={() => setShowServerConfig(!showServerConfig)}
            style={{ background: 'none', border: 'none', color: '#138a72', cursor: 'pointer', fontSize: '12px', fontWeight: 600, padding: 0 }}
          >
            ⚙️ API Server URL (Click to Change)
          </button>
          {showServerConfig && (
            <div style={{ marginTop: '10px', textAlign: 'left', background: '#f5f8f7', padding: '12px', borderRadius: '8px', border: '1px solid #d4dfdc' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#18332e', display: 'block', marginBottom: '4px' }}>
                Backend API URL
              </label>
              <input
                type="text"
                value={serverUrl}
                onChange={(e) => setServerUrl(e.target.value)}
                placeholder="https://your-backend.onrender.com/api/v1"
                style={{ fontSize: '13px', padding: '8px', width: '100%', marginBottom: '8px', boxSizing: 'border-box' }}
              />
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  style={{ fontSize: '11px', padding: '4px 10px', background: '#138a72', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                  onClick={() => {
                    const trimmed = serverUrl.trim();
                    localStorage.setItem('sangam_api_url', trimmed);
                    api.defaults.baseURL = trimmed;
                    showToast('Saved', 'API Server URL updated.', 'success');
                  }}
                >
                  Save URL
                </button>
                <button
                  type="button"
                  style={{ fontSize: '11px', padding: '4px 10px', background: '#f1f5f9', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '4px', cursor: 'pointer' }}
                  onClick={() => {
                    setServerUrl('http://localhost:8000/api/v1');
                    localStorage.setItem('sangam_api_url', 'http://localhost:8000/api/v1');
                    api.defaults.baseURL = 'http://localhost:8000/api/v1';
                  }}
                >
                  Reset Localhost
                </button>
              </div>
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------
const PIE_COLORS = ['#138a72', '#1ea88f', '#47c4ad', '#7dd8c6', '#b0e8de', '#dff5f0', '#f59e0b', '#ef4444', '#8b5cf6'];

function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['summary'],
    queryFn: () => api.get('/dashboard').then((r) => r.data),
  });

  if (isLoading) {
    return (
      <Shell title="Dashboard">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '30px', color: '#138a72' }}>
          <Loader2 size={24} className="spin" />
          <span>Synthesizing National Material Intelligence…</span>
        </div>
      </Shell>
    );
  }

  const cards: [string, number | string][] = [
    ['Total Materials', data?.total_materials ?? '—'],
    ['National Codes', data?.national_materials ?? '—'],
    ['Duplicate Groups', data?.materials_with_duplicates ?? '—'],
    ['Approved Mappings', data?.approved_mappings ?? '—'],
    ['Pending Reviews', data?.pending_matches ?? '—'],
    ['Avg Match Score', `${data?.avg_match_score ?? 0}%`],
    ['CPSEs Connected', data?.cpses ?? '—'],
    ['Audit Entries', data?.audit_entries ?? '—'],
  ];

  return (
    <Shell title="National material overview">
      <section className="cards">
        {cards.map(([label, value]) => (
          <article key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </article>
        ))}
      </section>

      {data?.savings_potential && (
        <div className="savings-banner">
          <Zap size={18} /> <strong>Savings Potential:</strong> {data.savings_potential}
        </div>
      )}

      <div className="chart-grid">
        <section className="panel">
          <h2>Material processing status</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={Object.entries(data?.materials_by_status || {}).map(([name, value]) => ({
                name,
                value,
              }))}
            >
              <XAxis dataKey="name" fontSize={11} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#138a72" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Match type distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={Object.entries(data?.matches_by_type || {}).map(([name, value]) => ({
                  name: name.replace(/_/g, ' '),
                  value,
                }))}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="value"
                label={({ name, value }: any) => `${name}: ${value}`}
              >
                {Object.keys(data?.matches_by_type || {}).map((_: string, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Materials per CPSE</h2>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data?.cpse_stats || []}>
              <XAxis dataKey="code" fontSize={11} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="material_count" fill="#1ea88f" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </section>

        <section className="panel">
          <h2>Category distribution</h2>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={(data?.category_distribution || []).filter((c: any) => c.count > 0)}
                cx="50%"
                cy="50%"
                outerRadius={90}
                dataKey="count"
                nameKey="category"
                label={({ category, count }: any) => `${category}: ${count}`}
              >
                {(data?.category_distribution || []).map((_: any, i: number) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </section>
      </div>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Materials browser
// ---------------------------------------------------------------------------
function Materials() {
  const { showToast } = useToast();
  const [search, setSearch] = useState('');
  const [matchingId, setMatchingId] = useState<number | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['materials', search],
    queryFn: () => api.get('/materials', { params: { search, size: 100 } }).then((r) => r.data),
  });

  const { data: cpses } = useQuery({
    queryKey: ['cpses'],
    queryFn: () => api.get('/cpses').then((r) => r.data),
  });

  const cpseMap: Record<number, string> = {};
  if (cpses) {
    (Array.isArray(cpses) ? cpses : cpses.items || []).forEach((c: any) => {
      cpseMap[c.id] = c.short_code;
    });
  }

  return (
    <Shell title="Materials">
      <div className="toolbar">
        <input
          placeholder="Search material code or description"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span>{data?.total || 0} records</span>
      </div>
      <div className="panel table">
        <table>
          <thead>
            <tr>
              <th>Code</th>
              <th>CPSE</th>
              <th>Original description</th>
              <th>Normalized description</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td><div className="skeleton-bar" style={{ width: '80px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '50px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '220px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '200px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '60px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '90px' }} /></td>
                </tr>
              ))
            ) : (
              data?.items.map((m: any) => (
                <tr key={m.id}>
                  <td data-label="Code">
                    <code>{m.legacy_material_code}</code>
                  </td>
                  <td data-label="CPSE">
                    <span className="cpse-tag">{cpseMap[m.cpse_id] || `CPSE-${m.cpse_id}`}</span>
                  </td>
                  <td data-label="Description">{m.original_description}</td>
                  <td data-label="Normalized">{m.normalized_description || m.original_description}</td>
                  <td data-label="Status">
                    <span className="badge">{m.status}</span>
                  </td>
                  <td data-label="Actions">
                    <button
                      disabled={matchingId !== null}
                      onClick={async () => {
                        setMatchingId(m.id);
                        try {
                          const { data: res } = await api.post('/matches/trigger', { material_id: m.id, top_k: 20 });
                          showToast(
                            'AI Matching Complete',
                            `Evaluated against all CPSEs. Generated ${res.length} matches for ${m.legacy_material_code}!`,
                            'success'
                          );
                          refetch();
                        } catch (err: any) {
                          const msg = err.response?.data?.detail || 'Failed to trigger matching. Check server connection.';
                          showToast('Matching Failed', msg, 'error');
                        } finally {
                          setMatchingId(null);
                        }
                      }}
                      className={`small-btn ${matchingId === m.id ? 'is-loading' : ''}`}
                    >
                      {matchingId === m.id ? (
                        <>
                          <Loader2 size={12} className="spin" /> Matching...
                        </>
                      ) : (
                        'Trigger Match'
                      )}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// AI Match Center
// ---------------------------------------------------------------------------
function Matches() {
  const { showToast } = useToast();
  const [statusFilter, setStatusFilter] = useState('');
  const [reviewingId, setReviewingId] = useState<number | null>(null);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['matches', statusFilter],
    queryFn: () =>
      api
        .get('/matches', { params: { size: 50, ...(statusFilter ? { status: statusFilter } : {}) } })
        .then((r) => r.data),
  });

  const { data: cpses } = useQuery({
    queryKey: ['cpses'],
    queryFn: () => api.get('/cpses').then((r) => r.data),
  });

  const cpseMap: Record<number, string> = {};
  if (cpses) {
    (Array.isArray(cpses) ? cpses : cpses.items || []).forEach((c: any) => {
      cpseMap[c.id] = c.short_code;
    });
  }

  const [batchLoading, setBatchLoading] = useState(false);
  const [batchResult, setBatchResult] = useState<any>(null);

  return (
    <Shell title="AI Match Center">
      <p className="lead">
        Hybrid semantic, fuzzy and technical-attribute comparison. Human approval triggers auto-generation of National Material Code and mapping.
      </p>

      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">All statuses</option>
          <option value="PENDING">Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
        <button
          className={`primary ${batchLoading ? 'is-loading' : ''}`}
          disabled={batchLoading}
          onClick={async () => {
            setBatchLoading(true);
            try {
              const { data: result } = await api.post('/matches/batch-detect');
              setBatchResult(result);
              showToast(
                'Batch Detection Finished',
                `Evaluated full dataset: ${result.newly_processed} materials processed, found ${result.duplicates_found} duplicates!`,
                'success'
              );
              refetch();
            } catch {
              showToast('Batch Detection Error', 'Batch duplicate detection encountered an error.', 'error');
            } finally {
              setBatchLoading(false);
            }
          }}
        >
          {batchLoading ? (
            <>
              <Loader2 size={14} className="spin" /> Evaluating Entire Master Dataset...
            </>
          ) : (
            '⚡ Run Batch Detection'
          )}
        </button>
      </div>

      {batchResult && (
        <div className="savings-banner">
          <Sparkles size={16} /> Batch complete: {batchResult.newly_processed} materials processed, {batchResult.duplicates_found} duplicate groups discovered, {batchResult.total_matches_created} pairs created.
        </div>
      )}

      <div className="panel table">
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Candidate</th>
              <th>Recommendation</th>
              <th>Confidence</th>
              <th>Score Breakdown</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td><div className="skeleton-bar" style={{ width: '140px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '140px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '80px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '60px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '180px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '70px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '90px' }} /></td>
                </tr>
              ))
            ) : data?.items && data.items.length > 0 ? (
              data.items.map((m: any) => (
                <tr key={m.id}>
                  <td data-label="Source">
                    <div>
                      <span className="cpse-tag">{cpseMap[m.source_material?.cpse_id] || `CPSE-${m.source_material?.cpse_id}`}</span>
                      <code>{m.source_material?.legacy_material_code}</code>
                    </div>
                    <div className="desc-small">{m.source_material?.original_description?.slice(0, 60)}</div>
                  </td>
                  <td data-label="Candidate">
                    <div>
                      <span className="cpse-tag">{cpseMap[m.candidate_material?.cpse_id] || `CPSE-${m.candidate_material?.cpse_id}`}</span>
                      <code>{m.candidate_material?.legacy_material_code}</code>
                    </div>
                    <div className="desc-small">{m.candidate_material?.original_description?.slice(0, 60)}</div>
                  </td>
                  <td data-label="Type">
                    <span
                      className={`badge ${
                        m.match_type === 'IDENTICAL'
                          ? 'badge-green'
                          : m.match_type === 'NEAR_DUPLICATE'
                          ? 'badge-amber'
                          : 'badge-grey'
                      }`}
                    >
                      {m.match_type?.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td data-label="Confidence">
                    <strong>{m.final_score.toFixed(1)}%</strong>
                    <div className="score-bar">
                      <div className="score-fill" style={{ width: `${m.final_score}%` }} />
                    </div>
                  </td>
                  <td data-label="Scores" style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                    Sem: {m.semantic_score.toFixed(0)}% | Fuz: {m.fuzzy_score.toFixed(0)}% | Att:{' '}
                    {m.attribute_score.toFixed(0)}% | Tech: {m.technical_score.toFixed(0)}%
                  </td>
                  <td data-label="Status">
                    <span
                      className={`badge ${
                        m.status === 'APPROVED' ? 'badge-green' : m.status === 'REJECTED' ? 'badge-red' : ''
                      }`}
                    >
                      {m.status}
                    </span>
                  </td>
                  <td data-label="Action">
                    {m.status === 'PENDING' && (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button
                          className={`btn-approve ${reviewingId === m.id ? 'is-loading' : ''}`}
                          disabled={reviewingId !== null}
                          onClick={async () => {
                            setReviewingId(m.id);
                            try {
                              await api.post(`/matches/${m.id}/review`, { action: 'APPROVED' });
                              showToast('Match Approved', 'National Material Code auto-generated and linked to both CPSEs!', 'success');
                              refetch();
                            } catch {
                              showToast('Approval Error', 'Failed to approve match.', 'error');
                            } finally {
                              setReviewingId(null);
                            }
                          }}
                        >
                          {reviewingId === m.id ? <Loader2 size={12} className="spin" /> : '✓ Approve'}
                        </button>
                        <button
                          className="btn-reject"
                          disabled={reviewingId !== null}
                          onClick={async () => {
                            setReviewingId(m.id);
                            try {
                              await api.post(`/matches/${m.id}/review`, { action: 'REJECTED' });
                              showToast('Match Rejected', 'Candidate marked as rejected.', 'info');
                              refetch();
                            } catch {
                              showToast('Reject Error', 'Failed to reject match.', 'error');
                            } finally {
                              setReviewingId(null);
                            }
                          }}
                        >
                          ✕ Reject
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '30px' }}>
                  Run matching from a material record or click Batch Detection above.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Upload page
// ---------------------------------------------------------------------------
function UploadPage() {
  const { showToast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [cpseId, setCpseId] = useState('1');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const { data: cpses } = useQuery({
    queryKey: ['cpses'],
    queryFn: () => api.get('/cpses').then((r) => r.data),
  });

  async function upload() {
    if (!file) return;
    setLoading(true);
    const form = new FormData();
    form.append('file', file);
    form.append('cpse_id', cpseId);
    try {
      const { data } = await api.post('/uploads', form);
      const msg = `Processed ${data.processed_records} records; ${data.failed_records} failed. Materials auto-classified & vector embedded.`;
      setResult(`✅ ${msg}`);
      showToast('CSV Ingestion Complete', msg, 'success');
    } catch {
      const err = 'Upload failed. Ensure CSV has legacy_material_code and original_description.';
      setResult(`❌ ${err}`);
      showToast('Upload Error', err, 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell title="Upload material data">
      <section className="panel upload">
        <h2>CSV Ingestion & Harmonization</h2>
        <p>
          Required columns: <code>legacy_material_code</code>, <code>original_description</code>. Optional: <code>unit_of_measure</code>, <code>manufacturer</code>.
        </p>
        <p className="desc-small">
          Materials are automatically normalized, classified by category, and embedded into pgvector for AI matching.
        </p>
        <label>
          Target CPSE
          <select value={cpseId} onChange={(e) => setCpseId(e.target.value)}>
            {(Array.isArray(cpses) ? cpses : cpses?.items || []).map((c: any) => (
              <option key={c.id} value={c.id}>
                {c.short_code} – {c.name}
              </option>
            ))}
          </select>
        </label>
        <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button className={`primary ${loading ? 'is-loading' : ''}`} onClick={upload} disabled={loading || !file}>
          {loading ? (
            <>
              <Loader2 size={16} className="spin" /> Processing, Classifying & Embedding...
            </>
          ) : (
            'Upload and normalize'
          )}
        </button>
        {result && (
          <p
            style={{
              marginTop: '15px',
              fontWeight: 'bold',
              color: result.startsWith('✅') ? '#138a72' : '#b32828',
            }}
          >
            {result}
          </p>
        )}
      </section>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// National Material Master
// ---------------------------------------------------------------------------
function National() {
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['national', search],
    queryFn: () => api.get('/national-materials', { params: search ? { search } : {} }).then((r) => r.data),
  });

  return (
    <Shell title="National Material Master">
      <div className="toolbar">
        <input
          placeholder="Search national material codes…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <span>{Array.isArray(data) ? data.length : 0} codes</span>
      </div>
      <section className="panel table">
        <table>
          <thead>
            <tr>
              <th>National material code</th>
              <th>Standard description</th>
              <th>Attributes</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td><div className="skeleton-bar" style={{ width: '180px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '220px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '180px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '70px' }} /></td>
                </tr>
              ))
            ) : data && data.length > 0 ? (
              data.map((n: any) => (
                <tr key={n.id}>
                  <td data-label="NMC">
                    <code>{n.national_material_code}</code>
                  </td>
                  <td data-label="Description">{n.standard_description}</td>
                  <td data-label="Attributes" style={{ fontSize: '11px', fontFamily: 'monospace' }}>
                    {n.standard_attributes
                      ? Object.entries(n.standard_attributes)
                          .map(([k, v]) => `${k}:${v}`)
                          .join(' | ')
                      : '—'}
                  </td>
                  <td data-label="Status">
                    <span className="badge badge-green">{n.status}</span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '30px' }}>
                  National codes are auto-generated when matches are approved. Upload data and approve matches to populate this master.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Audit Trail page
// ---------------------------------------------------------------------------
function AuditTrail() {
  const [actionFilter, setActionFilter] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['audit', actionFilter],
    queryFn: () =>
      api
        .get('/audit-logs', { params: { limit: 100, ...(actionFilter ? { action: actionFilter } : {}) } })
        .then((r) => r.data),
  });
  const { data: summary } = useQuery({
    queryKey: ['audit-summary'],
    queryFn: () => api.get('/audit-logs/summary').then((r) => r.data),
  });

  return (
    <Shell title="Audit Trail & Governance">
      <p className="lead">
        Immutable log of every action: match reviews, mapping approvals, NMC generation, uploads, and system operations.
      </p>

      {summary && (
        <section className="cards" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))' }}>
          <article>
            <span>Total Entries</span>
            <strong>{summary.total_entries}</strong>
          </article>
          {Object.entries(summary.by_action || {})
            .slice(0, 6)
            .map(([action, count]) => (
              <article key={action}>
                <span>{action.replace(/_/g, ' ')}</span>
                <strong>{count as number}</strong>
              </article>
            ))}
        </section>
      )}

      <div className="toolbar">
        <select value={actionFilter} onChange={(e) => setActionFilter(e.target.value)}>
          <option value="">All actions</option>
          <option value="MATCH_APPROVED">Match Approved</option>
          <option value="MATCH_REJECTED">Match Rejected</option>
          <option value="NMC_AUTO_GENERATED">NMC Generated</option>
          <option value="MAPPING_AUTO_CREATED">Mapping Created</option>
          <option value="CSV_UPLOAD_COMPLETED">CSV Upload</option>
          <option value="MATCHING_TRIGGERED">Matching Triggered</option>
          <option value="MATERIAL_CREATED">Material Created</option>
        </select>
      </div>

      <div className="panel table">
        <table>
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>Entity</th>
              <th>User</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <tr key={i} className="skeleton-row">
                  <td><div className="skeleton-bar" style={{ width: '90px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '110px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '130px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '70px' }} /></td>
                  <td><div className="skeleton-bar" style={{ width: '240px' }} /></td>
                </tr>
              ))
            ) : data && data.length > 0 ? (
              data.map((log: any) => (
                <tr key={log.id}>
                  <td data-label="Timestamp" style={{ fontSize: '11px', whiteSpace: 'nowrap' }}>
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td data-label="Action">
                    <span className="badge">{log.action?.replace(/_/g, ' ')}</span>
                  </td>
                  <td data-label="Entity">
                    <code>
                      {log.entity_type}#{log.entity_id}
                    </code>
                  </td>
                  <td data-label="User">{log.user_id ? `User #${log.user_id}` : 'System'}</td>
                  <td data-label="Details" style={{ fontSize: '11px', fontFamily: 'monospace', maxWidth: '300px', overflow: 'hidden' }}>
                    {log.new_value ? JSON.stringify(log.new_value).slice(0, 120) : '—'}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '30px' }}>
                  No audit entries yet. Perform actions (uploads, matching, reviews) to populate the trail.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// SAP/ERP Integration page
// ---------------------------------------------------------------------------
function IntegrationPage() {
  const { showToast } = useToast();
  const [desc, setDesc] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function lookup() {
    if (!desc.trim()) return;
    setLoading(true);
    try {
      const { data } = await api.post('/integration/lookup', { material_description: desc });
      setResult(data);
      showToast('ERP Lookup Complete', `Found recommendation: ${data.recommended_nmc || 'Pending review'}`, 'success');
    } catch {
      showToast('Lookup Failed', 'Failed to connect to integration service.', 'error');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell title="SAP/ERP Integration">
      <p className="lead">
        Simulates ERP system integration — send a material description, receive NMC recommendation and matching materials.
      </p>

      <section className="panel" style={{ maxWidth: '800px' }}>
        <h2>Material Lookup (ERP → SANGAM)</h2>
        <p className="desc-small">
          Enter a material description as an ERP system would send it. SANGAM normalizes, extracts attributes, and returns the best matching National Material Code.
        </p>
        <textarea
          placeholder='e.g. BALL VALVE 2" SS316 PN16 FLANGED'
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
          rows={3}
          style={{
            width: '100%',
            fontFamily: 'monospace',
            padding: '11px',
            borderRadius: '7px',
            border: '1px solid #cbd8d4',
            resize: 'vertical',
          }}
        />
        <button className={`primary ${loading ? 'is-loading' : ''}`} onClick={lookup} disabled={loading}>
          {loading ? (
            <>
              <Loader2 size={16} className="spin" /> Executing 4-Signal Scorer...
            </>
          ) : (
            'Lookup NMC'
          )}
        </button>
      </section>

      {result && (
        <section className="panel" style={{ maxWidth: '800px', marginTop: '16px' }}>
          <h2>Result</h2>
          <div className="result-grid">
            <div>
              <strong>Normalized:</strong>
              <p>{result.normalized_description}</p>
            </div>
            <div>
              <strong>Extracted Attributes:</strong>
              <p style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                {Object.entries(result.extracted_attributes || {})
                  .map(([k, v]) => `${k}: ${v}`)
                  .join(' | ')}
              </p>
            </div>
            {result.recommended_nmc && (
              <div className="savings-banner" style={{ margin: '10px 0' }}>
                <strong>Recommended NMC:</strong> <code>{result.recommended_nmc}</code> — {result.nmc_description} (Confidence: {result.confidence}%)
              </div>
            )}
          </div>
          {result.matching_materials && result.matching_materials.length > 0 && (
            <>
              <h3>Matching Materials in Database</h3>
              <table>
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Description</th>
                    <th>Similarity</th>
                    <th>NMC</th>
                  </tr>
                </thead>
                <tbody>
                  {result.matching_materials.map((m: any, i: number) => (
                    <tr key={i}>
                      <td data-label="Code">
                        <code>{m.legacy_code}</code>
                      </td>
                      <td data-label="Description">{m.description}</td>
                      <td data-label="Similarity">
                        <strong>{m.similarity}%</strong>
                      </td>
                      <td data-label="NMC">{m.national_material_code || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </section>
      )}
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Live AI Terminal Section (Real-Time Backend Trace)
// ---------------------------------------------------------------------------
function LiveTerminal() {
  const { showToast } = useToast();
  const [filter, setFilter] = useState<string>('ALL');
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [customLogs, setCustomLogs] = useState<any[]>([]);
  const terminalEndRef = useRef<HTMLDivElement>(null);

  const { data: serverLogs, refetch } = useQuery({
    queryKey: ['trace-logs'],
    queryFn: () => api.get('/system/trace-logs', { params: { limit: 80 } }).then((r) => r.data),
    refetchInterval: isPaused ? false : 2500,
  });

  const allLogs = [...customLogs, ...(serverLogs || [])];

  const filteredLogs = allLogs.filter((log) => {
    if (filter === 'ALL') return true;
    return log.subsystem === filter || log.level === filter;
  });

  useEffect(() => {
    if (!isPaused && terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [filteredLogs.length, isPaused]);

  function copyLogDump() {
    const text = filteredLogs
      .map((l) => `[${l.timestamp}] [${l.level}] [${l.subsystem}] ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text);
    showToast('Logs Copied', 'All terminal traces copied to clipboard!', 'success');
  }

  function clearLogs() {
    setCustomLogs([]);
    showToast('Terminal Cleared', 'Local console view reset.', 'info');
  }

  return (
    <Shell title="Live AI Engine Terminal">
      <p className="lead">
        Real-time telemetry and sub-system trace stream showing semantic embeddings, fuzzy string alignment, attribute cross-verification, and national master registry updates.
      </p>

      <div className="terminal-card">
        <div className="terminal-header">
          <div className="terminal-title">
            <span className="terminal-status-dot" />
            <span>SANGAM KERNEL TRACE v1.0.0 · [PORT 8000 · POSTGRES 5432 · VECTOR 384-D]</span>
          </div>
          <div className="terminal-actions">
            {['ALL', 'AI_CORE', 'VECTOR_EMBEDDING', 'MATCHING_ENGINE', 'GOVERNANCE'].map((f) => (
              <button
                key={f}
                className={`terminal-btn ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
              >
                {f.replace(/_/g, ' ')}
              </button>
            ))}
            <button
              className="terminal-btn"
              onClick={() => setIsPaused(!isPaused)}
              title={isPaused ? 'Resume Auto-Stream' : 'Pause Auto-Stream'}
            >
              {isPaused ? <Play size={12} /> : <Pause size={12} />}
              <span>{isPaused ? 'Resume' : 'Pause'}</span>
            </button>
            <button className="terminal-btn" onClick={() => refetch()} title="Poll Now">
              <RefreshCw size={12} />
            </button>
            <button className="terminal-btn" onClick={copyLogDump} title="Copy Dump">
              <Copy size={12} />
            </button>
            <button className="terminal-btn" onClick={clearLogs} title="Clear View">
              <X size={12} />
            </button>
          </div>
        </div>

        <div className="terminal-body">
          {filteredLogs.length === 0 ? (
            <div style={{ color: '#6ee7b7', padding: '20px' }}>
              &gt; Waiting for kernel telemetry... Trigger matching or run batch detection to view live trace.
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div key={index} className="terminal-line">
                <span className="term-time">{log.timestamp}</span>
                <span className={`term-level ${log.level}`}>{log.level}</span>
                <span className="term-subsystem">[{log.subsystem}]</span>
                <span className="term-msg">{log.message}</span>
              </div>
            ))
          )}
          <div ref={terminalEndRef} />
        </div>
      </div>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Auth guard & routing
// ---------------------------------------------------------------------------
function Protected({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('sangam_token') || localStorage.getItem('bmim_token');
  return token ? <>{children}</> : <Navigate to="/login" />;
}

const client = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 3000,
    },
  },
});

function App() {
  const location = useLocation();

  // If inside Capacitor Android container and on root web page, auto-route to native mobile scan screen
  if (isNativeMobile() && !location.pathname.startsWith('/mobile')) {
    return <Navigate to="/mobile/scan" replace />;
  }

  return (
    <Routes>
      <Route path="/mobile/*" element={<MobileApp />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protected>
            <Dashboard />
          </Protected>
        }
      />
      <Route
        path="/materials"
        element={
          <Protected>
            <Materials />
          </Protected>
        }
      />
      <Route
        path="/upload"
        element={
          <Protected>
            <UploadPage />
          </Protected>
        }
      />
      <Route
        path="/matches"
        element={
          <Protected>
            <Matches />
          </Protected>
        }
      />
      <Route
        path="/national"
        element={
          <Protected>
            <National />
          </Protected>
        }
      />
      <Route
        path="/audit"
        element={
          <Protected>
            <AuditTrail />
          </Protected>
        }
      />
      <Route
        path="/integration"
        element={
          <Protected>
            <IntegrationPage />
          </Protected>
        }
      />
      <Route
        path="/terminal"
        element={
          <Protected>
            <LiveTerminal />
          </Protected>
        }
      />
    </Routes>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <ToastProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
