/**
 * SANGAM Mobile App — Capacitor-wrapped mobile screens
 * 
 * All mobile screens live here, separate from the web dashboard.
 * They reuse the same backend API, same auth token, same data.
 * No new backend logic — everything calls existing endpoints.
 */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Routes, Route, Link, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  ScanLine, Search, Package, ClipboardList, User,
  Camera, Type, ArrowLeft, ChevronRight, Loader2,
  CheckCircle2, XCircle, AlertTriangle, Info,
  Plus, LogOut, Settings, Wifi,
} from 'lucide-react';

import './mobile.css';
import { Capacitor } from '@capacitor/core';
import { Preferences } from '@capacitor/preferences';
import { Camera as CapCamera, CameraResultType, CameraSource } from '@capacitor/camera';
import { BarcodeScanner } from '@capacitor-mlkit/barcode-scanning';
import { TextRecognition } from '@capacitor-mlkit/text-recognition';

// ---------------------------------------------------------------------------
// Storage adapter — Preferences on native, localStorage on web
// ---------------------------------------------------------------------------
export const StorageAdapter = {
  async get(key: string): Promise<string | null> {
    if (Capacitor.isNativePlatform() && Preferences) {
      const { value } = await Preferences.get({ key });
      return value;
    }
    return localStorage.getItem(key);
  },
  async set(key: string, value: string): Promise<void> {
    if (Capacitor.isNativePlatform() && Preferences) {
      await Preferences.set({ key, value });
    }
    localStorage.setItem(key, value);
  },
  async remove(key: string): Promise<void> {
    if (Capacitor.isNativePlatform() && Preferences) {
      await Preferences.remove({ key });
    }
    localStorage.removeItem(key);
  },
  async clear(): Promise<void> {
    if (Capacitor.isNativePlatform() && Preferences) {
      await Preferences.clear();
    }
    localStorage.clear();
  },
};

// ---------------------------------------------------------------------------
// API base URL — configurable at runtime for demo-day flexibility
// ---------------------------------------------------------------------------
function getApiBaseUrl(): string {
  // Check for saved custom URL first
  const saved = localStorage.getItem('sangam_api_url');
  if (saved) return saved;
  // Physical Android device default (host PC Wi-Fi IP)
  if (Capacitor.isNativePlatform()) return 'http://192.168.1.193:8000/api/v1';
  return import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
}

// Mobile API client
const mobileApi = axios.create({ baseURL: getApiBaseUrl(), timeout: 35000 });

mobileApi.interceptors.request.use(async (config) => {
  const token = await StorageAdapter.get('sangam_token') || await StorageAdapter.get('bmim_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  // Refresh base URL in case it changed
  config.baseURL = getApiBaseUrl();
  return config;
});

mobileApi.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      await StorageAdapter.remove('sangam_token');
      await StorageAdapter.remove('bmim_token');
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function confidenceTier(score: number): { label: string; color: string; bg: string } {
  if (score >= 95) return { label: 'Highly Confident', color: '#065f4b', bg: '#d4f0e8' };
  if (score >= 80) return { label: 'Strong Candidate', color: '#856404', bg: '#fef3cd' };
  if (score >= 60) return { label: 'Functionally Similar', color: '#9a3412', bg: '#fed7aa' };
  return { label: 'Not Meaningful', color: '#c5221f', bg: '#fce8e6' };
}

function TierBadge({ score }: { score: number }) {
  const tier = confidenceTier(score);
  return (
    <span style={{
      padding: '4px 10px', borderRadius: '20px', fontSize: '11px', fontWeight: 700,
      background: tier.bg, color: tier.color, whiteSpace: 'nowrap',
    }}>
      {score.toFixed(1)}% — {tier.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Mobile Shell with bottom tab bar
// ---------------------------------------------------------------------------
function MobileShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const tabs = [
    { p: '/mobile/scan', icon: ScanLine, n: 'Scan' },
    { p: '/mobile/search', icon: Search, n: 'Search' },
    { p: '/mobile/inventory', icon: Package, n: 'Inventory' },
    { p: '/mobile/tasks', icon: ClipboardList, n: 'Tasks' },
    { p: '/mobile/profile', icon: User, n: 'Profile' },
  ];

  return (
    <div className="m-shell">
      <div className="m-content">{children}</div>
      <nav className="m-tabs">
        {tabs.map(({ p, icon: Icon, n }) => (
          <Link
            to={p} key={p}
            className={`m-tab ${location.pathname.startsWith(p) ? 'm-tab-active' : ''}`}
          >
            <Icon size={20} />
            <span>{n}</span>
          </Link>
        ))}
      </nav>
    </div>
  );
}

function MobileHeader({ title, onBack }: { title: string; onBack?: () => void }) {
  return (
    <div className="m-header">
      {onBack && (
        <button className="m-back-btn" onClick={onBack}>
          <ArrowLeft size={20} />
        </button>
      )}
      <div className="m-header-content">
        <span className="m-header-eyebrow">SANGAM</span>
        <h1 className="m-header-title">{title}</h1>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Mobile Login
// ---------------------------------------------------------------------------
function MobileLogin() {
  const nav = useNavigate();
  const [email, setEmail] = useState('admin@sangam.gov.in');
  const [password, setPassword] = useState('admin_secure_password_2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [serverUrl, setServerUrl] = useState(getApiBaseUrl());
  const [showServerConfig, setShowServerConfig] = useState(false);

  function applyPresetUrl(url: string) {
    setServerUrl(url);
    localStorage.setItem('sangam_api_url', url);
  }

  function fillRole(roleEmail: string, rolePass: string) {
    setEmail(roleEmail);
    setPassword(rolePass);
    setError('');
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    const targetUrl = serverUrl.trim() || getApiBaseUrl();
    localStorage.setItem('sangam_api_url', targetUrl);

    try {
      const body = new URLSearchParams({ username: email, password });
      const { data } = await mobileApi.post('/auth/login', body, {
        baseURL: targetUrl,
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      await StorageAdapter.set('sangam_token', data.access_token);
      await StorageAdapter.set('bmim_token', data.access_token);
      nav('/mobile/scan');
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || !err.response) {
        setError(`Cannot reach API server at "${targetUrl}". If testing on your phone, ensure phone is on Wi-Fi and the backend is running with --host 0.0.0.0.`);
        setShowServerConfig(true);
      } else {
        setError('Invalid email or password. Please verify credentials or tap one of the quick test accounts.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="m-login">
      <form onSubmit={submit}>
        <div className="m-login-brand">
          <div className="m-login-icon">🇮🇳</div>
          <h1>SANGAM</h1>
          <p>Bharat Material Intelligence Network</p>
        </div>

        <div className="m-quick-roles">
          <span className="m-role-chip" onClick={() => fillRole('admin@sangam.gov.in', 'admin_secure_password_2026')}>
            👑 Admin
          </span>
          <span className="m-role-chip" onClick={() => fillRole('reviewer@example.com', 'Reviewer@123')}>
            🔍 Reviewer
          </span>
          <span className="m-role-chip" onClick={() => fillRole('manager@example.com', 'Manager@123')}>
            🏢 Manager
          </span>
        </div>

        <label>
          Email
          <input
            type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            placeholder="Enter your email" autoComplete="email"
          />
        </label>
        <label>
          Password
          <input
            type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password" autoComplete="current-password"
          />
        </label>

        {error && <p className="m-error">{error}</p>}

        <button type="submit" className="m-btn-primary" disabled={loading} style={{ marginTop: '16px' }}>
          {loading ? <><Loader2 size={16} className="spin" /> Signing in...</> : 'Sign In'}
        </button>

        <div className="m-server-toggle" onClick={() => setShowServerConfig(!showServerConfig)}>
          <span><Wifi size={13} style={{ verticalAlign: 'middle', marginRight: '6px' }} /> API Server: <strong>{serverUrl.replace(/https?:\/\//, '').split('/')[0]}</strong></span>
          <Settings size={14} />
        </div>

        {showServerConfig && (
          <div className="m-server-box">
            <label>API Server URL</label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              placeholder="http://192.168.1.193:8000/api/v1"
              style={{ fontSize: '13px', padding: '8px' }}
            />
            <div className="m-server-presets">
              <button type="button" className="m-preset-btn" onClick={() => applyPresetUrl('http://192.168.1.193:8000/api/v1')}>
                💻 PC Wi-Fi (192.168.1.193)
              </button>
              <button type="button" className="m-preset-btn" onClick={() => applyPresetUrl('http://10.0.2.2:8000/api/v1')}>
                📱 Emulator (10.0.2.2)
              </button>
              <button type="button" className="m-preset-btn" onClick={() => applyPresetUrl('http://localhost:8000/api/v1')}>
                🏠 Localhost
              </button>
            </div>
          </div>
        )}
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Universal Scanner
// ---------------------------------------------------------------------------
function ScannerScreen() {
  const nav = useNavigate();
  const [scanning, setScanning] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [scannedText, setScannedText] = useState('');
  const [manualInput, setManualInput] = useState('');
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  async function startBarcodeScan() {
    setError('');
    setScanning(true);
    try {
      if (BarcodeScanner) {
        const status = await BarcodeScanner.requestPermissions();
        if (status.camera !== 'granted') { setError('Camera permission denied'); setScanning(false); return; }
        const { barcodes } = await BarcodeScanner.scan();
        if (barcodes.length > 0) {
          const text = barcodes[0].rawValue || barcodes[0].displayValue || '';
          if (text) { setScannedText(text); await doLookup(text); }
        }
      } else {
        setError('Barcode scanner not available. Use text input or OCR capture.');
      }
    } catch (err: any) {
      setError(err.message || 'Scan failed');
    } finally {
      setScanning(false);
    }
  }

  async function startOCR() {
    setError('');
    setProcessing(true);
    try {
      if (CapCamera && TextRecognition) {
        const photo = await CapCamera.getPhoto({
          quality: 90,
          resultType: CameraResultType.Uri,
          source: CameraSource.Camera,
        });
        if (photo?.path) {
          const { text } = await TextRecognition.processImage({ path: photo.path });
          if (text) { setScannedText(text); await doLookup(text); }
          else setError('No text detected in image.');
        }
      } else {
        setError('Camera/OCR not available in browser. Use manual input.');
      }
    } catch (err: any) {
      setError(err.message || 'OCR capture failed');
    } finally {
      setProcessing(false);
    }
  }

  async function doLookup(text: string) {
    setProcessing(true);
    setResult(null);
    try {
      // First try material search by code
      const searchResp = await mobileApi.get('/materials', { params: { search: text, size: 5 } });
      const items = searchResp.data?.items || [];
      if (items.length === 1) {
        nav(`/mobile/material/${items[0].id}`);
        return;
      }
      // Otherwise do ERP lookup
      const lookupResp = await mobileApi.post('/integration/lookup', { material_description: text });
      setResult({ type: 'lookup', data: lookupResp.data, searchResults: items });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Lookup failed. Check server connection.');
    } finally {
      setProcessing(false);
    }
  }

  return (
    <MobileShell>
      <MobileHeader title="Scan Material" />
      <div className="m-page">
        {/* Scan actions */}
        <div className="m-scan-hero">
          <p className="m-scan-hint">Point at a barcode, QR code, or printed material label.</p>
          <div className="m-scan-actions">
            <button className="m-scan-btn" onClick={startBarcodeScan} disabled={scanning || processing}>
              <ScanLine size={24} />
              <span>{scanning ? 'Scanning...' : 'Scan Barcode/QR'}</span>
            </button>
            <button className="m-scan-btn m-scan-btn-alt" onClick={startOCR} disabled={scanning || processing}>
              <Camera size={24} />
              <span>{processing ? 'Processing...' : 'Capture Text (OCR)'}</span>
            </button>
          </div>
        </div>

        {/* Manual input */}
        <div className="m-card">
          <h3>Manual Lookup</h3>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              placeholder="Type material code or description..."
              value={manualInput}
              onChange={(e) => setManualInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && manualInput.trim() && doLookup(manualInput.trim())}
              style={{ flex: 1 }}
            />
            <button className="m-btn-primary" style={{ marginTop: 0 }}
              onClick={() => manualInput.trim() && doLookup(manualInput.trim())}
              disabled={processing || !manualInput.trim()}>
              {processing ? <Loader2 size={16} className="spin" /> : <Search size={16} />}
            </button>
          </div>
        </div>

        {scannedText && (
          <div className="m-card">
            <h3>Captured Text</h3>
            <code style={{ display: 'block', padding: '8px', background: '#f0f4f2', borderRadius: '6px', fontSize: '13px', wordBreak: 'break-all' }}>
              {scannedText}
            </code>
          </div>
        )}

        {error && (
          <div className="m-alert m-alert-error">
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        {/* Lookup results */}
        {result?.type === 'lookup' && (
          <div className="m-card">
            <h3>Lookup Results</h3>
            <div className="m-field">
              <label>Normalized Description</label>
              <p>{result.data.normalized_description}</p>
            </div>
            {result.data.extracted_attributes && Object.keys(result.data.extracted_attributes).length > 0 && (
              <div className="m-field">
                <label>Extracted Attributes</label>
                <div className="m-chips">
                  {Object.entries(result.data.extracted_attributes).map(([k, v]) => (
                    <span key={k} className="m-chip">{k}: {v as string}</span>
                  ))}
                </div>
              </div>
            )}
            {result.data.recommended_nmc && (
              <div className="m-nmc-banner">
                <strong>Recommended NMC:</strong>
                <code>{result.data.recommended_nmc}</code>
                <TierBadge score={result.data.confidence} />
              </div>
            )}
            {result.data.matching_materials?.length > 0 && (
              <>
                <h3>Equivalent Materials Across CPSEs</h3>
                {result.data.matching_materials.map((m: any, i: number) => (
                  <div key={i} className="m-match-card" onClick={() => m.material_id && nav(`/mobile/material/${m.material_id}`)}>
                    <div className="m-match-header">
                      <code>{m.legacy_code}</code>
                      <TierBadge score={m.similarity} />
                    </div>
                    <p>{m.description}</p>
                    {m.national_material_code && <small>NMC: {m.national_material_code}</small>}
                    <ChevronRight size={16} className="m-match-arrow" />
                  </div>
                ))}
              </>
            )}
            {result.searchResults?.length > 0 && (
              <>
                <h3>Direct Search Matches</h3>
                {result.searchResults.map((m: any) => (
                  <div key={m.id} className="m-match-card" onClick={() => nav(`/mobile/material/${m.id}`)}>
                    <div className="m-match-header">
                      <code>{m.legacy_material_code}</code>
                      <span className="badge">{m.status}</span>
                    </div>
                    <p>{m.original_description}</p>
                    <ChevronRight size={16} className="m-match-arrow" />
                  </div>
                ))}
              </>
            )}
          </div>
        )}
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Search Screen
// ---------------------------------------------------------------------------
function SearchScreen() {
  const nav = useNavigate();
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['m-materials', search],
    queryFn: () => mobileApi.get('/materials', { params: { search, size: 30 } }).then((r) => r.data),
    enabled: search.length >= 2,
  });

  return (
    <MobileShell>
      <MobileHeader title="Search Materials" />
      <div className="m-page">
        <input
          placeholder="Search by code, description, or keyword..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="m-search-input"
        />
        {isLoading && <div className="m-loading"><Loader2 size={20} className="spin" /> Searching...</div>}
        {data?.items?.map((m: any) => (
          <div key={m.id} className="m-match-card" onClick={() => nav(`/mobile/material/${m.id}`)}>
            <div className="m-match-header">
              <code>{m.legacy_material_code}</code>
              <span className="badge">{m.status}</span>
            </div>
            <p>{m.normalized_description || m.original_description}</p>
            <ChevronRight size={16} className="m-match-arrow" />
          </div>
        ))}
        {data?.items?.length === 0 && search.length >= 2 && (
          <div className="m-empty">No materials found for "{search}"</div>
        )}
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Material Detail
// ---------------------------------------------------------------------------
function MaterialDetail() {
  const nav = useNavigate();
  const id = window.location.pathname.split('/').pop();
  const [findingMatches, setFindingMatches] = useState(false);
  const [matches, setMatches] = useState<any[] | null>(null);
  const queryClient = useQueryClient();

  const { data: material, isLoading } = useQuery({
    queryKey: ['m-material', id],
    queryFn: () => mobileApi.get(`/materials/${id}`).then((r) => r.data),
    enabled: !!id,
  });

  const { data: cpses } = useQuery({
    queryKey: ['m-cpses'],
    queryFn: () => mobileApi.get('/cpses').then((r) => r.data),
  });
  const cpseMap: Record<number, string> = {};
  if (cpses) (Array.isArray(cpses) ? cpses : cpses.items || []).forEach((c: any) => { cpseMap[c.id] = c.short_code; });

  async function findEquivalents() {
    setFindingMatches(true);
    try {
      const { data } = await mobileApi.post(`/materials/${id}/find-matches`);
      setMatches(data);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to find matches');
    } finally {
      setFindingMatches(false);
    }
  }

  if (isLoading) return <MobileShell><div className="m-loading"><Loader2 size={20} className="spin" /> Loading...</div></MobileShell>;

  return (
    <MobileShell>
      <MobileHeader title="Material Detail" onBack={() => nav(-1)} />
      <div className="m-page">
        <div className="m-card">
          <div className="m-field">
            <label>CPSE</label>
            <span className="cpse-tag">{cpseMap[material?.cpse_id] || `CPSE-${material?.cpse_id}`}</span>
          </div>
          <div className="m-field">
            <label>Legacy Code</label>
            <code>{material?.legacy_material_code}</code>
          </div>
          <div className="m-field">
            <label>Original Description</label>
            <p>{material?.original_description}</p>
          </div>
          <div className="m-field">
            <label>Normalized Description</label>
            <p>{material?.normalized_description || '—'}</p>
          </div>
          {material?.attributes?.length > 0 && (
            <div className="m-field">
              <label>Extracted Attributes</label>
              <div className="m-chips">
                {material.attributes.map((a: any) => (
                  <span key={a.id} className="m-chip">{a.attribute_name}: {a.attribute_value}</span>
                ))}
              </div>
            </div>
          )}
          <div className="m-field">
            <label>Status</label>
            <span className="badge">{material?.status}</span>
          </div>
        </div>

        <button className="m-btn-primary m-btn-full" onClick={findEquivalents} disabled={findingMatches}>
          {findingMatches ? <><Loader2 size={16} className="spin" /> Finding Equivalents...</> : '🔍 Find Equivalent Materials'}
        </button>

        {matches && matches.length > 0 && (
          <div className="m-card">
            <h3>Equivalent Materials ({matches.length})</h3>
            {matches.map((m: any) => (
              <MatchCard key={m.id} match={m} cpseMap={cpseMap} onTap={() => nav(`/mobile/match/${m.id}`)} />
            ))}
          </div>
        )}
        {matches && matches.length === 0 && (
          <div className="m-empty">No equivalent materials found in the network.</div>
        )}
      </div>
    </MobileShell>
  );
}

function MatchCard({ match, cpseMap, onTap }: { match: any; cpseMap: Record<number, string>; onTap?: () => void }) {
  return (
    <div className="m-match-card" onClick={onTap}>
      <div className="m-match-header">
        <span className="cpse-tag">{cpseMap[match.candidate_material_id] || ''}</span>
        <TierBadge score={match.final_score} />
      </div>
      <div style={{ fontSize: '12px', color: '#607872', marginTop: '4px' }}>
        {match.match_type?.replace(/_/g, ' ')}
      </div>
      <ChevronRight size={16} className="m-match-arrow" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Match Detail + "Why Matched?" panel
// ---------------------------------------------------------------------------
function MatchDetail() {
  const nav = useNavigate();
  const id = window.location.pathname.split('/').pop();

  const { data: match, isLoading } = useQuery({
    queryKey: ['m-match', id],
    queryFn: () => mobileApi.get(`/matches/${id}`).then((r) => r.data),
    enabled: !!id,
  });

  if (isLoading) return <MobileShell><div className="m-loading"><Loader2 size={20} className="spin" /> Loading...</div></MobileShell>;
  if (!match) return <MobileShell><div className="m-empty">Match not found</div></MobileShell>;

  const exp = match.explanation || {};
  const signals = [
    { name: 'Semantic (Embedding)', score: exp.semantic_score ?? match.semantic_score, weight: exp.weights?.semantic ?? 0.35 },
    { name: 'Fuzzy (Text Match)', score: exp.fuzzy_score ?? match.fuzzy_score, weight: exp.weights?.fuzzy ?? 0.20 },
    { name: 'Attribute (Overlap)', score: exp.attribute_score ?? match.attribute_score, weight: exp.weights?.attribute ?? 0.25 },
    { name: 'Technical (UoM/Mfr)', score: exp.technical_score ?? match.technical_score, weight: exp.weights?.technical ?? 0.20 },
  ];

  const criticalFailures = exp.critical_attribute_failures || [];

  return (
    <MobileShell>
      <MobileHeader title="Match Analysis" onBack={() => nav(-1)} />
      <div className="m-page">
        {/* Score summary */}
        <div className="m-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h3 style={{ margin: 0 }}>Overall Score</h3>
            <TierBadge score={match.final_score} />
          </div>
          <div className="score-bar" style={{ height: '10px', borderRadius: '5px' }}>
            <div className="score-fill" style={{ width: `${match.final_score}%`, height: '10px', borderRadius: '5px' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '12px', color: '#607872' }}>
            <span>Type: {match.match_type?.replace(/_/g, ' ')}</span>
            <span>Status: {match.status}</span>
          </div>
        </div>

        {/* Source and candidate */}
        <div className="m-card">
          <h3>Source Material</h3>
          <p><code>{match.source_material?.legacy_material_code}</code></p>
          <p style={{ fontSize: '13px' }}>{match.source_material?.original_description}</p>
        </div>
        <div className="m-card">
          <h3>Candidate Material</h3>
          <p><code>{match.candidate_material?.legacy_material_code}</code></p>
          <p style={{ fontSize: '13px' }}>{match.candidate_material?.original_description}</p>
        </div>

        {/* Why Matched? panel */}
        <div className="m-card m-why-matched">
          <h3>Why Matched? — Signal Breakdown</h3>
          {signals.map((s) => {
            const pass = s.score >= 60;
            return (
              <div key={s.name} className="m-signal-row">
                <div className="m-signal-icon">
                  {pass ? <CheckCircle2 size={16} color="#065f4b" /> : <XCircle size={16} color="#c5221f" />}
                </div>
                <div className="m-signal-info">
                  <div className="m-signal-name">{s.name} <span style={{ color: '#94a3b8', fontSize: '10px' }}>({(s.weight * 100).toFixed(0)}% weight)</span></div>
                  <div className="score-bar" style={{ height: '6px' }}>
                    <div className="score-fill" style={{
                      width: `${s.score}%`,
                      background: pass ? 'linear-gradient(90deg, #138a72, #1ea88f)' : '#ef4444',
                    }} />
                  </div>
                </div>
                <span className="m-signal-score">{s.score?.toFixed(1)}%</span>
              </div>
            );
          })}
          <div style={{ marginTop: '12px', fontSize: '13px', padding: '8px 12px', background: criticalFailures.length > 0 ? '#fce8e6' : '#d4f0e8', borderRadius: '8px' }}>
            {criticalFailures.length > 0 ? (
              <><AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                Critical conflicts: {criticalFailures.join(', ')}</>
            ) : (
              <><CheckCircle2 size={14} style={{ verticalAlign: 'middle', marginRight: '6px' }} />
                No critical attribute conflicts</>
            )}
          </div>
        </div>
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Simulated Inventory
// ---------------------------------------------------------------------------
const SIMULATED_INVENTORY: Record<string, { location: string; qty: number; unit: string }[]> = {
  'NMC-VLV-BALLVALVE-SS316-DN50-0001': [
    { location: 'CPCL – Chennai Main Store', qty: 12, unit: 'EA' },
    { location: 'IOCL – Gujarat Refinery', qty: 8, unit: 'EA' },
    { location: 'SAIL – Bokaro Steel Store', qty: 3, unit: 'EA' },
  ],
  'NMC-VLV-BALLVALVE-SS316-DN100-0001': [
    { location: 'BHEL – Haridwar Plant', qty: 5, unit: 'EA' },
    { location: 'CPCL – Manali Refinery', qty: 7, unit: 'EA' },
  ],
};

function InventoryScreen() {
  const { data: nmcs, isLoading } = useQuery({
    queryKey: ['m-nmcs'],
    queryFn: () => mobileApi.get('/national-materials').then((r) => r.data),
  });

  return (
    <MobileShell>
      <MobileHeader title="Inventory Availability" />
      <div className="m-page">
        <div className="m-alert m-alert-info">
          <Info size={16} /> <strong>Simulated for Demo</strong> — Inventory data shown below is synthetic demonstration data. Not connected to live CPSE ERP stock levels.
        </div>

        {isLoading && <div className="m-loading"><Loader2 size={20} className="spin" /> Loading NMCs...</div>}

        {(Array.isArray(nmcs) ? nmcs : []).map((nmc: any) => {
          const inv = SIMULATED_INVENTORY[nmc.national_material_code] || [];
          return (
            <div key={nmc.id} className="m-card">
              <h3><code>{nmc.national_material_code}</code></h3>
              <p style={{ fontSize: '13px', color: '#607872', marginBottom: '8px' }}>{nmc.standard_description}</p>
              {inv.length > 0 ? inv.map((item, i) => (
                <div key={i} className="m-inv-row">
                  <span>📍 {item.location}</span>
                  <strong>{item.qty} {item.unit}</strong>
                </div>
              )) : (
                <p style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>No simulated stock data for this NMC</p>
              )}
            </div>
          );
        })}
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Create Material
// ---------------------------------------------------------------------------
function CreateMaterialScreen() {
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ cpse_id: '1', legacy_material_code: '', original_description: '', unit_of_measure: 'EA', manufacturer: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [created, setCreated] = useState<any>(null);

  const { data: cpses } = useQuery({
    queryKey: ['m-cpses'],
    queryFn: () => mobileApi.get('/cpses').then((r) => r.data),
  });

  const { data: me } = useQuery({
    queryKey: ['m-me'],
    queryFn: () => mobileApi.get('/auth/me').then((r) => r.data),
  });

  const canCreate = me?.role === 'ADMIN' || me?.role === 'CPSE_MANAGER';

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!canCreate) return;
    setLoading(true);
    setError('');
    try {
      const { data } = await mobileApi.post('/materials', {
        cpse_id: parseInt(form.cpse_id),
        legacy_material_code: form.legacy_material_code,
        original_description: form.original_description,
        unit_of_measure: form.unit_of_measure || undefined,
        manufacturer: form.manufacturer || undefined,
      });
      setCreated(data);
      queryClient.invalidateQueries({ queryKey: ['m-materials'] });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create material');
    } finally {
      setLoading(false);
    }
  }

  if (!canCreate) {
    return (
      <MobileShell>
        <MobileHeader title="Create Material" onBack={() => nav(-1)} />
        <div className="m-page">
          <div className="m-alert m-alert-error">
            <AlertTriangle size={16} /> CPSE Manager or Admin role required to create materials.
          </div>
        </div>
      </MobileShell>
    );
  }

  return (
    <MobileShell>
      <MobileHeader title="Create Material" onBack={() => nav(-1)} />
      <div className="m-page">
        {created ? (
          <div className="m-card">
            <h3>✅ Material Created</h3>
            <p><code>{created.legacy_material_code}</code> — {created.original_description}</p>
            <button className="m-btn-primary m-btn-full" onClick={() => nav(`/mobile/material/${created.id}`)}>
              View & Find Equivalents →
            </button>
          </div>
        ) : (
          <form onSubmit={handleCreate}>
            <div className="m-card">
              <label className="m-form-label">
                Target CPSE
                <select value={form.cpse_id} onChange={(e) => setForm({ ...form, cpse_id: e.target.value })}>
                  {(Array.isArray(cpses) ? cpses : cpses?.items || []).map((c: any) => (
                    <option key={c.id} value={c.id}>{c.short_code} – {c.name}</option>
                  ))}
                </select>
              </label>
              <label className="m-form-label">
                Legacy Material Code *
                <input required value={form.legacy_material_code} onChange={(e) => setForm({ ...form, legacy_material_code: e.target.value })}
                  placeholder="e.g. CPCL-VLV-001" />
              </label>
              <label className="m-form-label">
                Description *
                <textarea required value={form.original_description} onChange={(e) => setForm({ ...form, original_description: e.target.value })}
                  placeholder='e.g. BALL VALVE 2" SS316 PN16 FLANGED' rows={3} />
              </label>
              <label className="m-form-label">
                Unit of Measure
                <input value={form.unit_of_measure} onChange={(e) => setForm({ ...form, unit_of_measure: e.target.value })} placeholder="EA" />
              </label>
              <label className="m-form-label">
                Manufacturer
                <input value={form.manufacturer} onChange={(e) => setForm({ ...form, manufacturer: e.target.value })} placeholder="Optional" />
              </label>
              {error && <p className="m-error">{error}</p>}
              <button type="submit" className="m-btn-primary m-btn-full" disabled={loading}>
                {loading ? <><Loader2 size={16} className="spin" /> Creating...</> : '+ Create Material'}
              </button>
            </div>
          </form>
        )}
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Pending Tasks (Reviewer)
// ---------------------------------------------------------------------------
function PendingTasksScreen() {
  const queryClient = useQueryClient();
  const [reviewingId, setReviewingId] = useState<number | null>(null);

  const { data: me } = useQuery({
    queryKey: ['m-me'],
    queryFn: () => mobileApi.get('/auth/me').then((r) => r.data),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['m-pending'],
    queryFn: () => mobileApi.get('/matches', { params: { status: 'PENDING', size: 50 } }).then((r) => r.data),
  });

  const { data: cpses } = useQuery({
    queryKey: ['m-cpses'],
    queryFn: () => mobileApi.get('/cpses').then((r) => r.data),
  });
  const cpseMap: Record<number, string> = {};
  if (cpses) (Array.isArray(cpses) ? cpses : cpses.items || []).forEach((c: any) => { cpseMap[c.id] = c.short_code; });

  const canReview = me?.role === 'ADMIN' || me?.role === 'CPSE_MANAGER' || me?.role === 'TECHNICAL_REVIEWER';
  const nav = useNavigate();

  async function review(matchId: number, action: string) {
    setReviewingId(matchId);
    try {
      await mobileApi.post(`/matches/${matchId}/review`, { action });
      refetch();
    } catch (err: any) {
      alert(err.response?.data?.detail || `Failed to ${action.toLowerCase()} match`);
    } finally {
      setReviewingId(null);
    }
  }

  return (
    <MobileShell>
      <MobileHeader title="Pending Reviews" />
      <div className="m-page">
        {!canReview && (
          <div className="m-alert m-alert-error">
            <AlertTriangle size={16} /> Reviewer or Admin role required.
          </div>
        )}

        {isLoading && <div className="m-loading"><Loader2 size={20} className="spin" /> Loading...</div>}

        <div style={{ marginBottom: '12px', fontSize: '13px', color: '#607872' }}>
          {data?.total || 0} pending reviews
        </div>

        {data?.items?.map((m: any) => (
          <div key={m.id} className="m-card m-task-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <div>
                  <span className="cpse-tag">{cpseMap[m.source_material?.cpse_id] || '?'}</span>
                  <code style={{ fontSize: '12px' }}>{m.source_material?.legacy_material_code}</code>
                </div>
                <div style={{ fontSize: '12px', color: '#607872', margin: '4px 0' }}>{m.source_material?.original_description?.slice(0, 50)}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>↔ {m.candidate_material?.legacy_material_code}</div>
              </div>
              <TierBadge score={m.final_score} />
            </div>
            <div style={{ fontSize: '11px', fontFamily: 'monospace', color: '#607872', margin: '8px 0' }}>
              Sem: {m.semantic_score?.toFixed(0)}% | Fuz: {m.fuzzy_score?.toFixed(0)}% | Att: {m.attribute_score?.toFixed(0)}% | Tech: {m.technical_score?.toFixed(0)}%
            </div>
            {canReview && (
              <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
                <button className="btn-approve" style={{ flex: 1 }} disabled={reviewingId !== null}
                  onClick={() => review(m.id, 'APPROVED')}>
                  {reviewingId === m.id ? <Loader2 size={12} className="spin" /> : '✓ Approve'}
                </button>
                <button className="btn-reject" style={{ flex: 1 }} disabled={reviewingId !== null}
                  onClick={() => review(m.id, 'REJECTED')}>
                  ✕ Reject
                </button>
                <button className="small-btn" onClick={() => nav(`/mobile/match/${m.id}`)}>
                  Details
                </button>
              </div>
            )}
          </div>
        ))}

        {data?.items?.length === 0 && !isLoading && (
          <div className="m-empty">🎉 No pending reviews! All caught up.</div>
        )}
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Profile & Settings
// ---------------------------------------------------------------------------
function ProfileScreen() {
  const nav = useNavigate();
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('sangam_api_url') || '');
  const [saved, setSaved] = useState(false);

  const { data: me, isLoading } = useQuery({
    queryKey: ['m-me'],
    queryFn: () => mobileApi.get('/auth/me').then((r) => r.data),
  });

  function saveApiUrl() {
    if (apiUrl.trim()) {
      localStorage.setItem('sangam_api_url', apiUrl.trim());
    } else {
      localStorage.removeItem('sangam_api_url');
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  async function logout() {
    await StorageAdapter.clear();
    nav('/mobile/login');
  }

  return (
    <MobileShell>
      <MobileHeader title="Profile & Settings" />
      <div className="m-page">
        <div className="m-card">
          <h3>Current User</h3>
          {isLoading ? (
            <div className="m-loading"><Loader2 size={16} className="spin" /> Loading...</div>
          ) : me ? (
            <>
              <div className="m-field"><label>Name</label><p>{me.name}</p></div>
              <div className="m-field"><label>Email</label><p>{me.email}</p></div>
              <div className="m-field"><label>Role</label><span className="badge badge-green">{me.role}</span></div>
            </>
          ) : (
            <p>Not logged in</p>
          )}
        </div>

        <div className="m-card">
          <h3><Settings size={16} style={{ verticalAlign: 'middle', marginRight: '6px' }} />API Server Configuration</h3>
          <p style={{ fontSize: '12px', color: '#607872', marginBottom: '8px' }}>
            Change the API base URL for demo day. Leave empty for default ({Capacitor.isNativePlatform() ? '10.0.2.2:8000' : 'localhost:8000'}).
          </p>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              placeholder="e.g. http://192.168.1.5:8000/api/v1"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="m-btn-primary" style={{ marginTop: 0, whiteSpace: 'nowrap' }} onClick={saveApiUrl}>
              {saved ? '✓ Saved' : 'Save'}
            </button>
          </div>
          <div style={{ marginTop: '8px', fontSize: '11px', color: '#94a3b8' }}>
            <Wifi size={12} style={{ verticalAlign: 'middle' }} /> Current: {getApiBaseUrl()}
          </div>
        </div>

        <div className="m-card">
          <h3>Quick Actions</h3>
          <button className="m-btn-primary m-btn-full" onClick={() => nav('/mobile/create-material')}>
            <Plus size={16} /> Create New Material
          </button>
        </div>

        <button className="m-btn-danger m-btn-full" onClick={logout}>
          <LogOut size={16} /> Sign Out
        </button>
      </div>
    </MobileShell>
  );
}

// ---------------------------------------------------------------------------
// Mobile Auth Guard
// ---------------------------------------------------------------------------
function MobileProtected({ children }: { children: React.ReactNode }) {
  const [checked, setChecked] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  useEffect(() => {
    (async () => {
      const token = await StorageAdapter.get('sangam_token') || await StorageAdapter.get('bmim_token');
      setHasToken(!!token);
      setChecked(true);
    })();
  }, []);

  if (!checked) return null;
  return hasToken ? <>{children}</> : <Navigate to="/mobile/login" />;
}

// ---------------------------------------------------------------------------
// Mobile App Router
// ---------------------------------------------------------------------------
export function MobileApp() {
  return (
    <Routes>
      <Route path="login" element={<MobileLogin />} />
      <Route path="scan" element={<MobileProtected><ScannerScreen /></MobileProtected>} />
      <Route path="search" element={<MobileProtected><SearchScreen /></MobileProtected>} />
      <Route path="inventory" element={<MobileProtected><InventoryScreen /></MobileProtected>} />
      <Route path="tasks" element={<MobileProtected><PendingTasksScreen /></MobileProtected>} />
      <Route path="profile" element={<MobileProtected><ProfileScreen /></MobileProtected>} />
      <Route path="material/:id" element={<MobileProtected><MaterialDetail /></MobileProtected>} />
      <Route path="match/:id" element={<MobileProtected><MatchDetail /></MobileProtected>} />
      <Route path="create-material" element={<MobileProtected><CreateMaterialScreen /></MobileProtected>} />
      <Route path="*" element={<Navigate to="/mobile/scan" />} />
    </Routes>
  );
}

// ---------------------------------------------------------------------------
// Check if running as native mobile app
// ---------------------------------------------------------------------------
export function isNativeMobile(): boolean {
  try { return Capacitor.isNativePlatform(); } catch { return false; }
}
