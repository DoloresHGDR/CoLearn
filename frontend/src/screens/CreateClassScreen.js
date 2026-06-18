import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import TopBar from "../components/TopBar";
import { createClass } from "../services/api";
import { colors, fontFamily, radius } from "../styles/theme";

const FOCUS_OPTS = ["Comprensión literal", "Inferencia", "Vocabulario", "Idea principal", "Resumen"];
const LEVEL = "7mo grado de primaria";

export default function CreateClassScreen({ navigation }) {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState(["Inferencia"]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggle(o) {
    setSelected((s) => (s.includes(o) ? s.filter((x) => x !== o) : [...s, o]));
  }

  async function pickFile() {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
    });
    if (!result.canceled && result.assets?.length > 0) setFile(result.assets[0]);
  }

  async function handleCreate() {
    if (!name.trim()) { setError("El título es obligatorio."); return; }
    if (!file) { setError("Subí un documento."); return; }
    if (selected.length === 0) { setError("Elegí al menos un enfoque."); return; }
    setError("");
    setLoading(true);
    try {
      await createClass(name, LEVEL, selected, file.uri, file.name, file.mimeType);
      navigation.goBack();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const canCreate = !!name.trim() && !!file;

  return (
    <View style={styles.container}>
      <TopBar title="Crear clase" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {error ? <Text style={styles.error}>{error}</Text> : null}

        <AppInput label="Título del texto" value={name} onChangeText={setName} placeholder="Ej: El viaje de las ballenas grises" />

        {/* upload */}
        <Text style={styles.label}>Texto base (PDF, DOCX o TXT)</Text>
        <TouchableOpacity
          onPress={pickFile}
          activeOpacity={0.8}
          style={[styles.upload, { borderColor: file ? colors.primary : colors.border, backgroundColor: file ? colors.primarySoft : colors.surface }]}
        >
          <Ionicons name="document-outline" size={22} color={file ? colors.primary : colors.faint} />
          <View style={{ minWidth: 0 }}>
            <Text style={[styles.uploadTitle, { color: file ? colors.primary : colors.faint }]} numberOfLines={1}>
              {file ? file.name : "Subir documento"}
            </Text>
            {!file ? <Text style={styles.uploadHint}>PDF, DOCX o TXT · máx 10 MB</Text> : null}
          </View>
        </TouchableOpacity>

        {/* approaches */}
        <Text style={[styles.label, { marginTop: 20 }]}>Enfoques pedagógicos</Text>
        <View style={styles.chipRow}>
          {FOCUS_OPTS.map((o) => {
            const on = selected.includes(o);
            return (
              <TouchableOpacity
                key={o}
                onPress={() => toggle(o)}
                activeOpacity={0.8}
                style={[styles.chip, { borderColor: on ? colors.primary : colors.border, backgroundColor: on ? colors.primarySoft : colors.surface }]}
              >
                <Text style={[styles.chipText, { color: on ? colors.primary : colors.muted }]}>{o}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        {loading ? (
          <Text style={styles.loadingNote}>La IA está procesando el documento y generando las preguntas. Puede tardar unos segundos…</Text>
        ) : null}

        <AppButton title="Crear clase" onPress={handleCreate} loading={loading} disabled={!canCreate} style={{ marginTop: 8 }} />
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  content: { padding: 20, paddingTop: 24 },
  error: { color: colors.error, fontFamily: fontFamily.sansRegular, fontSize: 13, marginBottom: 12 },
  label: { fontFamily: fontFamily.sansSemi, fontSize: 12.5, color: colors.muted, marginBottom: 8 },
  upload: { height: 82, borderRadius: radius.lg, borderWidth: 2, borderStyle: "dashed", flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 11, paddingHorizontal: 16 },
  uploadTitle: { fontFamily: fontFamily.sansSemi, fontSize: 14 },
  uploadHint: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, color: colors.faint, marginTop: 2 },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginBottom: 8 },
  chip: { paddingVertical: 8, paddingHorizontal: 14, borderRadius: radius.sm, borderWidth: 1.5 },
  chipText: { fontFamily: fontFamily.sansSemi, fontSize: 13 },
  loadingNote: { fontFamily: fontFamily.sansRegular, fontSize: 12.5, color: colors.muted, fontStyle: "italic", textAlign: "center", marginBottom: 12, marginTop: 4 },
});
