// Test helper: lets Node (type stripping) resolve the extension-less relative imports used by the Vite sources.
import { register } from 'node:module'
register('./resolve-hook.mjs', import.meta.url)
