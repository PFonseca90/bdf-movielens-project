# Film Snob or Popcorn Person?

The classroom game from your movie critics vs audience project. Dark cinema look,
poster quiz, Snob-o-meter, Hall of Shame, Genre Battle and Class Board.
It runs on the REAL analysis: src/gameData.json is written by
src/08_export_game_data.py (critics = Rotten Tomatoes Tomatometer,
crowd = % of MovieLens 32M ratings >= 3.5 stars).

## Play it right now (no setup)

1. Open the `dist` folder and double-click `index.html`.
   It opens in your browser and plays exactly like the online version.

## Look at the code in VS Code

1. In VS Code: File > Open Folder, and pick this `film-snob-game` folder.
2. The files that matter:
   - `src/gameData.json` - the real films, scores, genres and stats.
     Never edit by hand: re-run `python src/07_critics_vs_crowd.py` and
     `python src/08_export_game_data.py` from the project root, then `npm run build`.
   - `src/data.ts` - the types + reads gameData.json. Class Board starts empty.
   - `src/App.tsx` - the screens and game logic (quiz rounds, Snob-o-meter,
     Hall of Shame, Genre Battle, badges).
   - `src/Poster.tsx` - code-drawn posters (real titles + directors; no copyrighted poster images).
   - `src/style.css` - colors, fonts and layout.

## Run it in dev mode on your Mac (optional, for live editing)

You only need this if you want to edit the code and see changes live.

1. Install Node.js (free): download the LTS version from https://nodejs.org
   and run the installer.
2. In VS Code, open a terminal (Terminal > New Terminal), then run:

   npm install
   npm run dev

3. The terminal prints a local address like http://localhost:5173 - open it
   in your browser. Every save in VS Code refreshes the page.

To rebuild the double-click version after your edits:

   npm run build

That refreshes `dist/index.html`.

## Notes

- Scores on the Class Board reset when the page reloads.
- The old online copy (dummy data) is at https://files.instinct.com/7pwau7qgfskr-film-snob-or-popcorn-person
