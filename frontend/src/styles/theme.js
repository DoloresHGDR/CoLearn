// Paleta de colores y estilos compartidos de la aplicación
export const colors = {
  primary: "#4F46E5",       // violeta principal
  primaryLight: "#EEF2FF",  // fondo suave para tarjetas
  background: "#F9FAFB",    // fondo general
  white: "#FFFFFF",
  text: "#111827",          // texto principal
  textMuted: "#6B7280",     // texto secundario
  border: "#E5E7EB",
  error: "#EF4444",
  success: "#10B981",
  warning: "#F59E0B",
};

export const typography = {
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: colors.text,
  },
  subtitle: {
    fontSize: 16,
    fontWeight: "600",
    color: colors.text,
  },
  body: {
    fontSize: 14,
    color: colors.text,
  },
  muted: {
    fontSize: 13,
    color: colors.textMuted,
  },
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};

export const radius = {
  sm: 8,
  md: 12,
  lg: 16,
  full: 999,
};
