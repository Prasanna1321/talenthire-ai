// Belongs in: frontend/src/lib/utils.js
// Minimal class-name joiner, compatible with how the imported components
// call cn(...). Deliberately dependency-free (no clsx/tailwind-merge)
// to avoid adding extra npm installs beyond `ogl`.

export function cn(...inputs) {
  return inputs
    .flat(Infinity)
    .filter(Boolean)
    .join(" ");
}