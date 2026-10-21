// Shared by the page scripts: the shared episode (built once per page from EXP-002), lazy mounting of
// below-the-fold sections, and moving between chapters with the episode in the URL.
import { loadExperiment, BASE } from './data.js';
import { fail } from './shell.js';
import { ScrollTrigger, REDUCE } from './motion-kit.js';

let episodes = null;
export const getEpisodes = () => (episodes ??= Promise.all([import('./episode.js'), loadExperiment(BASE, 'exp002')])
  .then(([{ createEpisodes }, exp]) => createEpisodes(exp)));

// scroll to a section on this page, or go to the chapter that has it, carrying the episode
export function goTo(sel, chapter) {
  const el = document.querySelector(sel);
  if (el) { el.scrollIntoView({ behavior: matchMedia(REDUCE).matches ? 'auto' : 'smooth' }); return; }
  location.href = `${BASE}${chapter}/${location.search}${sel}`;
}

// A section's code and data are fetched when it comes within half a screen of the viewport, not at
// load. <html data-mounted> counts mounted sections for the QA (design/scripts/lib/mount.mjs).
export function lazySections(sections) {
  const root = document.documentElement;
  root.dataset.sections = String(sections.length);
  root.dataset.mounted = '0';
  const pending = new Map(sections.map(([sel, mount]) => [document.querySelector(sel), mount]));
  const io = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting || !pending.has(entry.target)) continue;
      const mount = pending.get(entry.target);
      pending.delete(entry.target);
      io.unobserve(entry.target);
      mount(entry.target).catch((e) => fail(entry.target, e)).finally(() => {
        root.dataset.mounted = String(+root.dataset.mounted + 1);
        ScrollTrigger.refresh();  // a mounted section changes the page height under every trigger
        if (location.hash && root.dataset.mounted === root.dataset.sections) {
          document.querySelector(location.hash)?.scrollIntoView();  // a deep link lands once laid out
        }
      });
    }
  }, { rootMargin: '50% 0px' });
  pending.forEach((_, el) => io.observe(el));
}
