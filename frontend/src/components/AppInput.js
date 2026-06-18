import React, { useState } from "react";
import { StyleSheet, Text, TextInput, View } from "react-native";
import { colors, fontFamily, radius, spacing } from "../styles/theme";

// Campo de texto con etiqueta. El borde se resalta en primary al enfocar.
export default function AppInput({ label, error, style, onFocus, onBlur, ...props }) {
  const [focused, setFocused] = useState(false);
  const borderColor = error ? colors.error : focused ? colors.primary : colors.border;

  return (
    <View style={[styles.container, style]}>
      {label ? <Text style={styles.label}>{label}</Text> : null}
      <View style={[styles.box, { borderColor }]}>
        <TextInput
          style={styles.input}
          placeholderTextColor={colors.faint}
          onFocus={(e) => { setFocused(true); onFocus && onFocus(e); }}
          onBlur={(e) => { setFocused(false); onBlur && onBlur(e); }}
          {...props}
        />
      </View>
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: spacing.lg },
  label: {
    fontFamily: fontFamily.sansSemi,
    fontSize: 12.5,
    color: colors.muted,
    marginBottom: 5,
  },
  box: {
    height: 50,
    borderRadius: radius.input,
    borderWidth: 1.5,
    backgroundColor: colors.surface,
    justifyContent: "center",
    paddingHorizontal: 16,
  },
  input: {
    fontFamily: fontFamily.sansRegular,
    fontSize: 15,
    color: colors.ink,
    padding: 0,
  },
  error: {
    fontFamily: fontFamily.sansRegular,
    fontSize: 12,
    color: colors.error,
    marginTop: spacing.xs,
  },
});
