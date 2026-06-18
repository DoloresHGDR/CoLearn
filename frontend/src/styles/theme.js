// Paleta "Ladrillo" y tokens de diseño de CoLearn
// (rediseño del handoff: terracota + ambar + crema calido)

export const colors = {
  // Fondos
  bg: "#FBF2E9",         // fondo general calido crema
  surface: "#FFFDF9",    // cards, inputs, modales
  card2: "#F4E5D6",      // fondo de barras de progreso
  sunk: "#F2E8D8",       // segmented control, pill inputs

  // Primario — Ladrillo
  primary: "#A83E32",
  primaryDeep: "#83291F",
  primarySoft: "#F0DACE",

  // Acento — Ambar
  accent: "#DDA34A",
  accentSoft: "#F7E8CC",

  // Texto
  ink: "#3A211A",
  muted: "#88695C",
  faint: "#B69C8B",

  // Bordes
  border: "#EDDECB",
  line: "#F1E4D3",

  // Estados semanticos (dificultad)
  success: "#5A9152",   // Facil
  amber: "#D08A2A",     // Medio
  error: "#C04E36",     // Dificil / error

  // --- Alias de compatibilidad (pantallas aun no rediseñadas) ---
  background: "#FBF2E9",   // = bg
  white: "#FFFDF9",        // = surface
  text: "#3A211A",         // = ink
  textMuted: "#88695C",    // = muted
  primaryLight: "#F0DACE", // = primarySoft
  warning: "#D08A2A",      // = amber
};

// Familias de fuente (deben coincidir con las cargadas en App.js via useFonts)
export const fontFamily = {
  serifMedium: "Spectral_500Medium",
  serifSemi: "Spectral_600SemiBold",
  serifBold: "Spectral_700Bold",
  sansRegular: "HankenGrotesk_400Regular",
  sansMedium: "HankenGrotesk_500Medium",
  sansSemi: "HankenGrotesk_600SemiBold",
  sansBold: "HankenGrotesk_700Bold",
};

// Escala tipografica (el peso va en el fontFamily, no en fontWeight)
export const type = {
  logo:      { fontFamily: fontFamily.serifSemi, fontSize: 19, letterSpacing: -0.3, color: colors.ink },
  h1:        { fontFamily: fontFamily.serifSemi, fontSize: 30, letterSpacing: -0.6, lineHeight: 34, color: colors.ink },
  h2:        { fontFamily: fontFamily.serifSemi, fontSize: 22, color: colors.ink },
  cardTitle: { fontFamily: fontFamily.serifSemi, fontSize: 15.5, lineHeight: 20, color: colors.ink },
  topBar:    { fontFamily: fontFamily.serifSemi, fontSize: 16.5, lineHeight: 20, color: colors.ink },
  body:      { fontFamily: fontFamily.sansRegular, fontSize: 14, lineHeight: 21, color: colors.ink },
  bodyMd:    { fontFamily: fontFamily.sansRegular, fontSize: 15, color: colors.ink },
  label:     { fontFamily: fontFamily.sansBold, fontSize: 11.5, letterSpacing: 1.2, textTransform: "uppercase", color: colors.muted },
  caption:   { fontFamily: fontFamily.sansRegular, fontSize: 12, color: colors.muted },
  badge:     { fontFamily: fontFamily.sansBold, fontSize: 11, letterSpacing: 0.3, textTransform: "uppercase" },
  btn:       { fontFamily: fontFamily.sansSemi, fontSize: 15 },
  btnSm:     { fontFamily: fontFamily.sansSemi, fontSize: 14 },
};

export const spacing = {
  xs: 4, sm: 8, md: 12, lg: 16, xl: 20, xxl: 24, xxxl: 28, huge: 32, x5: 40, x6: 52,
};

export const radius = {
  sm: 10, md: 13, lg: 14, xl: 18, xxl: 20, pill: 999, full: 999,
  card: 20, btn: 14, input: 13, chip: 8, icon: 13,
};

// Compatibilidad con pantallas que todavia usan typography.*
export const typography = {
  title:    { fontSize: 24, fontWeight: "700", color: colors.ink },
  subtitle: { fontSize: 16, fontWeight: "600", color: colors.ink },
  body:     { fontSize: 14, color: colors.ink },
  muted:    { fontSize: 13, color: colors.muted },
};
