/**
 * Classe une erreur axios en une catégorie actionnable + un message en clair.
 *
 * Objectif (critique P0) : sur un gestionnaire de mots de passe, un échec brut
 * (« Failed to decrypt », un 500, un toast générique) se lit comme une PERTE de
 * données et détruit la confiance. On distingue réseau / session / verrouillage /
 * déchiffrement / serveur pour pouvoir proposer la bonne récupération, et on ne
 * fuit JAMAIS un message serveur brut vers l'utilisateur.
 *
 * @returns {{ kind: string, message: string, retryable: boolean }}
 */
export function classifyApiError(
  error,
  fallback = "Something went wrong. Please try again.",
) {
  // Pas de réponse HTTP = coupure réseau / timeout / serveur injoignable.
  if (!error || !error.response) {
    return {
      kind: "network",
      message: "Can't reach the server — check your connection and try again.",
      retryable: true,
    };
  }

  const status = error.response.status;

  switch (status) {
    case 401:
      return {
        kind: "auth",
        message:
          "Your session expired. Please sign in again to unlock your vault.",
        retryable: false,
      };
    case 403:
      return {
        kind: "auth",
        message: "You don't have permission to do that.",
        retryable: false,
      };
    case 404:
      return {
        kind: "notfound",
        message: "This entry no longer exists.",
        retryable: false,
      };
    case 423:
      return {
        kind: "locked",
        message: "Your vault is locked. Reconnect to unlock it.",
        retryable: false,
      };
    case 429:
      return {
        kind: "ratelimit",
        message: "Too many attempts. Wait a moment, then try again.",
        retryable: true,
      };
    default:
      if (status >= 500) {
        const serverMsg = error.response.data && error.response.data.error;
        // Le backend renvoie 500 + « Unable to decrypt password » sur un échec GCM.
        if (serverMsg && /decrypt/i.test(serverMsg)) {
          return {
            kind: "decrypt",
            message:
              "This entry couldn't be decrypted right now. Your session may have changed — reopen your vault and try again.",
            retryable: true,
          };
        }
        return {
          kind: "server",
          message: "The server hit an error. Please try again in a moment.",
          retryable: true,
        };
      }
      // 4xx divers : on peut afficher un message serveur court s'il existe, sinon fallback.
      return {
        kind: "unknown",
        message: (error.response.data && error.response.data.error) || fallback,
        retryable: false,
      };
  }
}

export default classifyApiError;
