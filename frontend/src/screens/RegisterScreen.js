import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import { login, register } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const ROLES = [
  { value: "student", label: "Alumno" },
  { value: "teacher", label: "Docente" },
];

export default function RegisterScreen({ navigation }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("student");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleRegister() {
    if (!name || !email || !password) {
      setError("Completá todos los campos.");
      return;
    }
    if (name.trim().length < 2) {
      setError("El nombre debe tener al menos 2 caracteres.");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError("El email no tiene un formato válido.");
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      // Registrar y luego hacer login automáticamente
      await register(name, email, password, role);
      const data = await login(email, password);
      await AsyncStorage.setItem("token", data.access_token);
      navigation.replace("Home");
    } catch (e) {
      // Mostrar mensaje de error descriptivo
      const msg = e.message || "Error desconocido. Verificá tu conexión.";
      setError(msg);
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
        <Text style={styles.title}>Crear cuenta</Text>
        <Text style={styles.subtitle}>Ingresá tus datos para registrarte</Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <AppInput label="Nombre completo" value={name} onChangeText={setName} placeholder="Tu nombre" />
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

        {/* Selector de rol */}
        <Text style={styles.roleLabel}>¿Cuál es tu rol?</Text>
        <View style={styles.roleRow}>
          {ROLES.map((r) => (
            <TouchableOpacity
              key={r.value}
              style={[styles.roleOption, role === r.value && styles.roleSelected]}
              onPress={() => setRole(r.value)}
            >
              <Text style={[styles.roleText, role === r.value && styles.roleTextSelected]}>
                {r.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <AppButton title="Registrarme" onPress={handleRegister} loading={loading} style={styles.button} />

        <TouchableOpacity onPress={() => navigation.navigate("Login")}>
          <Text style={styles.link}>¿Ya tenés cuenta? <Text style={styles.linkBold}>Iniciá sesión</Text></Text>
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
    marginBottom: spacing.xs,
  },
  subtitle: {
    ...typography.muted,
    marginBottom: spacing.xl,
  },
  error: {
    color: colors.error,
    fontSize: 13,
    marginBottom: spacing.md,
    textAlign: "center",
  },
  roleLabel: {
    ...typography.muted,
    fontWeight: "500",
    marginBottom: spacing.sm,
  },
  roleRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  roleOption: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: radius.sm,
    borderWidth: 1.5,
    borderColor: colors.border,
    alignItems: "center",
  },
  roleSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  roleText: {
    ...typography.body,
    fontWeight: "600",
    color: colors.textMuted,
  },
  roleTextSelected: {
    color: colors.primary,
  },
  button: {
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
