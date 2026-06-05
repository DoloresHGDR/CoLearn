import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import { login } from "../services/api";
import { colors, spacing, typography } from "../styles/theme";

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin() {
    if (!email || !password) {
      setError("Completá todos los campos.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("El email no tiene un formato válido.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      await AsyncStorage.setItem("token", data.access_token);
      navigation.replace("Home");
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
        <Text style={styles.title}>CoLearn</Text>
        <Text style={styles.subtitle}>Iniciá sesión para continuar</Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <AppInput
          label="Email"
          value={email}
          onChangeText={setEmail}
          placeholder="tu@email.com"
          keyboardType="email-address"
          autoCapitalize="none"
        />
        <AppInput
          label="Contraseña"
          value={password}
          onChangeText={setPassword}
          placeholder="••••••••"
          secureTextEntry
        />

        <AppButton title="Ingresar" onPress={handleLogin} loading={loading} style={styles.button} />

        <TouchableOpacity onPress={() => navigation.navigate("Register")}>
          <Text style={styles.link}>¿No tenés cuenta? <Text style={styles.linkBold}>Registrate</Text></Text>
        </TouchableOpacity>
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
    fontSize: 36,
    color: colors.primary,
    marginBottom: spacing.xs,
    textAlign: "center",
  },
  subtitle: {
    ...typography.muted,
    textAlign: "center",
    marginBottom: spacing.xl,
  },
  error: {
    color: colors.error,
    fontSize: 13,
    marginBottom: spacing.md,
    textAlign: "center",
  },
  button: {
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  link: {
    ...typography.muted,
    textAlign: "center",
  },
  linkBold: {
    color: colors.primary,
    fontWeight: "600",
  },
});
