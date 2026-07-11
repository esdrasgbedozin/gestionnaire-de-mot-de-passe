import zxcvbn from 'zxcvbn';

/**
 * Moteur de force UNIQUE de l'app (critique P1 : avant, 4-5 algorithmes
 * incohérents donnaient "Moyen / Medium / 62%" pour le même mot de passe).
 *
 * Adossé à zxcvbn (déjà une dépendance, jusque-là inutilisée) — la même mesure
 * que le backend (cf. gate M6). Échelle canonique : score 0-4, 3 couleurs
 * sémantiques (red/yellow/green) + gray pour le vide. Plus d'orange/emerald
 * décoratifs (fuite de palette supprimée).
 */

const LEVELS = [
  { label: 'Very weak', color: 'red' },
  { label: 'Weak', color: 'red' },
  { label: 'Fair', color: 'yellow' },
  { label: 'Strong', color: 'green' },
  { label: 'Very strong', color: 'green' },
];

const EMPTY = { score: -1, label: 'None', color: 'gray', percent: 0, feedback: [] };

/**
 * Évalue un mot de passe en clair.
 * @returns {{ score:number, label:string, color:string, percent:number, feedback:string[] }}
 */
export function evaluateStrength(password) {
  if (!password) return { ...EMPTY };
  // zxcvbn est super-linéaire ; on borne l'entrée pour éviter un gel du thread UI
  // sur un collage très long (un mot de passe > 128 car. est déjà au maximum).
  const { score, feedback } = zxcvbn(password.slice(0, 128)); // score ∈ [0,4]
  const meta = LEVELS[score] || LEVELS[0];
  const suggestions = [feedback && feedback.warning, ...((feedback && feedback.suggestions) || [])].filter(
    Boolean,
  );
  return {
    score,
    label: meta.label,
    color: meta.color,
    percent: (score + 1) * 20, // 20..100
    feedback: suggestions,
  };
}

/**
 * Mappe le score de force stocké par le backend (1-5, zxcvbn+1 cf. M6) sur la
 * MÊME échelle, pour que la carte affiche le même vocabulaire que les meters.
 */
export function strengthFromBackendScore(backendScore) {
  const s = Math.max(0, Math.min(4, (Number(backendScore) || 1) - 1));
  const meta = LEVELS[s];
  return { score: s, label: meta.label, color: meta.color, percent: (s + 1) * 20, feedback: [] };
}

/** True si le mot de passe atteint le seuil "fort" exigé (aligné backend M6 : zxcvbn ≥ 3). */
export function meetsStrengthRequirement(password) {
  return evaluateStrength(password).score >= 3;
}
