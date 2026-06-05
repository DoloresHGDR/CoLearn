import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import { joinClass } from "../services/api";
import { colors, spacing, typography } from "../styles/theme";

export default function JoinClassScreen({ navigation }) {
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Inserta el guion automáticamente después de los primeros 3 caracteres
  function handleCodeChange(text) {
    const clean = text.replace(/-/g, "").toLowerCase().slice(0, 6);
    if (clean.length > 3) {
      setCode(clean.slice(0, 3) + "-" + clean.slice(3));
    } else {
      setCode(clean);
    }
  }

  async function handleJoin() {
    if (code.length < 7) {
      setError("El código tiene el formato abc-123.");
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
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={80}
    >
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
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
          onChangeText={handleCodeChange}
          placeholder="abc-123"
          autoCapitalize="none"
          autoCorrect={false}
          maxLength={7}
        />

        <AppButton title="Unirse" onPress={handleJoin} loading={loading} />
      </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  scroll: {
    flexGrow: 1,
    justifyContent: "center",
  },
  content: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
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
