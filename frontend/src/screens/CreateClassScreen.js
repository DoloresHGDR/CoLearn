import * as DocumentPicker from "expo-document-picker";
import React, { useState } from "react";
import { ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import AppInput from "../components/AppInput";
import { createClass } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const DEFAULT_FOCUSES = ["comprensión lectora", "vocabulario", "análisis crítico", "síntesis", "inferencia"];

// Sistema diseñado para 7mo grado de primaria (TIF — Universidad de Mendoza)
const LEVEL = "7mo grado de primaria";

export default function CreateClassScreen({ navigation }) {
  const [name, setName] = useState("");
  const [focuses, setFocuses] = useState(DEFAULT_FOCUSES);
  const [selectedFocuses, setSelectedFocuses] = useState(["comprensión lectora"]);
  const [customFocus, setCustomFocus] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function toggleFocus(focus) {
    setSelectedFocuses((prev) =>
      prev.includes(focus) ? prev.filter((f) => f !== focus) : [...prev, focus]
    );
  }

  function addCustomFocus() {
    const val = customFocus.trim().toLowerCase();
    if (!val) return;
    if (!focuses.includes(val)) {
      setFocuses((prev) => [...prev, val]);
    }
    setSelectedFocuses((prev) => prev.includes(val) ? prev : [...prev, val]);
    setCustomFocus("");
  }

  async function pickFile() {
    const result = await DocumentPicker.getDocumentAsync({
      type: ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"],
    });
    if (!result.canceled && result.assets?.length > 0) {
      setFile(result.assets[0]);
    }
  }

  async function handleCreate() {
    if (!name.trim()) { setError("El nombre de la clase es obligatorio."); return; }
    if (!file) { setError("Seleccioná un archivo."); return; }
    if (selectedFocuses.length === 0) { setError("Elegí al menos un enfoque."); return; }

    setError("");
    setLoading(true);
    try {
      await createClass(name, LEVEL, selectedFocuses, file.uri, file.name, file.mimeType);
      navigation.goBack();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>Nueva clase</Text>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <AppInput
        label="Nombre de la clase"
        value={name}
        onChangeText={setName}
        placeholder="Ej: Fotosíntesis — 5to año"
      />

      {/* Selector de enfoques */}
      <Text style={styles.sectionLabel}>Enfoques pedagógicos</Text>
      <View style={styles.chipRow}>
        {focuses.map((f) => (
          <TouchableOpacity
            key={f}
            style={[styles.chip, selectedFocuses.includes(f) && styles.chipSelected]}
            onPress={() => toggleFocus(f)}
          >
            <Text style={[styles.chipText, selectedFocuses.includes(f) && styles.chipTextSelected]}>
              {f}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Agregar enfoque personalizado */}
      <View style={styles.customFocusRow}>
        <TextInput
          style={styles.customFocusInput}
          value={customFocus}
          onChangeText={setCustomFocus}
          placeholder="Agregar otro enfoque..."
          placeholderTextColor={colors.textMuted}
          onSubmitEditing={addCustomFocus}
          returnKeyType="done"
        />
        <TouchableOpacity style={styles.addButton} onPress={addCustomFocus}>
          <Text style={styles.addButtonText}>+</Text>
        </TouchableOpacity>
      </View>

      {/* Selector de archivo */}
      <Text style={styles.sectionLabel}>Documento</Text>
      <TouchableOpacity style={styles.filePicker} onPress={pickFile}>
        <Text style={file ? styles.fileSelected : styles.filePlaceholder}>
          {file ? `📄 ${file.name}` : "Tocá para seleccionar un archivo (PDF, DOCX, TXT)"}
        </Text>
      </TouchableOpacity>

      {loading && (
        <Text style={styles.loadingNote}>
          La IA está procesando el documento y generando las actividades. Puede tardar unos segundos...
        </Text>
      )}

      <AppButton title="Crear clase" onPress={handleCreate} loading={loading} style={styles.button} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.lg,
  },
  title: {
    ...typography.title,
    marginBottom: spacing.lg,
  },
  error: {
    color: colors.error,
    fontSize: 13,
    marginBottom: spacing.md,
  },
  sectionLabel: {
    ...typography.muted,
    fontWeight: "500",
    marginBottom: spacing.sm,
  },
  chipRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.full,
    borderWidth: 1.5,
    borderColor: colors.border,
    backgroundColor: colors.white,
  },
  chipSelected: {
    borderColor: colors.primary,
    backgroundColor: colors.primaryLight,
  },
  chipText: {
    fontSize: 13,
    color: colors.textMuted,
    fontWeight: "500",
  },
  chipTextSelected: {
    color: colors.primary,
  },
  customFocusRow: {
    flexDirection: "row",
    gap: spacing.sm,
    marginBottom: spacing.lg,
  },
  customFocusInput: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    fontSize: 13,
    color: colors.text,
    backgroundColor: colors.white,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  addButtonText: {
    color: colors.white,
    fontSize: 22,
    fontWeight: "600",
    lineHeight: 26,
  },
  filePicker: {
    borderWidth: 1.5,
    borderColor: colors.border,
    borderStyle: "dashed",
    borderRadius: radius.md,
    padding: spacing.lg,
    alignItems: "center",
    marginBottom: spacing.lg,
    backgroundColor: colors.white,
  },
  filePlaceholder: {
    ...typography.muted,
    textAlign: "center",
  },
  fileSelected: {
    ...typography.body,
    color: colors.primary,
    fontWeight: "500",
  },
  loadingNote: {
    ...typography.muted,
    textAlign: "center",
    marginBottom: spacing.md,
    fontStyle: "italic",
  },
  button: {
    marginTop: spacing.sm,
  },
});
