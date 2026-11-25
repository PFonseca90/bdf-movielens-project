// ---------------------------------------------------------------
// REAL DATA. Everything below comes from src/gameData.json, which is
// written by  src/08_export_game_data.py  in the analysis project.
//   critics  = Rotten Tomatoes Tomatometer (% of critics positive, 0-100)
//   audience = MovieLens 32M crowd score   (% of ratings >= 3.5 stars, 0-100)
// To refresh: run 07 + 08 in Python, then `npm run build` here.
// ---------------------------------------------------------------
import gameData from './gameData.json';

export type Motif = 'sun' | 'fin' | 'city' | 'eye' | 'heart' | 'slice' | 'beige' | 'crescent';

export interface Movie {
    id: number;
    movieId: number;        // MovieLens id
    title: string;
    year: number;
    genre: string;
    critics: number;        // Tomatometer 0-100
    audience: number;       // MovieLens crowd score 0-100
    criticsPct: number;     // percentile of the critics score among all analysed films
    audiencePct: number;    // percentile of the crowd score among all analysed films
    rankGap: number;        // audiencePct - criticsPct  (+ crowd ranks it higher)
    nRatings: number;       // number of MovieLens ratings behind the crowd score
    criticReviews: number;  // number of critic reviews behind the Tomatometer
    imdb: number | null;    // IMDb user rating 1-10 (third voice, for context)
    director: string;
    motif: Motif;
    colors: [string, string, string]; // top, bottom, accent
    tagline: string;
    criticQuote: string;    // Rotten Tomatoes critics consensus
    audienceQuote: string;  // most-used MovieLens user tags
}

export interface GenreGap { name: string; gap: number; rawGap: number; critics: number; crowd: number; movies: number; example: string }

export const movies = gameData.movies as unknown as Movie[];

// gap = average RANK gap (percentile points). Positive = crowd ranks the genre higher than critics.
export const genres = gameData.genres as GenreGap[];

export const stats = gameData.stats as { movies: number; ratings: number; correlation: number; avgCritics: number; avgCrowd: number; agreePct: number };

export const GAME_ROUNDS = 5;

// Starts empty: the class fills it live during the presentation.
export const classBoard: { name: string; score: number }[] = [];

export const titles = [
    { min: 5, name: 'Certified Film Snob', he: '', blurb: 'You can smell a Cannes premiere from the parking lot.', icon: 'hat' },
    { min: 4, name: 'Festival Regular', he: '', blurb: 'Subtitles do not scare you. Much.', icon: 'ticket' },
    { min: 3, name: 'Weekend Cinephile', he: '', blurb: 'Half critic, half couch. Balanced.', icon: 'reel' },
    { min: 2, name: 'Popcorn Enthusiast', he: '', blurb: 'You vote with your snack bucket.', icon: 'corn' },
    { min: 0, name: 'Proud Common Folk', he: 'קהל פשוטי העם', blurb: 'Critics fear you. Studios love you.', icon: 'corn' },
];
export const titleFor = (score: number) => titles.find((t) => score >= t.min)!;
