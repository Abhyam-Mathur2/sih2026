import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Navigate, Route, Routes, Link, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { LayoutDashboard, Database, Upload, Sparkles, Landmark, LogOut } from 'lucide-react';
import { BarChart, Bar, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';
import './styles.css';

// ---------------------------------------------------------------------------
// API client
// ---------------------------------------------------------------------------
// VITE_API_BASE_URL should be set to http://localhost:8000/api/v1 in frontend/.env
// Falls back to http://localhost:8000/api/v1 if not set.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('bmim_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
type PageProps = { title: string; children: React.ReactNode };

// ---------------------------------------------------------------------------
// Shell / navigation
// ---------------------------------------------------------------------------
function Shell({ title, children }: PageProps) {
  const nav = [
    { p: '/', icon: LayoutDashboard, n: 'Dashboard' },
    { p: '/materials', icon: Database, n: 'Materials' },
    { p: '/upload', icon: Upload, n: 'Upload Data' },
    { p: '/matches', icon: Sparkles, n: 'AI Match Center' },
    { p: '/national', icon: Landmark, n: 'National Master' },
  ];
  return (
    <div className="shell">
      <aside>
        <div className="brand">
          BMIM <small>One Nation · One Material Code</small>
        </div>
        {nav.map(({ p, icon: Icon, n }) => (
          <Link to={p} key={p}>
            <Icon size={18} /> {n}
          </Link>
        ))}
        <button
          onClick={() => {
            localStorage.clear();
            location.href = '/login';
          }}
        >
          <LogOut size={18} /> Sign out
        </button>
      </aside>
      <main>
        <header>
          <div>
            <span className="eyebrow">BHARAT MATERIAL INTELLIGENCE NETWORK</span>
            <h1>{title}</h1>
          </div>
          <span className="user">Secure government data workspace</span>
        </header>
        {children}
      </main>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Login page
// ---------------------------------------------------------------------------
function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState('admin@bmim.gov.in');
  const [password, setPassword] = useState('admin_secure_password_2026');
  const [error, setError] = useState('');

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    try {
      // FastAPI's OAuth2PasswordRequestForm expects form-encoded body
      const body = new URLSearchParams({ username: email, password });
      const { data } = await api.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      localStorage.setItem('bmim_token', data.access_token);
      nav('/');
    } catch {
      setError('Invalid email or password');
    }
  }

  return (
    <div className="login">
      <form onSubmit={submit}>
        <span className="eyebrow">BMIM SECURE ACCESS</span>
        <h1>Material intelligence, unified.</h1>
        <p>Sign in to review material matches and national mappings.</p>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
        </label>
        <label>
          Password
          <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary">Sign in</button>
        <small>
          Demo: admin@bmim.gov.in / admin_secure_password_2026
        </small>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard page
// ---------------------------------------------------------------------------
function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['summary'],
    queryFn: () => api.get('/dashboard').then((r) => r.data),
  });

  if (isLoading)
    return (
      <Shell title="Dashboard">
        <p>Loading network intelligence…</p>
      </Shell>
    );

  const cards: [string, number][] = [
    ['Total Materials', data.total_materials],
    ['Duplicate Candidates', data.pending_matches],
    ['Pending Reviews', data.pending_mappings],
    ['Approved Mappings', data.approved_mappings],
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
      <section className="panel">
        <h2>Material processing status</h2>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart
            data={Object.entries(data.materials_by_status).map(([name, value]) => ({
              name,
              value,
            }))}
          >
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="value" fill="#138a72" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// Materials browser
// ---------------------------------------------------------------------------
function Materials() {
  const [search, setSearch] = useState('');
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['materials', search],
    queryFn: () =>
      api.get('/materials', { params: { search, size: 100 } }).then((r) => r.data),
  });

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
              <tr>
                <td colSpan={6}>Loading…</td>
              </tr>
            ) : (
              data?.items.map((m: any) => (
                <tr key={m.id}>
                  <td>{m.legacy_material_code}</td>
                  <td>
                    {m.cpse_id === 1
                      ? 'ONGC'
                      : m.cpse_id === 2
                      ? 'NTPC'
                      : m.cpse_id === 3
                      ? 'SAIL'
                      : 'BHEL'}
                  </td>
                  <td>{m.original_description}</td>
                  <td>{m.normalized_description || m.original_description}</td>
                  <td>
                    <span className="badge">{m.status}</span>
                  </td>
                  <td>
                    <button
                      onClick={async () => {
                        try {
                          await api.post('/matches/trigger', { material_id: m.id });
                          alert('AI Matching triggered successfully!');
                          refetch();
                        } catch {
                          alert('Failed to trigger matching.');
                        }
                      }}
                      style={{ padding: '4px 8px', fontSize: '11px' }}
                    >
                      Trigger Match
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
  const { data, refetch } = useQuery({
    queryKey: ['matches'],
    queryFn: () => api.get('/matches', { params: { size: 30 } }).then((r) => r.data),
  });

  return (
    <Shell title="AI Match Center">
      <p className="lead">
        Hybrid semantic, fuzzy and technical-attribute comparison. Human approval is required
        before any master mapping.
      </p>
      <div className="panel table">
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Candidate</th>
              <th>Recommendation</th>
              <th>Confidence</th>
              <th>Score Breakdown</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {data?.items && data.items.length > 0 ? (
              data.items.map((m: any) => (
                <tr key={m.id}>
                  <td>{m.source_material?.legacy_material_code}</td>
                  <td>{m.candidate_material?.legacy_material_code}</td>
                  <td>
                    <span className="badge">{m.match_type}</span>
                  </td>
                  <td>{m.final_score.toFixed(1)}%</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '11px' }}>
                    Sem: {m.semantic_score.toFixed(0)}% | Fuz: {m.fuzzy_score.toFixed(0)}% | Att:{' '}
                    {m.attribute_score.toFixed(0)}% | Tech: {m.technical_score.toFixed(0)}%
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={async () => {
                          await api.post(`/matches/${m.id}/review`, { action: 'APPROVED' });
                          refetch();
                        }}
                      >
                        Approve
                      </button>
                      <button
                        onClick={async () => {
                          await api.post(`/matches/${m.id}/review`, { action: 'REJECTED' });
                          refetch();
                        }}
                        style={{ background: '#fce8e6', color: '#c5221f' }}
                      >
                        Reject
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} style={{ textAlign: 'center', padding: '30px' }}>
                  Run matching from a material record after data upload.
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
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState('');

  async function upload() {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    form.append('cpse_id', '1');
    try {
      const { data } = await api.post('/uploads', form);
      setResult(
        `Processed ${data.processed_records} records; ${data.failed_records} failed.`
      );
    } catch {
      setResult(
        'Upload failed. CSV must contain legacy_material_code and original_description.'
      );
    }
  }

  return (
    <Shell title="Upload material data">
      <section className="panel upload">
        <h2>CSV Ingestion</h2>
        <p>
          Required columns: <code>legacy_material_code</code>, <code>original_description</code>.
        </p>
        <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files?.[0] || null)} />
        <button className="primary" onClick={upload}>
          Upload and normalize
        </button>
        {result && (
          <p style={{ marginTop: '15px', fontWeight: 'bold', color: '#138a72' }}>{result}</p>
        )}
      </section>
    </Shell>
  );
}

// ---------------------------------------------------------------------------
// National Material Master
// ---------------------------------------------------------------------------
function National() {
  const { data } = useQuery({
    queryKey: ['national'],
    queryFn: () => api.get('/national-materials').then((r) => r.data),
  });

  return (
    <Shell title="National Material Master">
      <section className="panel table">
        <table>
          <thead>
            <tr>
              <th>National material code</th>
              <th>Standard description</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data && data.length > 0 ? (
              data.map((n: any) => (
                <tr key={n.id}>
                  <td>{n.national_material_code}</td>
                  <td>{n.standard_description}</td>
                  <td>
                    <span className="badge">{n.status}</span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={3} style={{ textAlign: 'center', padding: '30px' }}>
                  No national material masters yet. Approve a match to create a reviewed mapping.
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
// Auth guard & routing
// ---------------------------------------------------------------------------
function Protected({ children }: { children: React.ReactNode }) {
  return localStorage.getItem('bmim_token') ? <>{children}</> : <Navigate to="/login" />;
}

const client = new QueryClient();

function App() {
  return (
    <Routes>
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
    </Routes>
  );
}

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={client}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
