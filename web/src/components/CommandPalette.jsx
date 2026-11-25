import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ArrowUpRight } from 'lucide-react';

export default function CommandPalette({ open, onClose, items, onSelect }) {
  const [query, setQuery] = useState('');
  const [cursor, setCursor] = useState(0);

  const filtered = items
    .filter((it) => {
      if (!query.trim()) return true;
      const q = query.toLowerCase();
      return (
        it.title.toLowerCase().includes(q) ||
        it.keyword.toLowerCase().includes(q) ||
        it.resource_url.toLowerCase().includes(q)
      );
    })
    .slice(0, 10);

  useEffect(() => {
    setCursor(0);
  }, [query, open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setCursor((c) => Math.min(c + 1, Math.max(0, filtered.length - 1)));
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setCursor((c) => Math.max(c - 1, 0));
      }
      if (e.key === 'Enter' && filtered[cursor]) {
        e.preventDefault();
        onSelect(filtered[cursor]);
        onClose();
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, filtered, cursor, onClose, onSelect]);

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="cmd-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <motion.div
            className="cmd-modal"
            initial={{ opacity: 0, y: -12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="cmd-input-row">
              <Search size={16} color="#8b8a85" />
              <input
                autoFocus
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Jump to tool, keyword, or repo..."
              />
              <span className="kbd">ESC</span>
            </div>
            <div className="cmd-list">
              {filtered.length === 0 ? (
                <div style={{ padding: '18px 12px', color: '#8b8a85', fontSize: '0.85rem' }}>
                  No matching drops.
                </div>
              ) : (
                filtered.map((it, idx) => (
                  <button
                    key={it.resource_url + idx}
                    type="button"
                    className={`cmd-item ${idx === cursor ? 'selected' : ''}`}
                    onClick={() => {
                      onSelect(it);
                      onClose();
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
                      <span className="tag-kw">{it.keyword || 'TOOL'}</span>
                      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.88rem' }}>
                        {it.title}
                      </span>
                    </div>
                    <ArrowUpRight size={15} color="#8b8a85" />
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
