// Exécute `fn` sur chaque item avec une concurrence BORNÉE (au plus `limit` en
// vol à tout instant). Préserve l'ordre des résultats et remonte l'avancement
// via `onProgress(done)`. Utilisé par SecurityCheck pour déchiffrer le coffre
// sans burst au-delà du rate-limit C7 des GET déchiffrants (paralléliser ne
// change pas le nombre total de requêtes, seulement leur cadence).
export async function mapWithConcurrency(items, limit, fn, onProgress) {
  const results = new Array(items.length);
  let next = 0;
  let done = 0;
  const worker = async () => {
    while (next < items.length) {
      const i = next++;
      results[i] = await fn(items[i], i);
      done += 1;
      onProgress?.(done);
    }
  };
  const size = Math.min(Math.max(1, limit), items.length);
  const pool = Array.from({ length: size }, worker);
  await Promise.all(pool);
  return results;
}
