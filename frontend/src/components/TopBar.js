import { Ionicons } from "@expo/vector-icons";
import React from "react";
import { StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, fontFamily } from "../styles/theme";

// Barra superior custom (reemplaza el header nativo). Variante oscura para el chat.
export default function TopBar({ title, subtitle, onBack, right, dark = false }) {
  const insets = useSafeAreaInsets();
  const fg = dark ? "#fff" : colors.ink;
  return (
    <View
      style={[
        { paddingTop: insets.top + 4, backgroundColor: dark ? colors.primary : colors.surface },
        !dark && styles.border,
      ]}
    >
      <View style={styles.row}>
        {onBack ? (
          <TouchableOpacity onPress={onBack} hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}>
            <Ionicons name="arrow-back" size={22} color={fg} />
          </TouchableOpacity>
        ) : null}
        <View style={styles.titleWrap}>
          <Text numberOfLines={1} style={[styles.title, { color: fg }]}>{title}</Text>
          {subtitle ? (
            <Text numberOfLines={1} style={[styles.subtitle, { color: dark ? "rgba(255,255,255,0.7)" : colors.muted }]}>
              {subtitle}
            </Text>
          ) : null}
        </View>
        {right}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  border: { borderBottomWidth: 1, borderBottomColor: colors.line },
  row: { flexDirection: "row", alignItems: "center", gap: 12, paddingHorizontal: 16, paddingTop: 10, paddingBottom: 12 },
  titleWrap: { flex: 1, minWidth: 0 },
  title: { fontFamily: fontFamily.serifSemi, fontSize: 16.5, lineHeight: 20 },
  subtitle: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, marginTop: 1 },
});
