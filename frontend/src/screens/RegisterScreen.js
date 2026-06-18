import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import TopBar from "../components/TopBar";
import { login, register } from "../services/api";
import { colors, fontFamily, radius, spacing } from "../styles/theme";

const ROLES = [
  { value: "student", label: "Alumno", icon: "book-outline" },
  { value: "teacher", label: "Docente", icon: "people-outline" },
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
    const domain = (email.split("@")[1] || "").toLowerCase();
    const expected = role === "teacher" ? "docente.edu.ar" : "alumno.edu.ar";
    if (domain !== expected) {
      setError(`Usá tu correo institucional: nombre@${expected}`);
      return;
    }
    if (password.length < 6) {
      setError("La contraseña debe tener al menos 6 caracteres.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      await register(name, email, password, role);
      const data = await login(email, password);
      await AsyncStorage.setItem("token", data.access_token);
      navigation.replace("Home");
    } catch (e) {
      setError(e.message || "Error desconocido. Verificá tu conexión.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <View style={styles.container}>
      <TopBar title="Crear cuenta" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {error ? <Text style={styles.error}>{error}</Text> : null}

          {/* Selector de rol */}
          <Text style={styles.roleLabel}>Soy...</Text>
          <View style={styles.roleRow}>
            {ROLES.map((r) => {
              const on = role === r.value;
              return (
                <TouchableOpacity
                  key={r.value}
                  onPress={() => setRole(r.value)}
                  activeOpacity={0.85}
                  style={[
                    styles.roleCard,
                    { borderColor: on ? colors.primary : colors.border, backgroundColor: on ? colors.primarySoft : colors.surface },
                  ]}
                >
                  <Ionicons name={r.icon} size={20} color={on ? colors.primary : colors.muted} />
                  <Text style={[styles.roleText, { color: on ? colors.primary : colors.muted }]}>{r.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <AppInput label="Nombre completo" value={name} onChangeText={setName} placeholder="Tu nombre" />
          <AppInput
            label="Correo electrónico"
            value={email}
            onChangeText={setEmail}
            placeholder={`nombre@${role === "teacher" ? "docente" : "alumno"}.edu.ar`}
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

          <AppButton title="Crear cuenta" onPress={handleRegister} loading={loading} style={{ marginTop: spacing.sm }} />

          <TouchableOpacity onPress={() => navigation.navigate("Login")} style={{ marginTop: spacing.lg }}>
            <Text style={styles.link}>
              ¿Ya tenés cuenta? <Text style={styles.linkBold}>Iniciá sesión</Text>
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingTop: 24 },
  error: { color: colors.error, fontFamily: fontFamily.sansRegular, fontSize: 13, marginBottom: spacing.md, textAlign: "center" },
  roleLabel: { fontFamily: fontFamily.sansSemi, fontSize: 12.5, color: colors.muted, marginBottom: 10 },
  roleRow: { flexDirection: "row", gap: 11, marginBottom: spacing.lg },
  roleCard: { flex: 1, height: 76, borderRadius: radius.lg, borderWidth: 2, alignItems: "center", justifyContent: "center", gap: 7 },
  roleText: { fontFamily: fontFamily.sansSemi, fontSize: 13.5 },
  link: { textAlign: "center", fontFamily: fontFamily.sansRegular, fontSize: 13.5, color: colors.muted },
  linkBold: { color: colors.primary, fontFamily: fontFamily.sansSemi },
});
