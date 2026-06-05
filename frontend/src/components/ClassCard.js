import React from "react";
import { Alert, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, radius, spacing, typography } from "../styles/theme";

export default function ClassCard({ classroom, isTeacher, onPress, onDelete }) {

  function handleDeletePress() {
    const title = isTeacher ? "Eliminar clase" : "Salir de la clase";
    const message = isTeacher
      ? `¿Estás seguro que querés eliminar "${classroom.name}"? Se borrará para todos los alumnos.`
      : `¿Querés salir de "${classroom.name}"? Perderás tu progreso.`;
    const action = isTeacher ? "Eliminar" : "Salir";

    Alert.alert(title, message, [
      { text: "Cancelar", style: "cancel" },
      { text: action, style: "destructive", onPress: onDelete },
    ]);
  }

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1}>{classroom.name}</Text>
        <View style={styles.headerRight}>
          <View style={styles.badge}>
            <Text style={styles.badgeText}>7mo Primaria</Text>
          </View>
          <TouchableOpacity onPress={handleDeletePress} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
            <Text style={styles.deleteIcon}>{isTeacher ? "🗑" : "✕"}</Text>
          </TouchableOpacity>
        </View>
      </View>

      <Text style={styles.code}>Código: {classroom.join_code}</Text>
      <Text style={styles.focuses} numberOfLines={1}>
        {classroom.focuses.join(" · ")}
      </Text>
      <Text style={styles.action}>
        {isTeacher ? "Ver métricas y preguntas →" : "Entrar a la clase →"}
      </Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.xs,
  },
  headerRight: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
  },
  name: {
    ...typography.subtitle,
    flex: 1,
    marginRight: spacing.sm,
  },
  badge: {
    backgroundColor: colors.primaryLight,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.full,
  },
  badgeText: {
    fontSize: 11,
    color: colors.primary,
    fontWeight: "600",
  },
  deleteIcon: {
    fontSize: 16,
    color: colors.textMuted,
  },
  code: {
    ...typography.muted,
    marginBottom: spacing.xs,
    fontWeight: "600",
    letterSpacing: 0.5,
  },
  focuses: {
    ...typography.muted,
    marginBottom: spacing.sm,
  },
  action: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: "600",
    marginTop: spacing.xs,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
});
