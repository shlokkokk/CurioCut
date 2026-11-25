import { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import gsap from 'gsap';
import {
  AlertTriangle,
  ArrowUpRight,
  Check,
  Copy,
  Film,
  RefreshCw,
  Search,
  Terminal,
  X,
} from 'lucide-react';
import WebGLCanvas from './components/WebGLCanvas';
import CommandPalette from './components/CommandPalette';

const API_URL = 'https://curiocut-corn.pcgpt00.workers.dev/api/vault';
const TRACK_URL = 'https://curiocut-corn.pcgpt00.workers.dev/api/track';
const CACHE_KEY = 'curiocut_index_cache_v1';
const PAGE_SIZE = 12;
const REFRESH_COOLDOWN_MS = 15000;
const REFRESH_WINDOW_MS = 5 * 60 * 1000;
const MAX_REFRESHES_PER_WINDOW = 5;

function trackEvent(event, keyword = '') {
  try {
    if (typeof window !== 'undefined' && typeof window.clarity === 'function') {
      window.clarity('event', keyword ? `${event}_${keyword}` : event);
    }
    if (typeof navigator !== 'undefined' && navigator.sendBeacon) {
      const blob = new Blob([JSON.stringify({ event, keyword })], { type: 'application/json' });
      navigator.sendBeacon(TRACK_URL, blob);
    }
  } catch {}
}

const CATEGORIES = [
  { id: 'all', label: 'All Drops' },
  { id: 'claude', label: 'Claude Skills' },
  { id: 'agents', label: 'AI Agents' },
  { id: 'opensource', label: 'Open Source' },
];

function getDropCategories(item) {
  const hay = `${item.title} ${item.category} ${item.keyword}`.toLowerCase();
  const url = String(item.resource_url || '').toLowerCase();
  const cats = [];
  if (item.is_claude_skill || hay.includes('claude') || hay.includes('mcp') || hay.includes('skill')) {
    cats.push('claude');
  }
  if (hay.includes('agent') || hay.includes('auto') || hay.includes('workflow') || hay.includes('bot') || hay.includes('mika') || hay.includes('assistant')) {
    cats.push('agents');
  }
  if (url.includes('github.com') || url.includes('huggingface.co') || hay.includes('open-source') || hay.includes('open source') || cats.length === 0) {
    cats.push('opensource');
  }
  return cats;
}

function primaryBadgeLabel(cats) {
  if (cats.includes('claude')) return 'Claude Skill';
  if (cats.includes('agents')) return 'AI Agent';
  return 'Open Source';
}

function formatRepoPath(url) {
  return String(url || '').replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
}

function IgIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
      <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
      <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
    </svg>
  );
}

function YtIcon({ size = 14 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-2 29 29 0 0 0 .46-5.25 29 29 0 0 0-.46-5.33z" />
      <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" fill="currentColor" stroke="none" />
    </svg>
  );
}

function updateSpotlight(e) {
  const rect = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty('--mx', `${e.clientX - rect.left}px`);
  e.currentTarget.style.setProperty('--my', `${e.clientY - rect.top}px`);
}

export default function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isStale, setIsStale] = useState(false);
  const [staleReason, setStaleReason] = useState('');
  const [activeCat, setActiveCat] = useState('all');
  const [query, setQuery] = useState('');
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [selected, setSelected] = useState(null);
  const [pendingLink, setPendingLink] = useState(null);
  const [cmdOpen, setCmdOpen] = useState(false);
  const [toast, setToast] = useState(null);
  const heroRef = useRef(null);
  const lastRefreshRef = useRef(0);
  const refreshLogRef = useRef([]);
  const cooldownMsRef = useRef(REFRESH_COOLDOWN_MS);
  const toastTimerRef = useRef(null);

  const loadDrops = (manual = false) => {
    if (manual) {
      const now = Date.now();
      const elapsed = now - lastRefreshRef.current;
      if (elapsed < cooldownMsRef.current) {
        const waitSec = Math.ceil((cooldownMsRef.current - elapsed) / 1000);
        // Escalate cooldown (15s -> 30s -> 60s -> 120s max) when spammed
        cooldownMsRef.current = Math.min(cooldownMsRef.current * 2, 120000);
        showToast(`Slow down, wait ${waitSec}s before refreshing`, 'warning', 5000);
        return;
      }
      refreshLogRef.current = refreshLogRef.current.filter((t) => now - t < REFRESH_WINDOW_MS);
      if (refreshLogRef.current.length >= MAX_REFRESHES_PER_WINDOW) {
        showToast('Refresh limit reached, try again in a few minutes', 'warning', 5000);
        return;
      }
      cooldownMsRef.current = REFRESH_COOLDOWN_MS;
      lastRefreshRef.current = now;
      refreshLogRef.current.push(now);
      setRefreshing(true);
    }

    fetch(API_URL, manual ? { cache: 'no-store' } : undefined)
      .then((r) => {
        if (!r.ok) {
          const err = new Error(`HTTP ${r.status}`);
          err.statusCode = r.status;
          throw err;
        }
        return r.json();
      })
      .then((data) => {
        if (!data || !Array.isArray(data.items)) {
          const err = new Error('Invalid response');
          err.statusCode = 502;
          throw err;
        }
        setItems(data.items);
        setIsStale(false);
        setStaleReason('');
        try {
          localStorage.setItem(CACHE_KEY, JSON.stringify(data.items));
        } catch {}
        if (manual) showToast('Index refreshed');
      })
      .catch((err) => {
        const isClientOffline = typeof navigator !== 'undefined' && navigator.onLine === false;
        const isServerSide = Boolean(err && err.statusCode);
        const reason = isClientOffline
          ? 'Your internet connection appears offline. Showing saved drops.'
          : isServerSide
            ? `Our server returned an error (${err.message}). Showing saved drops.`
            : 'Network error reaching the server. Check your connection and retry.';

        setStaleReason(reason);
        try {
          const backup = JSON.parse(localStorage.getItem(CACHE_KEY) || 'null');
          if (Array.isArray(backup) && backup.length > 0) {
            setItems(backup);
            setIsStale(true);
          } else {
            setIsStale(true);
          }
        } catch {
          setIsStale(true);
        }
        if (manual) {
          showToast(
            isClientOffline ? 'You appear to be offline' : 'Refresh failed, try again shortly',
            'warning',
            5000,
          );
        }
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  };

  useEffect(() => {
    const mode = new URLSearchParams(window.location.search).get('preview');
    if (mode === 'offline') {
      setIsStale(true);
      setStaleReason('Your internet connection appears offline. Showing saved drops.');
      showToast('You appear to be offline', 'warning', 5000);
    } else if (mode === 'server') {
      setIsStale(true);
      setStaleReason('Our server returned an error (HTTP 502). Showing saved drops.');
      showToast('Refresh failed, try again shortly', 'warning', 5000);
    } else if (mode === 'network') {
      setIsStale(true);
      setStaleReason('Network error reaching the server. Check your connection and retry.');
    } else if (mode === 'ratelimit') {
      showToast('Slow down, wait 30s before refreshing', 'warning', 5000);
    }
    if (mode === 'offline' || mode === 'server' || mode === 'network') {
      fetch(API_URL)
        .then((r) => r.json())
        .then((d) => Array.isArray(d.items) && setItems(d.items))
        .catch(() => {})
        .finally(() => setLoading(false));
      return;
    }
    if (!mode) {
      trackEvent('visit');
    }
    loadDrops(false);
  }, []);

  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [activeCat, query]);

  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from('.hero-anim', {
        y: 26,
        opacity: 0,
        duration: 0.75,
        stagger: 0.08,
        ease: 'power3.out',
      });
    }, heroRef);
    return () => ctx.revert();
  }, []);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCmdOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  useEffect(() => {
    const locked = Boolean(selected || pendingLink || cmdOpen);
    if (!locked) return;
    const scrollY = window.scrollY;
    const html = document.documentElement;
    const body = document.body;
    const prevHtmlOverflow = html.style.overflow;
    const prevBodyOverflow = body.style.overflow;
    const prevBodyPosition = body.style.position;
    const prevBodyTop = body.style.top;
    const prevBodyWidth = body.style.width;

    html.style.overflow = 'hidden';
    body.style.overflow = 'hidden';
    body.style.position = 'fixed';
    body.style.top = `-${scrollY}px`;
    body.style.width = '100%';

    return () => {
      html.style.overflow = prevHtmlOverflow;
      body.style.overflow = prevBodyOverflow;
      body.style.position = prevBodyPosition;
      body.style.top = prevBodyTop;
      body.style.width = prevBodyWidth;
      window.scrollTo(0, scrollY);
    };
  }, [selected, pendingLink, cmdOpen]);

  const dismissToast = () => {
    if (toastTimerRef.current) {
      clearTimeout(toastTimerRef.current);
      toastTimerRef.current = null;
    }
    setToast(null);
  };

  const showToast = (msg, type = 'success', duration) => {
    const ms = duration ?? (type === 'warning' ? 5000 : 2800);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ id: Date.now(), msg, type, duration: ms });
    toastTimerRef.current = setTimeout(() => {
      setToast(null);
      toastTimerRef.current = null;
    }, ms);
  };

  const copyText = (text, label) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(() => showToast(label)).catch(() => {});
    }
  };

  const handleExternalClick = (e, item, kind) => {
    e.preventDefault();
    const url = kind === 'reel' ? item.permalink : kind === 'yt' ? item.yt_url : item.resource_url;
    if (!url) return;
    setPendingLink({
      title: item.title,
      url,
      kind,
      keyword: item.keyword || '',
      host: formatRepoPath(url).split('/')[0] || 'external link',
    });
  };

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items.filter((it) => {
      if (activeCat !== 'all' && !getDropCategories(it).includes(activeCat)) return false;
      if (!q) return true;
      return `${it.title} ${it.keyword} ${it.resource_url}`.toLowerCase().includes(q);
    });
  }, [items, activeCat, query]);

  const showFeatured = activeCat === 'all' && !query.trim() && filtered.length > 0;
  const featuredItem = showFeatured ? filtered[0] : null;
  const allGridItems = showFeatured ? filtered.slice(1) : filtered;
  const gridItems = allGridItems.slice(0, visibleCount);
  const remainingCount = Math.max(0, allGridItems.length - gridItems.length);

  return (
    <>
      <WebGLCanvas />
      <div className="noise-overlay" aria-hidden="true" />

      <div className="app-shell">
        <header className="topbar">
          {/* ── Desktop layout (flex row, unchanged) ── */}
          <a className="brand-lockup" href="/">
            <img className="brand-icon" src="/icon.png" alt="CurioCut" />
            <div style={{ minWidth: 0 }}>
              <div className="brand-name">CurioCut</div>
              <div className="brand-tag">Drops &amp; Index</div>
            </div>
          </a>

          <div className="topbar-right">
            <button type="button" className="cmd-trigger" onClick={() => setCmdOpen(true)} aria-label="Search Index">
              <Search size={13} />
              <span>Search</span>
            </button>
            <a className="yt-link" href="https://www.youtube.com/@CurioCutt" target="_blank" rel="noopener noreferrer">
              <YtIcon size={14} />
              YouTube
              <ArrowUpRight size={13} />
            </a>
            <a className="ig-link" href="https://instagram.com/curiocutt" target="_blank" rel="noopener noreferrer">
              <IgIcon size={13} />
              @curiocutt
              <ArrowUpRight size={13} />
            </a>
          </div>

          {/* ── Mobile-only: two-row header ── */}
          <div className="topbar-row1">
            <a className="brand-lockup" href="/" style={{ gap: '0.55rem' }}>
              <img className="brand-icon" src="/icon.png" alt="CurioCut" />
              <div className="brand-name">CurioCut</div>
            </a>
            <div className="mobile-social-pills">
              <a
                className="social-pill-mobile"
                href="https://instagram.com/curiocutt"
                target="_blank" rel="noopener noreferrer"
                aria-label="Instagram @curiocutt"
              >
                <IgIcon size={14} />
                <span>IG</span>
              </a>
              <a
                className="social-pill-mobile social-pill-yt"
                href="https://www.youtube.com/@CurioCutt"
                target="_blank" rel="noopener noreferrer"
                aria-label="YouTube @CurioCutt"
              >
                <YtIcon size={14} />
                <span>YT</span>
              </a>
            </div>
          </div>
          <div className="topbar-row2">
            <button type="button" className="mobile-search-bar" onClick={() => setCmdOpen(true)} aria-label="Search drops">
              <Search size={13} />
              <span>Search drops, keywords, tools&hellip;</span>
            </button>
          </div>
        </header>

        <section className="hero" ref={heroRef}>
          <div className="hero-kicker hero-anim">
            <span className="pulse-dot" />
            Live Synced Index • Updated Every Drop
          </div>
          <h1 className="hero-title hero-anim">
            Open-Source <em>Intelligence.</em>
            <br />
            Curated Daily.
          </h1>
          <p className="hero-sub hero-anim">
            Every AI agent, Claude skill, and developer exploit featured on{' '}
            <a
              href="https://instagram.com/curiocutt"
              target="_blank" rel="noopener noreferrer"
              style={{ color: 'var(--text)', textDecoration: 'underline', textDecorationColor: 'var(--accent)', textUnderlineOffset: '3px', fontWeight: 600 }}
            >
              @curiocutt
            </a>
            . Search by comment keyword, inspect setup commands, or launch the repository directly.
          </p>
          <div className="hero-metrics hero-anim">
            <div className="metric">
              <span className="metric-val">{loading ? '-' : String(items.length).padStart(2, '0')}</span>
              <span className="metric-label">Indexed Drops</span>
            </div>
            <div className="metric">
              <span className="metric-val">
                {loading ? '-' : String(items.filter((i) => getDropCategories(i).includes('claude')).length).padStart(2, '0')}
              </span>
              <span className="metric-label">Claude Skills</span>
            </div>
            <div className="metric">
              <span className="metric-val">$0</span>
              <span className="metric-label">Paywalls</span>
            </div>
          </div>
        </section>

        <div className="toolbar">
          <div className="tabs" role="tablist">
            {CATEGORIES.map((cat) => {
              const isActive = activeCat === cat.id;
              return (
                <button
                  key={cat.id}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  className={`tab-btn ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveCat(cat.id)}
                >
                  {isActive && (
                    <motion.span
                      layoutId="active-pill"
                      className="tab-pill"
                      transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                    />
                  )}
                  {cat.label}
                </button>
              );
            })}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 240px', maxWidth: 380 }}>
            <div className="search-wrap" style={{ maxWidth: 'none' }}>
              <Search size={15} className="search-icon" />
              <input
                className="search-input"
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter by keyword (AGENT, CLAUDE, MCP)..."
              />
            </div>
            <button
              type="button"
              className="btn btn-ghost drop-icon-btn"
              onClick={() => loadDrops(true)}
              disabled={refreshing}
              aria-label="Refresh drops"
              title="Refresh drops"
            >
              <RefreshCw size={14} className={refreshing ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {isStale && (
          <div className="stale-banner">
            <span style={{ flex: 1, minWidth: 0 }}>{staleReason || 'Showing cached drops, live sync failed.'}</span>
            <button
              type="button"
              className="btn btn-outline"
              style={{ flexShrink: 0, padding: '6px 12px', fontSize: '0.76rem', borderColor: 'rgba(245, 158, 11, 0.45)', color: '#fde68a' }}
              onClick={() => loadDrops(true)}
            >
              Retry
            </button>
          </div>
        )}

        {loading ? (
          <div className="vault-grid">
            {[1, 2, 3, 4].map((n) => (
              <div key={n} className="drop-card" style={{ minHeight: 168, opacity: 0.45 }}>
                <div className="drop-index">00{n} • LOADING</div>
              </div>
            ))}
          </div>
        ) : (
          <>
            {featuredItem && (
              <motion.article
                className="featured-card"
                onPointerMove={updateSpotlight}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35 }}
              >
                <div className="featured-top">
                  <div className="tag-row">
                    <span className="tag-live">Latest Drop • #001</span>
                    <span className="tag-kw">{featuredItem.keyword || 'TOOL'}</span>
                    <span className="tag-cat">{primaryBadgeLabel(getDropCategories(featuredItem))}</span>
                  </div>
                </div>

                <h2 className="featured-title">{featuredItem.title}</h2>
                <div className="repo-line">
                  <Terminal size={14} />
                  <span>{formatRepoPath(featuredItem.resource_url)}</span>
                </div>

                <div className="featured-actions">
                  <a
                    className="btn btn-accent featured-primary"
                    href={featuredItem.resource_url}
                    target="_blank" rel="noopener noreferrer"
                    onClick={(e) => handleExternalClick(e, featuredItem, 'repo')}
                  >
                    Open Repository
                    <ArrowUpRight size={15} />
                  </a>
                  <div className={`featured-secondary ${featuredItem.permalink || featuredItem.yt_url ? 'two-col' : 'one-col'}`}>
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={() => setSelected(featuredItem)}
                    >
                      <Terminal size={14} />
                      Setup &amp; Prompt
                    </button>
                    {(featuredItem.permalink || featuredItem.yt_url) && (
                      <div className="featured-watch-group">
                        {featuredItem.permalink && (
                          <a
                            className="btn btn-outline"
                            href={featuredItem.permalink}
                            target="_blank" rel="noopener noreferrer"
                            onClick={(e) => handleExternalClick(e, featuredItem, 'reel')}
                          >
                            <IgIcon size={13} />
                            Reel
                          </a>
                        )}
                        {featuredItem.yt_url && (
                          <a
                            className="btn btn-outline"
                            href={featuredItem.yt_url}
                            target="_blank" rel="noopener noreferrer"
                            onClick={(e) => handleExternalClick(e, featuredItem, 'yt')}
                          >
                            <YtIcon size={13} />
                            Short
                          </a>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.article>
            )}

            {gridItems.length === 0 && !featuredItem ? (
              <div className="drop-card" style={{ padding: 32, textAlign: 'center' }}>
                <div style={{ fontSize: '1rem', fontWeight: 600 }}>No matching drops</div>
                <div style={{ color: 'var(--muted)', fontSize: '0.86rem', marginTop: 6 }}>
                  Try clearing your search or switching categories.
                </div>
              </div>
            ) : (
              <>
                <div className="vault-grid">
                {gridItems.map((it, idx) => {
                  const num = String(showFeatured ? idx + 2 : idx + 1).padStart(3, '0');
                  const cats = getDropCategories(it);
                  return (
                    <motion.article
                      key={it.resource_url + idx}
                      className="drop-card"
                      onPointerMove={updateSpotlight}
                      initial={{ opacity: 0, y: 14 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.25, delay: Math.min(idx * 0.025, 0.25) }}
                    >
                      <div>
                        <div className="drop-head">
                          <span className="drop-index">
                            #{num} • {primaryBadgeLabel(cats)}
                          </span>
                          <span className="tag-kw">{it.keyword || 'TOOL'}</span>
                        </div>
                        <h3 className="drop-title">{it.title}</h3>
                        <div className="drop-path">{formatRepoPath(it.resource_url)}</div>
                      </div>

                      <div className="drop-foot">
                        <div className="drop-foot-row1">
                          <a
                            className="btn btn-outline drop-open-btn"
                            href={it.resource_url}
                            target="_blank" rel="noopener noreferrer"
                            onClick={(e) => handleExternalClick(e, it, 'repo')}
                          >
                            Open Repo
                            <ArrowUpRight size={14} />
                          </a>
                          <button
                            type="button"
                            className="btn drop-setup-btn"
                            onClick={() => setSelected(it)}
                            aria-label="Setup & Prompt"
                            title="Setup & Prompt"
                          >
                            <Terminal size={13} />
                            Setup
                          </button>
                        </div>
                        {(it.permalink || it.yt_url) && (
                          <div className="drop-foot-row2">
                            {it.permalink && (
                              <a
                                className="btn drop-social-btn drop-ig-btn"
                                href={it.permalink}
                                target="_blank" rel="noopener noreferrer"
                                onClick={(e) => handleExternalClick(e, it, 'reel')}
                              >
                                <IgIcon size={13} />
                                Instagram
                              </a>
                            )}
                            {it.yt_url && (
                              <a
                                className="btn drop-social-btn drop-yt-btn"
                                href={it.yt_url}
                                target="_blank" rel="noopener noreferrer"
                                onClick={(e) => handleExternalClick(e, it, 'yt')}
                              >
                                <YtIcon size={13} />
                                YouTube
                              </a>
                            )}
                          </div>
                        )}
                      </div>
                    </motion.article>
                  );
                })}
              </div>
              {remainingCount > 0 && (
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '1.5rem' }}>
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ minWidth: 'min(100%, 16rem)' }}
                    onClick={() => setVisibleCount((c) => c + PAGE_SIZE)}
                  >
                    Show More ({remainingCount} remaining)
                  </button>
                </div>
              )}
              </>
            )}
          </>
        )}

        <footer className="footer">
          <span>CURIOCUT INDEX • LIVE EDGE FEED</span>
          <div style={{ display: 'flex', gap: 16 }}>
            <a href="https://instagram.com/curiocutt" target="_blank" rel="noopener noreferrer">Instagram</a>
            <a href="https://curiocut-corn.pcgpt00.workers.dev/privacy" target="_blank" rel="noopener noreferrer">Privacy</a>
          </div>
        </footer>
      </div>

      {/* Slide-over Inspector Drawer */}
      <AnimatePresence>
        {selected && (
          <motion.div
            className="drawer-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelected(null)}
          >
            <motion.aside
              className="drawer-panel"
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 32 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="tag-kw">KEYWORD: {selected.keyword || 'TOOL'}</span>
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ padding: 7 }}
                  onClick={() => setSelected(null)}
                  aria-label="Close drawer"
                >
                  <X size={16} />
                </button>
              </div>

              <div>
                <h2 style={{ margin: '0 0 8px', fontSize: '1.35rem', lineHeight: 1.25 }}>
                  {selected.title}
                </h2>
                <div className="repo-line">{formatRepoPath(selected.resource_url)}</div>
              </div>

              <div>
                <div className="metric-label" style={{ marginBottom: 8 }}>
                  AI Agent Setup Prompt (Claude / Cursor / Antigravity)
                </div>
                <div className="code-block">
                  Install, configure, and walk me through running {selected.resource_url} locally.
                </div>
                <button
                  type="button"
                  className="btn btn-accent"
                  style={{ width: '100%', marginTop: 10 }}
                  onClick={() => {
                    trackEvent('copy_prompt', selected.keyword);
                    copyText(
                      `Install, configure, and walk me through running ${selected.resource_url} locally.`,
                      'Copied AI Setup Prompt'
                    );
                  }}
                >
                  <Copy size={14} />
                  Copy AI Setup Prompt
                </button>
              </div>

              {selected.resource_url.includes('github.com') && (
                <div>
                  <div className="metric-label" style={{ marginBottom: 8 }}>
                    Terminal Clone
                  </div>
                  <div className="code-block">git clone {selected.resource_url}</div>
                  <button
                    type="button"
                    className="btn btn-outline"
                    style={{ width: '100%', marginTop: 10 }}
                    onClick={() => {
                      trackEvent('copy_git', selected.keyword);
                      copyText(`git clone ${selected.resource_url}`, 'Copied git clone');
                    }}
                  >
                    <Copy size={14} />
                    Copy Command
                  </button>
                </div>
              )}

              <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 8 }}>
                <a
                  className="btn btn-outline"
                  style={{ width: '100%' }}
                  href={selected.resource_url}
                  target="_blank" rel="noopener noreferrer"
                  onClick={(e) => handleExternalClick(e, selected, 'repo')}
                >
                  Open Repository
                  <ArrowUpRight size={14} />
                </a>
                {(selected.permalink || selected.yt_url) && (
                  <div style={{ display: 'grid', gridTemplateColumns: selected.permalink && selected.yt_url ? '1fr 1fr' : '1fr', gap: 8 }}>
                    {selected.permalink && (
                      <a
                        className="btn btn-ghost"
                        href={selected.permalink}
                        target="_blank" rel="noopener noreferrer"
                        onClick={(e) => handleExternalClick(e, selected, 'reel')}
                      >
                        <IgIcon size={14} />
                        Instagram
                      </a>
                    )}
                    {selected.yt_url && (
                      <a
                        className="btn btn-ghost"
                        href={selected.yt_url}
                        target="_blank" rel="noopener noreferrer"
                        onClick={(e) => handleExternalClick(e, selected, 'yt')}
                      >
                        <YtIcon size={14} />
                        YouTube
                      </a>
                    )}
                  </div>
                )}
              </div>
            </motion.aside>
          </motion.div>
        )}
      </AnimatePresence>

      <CommandPalette
        open={cmdOpen}
        onClose={() => setCmdOpen(false)}
        items={items}
        onSelect={(item) => setSelected(item)}
      />

      {/* External Link Confirmation Modal */}
      <AnimatePresence>
        {pendingLink && (
          <motion.div
            className="confirm-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setPendingLink(null)}
          >
            <motion.div
              className="confirm-modal"
              initial={{ opacity: 0, y: 16, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.97 }}
              transition={{ duration: 0.16 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span className="tag-kw">
                  {pendingLink.kind === 'reel'
                    ? 'LEAVING TO INSTAGRAM'
                    : pendingLink.kind === 'yt'
                      ? 'LEAVING TO YOUTUBE'
                      : 'LEAVING TO REPOSITORY'}
                </span>
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ padding: 6 }}
                  onClick={() => setPendingLink(null)}
                  aria-label="Close"
                >
                  <X size={15} />
                </button>
              </div>
              <div>
                <h3 style={{ margin: '0 0 6px', fontSize: '1.1rem', lineHeight: 1.3 }}>
                  {pendingLink.title}
                </h3>
                <div className="code-block" style={{ fontSize: '0.73rem' }}>
                  {pendingLink.url}
                </div>
              </div>
              <div style={{ display: 'grid', gap: 8 }}>
                <a
                  className="btn btn-accent"
                  style={{ width: '100%', whiteSpace: 'nowrap' }}
                  href={pendingLink.url}
                  target="_blank" rel="noopener noreferrer"
                  onClick={() => {
                    const evName =
                      pendingLink.kind === 'reel'
                        ? 'watch_reel'
                        : pendingLink.kind === 'yt'
                          ? 'watch_yt'
                          : 'open_repo';
                    trackEvent(evName, pendingLink.keyword);
                    setPendingLink(null);
                  }}
                >
                  Continue to {pendingLink.host}
                  <ArrowUpRight size={15} />
                </a>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                  <button
                    type="button"
                    className="btn btn-outline"
                    onClick={() => copyText(pendingLink.url, 'Copied URL')}
                  >
                    <Copy size={14} />
                    Copy Link
                  </button>
                  <button
                    type="button"
                    className="btn btn-ghost"
                    onClick={() => setPendingLink(null)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="toast-viewport" aria-live="polite" aria-atomic="true">
        <AnimatePresence mode="wait">
          {toast && (
            <motion.div
              key={toast.id}
              className={`toast toast-${toast.type}`}
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 8, scale: 0.96 }}
              transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
              role="status"
            >
              <span className="toast-icon" aria-hidden="true">
                {toast.type === 'warning' ? <AlertTriangle size={14} /> : <Check size={14} />}
              </span>
              <span className="toast-msg">{toast.msg}</span>
              <button
                type="button"
                className="toast-close"
                onClick={dismissToast}
                aria-label="Dismiss notification"
              >
                <X size={13} />
              </button>
              <motion.span
                className="toast-progress"
                initial={{ scaleX: 1 }}
                animate={{ scaleX: 0 }}
                transition={{ duration: toast.duration / 1000, ease: 'linear' }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
}
