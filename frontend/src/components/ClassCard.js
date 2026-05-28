import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { colors, radius, spacing, typography } from "../styles/theme";

// Tarjeta que muestra la información de una clase
export default function ClassCard({ classroom, onPress, onQuestionsPress }) {
  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.85}>
      <View style={styles.header}>
        <Text style={styles.name} numberOfLines={1}>{classroom.name}</Text>
        <View style={styles.badge}>
          <Text style={styles.badgeText}>{classroom.level}</Text>
        </View>
      </View>
      <Text style={styles.code}>Código: {classroom.join_code}</Text>
      <Text style={styles.focuses} numberOfLines={1}>
        {classroom.focuses.join(" · ")}
      </Text>
      {onQuestionsPress && (
        <TouchableOpacity style={styles.questionsLink} onPress={onQuestionsPress}>
          <Text style={styles.questionsLinkText}>Ver preguntas →</Text>
        </TouchableOpacity>
      )}
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
    textTransform: "capitalize",
  },
  code: {
    ...typography.muted,
    marginBottom: spacing.xs,
    fontWeight: "600",
    letterSpacing: 0.5,
  },
  focuses: {
    ...typography.muted,
  },
  questionsLink: {
    marginTop: spacing.sm,
    paddingTop: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  questionsLinkText: {
    fontSize: 13,
    color: colors.primary,
    fontWeight: "600",
  },
});
