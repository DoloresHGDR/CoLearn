import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import { joinClass } from "../services/api";
import { colors, spacing, typography } from "../styles/theme";

export default function JoinClassScreen({ navigation }) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleJoin() {
    if (!code.trim()) {
      setError("Ingresá el código de la clase.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await joinClass(code.trim().toLowerCase());
      navigation.goBack();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={styles.content}>
        <Text style={styles.title}>Unirse a una clase</Text>
        <Text style={styles.subtitle}>
          Pedile el código a tu docente. Tiene el formato{" "}
          <Text style={styles.codeExample}>abc-123</Text>.
        </Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <AppInput
          label="Código de clase"
          value={code}
          onChangeText={setCode}
          placeholder="abc-123"
          autoCapitalize="none"
          autoCorrect={false}
        />

        <AppButton title="Unirse" onPress={handleJoin} loading={loading} />
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    flex: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  title: {
    ...typography.title,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typography.muted,
    marginBottom: spacing.xl,
    lineHeight: 20,
  },
  codeExample: {
    fontWeight: "700",
    color: colors.primary,
    fontFamily: Platform.OS === "ios" ? "Courier" : "monospace",
  },
  error: {
    color: colors.error,
    fontSize: 13,
    marginBottom: spacing.md,
  },
});
