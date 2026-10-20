import { resolve } from 'node:path';

// Multi-page static build. The scene, tokens and fonts are imported from ../design (ADR-016) so
// the site and the video share one source; dev needs permission to serve files outside web/.
export default {
  base: './',
  server: { fs: { allow: ['..'] } },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    rollupOptions: {
      input: {
        home: resolve(import.meta.dirname, 'index.html'),
        run: resolve(import.meta.dirname, 'run/index.html'),
        survival: resolve(import.meta.dirname, 'survival/index.html'),
        about: resolve(import.meta.dirname, 'about/index.html'),
      },
    },
  },
};
