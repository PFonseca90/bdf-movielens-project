import React, { useEffect, useMemo, useRef, useState } from 'react';
import { movies, genres, stats, classBoard, titleFor, titles, GAME_ROUNDS, type Movie } from './data';
import { Poster } from './Poster';

type Tab = 'play' | 'shame' | 'genre' | 'board';
type Pick = 'critics' | 'audience';
const gapOf = (m: Movie) => m.audience - m.critics;
// Percentile -> words: 93 -> "top 7%", 14 -> "bottom 14%"
const rankWords = (pct: number) => pct >= 50 ? `top ${Math.max(1, 100 - pct)}%` : `bottom ${Math.max(1, pct)}%`;
const fmt = (n: number) => n.toLocaleString('en-US');

function shuffle<T>(arr: T[]): T[] {
    const a = [...arr];
    for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
    return a;
}

function Bulbs() { return <div className="fs-bulbs" aria-hidden="true">{Array.from({ length: 28 }).map((_, i) => <i key={i} style={{ animationDelay: `${(i % 4) * 0.25}s` }} />)}</div>; }

function Icon({ name }: { name: string }) {
    const p = { width: 28, height: 28, viewBox: '0 0 32 32', fill: 'none', stroke: 'currentColor', strokeWidth: 1.8, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const };
    if (name === 'hat') return <svg {...p}><path d="M6 22h20M9 22c0-8 2-12 7-12s7 4 7 12M9 18h14" /><circle cx="16" cy="7" r="1.5" /></svg>;
    if (name === 'ticket') return <svg {...p}><path d="M4 11a2 2 0 0 0 0 4v0a2 2 0 0 1 0 4v3h24v-3a2 2 0 0 1 0-4v0a2 2 0 0 0 0-4V8H4z" /><path d="M20 8v14" strokeDasharray="2 3" /></svg>;
    if (name === 'reel') return <svg {...p}><circle cx="16" cy="16" r="11" /><circle cx="16" cy="16" r="2" /><circle cx="16" cy="9" r="2" /><circle cx="16" cy="23" r="2" /><circle cx="9" cy="16" r="2" /><circle cx="23" cy="16" r="2" /></svg>;
    return <svg {...p}><path d="M8 12h16l-2 15H10z" /><path d="M8 12c-2-4 2-6 4-4 1-3 5-3 6-1 2-2 6 0 5 3 2 0 3 2 1 4" /><path d="M13 12l1 15M19 12l-1 15" /></svg>;
}

function Gauge({ value, left, right }: { value: number; left: string; right: string }) {
    const [gid] = useState(() => 'fsg' + Math.random().toString(36).slice(2, 8));
    const [v, setV] = useState(0.5);
    useEffect(() => { const t = setTimeout(() => setV(value), 350); return () => clearTimeout(t); }, [value]);
    const angle = -90 + v * 180;
    const ticks = Array.from({ length: 11 }, (_, i) => i);
    return <figure className="fs-gauge" aria-label={`Snob-o-meter: ${Math.round(value * 100)} percent on the snob side`}>
        <svg viewBox="0 0 300 180">
            <defs><linearGradient id={gid} x1="0" x2="1"><stop offset="0" stopColor="#ffb703" /><stop offset=".5" stopColor="#f4efe6" /><stop offset="1" stopColor="#c8102e" /></linearGradient></defs>
            <path d="M30 150 A120 120 0 0 1 270 150" stroke={`url(#${gid})`} strokeWidth="16" fill="none" strokeLinecap="round" />
            {ticks.map((i) => { const a = (-180 + i * 18) * Math.PI / 180; return <line key={i} x1={150 + Math.cos(a) * 98} y1={150 + Math.sin(a) * 98} x2={150 + Math.cos(a) * (i % 5 === 0 ? 86 : 91)} y2={150 + Math.sin(a) * (i % 5 === 0 ? 86 : 91)} stroke="#f4efe6" strokeOpacity=".5" strokeWidth="2" />; })}
            <g className="fs-needle" style={{ transform: `rotate(${angle}deg)` }}><path d="M150 150 L146 62 L150 54 L154 62Z" fill="#f4efe6" /></g>
            <circle cx="150" cy="150" r="10" fill="#0b0a0f" stroke="#f4efe6" strokeWidth="3" />
        </svg>
        <figcaption><span>{left}</span><span>{right}</span></figcaption>
    </figure>;
}

function Confetti({ burst }: { burst: number }) {
    if (!burst) return null;
    return <div className="fs-confetti" key={burst} aria-hidden="true">{Array.from({ length: 22 }).map((_, i) => <i key={i} style={{ ['--x' as string]: `${(Math.random() - 0.5) * 520}px`, ['--y' as string]: `${-120 - Math.random() * 260}px`, ['--r' as string]: `${Math.random() * 720}deg`, ['--d' as string]: `${Math.random() * 0.15}s` }} />)}</div>;
}

/* ---------------------------------- PLAY ---------------------------------- */
function Play({ onFinish, onToHall }: { onFinish: (name: string, score: number, criticsShare: number) => void; onToHall: () => void }) {
    const [phase, setPhase] = useState<'home' | 'game' | 'result'>('home');
    const [name, setName] = useState('');
    const [deck, setDeck] = useState<Movie[]>([]);
    const [i, setI] = useState(0);
    const [picked, setPicked] = useState<Pick | null>(null);
    const [score, setScore] = useState(0);
    const [streak, setStreak] = useState(0);
    const [criticsPicks, setCriticsPicks] = useState(0);
    const [burst, setBurst] = useState(0);
    const [curtain, setCurtain] = useState(false);
    const cardRef = useRef<HTMLDivElement>(null);

    const start = () => {
        const nCrowd = Math.random() < 0.5 ? Math.floor(GAME_ROUNDS / 2) : Math.ceil(GAME_ROUNDS / 2);
        const crowdFilms = shuffle(movies.filter((mv) => gapOf(mv) > 0)).slice(0, nCrowd);
        const criticFilms = shuffle(movies.filter((mv) => gapOf(mv) < 0)).slice(0, GAME_ROUNDS - nCrowd);
        setDeck(shuffle([...crowdFilms, ...criticFilms])); setI(0); setPicked(null); setScore(0); setStreak(0); setCriticsPicks(0); setBurst(0);
        setCurtain(true); setTimeout(() => setPhase('game'), 650); setTimeout(() => setCurtain(false), 1500);
    };
    const m = deck[i];
    const correct = m && picked ? (picked === 'audience') === (gapOf(m) > 0) : false;
    const choose = (p: Pick) => {
        if (picked || !m) return;
        setPicked(p); if (p === 'critics') setCriticsPicks((c) => c + 1);
        const ok = (p === 'audience') === (gapOf(m) > 0);
        if (ok) { setScore((s) => s + 1); setStreak((s) => s + 1); setBurst((b) => b + 1); } else setStreak(0);
    };
    const next = () => {
        if (i + 1 >= deck.length) { setPhase('result'); onFinish(name.trim() || 'You', score, criticsPicks / GAME_ROUNDS); return; }
        setI(i + 1); setPicked(null);
    };
    const title = titleFor(score);

    return <section className="fs-stage">
        {curtain && <div className="fs-curtain" aria-hidden="true"><i /><i /></div>}
        {phase === 'home' && <div className="fs-hero">
            <div className="fs-hero-copy">
                <p className="fs-eyebrow">Now showing · Audience of one (or thirty)</p>
                <h1 className="fs-title"><span>Film Snob</span><em>or</em><span className="fs-red">Popcorn Person?</span></h1>
                <p className="fs-lede">Five posters. One question each: who liked it more, the critics or the crowd? Get it wrong and the tomatoes come out.</p>
                <label className="fs-field"><span>Your name for the leaderboard</span><input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Libi" maxLength={16} onKeyDown={(e) => { if (e.key === 'Enter') start(); }} /></label>
                <div className="fs-actions">
                    <button type="button" className="fs-ticket" onClick={start}><span className="fs-ticket-main">Take your seat</span><span className="fs-ticket-sub">ADMIT ONE · {GAME_ROUNDS} ROUNDS</span></button>
                    <button type="button" className="fs-link" onClick={onToHall}>See the Hall of Shame →</button>
                </div>
            </div>
            <div className="fs-hero-posters" aria-hidden="true">
                {[movies[1], movies[0], movies[2]].map((mv, k) => <Poster key={mv.id} movie={mv} className={`fs-hp fs-hp-${k}`} />)}
            </div>
        </div>}

        {phase === 'game' && m && <div className="fs-game">
            <div className="fs-hud">
                <div className="fs-strip" aria-label={`Round ${i + 1} of ${deck.length}`}>{deck.map((_, k) => <i key={k} className={k < i ? 'is-done' : k === i ? 'is-now' : ''} />)}</div>
                <div className="fs-hud-stats"><span>Round <b>{i + 1}</b>/{deck.length}</span><span>Score <b>{score}</b></span><span className={streak > 1 ? 'is-hot' : ''}>Streak <b>{streak}</b>{streak > 1 ? ' 🔥' : ''}</span></div>
            </div>
            <div className="fs-grid">
                <div className="fs-poster-wrap" ref={cardRef}>
                    <div className="fs-spot" aria-hidden="true" />
                    <Poster movie={m} className={`fs-big ${picked ? (correct ? 'is-right' : 'is-wrong') : ''}`} />
                    <span className="fs-meta">{m.genre} · {m.year}</span>
                    <Confetti burst={burst} />
                </div>
                <div className="fs-panel">
                    {!picked && <>
                        <h2 className="fs-q">Who rated this one higher?</h2>
                        <p className="fs-sub">Trust your gut. No Googling.</p>
                        <div className="fs-choices">
                            <button type="button" className="fs-choice fs-critic" onClick={() => choose('critics')}><span className="fs-choice-ico"><Icon name="hat" /></span><b>The Critics</b><small>Berets. Opinions. Espresso.</small></button>
                            <button type="button" className="fs-choice fs-crowd" onClick={() => choose('audience')}><span className="fs-choice-ico"><Icon name="corn" /></span><b>The Crowd</b><small>Popcorn. Feelings. Snacks.</small></button>
                        </div>
                    </>}
                    {picked && <div className="fs-reveal">
                        <p className={`fs-verdict ${correct ? 'ok' : 'no'}`}>{correct ? 'Correct. You get movies.' : 'Splat. A tomato for you.'}</p>
                        <h2 className="fs-q fs-q-sm">{gapOf(m) > 0 ? 'The crowd adored it.' : 'The critics adored it.'}</h2>
                        <div className="fs-bars">
                            <div className="fs-bar"><label>Critics</label><div><i className="fs-bar-c" style={{ width: `${m.critics}%` }} /></div><b>{m.critics}</b></div>
                            <div className="fs-bar"><label>Crowd</label><div><i className="fs-bar-a" style={{ width: `${m.audience}%` }} /></div><b>{m.audience}</b></div>
                        </div>
                        <p className="fs-gap">Gap: <b>{Math.abs(gapOf(m))} points</b> · critics put it in their <b>{rankWords(m.criticsPct)}</b>, the crowd in its <b>{rankWords(m.audiencePct)}</b></p>
                        <blockquote className="fs-quote"><p><span>Critics' consensus:</span> “{m.criticQuote}”</p><p><span>Crowd's top tags:</span> {m.audienceQuote}</p></blockquote>
                        <p className="fs-src">{fmt(m.criticReviews)} critic reviews · {fmt(m.nRatings)} MovieLens ratings{m.imdb ? ` · IMDb ${m.imdb}` : ''}</p>
                        <button type="button" className="fs-next" onClick={next}>{i + 1 >= deck.length ? 'Roll the credits' : 'Next film'} →</button>
                    </div>}
                </div>
            </div>
        </div>}

        {phase === 'result' && <div className="fs-result">
            <p className="fs-eyebrow">The envelope, please</p>
            <h2 className="fs-title fs-title-sm"><span>You scored</span> <span className="fs-red">{score}/{GAME_ROUNDS}</span></h2>
            <div className="fs-badge"><Icon name={title.icon} /><div><b>{title.name}</b>{title.he && <bdi dir="rtl" lang="he" className="fs-he">{title.he}</bdi>}<small>{title.blurb}</small></div></div>
            <div className="fs-snob">
                <h3>Your Snob-o-meter</h3>
                <Gauge value={score / GAME_ROUNDS} left="Popcorn Person" right="Film Snob" />
                <p className="fs-sub">You read {score} of {GAME_ROUNDS} films right. You bet on the critics {criticsPicks}× and on the crowd {GAME_ROUNDS - criticsPicks}×.</p>
            </div>
            <div className="fs-actions fs-center">
                <button type="button" className="fs-ticket" onClick={() => { setPhase('home'); }}><span className="fs-ticket-main">Play again</span><span className="fs-ticket-sub">NEW FILMS EACH SHOW</span></button>
                <button type="button" className="fs-link" onClick={onToHall}>On to the Hall of Shame →</button>
            </div>
        </div>}
    </section>;
}

/* ---------------------------------- SHAME --------------------------------- */
function Shame() {
    const [side, setSide] = useState<'crowd' | 'critics'>('crowd');
    const list = useMemo(() => movies.filter((m) => (side === 'crowd' ? gapOf(m) > 0 : gapOf(m) < 0)).sort((a, b) => Math.abs(gapOf(b)) - Math.abs(gapOf(a))).slice(0, 5), [side]);
    return <section className="fs-section">
        <p className="fs-eyebrow">The Hall of Shame</p>
        <h2 className="fs-h2">The biggest gaps between <span className="fs-red">critics</span> and <span className="fs-gold">crowd</span></h2>
        <p className="fs-sub">Well-known films (10,000+ MovieLens ratings) where critics and crowd disagree the most. Bars: critics (red) vs crowd (gold), % who liked it.</p>
        <div className="fs-seg" role="tablist" aria-label="Choose a side">
            <button type="button" role="tab" aria-selected={side === 'crowd'} className={side === 'crowd' ? 'is-on' : ''} onClick={() => setSide('crowd')}>
                <Icon name="corn" /> Crowd loved, critics hated</button>
            <button type="button" role="tab" aria-selected={side === 'critics'} className={side === 'critics' ? 'is-on' : ''} onClick={() => setSide('critics')}>
                <Icon name="hat" /> Critics loved, crowd hated</button>
        </div>
        <ol className="fs-shame" key={side}>
            {list.map((m, k) => <li key={m.id} style={{ animationDelay: `${k * 90}ms` }}>
                <span className="fs-rank">{k + 1}</span>
                <Poster movie={m} className="fs-thumb" />
                <div className="fs-shame-body">
                    <h3>{m.title} <small>{m.genre} · {m.year}</small></h3>
                    <p className="fs-hl"><span>Critics:</span> “{m.criticQuote}” <span className="fs-sep">/</span> <span>Crowd tags:</span> {m.audienceQuote}</p>
                    <div className="fs-duo"><i className="fs-bar-c" style={{ width: `${m.critics}%` }}><b>{m.critics}</b></i><i className="fs-bar-a" style={{ width: `${m.audience}%` }}><b>{m.audience}</b></i></div>
                </div>
                <div className="fs-gapbadge"><b>{Math.abs(gapOf(m))}</b><small>pt gap</small></div>
            </li>)}
        </ol>
    </section>;
}

/* ---------------------------------- GENRE --------------------------------- */
function Genre() {
    const sorted = [...genres].sort((a, b) => b.gap - a.gap);
    const [sel, setSel] = useState(sorted[0].name);
    const g = sorted.find((x) => x.name === sel)!;
    const max = Math.max(...sorted.map((x) => Math.abs(x.gap)));
    const pct = (g.gap + max) / (2 * max);
    return <section className="fs-section">
        <p className="fs-eyebrow">Genre Battle</p>
        <h2 className="fs-h2">Which genre do critics <span className="fs-red">hate</span> while everyone else <span className="fs-gold">loves</span> it?</h2>
        <p className="fs-sub">Average rank gap per genre. MovieLens users grade harder overall (crowd {stats.avgCrowd}% vs critics {stats.avgCritics}%), so we compare ranks, not raw scores.</p>
        <div className="fs-battle">
            <div className="fs-div" role="list">
                <div className="fs-axis"><span>← Critics higher</span><span>Crowd higher →</span></div>
                {sorted.map((x) => <button type="button" role="listitem" key={x.name} className={`fs-drow ${x.name === sel ? 'is-on' : ''}`} onClick={() => setSel(x.name)} aria-pressed={x.name === sel}>
                    <span className="fs-dname">{x.name}</span>
                    <span className="fs-dtrack"><i className={x.gap >= 0 ? 'pos' : 'neg'} style={{ width: `${(Math.abs(x.gap) / max) * 50}%`, [x.gap >= 0 ? 'left' : 'right']: '50%' }} /></span>
                    <b>{x.gap > 0 ? '+' : ''}{x.gap}</b>
                </button>)}
            </div>
            <aside className="fs-verdict-card">
                <h3>Snob-o-meter: {g.name}</h3>
                <Gauge value={1 - pct} left="Crowd higher" right="Critics higher" />
                <p className="fs-sub">{g.gap > 0 ? `The crowd ranks ${g.name} films ${g.gap} percentile points higher than the critics do.` : `The critics rank ${g.name} films ${Math.abs(g.gap)} percentile points higher than the crowd does.`}</p>
                <p className="fs-src">{fmt(g.movies)} films · critics liked {g.critics}% on average · crowd liked {g.crowd}%</p>
                <p className="fs-example">Exhibit A: <b>{g.example}</b></p>
            </aside>
        </div>
    </section>;
}

/* ---------------------------------- BOARD --------------------------------- */
type Player = { name: string; score: number };
function Board({ players }: { players: Player[] }) {
    const me = players.length ? players[players.length - 1] : null;
    const rows = [...classBoard.map((r) => ({ ...r, me: false })), ...players.map((p) => ({ ...p, me: p === me }))].sort((a, b) => b.score - a.score);
    return <section className="fs-section">
        <p className="fs-eyebrow">The Class Board</p>
        <h2 className="fs-h2">Who in this room <span className="fs-gold">really</span> understands movies?</h2>
        {!me && <p className="fs-sub">Play a round to put your name up in lights.</p>}
        <ol className="fs-board">
            {rows.map((r, k) => { const t = titleFor(r.score); return <li key={r.name + k} className={r.me ? 'is-me' : ''} style={{ animationDelay: `${k * 70}ms` }}>
                <span className="fs-rank">{k + 1}</span><span className="fs-bname">{r.name}{r.me && <em> (you)</em>}</span>
                <span className="fs-btitle">{t.name}</span>
                <span className="fs-bscore">{Array.from({ length: GAME_ROUNDS }).map((_, j) => <i key={j} className={j < r.score ? 'on' : ''} />)}</span>
            </li>; })}
        </ol>
        <div className="fs-titles">{titles.map((t) => <span key={t.name}><Icon name={t.icon} />{t.name}<small>{t.min === 0 ? '0 to 1' : t.min === 5 ? '5' : `${t.min}`}</small></span>)}</div>
    </section>;
}

/* ----------------------------------- APP ---------------------------------- */
export function App() {
    const [tab, setTab] = useState<Tab>('play');
    const [players, setPlayers] = useState<Player[]>([]);
    const tabs: [Tab, string][] = [['play', 'Play'], ['shame', 'Hall of Shame'], ['genre', 'Genre Battle'], ['board', 'Class Board']];
    return <div className="fs-app">
        <div className="fs-bg" aria-hidden="true"><i className="fs-beam b1" /><i className="fs-beam b2" /><svg className="fs-noise"><filter id="fsn"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch" /></filter><rect width="100%" height="100%" filter="url(#fsn)" /></svg></div>
        <header className="fs-top">
            <div className="fs-logo"><svg viewBox="0 0 32 32" width="26" height="26" aria-hidden="true"><circle cx="16" cy="16" r="13" fill="none" stroke="currentColor" strokeWidth="2" /><circle cx="16" cy="16" r="3" fill="currentColor" />{[0, 72, 144, 216, 288].map((a) => <circle key={a} cx={16 + Math.cos(a * Math.PI / 180) * 7.5} cy={16 + Math.sin(a * Math.PI / 180) * 7.5} r="2.2" fill="currentColor" />)}</svg><span>SNOB<em>/</em>POPCORN</span></div>
            <nav className="fs-tabs" aria-label="Sections">{tabs.map(([k, label]) => <button type="button" key={k} className={tab === k ? 'is-on' : ''} aria-current={tab === k ? 'page' : undefined} onClick={() => setTab(k)}>{label}</button>)}</nav>
        </header>
        <Bulbs />
        <main>
            <div className={tab === 'play' ? '' : 'fs-hidden'}><Play onFinish={(name, score) => setPlayers((p) => [...p, { name, score }])} onToHall={() => setTab('shame')} /></div>
            {tab === 'shame' && <Shame />}
            {tab === 'genre' && <Genre />}
            {tab === 'board' && <Board players={players} />}
        </main>
        <footer className="fs-foot">Critics = Rotten Tomatoes Tomatometer (% of critics positive) · Crowd = % of MovieLens 32M ratings ≥ 3.5★ · {fmt(stats.movies)} matched films · {fmt(stats.ratings)} ratings · correlation {stats.correlation}<br />Pipeline: CSV → Parquet → DuckDB (local) · S3 + Glue + Athena (cloud). Data refreshed by <code>src/08_export_game_data.py</code>.</footer>
    </div>;
}
