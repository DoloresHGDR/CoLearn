import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import TopBar from "../components/TopBar";
import { login } from "../services/api";
import { colors, fontFamily, spacing } from "../styles/theme";

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
    <View style={styles.container}>
      <TopBar title="Ingresar" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          {error ? <Text style={styles.error}>{error}</Text> : null}

          <AppInput
            label="Correo electrónico"
            value={email}
            onChangeText={setEmail}
            placeholder="nombre@institucion.edu.ar"
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

          <AppButton title="Ingresar" onPress={handleLogin} loading={loading} style={{ marginTop: spacing.sm }} />

          <TouchableOpacity onPress={() => navigation.navigate("Register")} style={{ marginTop: spacing.lg }}>
            <Text style={styles.link}>
              ¿No tenés cuenta? <Text style={styles.linkBold}>Registrate</Text>
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
  link: { textAlign: "center", fontFamily: fontFamily.sansRegular, fontSize: 13.5, color: colors.muted },
  linkBold: { color: colors.primary, fontFamily: fontFamily.sansSemi },
});
