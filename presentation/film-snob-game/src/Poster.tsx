import React from 'react';
import type { Movie } from './data';

function Art({ m }: { m: Movie }) {
    const [a, b, c] = m.colors;
    switch (m.motif) {
        case 'sun': return <g><circle cx="100" cy="120" r="56" fill={c} />{[0, 1, 2, 3, 4].map((i) => <rect key={i} x="30" y={128 + i * 9} width="140" height={2 + i * 1.6} fill={b} />)}<path d="M0 220 L60 160 L110 210 L150 170 L200 220 V300 H0Z" fill="#0006" /></g>;
        case 'fin': return <g><path d="M0 190 Q50 175 100 190 T200 190 V300 H0Z" fill="#0008" /><path d="M92 190 L112 112 L136 190Z" fill={c} /><path d="M0 214 Q50 200 100 214 T200 214" stroke="#fff6" strokeWidth="2" fill="none" /><path d="M0 238 Q50 224 100 238 T200 238" stroke="#fff3" strokeWidth="2" fill="none" /></g>;
        case 'city': return <g fill={c} opacity=".85">{[[14, 150, 26], [44, 110, 30], [78, 170, 22], [104, 90, 34], [142, 140, 26], [172, 175, 20]].map(([x, y, w], i) => <rect key={i} x={x} y={y} width={w} height={300 - y} />)}<g fill={a} opacity=".9">{[0, 1, 2, 3].map((i) => <rect key={i} x="110" y={102 + i * 20} width="6" height="8" />)}</g></g>;
        case 'eye': return <g><ellipse cx="100" cy="130" rx="70" ry="38" fill="none" stroke={c} strokeWidth="3" /><circle cx="100" cy="130" r="24" fill={c} /><circle cx="100" cy="130" r="9" fill={b} /><path d="M20 200 H180 M40 212 H160 M60 224 H140" stroke={c} strokeWidth="2" opacity=".6" /></g>;
        case 'heart': return <g><path d="M100 190 C20 130 40 60 100 105 C160 60 180 130 100 190Z" fill={c} /><circle cx="70" cy="200" r="10" fill="none" stroke={c} strokeWidth="3" /><path d="M70 200 L40 240 M70 200 L100 244" stroke={c} strokeWidth="3" /></g>;
        case 'slice': return <g><path d="M100 70 L32 206 Q100 232 168 206Z" fill={c} /><path d="M100 70 L32 206 Q100 232 168 206Z" fill="none" stroke="#a5651d" strokeWidth="8" strokeLinejoin="round" /><circle cx="86" cy="150" r="10" fill={b} /><circle cx="116" cy="170" r="12" fill={b} /><circle cx="94" cy="190" r="8" fill={b} /></g>;
        case 'beige': return <g><rect x="52" y="60" width="96" height="150" fill={c} opacity=".9" /><rect x="56" y="64" width="88" height="142" fill={a} /><rect x="0" y="218" width="200" height="2" fill={c} opacity=".5" /></g>;
        case 'crescent': return <g><circle cx="100" cy="125" r="52" fill={c} /><circle cx="124" cy="112" r="48" fill={a} /><g fill={c}>{[[30, 50], [160, 70], [150, 200], [48, 180], [76, 38]].map(([x, y], i) => <circle key={i} cx={x} cy={y} r="1.8" />)}</g></g>;
    }
}

export function Poster({ movie, hideTitle, className = '' }: { movie: Movie; hideTitle?: boolean; className?: string }) {
    const [top, bottom] = movie.colors;
    const dark = movie.motif === 'beige';
    return <div className={`fs-poster ${className}`} style={{ background: `linear-gradient(170deg, ${top}, ${bottom})`, color: dark ? '#2b2418' : '#fff' }} role="img" aria-label={hideTitle ? 'Movie poster' : `Poster for ${movie.title}`}>
        <svg viewBox="0 0 200 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><Art m={movie} /></svg>
        <div className="fs-poster-grain" />
        <div className="fs-poster-text">
            <span className="fs-poster-tag">{movie.tagline}</span>
            <strong>{movie.title}</strong>
            <span className="fs-poster-credit">{movie.director ? `A FILM BY ${movie.director.toUpperCase()} · ` : ''}{movie.year}</span>
        </div>
    </div>;
}
