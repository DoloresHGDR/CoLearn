import { Ionicons } from "@expo/vector-icons";
import * as DocumentPicker from "expo-document-picker";
import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import TopBar from "../components/TopBar";
import { createClass } from "../services/api";
import { colors, fontFamily, radius } from "../styles/theme";

const FOCUS_OPTS = ["Comprensión literal", "Inferencia", "Vocabulario", "Idea principal", "Resumen"];
const LEVEL = "7mo grado de primaria";
const MAX_MB = 20; // debe coincidir con MAX_FILE_SIZE del backend
const MAX_FOCUS = 3; // el backend solo aplica hasta 3 enfoques en la generacion

export default function CreateClassScreen({ navigation }) {
  const [name, setName] = useState("");
  const [selected, setSelected] = useState(["Inferencia"]);
  const [customOpts, setCustomOpts] = useState([]);
  const [customInput, setCustomInput] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggle(o) {
    setSelected((s) => {
      if (s.includes(o)) return s.filter((x) => x !== o);
      if (s.length >= MAX_FOCUS) {
        setError(`Podés elegir hasta ${MAX_FOCUS} enfoques.`);
        return s;
      }
      setError("");
      return [...s, o];
    });
  }

  // Agrega un enfoque personalizado escrito por el docente. La coma se quita
  // porque los enfoques se guardan separados por comas en el backend.
  function addCustom() {
    const value = customInput.trim().replace(/,/g, "");
    if (!value) return;
    if (selected.length >= MAX_FOCUS) {
      setError(`Podés elegir hasta ${MAX_FOCUS} enfoques.`);
      return;
    }
    const exists = [...FOCUS_OPTS, ...customOpts].some(
      (o) => o.toLowerCase() === value.toLowerCase()
    );
    if (!exists) {
      setCustomOpts((c) => [...c, value]);
      setSelected((s) => [...s, value]);
    }
    setCustomInput("");
  }

  // Elimina por completo un enfoque personalizado (de la lista y de lo elegido).
  function removeCustom(o) {
    setCustomOpts((c) => c.filter((x) => x !== o));
    setSelected((s) => s.filter((x) => x !== o));
  }

  async function pickFile() {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
    });
    if (result.canceled || !result.assets?.length) return;
    const picked = result.assets[0];
    // Validar el peso antes de subir para evitar una espera larga que termina en error
    if (picked.size && picked.size > MAX_MB * 1024 * 1024) {
      setError(`El archivo supera el límite de ${MAX_MB} MB.`);
      return;
    }
    setError("");
    setFile(picked);
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
            {!file ? <Text style={styles.uploadHint}>PDF, DOCX o TXT · máx {MAX_MB} MB</Text> : null}
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
          {customOpts.map((o) => {
            const on = selected.includes(o);
            return (
              <TouchableOpacity
                key={o}
                onPress={() => toggle(o)}
                activeOpacity={0.8}
                style={[styles.chip, styles.chipCustom, { borderColor: on ? colors.primary : colors.border, backgroundColor: on ? colors.primarySoft : colors.surface }]}
              >
                <Text style={[styles.chipText, { color: on ? colors.primary : colors.muted }]}>{o}</Text>
                <TouchableOpacity onPress={() => removeCustom(o)} hitSlop={8}>
                  <Ionicons name="close-circle" size={15} color={on ? colors.primary : colors.faint} />
                </TouchableOpacity>
              </TouchableOpacity>
            );
          })}
        </View>

        {/* enfoque personalizado */}
        <View style={styles.customRow}>
          <View style={[styles.customBox, { borderColor: customInput ? colors.primary : colors.border }]}>
            <TextInput
              style={styles.customInput}
              value={customInput}
              onChangeText={setCustomInput}
              placeholder="Agregar un enfoque propio"
              placeholderTextColor={colors.faint}
              onSubmitEditing={addCustom}
              returnKeyType="done"
              maxLength={40}
            />
          </View>
          <TouchableOpacity
            onPress={addCustom}
            activeOpacity={0.8}
            disabled={!customInput.trim()}
            style={[styles.addBtn, { backgroundColor: customInput.trim() ? colors.primary : colors.border }]}
          >
            <Ionicons name="add" size={22} color="#fff" />
          </TouchableOpacity>
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
  chipCustom: { flexDirection: "row", alignItems: "center", gap: 7, paddingRight: 10 },
  chipText: { fontFamily: fontFamily.sansSemi, fontSize: 13 },
  customRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 4 },
  customBox: { flex: 1, height: 46, borderRadius: radius.input, borderWidth: 1.5, backgroundColor: colors.surface, justifyContent: "center", paddingHorizontal: 14 },
  customInput: { fontFamily: fontFamily.sansRegular, fontSize: 14, color: colors.ink, padding: 0 },
  addBtn: { width: 46, height: 46, borderRadius: radius.input, alignItems: "center", justifyContent: "center" },
  loadingNote: { fontFamily: fontFamily.sansRegular, fontSize: 12.5, color: colors.muted, fontStyle: "italic", textAlign: "center", marginBottom: 12, marginTop: 4 },
});
