import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { viteSingleFile } from 'vite-plugin-singlefile';

// Everything is inlined into one HTML file, so dist/index.html runs by double-clicking it.
export default defineConfig({
  plugins: [react(), viteSingleFile()],
  base: './',
});
