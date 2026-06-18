import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity } from "react-native";
import { colors, radius, type } from "../styles/theme";

// Alias para compatibilidad con pantallas viejas (variant="primary"/"secondary")
const ALIAS = { primary: "fill", secondary: "ghost" };

const VARIANTS = {
  fill:    { box: { backgroundColor: colors.primary }, fg: "#fff" },
  accent:  { box: { backgroundColor: colors.accent }, fg: "#fff" },
  outline: { box: { backgroundColor: colors.surface, borderWidth: 1.5, borderColor: colors.border }, fg: colors.ink },
  ghost:   { box: { backgroundColor: "transparent", borderWidth: 1.5, borderColor: "#A83E3244" }, fg: colors.primary },
  dark:    { box: { backgroundColor: colors.ink }, fg: "#fff" },
};

export default function AppButton({ title, onPress, loading = false, disabled = false, variant = "fill", small = false, icon, style }) {
  const v = ALIAS[variant] || variant;
  const conf = VARIANTS[v] || VARIANTS.fill;
  const lightText = v === "fill" || v === "dark" || v === "accent";

  return (
    <TouchableOpacity
      style={[
        styles.base,
        small && styles.small,
        conf.box,
        v === "fill" && styles.fillShadow,
        (disabled || loading) && styles.disabled,
        style,
      ]}
      onPress={onPress}
      disabled={loading || disabled}
      activeOpacity={0.85}
    >
      {loading ? (
        <ActivityIndicator color={lightText ? "#fff" : colors.primary} />
      ) : (
        <>
          {icon ? <Ionicons name={icon} size={19} color={conf.fg} /> : null}
          <Text style={[type.btn, { color: conf.fg }]}>{title}</Text>
        </>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  base: {
    height: 52,
    borderRadius: radius.btn,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
  },
  small: { height: 44 },
  fillShadow: {
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.25,
    shadowRadius: 14,
    elevation: 4,
  },
  disabled: { opacity: 0.5 },
});
