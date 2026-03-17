import { RefreshCw } from 'lucide-react';
import { useEffect, useMemo, useRef, useState } from 'react';
import { Card } from '../components/Card';
import { MarketBetModal } from '../components/MarketBetModal';
import { listMarkets } from '../lib/api';
import type { Market, User } from '../lib/types';

export function DashboardPage(props: { user: User | null; onRefreshMe?: () => Promise<void> | void; onOptimisticBalance?: (delta: number) => void }) {
  const [markets, setMarkets] = useState<Market[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [selected, setSelected] = useState<Market | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [tab, setTab] = useState<'open' | 'resolved'>('open');
  const [sort, setSort] = useState<'title_asc' | 'title_desc' | 'date_desc' | 'date_asc'>('date_desc');
  const [sortOpen, setSortOpen] = useState(false);
  const sortRef = useRef<HTMLDivElement | null>(null);
  const [query, setQuery] = useState('');

  const subtitle = useMemo(() => {
    if (!lastUpdated) return null;
    return `Actualisé à ${lastUpdated.toLocaleTimeString()} — Rotation automatique des paris toutes les 5 min`;
  }, [lastUpdated]);

  useEffect(() => {
    const load = async () => {
      setErr(null);
      try {
        setMarkets(await listMarkets());
        setLastUpdated(new Date());
      } catch (e) {
        setErr((e as Error).message);
      }
    };
    void load();
  }, []);

  useEffect(() => {
    if (!sortOpen) return;
    const onDown = (e: MouseEvent) => {
      if (!sortRef.current) return;
      if (e.target instanceof Node && !sortRef.current.contains(e.target)) {
        setSortOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSortOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [sortOpen]);

  const sortLabel = useMemo(() => {
    switch (sort) {
      case 'title_asc':
        return 'Alphabetique (A → Z)';
      case 'title_desc':
        return 'Alphabetique (Z → A)';
      case 'date_asc':
        return 'Date (ancien → récent)';
      case 'date_desc':
      default:
        return 'Date (récent → ancien)';
    }
  }, [sort]);

  const visibleMarkets = useMemo(() => {
    const filtered = markets.filter((m) => (tab === 'open' ? m.status === 'open' : m.status === 'resolved'));
    const q = query.trim().toLowerCase();
    const searched = q ? filtered.filter((m) => m.title.toLowerCase().includes(q)) : filtered;
    const timeKey = (m: Market) => {
      if (tab === 'resolved') return new Date((m.resolved_at ?? m.created_at) as string).getTime();
      return new Date(m.created_at).getTime();
    };
    const byDate = (a: Market, b: Market) => timeKey(a) - timeKey(b);
    const byTitle = (a: Market, b: Market) => a.title.localeCompare(b.title, 'fr', { sensitivity: 'base' });
    const sorted = [...searched];
    if (sort === 'date_asc') sorted.sort(byDate);
    if (sort === 'date_desc') sorted.sort((a, b) => byDate(b, a));
    if (sort === 'title_asc') sorted.sort(byTitle);
    if (sort === 'title_desc') sorted.sort((a, b) => byTitle(b, a));
    return sorted;
  }, [markets, query, sort, tab]);

  const searchHint = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return null;
    const currentHas = markets.some((m) => (tab === 'open' ? m.status === 'open' : m.status === 'resolved') && m.title.toLowerCase().includes(q));
    if (currentHas) return null;
    const otherHas = markets.some((m) => (tab === 'open' ? m.status === 'resolved' : m.status === 'open') && m.title.toLowerCase().includes(q));
    if (tab === 'open') {
      return otherHas ? 'Aucun paris en cours ne porte ce nom' : 'Aucun paris en cours ne porte ce nom';
    }
    // tab === 'resolved'
    return otherHas ? "Oups ! Le paris n'est peut-être pas encore terminé !" : "Oups ! Le paris n'est peut-être pas encore terminé !";
  }, [markets, query, tab]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-xs text-white/60">{subtitle}</div>
        <button
          type="button"
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-xs font-semibold text-white/70 hover:bg-white/5"
          onClick={async () => {
            try {
              setMarkets(await listMarkets());
              setLastUpdated(new Date());
            } catch (e) {
              setErr(e instanceof Error ? e.message : String(e));
            }
          }}
        >
          <RefreshCw size={14} /> Rafraîchir
        </button>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="inline-flex w-full rounded-2xl border border-white/10 bg-black/20 p-1 sm:w-auto">
          <button
            type="button"
            className={`flex-1 rounded-2xl px-4 py-2 text-sm font-extrabold transition sm:flex-none ${
              tab === 'open' ? 'bg-primary/15 text-white' : 'text-white/60 hover:text-white'
            }`}
            onClick={() => setTab('open')}
          >
            Paris en cours
          </button>
          <button
            type="button"
            className={`flex-1 rounded-2xl px-4 py-2 text-sm font-extrabold transition sm:flex-none ${
              tab === 'resolved' ? 'bg-white/5 text-white' : 'text-white/60 hover:text-white'
            }`}
            onClick={() => setTab('resolved')}
          >
            Paris terminés
          </button>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-end" ref={sortRef}>
          <div className="flex items-center gap-2">
            <div className="text-xs font-semibold text-white/60">Trier</div>
            <div className="relative w-full sm:w-72">
            <button
              type="button"
              className="flex h-10 w-full items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-3 text-sm font-semibold text-white/80 outline-none transition hover:border-white/20 hover:bg-white/5 focus:ring-2 focus:ring-accent/70"
              onClick={() => setSortOpen((v) => !v)}
              aria-haspopup="menu"
              aria-expanded={sortOpen}
            >
              <span className="truncate">{sortLabel}</span>
              <span className={`ml-3 text-white/60 transition ${sortOpen ? 'rotate-180' : ''}`}>▾</span>
            </button>

            {sortOpen ? (
              <div className="absolute right-0 z-30 mt-2 w-full overflow-hidden rounded-2xl border border-white/10 bg-bg2/95 shadow-2xl backdrop-blur tb-animate-in">
                {(
                  [
                    ['title_asc', 'Alphabetique (A → Z)'],
                    ['title_desc', 'Alphabetique (Z → A)'],
                    ['date_desc', 'Date (récent → ancien)'],
                    ['date_asc', 'Date (ancien → récent)'],
                  ] as const
                ).map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    className={`flex w-full items-center justify-between px-4 py-3 text-sm font-semibold transition hover:bg-white/5 ${
                      sort === value ? 'text-white' : 'text-white/75'
                    }`}
                    onClick={() => {
                      setSort(value);
                      setSortOpen(false);
                    }}
                  >
                    <span>{label}</span>
                    {sort === value ? <span className="text-primary">●</span> : <span className="text-white/20">●</span>}
                  </button>
                ))}
              </div>
            ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="text-xs font-semibold text-white/60">Rechercher</div>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nom d’un paris…"
              className="h-10 w-full rounded-2xl border border-white/10 bg-black/20 px-3 text-sm font-semibold text-white/80 outline-none transition placeholder:text-white/30 hover:border-white/20 hover:bg-white/5 focus:ring-2 focus:ring-accent/70 sm:w-72"
            />
          </div>
        </div>
      </div>

      {!props.user ? (
        <Card>
          <div className="text-sm text-white/70">Mode invité: consulte les marchés, connecte-toi pour miser.</div>
        </Card>
      ) : null}

      {err ? <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-sm">{err}</div> : null}
      {searchHint ? <div className="text-xs text-white/50">{searchHint}</div> : null}

      <div className="grid gap-4 md:grid-cols-2">
        {visibleMarkets.map((m) => (
          <button key={m.id} type="button" className="text-left" onClick={() => setSelected(m)}>
            <div className="relative overflow-hidden rounded-3xl border border-white/10 bg-black/20 p-6 shadow-xl transition hover:border-white/20">
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/15 via-transparent to-accent/15" />
              <div className="relative">
                <div className="text-lg font-extrabold leading-snug">{m.title}</div>
                <div className="mt-2 text-sm text-white/60">{m.description}</div>
                <div className="mt-6 rounded-2xl border border-white/10 bg-black/25 p-4 text-center text-sm italic text-white/50">
                  {m.status === 'open' ? (
                    <span className="text-white/60">Soyez le premier à parier !</span>
                  ) : (
                    <span
                      className={`inline-flex items-center justify-center rounded-2xl px-4 py-3 text-base font-extrabold tracking-wide ${
                        m.resolved_outcome === 'yes'
                          ? 'bg-primary/20 text-white border border-primary/40'
                          : 'bg-accent/25 text-white border border-accent/50'
                      }`}
                    >
                      RÉSULTAT : {m.resolved_outcome === 'yes' ? 'OUI' : 'NON'}
                    </span>
                  )}
                </div>
                <div className="mt-4 text-xs text-white/60">
                  Min: 5.00 € · Pool: {(m.yes_pool + m.no_pool).toFixed(2)} € · {m.yes_pool + m.no_pool > 0 ? '—' : '0'} participants · Comm: 10%
                </div>
              </div>
            </div>
          </button>
        ))}
        {visibleMarkets.length === 0 ? (
          <Card>
            <div className="text-sm text-white/70">{tab === 'open' ? 'Aucun marché en cours.' : 'Aucun marché terminé.'}</div>
          </Card>
        ) : null}
      </div>

      {selected ? (
        <MarketBetModal
          market={selected}
          user={props.user}
          onClose={() => setSelected(null)}
          onOptimisticBalance={(d) => props.onOptimisticBalance?.(d)}
          onPlaced={async () => {
            setSelected(null);
            setMarkets(await listMarkets());
            setLastUpdated(new Date());
            await props.onRefreshMe?.();
          }}
        />
      ) : null}
    </div>
  );
}

