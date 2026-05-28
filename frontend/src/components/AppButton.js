import React from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from "react-native";
import { colors, radius, typography } from "../styles/theme";

// Botón principal reutilizable con estado de carga
export default function AppButton({ title, onPress, loading = false, variant = "primary", style }) {
  const isPrimary = variant === "primary";

  return (
    <TouchableOpacity
      style={[styles.button, isPrimary ? styles.primary : styles.secondary, style]}
      onPress={onPress}
      disabled={loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color={isPrimary ? colors.white : colors.primary} />
      ) : (
        <Text style={[styles.label, !isPrimary && styles.labelSecondary]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
  },
  primary: {
    backgroundColor: colors.primary,
  },
  secondary: {
    backgroundColor: "transparent",
    borderWidth: 1.5,
    borderColor: colors.primary,
  },
  label: {
    ...typography.subtitle,
    color: colors.white,
  },
  labelSecondary: {
    color: colors.primary,
  },
});
