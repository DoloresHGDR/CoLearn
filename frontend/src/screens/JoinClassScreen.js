import React, { useState } from "react";
import { KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from "react-native";
import AppButton from "../components/AppButton";
import OwlMascot from "../components/OwlMascot";
import TopBar from "../components/TopBar";
import { joinClass } from "../services/api";
import { colors, fontFamily } from "../styles/theme";

const MONO = Platform.OS === "ios" ? "Courier" : "monospace";

export default function JoinClassScreen({ navigation }) {
  const [code, setCode] = useState("");
  const [focused, setFocused] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function handleCodeChange(text) {
    const clean = text.replace(/-/g, "").toLowerCase().slice(0, 6);
    setCode(clean.length > 3 ? clean.slice(0, 3) + "-" + clean.slice(3) : clean);
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
    <View style={styles.container}>
      <TopBar title="Unirse a una clase" onBack={() => navigation.goBack()} />
      <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"} keyboardVerticalOffset={80}>
        <View style={styles.content}>
          <View style={styles.illoWrap}>
            <View style={styles.illo}><OwlMascot size={56} /></View>
          </View>

          <Text style={styles.title}>Ingresá el código</Text>
          <Text style={styles.desc}>
            Tu docente tiene un código de 7 caracteres, como <Text style={styles.codeExample}>abc-123</Text>
          </Text>

          {error ? <Text style={styles.error}>{error}</Text> : null}

          <View style={[styles.codeBox, { borderColor: focused || code.length > 0 ? colors.primary : colors.border }]}>
            <TextInput
              value={code}
              onChangeText={handleCodeChange}
              onFocus={() => setFocused(true)}
              onBlur={() => setFocused(false)}
              placeholder="abc-123"
              placeholderTextColor={colors.faint}
              autoCapitalize="none"
              autoCorrect={false}
              maxLength={7}
              style={styles.codeInput}
            />
          </View>

          <AppButton title="Unirse" onPress={handleJoin} loading={loading} />
        </View>
      </KeyboardAvoidingView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { flex: 1, paddingHorizontal: 24, paddingTop: 36 },
  illoWrap: { alignItems: "center", marginBottom: 28 },
  illo: { width: 90, height: 90, borderRadius: 28, backgroundColor: colors.primarySoft, alignItems: "center", justifyContent: "center" },
  title: { fontFamily: fontFamily.serifSemi, fontSize: 22, color: colors.ink, textAlign: "center" },
  desc: { fontFamily: fontFamily.sansRegular, fontSize: 14, color: colors.muted, textAlign: "center", marginTop: 7, lineHeight: 21, marginBottom: 28 },
  codeExample: { fontFamily: MONO, fontWeight: "700", color: colors.primary, letterSpacing: 2 },
  error: { color: colors.error, fontFamily: fontFamily.sansRegular, fontSize: 13, textAlign: "center", marginBottom: 12 },
  codeBox: { height: 68, borderRadius: 18, borderWidth: 2, backgroundColor: colors.surface, alignItems: "center", justifyContent: "center", marginBottom: 16 },
  codeInput: { fontFamily: MONO, fontSize: 28, fontWeight: "700", color: colors.ink, letterSpacing: 5, textAlign: "center", width: "100%" },
});
