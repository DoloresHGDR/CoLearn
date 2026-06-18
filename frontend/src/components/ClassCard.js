import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { Alert, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, fontFamily, radius } from "../styles/theme";

// Colores de ícono alternados según la posición de la card
const ACCENTS = [
  { bg: colors.primarySoft, fg: colors.primary },
  { bg: colors.accentSoft, fg: colors.accent },
];

export default function ClassCard({ classroom, isTeacher, index = 0, onPress, onDelete }) {
  const accent = ACCENTS[index % ACCENTS.length];
  const focusText = Array.isArray(classroom.focuses) ? classroom.focuses.join(" · ") : "";

  function handleDeletePress() {
    const title = isTeacher ? "Eliminar clase" : "Salir de la clase";
    const message = isTeacher
      ? `¿Eliminar "${classroom.name}"? Se borra para todos los alumnos.`
      : `¿Salir de "${classroom.name}"? Perdés tu progreso.`;
    Alert.alert(title, message, [
      { text: "Cancelar", style: "cancel" },
      { text: isTeacher ? "Eliminar" : "Salir", style: "destructive", onPress: onDelete },
    ]);
  }

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <View style={[styles.icon, { backgroundColor: accent.bg }]}>
        <Ionicons name="book-outline" size={22} color={accent.fg} />
      </View>

      <View style={styles.body}>
        <Text style={styles.name} numberOfLines={1}>{classroom.name}</Text>
        <View style={styles.metaRow}>
          <Text style={[styles.badge, { color: accent.fg }]}>7.º grado</Text>
          {focusText ? <View style={styles.dot} /> : null}
          {focusText ? <Text style={styles.focus} numberOfLines={1}>{focusText}</Text> : null}
        </View>
        <Text style={styles.action} numberOfLines={1}>
          {isTeacher ? `Código   ${classroom.join_code}` : "Entrar a la clase   →"}
        </Text>
      </View>

      <TouchableOpacity onPress={handleDeletePress} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }} style={styles.del}>
        <Ionicons name={isTeacher ? "trash-outline" : "exit-outline"} size={18} color={colors.faint} />
      </TouchableOpacity>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.card,
    padding: 16,
  },
  icon: { width: 46, height: 46, borderRadius: radius.icon, alignItems: "center", justifyContent: "center" },
  body: { flex: 1, minWidth: 0, gap: 7 },
  name: { fontFamily: fontFamily.serifSemi, fontSize: 15.5, color: colors.ink, lineHeight: 20 },
  metaRow: { flexDirection: "row", alignItems: "center", gap: 7 },
  badge: { fontFamily: fontFamily.sansBold, fontSize: 11, letterSpacing: 0.3, textTransform: "uppercase" },
  dot: { width: 3, height: 3, borderRadius: 2, backgroundColor: colors.faint },
  focus: { flex: 1, fontFamily: fontFamily.sansRegular, fontSize: 12.5, color: colors.muted },
  action: { fontFamily: fontFamily.sansSemi, fontSize: 12.5, color: colors.primary },
  del: { padding: 2 },
});
