module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class", // Activer le mode sombre basé sur les classes
  theme: {
    extend: {
      colors: {
        // Accent UNIQUE de l'app = indigo (source de vérité unique du design system).
        primary: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        success: {
          50: "#f0fdf4",
          500: "#22c55e",
          700: "#15803d",
        },
        error: {
          50: "#fef2f2",
          500: "#ef4444",
          700: "#b91c1c",
        },
      },
      // Piles système réelles : Inter/JetBrains Mono n'ont jamais été chargées
      // (aucun @font-face/link), et on évite Google Fonts (fuite réseau vers un
      // tiers, proscrite sur un produit de sécurité). La config reflète donc ce
      // qui est réellement rendu — cf. le body dans index.css.
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "Helvetica Neue",
          "Arial",
          "sans-serif",
        ],
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};
