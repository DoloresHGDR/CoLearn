import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { BASE_URL, getChatHistory, sendMessage } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

export default function ChatScreen({ route }) {
  const { classId, className } = route.params;
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [downloadingFile, setDownloadingFile] = useState(false);
  const flatListRef = useRef(null);

  useEffect(() => {
    initChat();
  }, []);

  async function initChat() {
    try {
      const history = await getChatHistory(classId);
      if (history.length === 0) {
        // Chat vacío → pedir intro al backend
        setSending(true);
        const data = await sendMessage(classId, "__init__");
        setMessages([{ role: "assistant", content: data.reply, created_at: new Date().toISOString() }]);
      } else {
        setMessages(history);
      }
    } catch (e) {
      // Si falla la intro, mostrar mensaje de bienvenida básico
      setMessages([{
        role: "assistant",
        content: "Hola! Cuando estes listo para empezar, escribime y comenzamos con las preguntas.",
        created_at: new Date().toISOString(),
      }]);
    } finally {
      setLoading(false);
      setSending(false);
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg = { role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const data = await sendMessage(classId, text);
      const aiMsg = { role: "assistant", content: data.reply, created_at: new Date().toISOString() };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      const errMsg = {
        role: "assistant",
        content: "Hubo un error al contactar al tutor. Intentá de nuevo.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  }

  // Descarga el archivo con autenticación y lo abre con la app preferida
  async function handleVerTexto() {
    setDownloadingFile(true);
    try {
      const token = await AsyncStorage.getItem("token");
      const url = `${BASE_URL}/classes/${classId}/file`;

      // Primero hacer HEAD para obtener el nombre real del archivo
      const headRes = await fetch(url, {
        method: "GET",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!headRes.ok) {
        Alert.alert("Error", "El archivo no está disponible en el servidor.");
        return;
      }

      // Obtener extensión del Content-Type o Content-Disposition
      const contentType = headRes.headers.get("content-type") || "";
      const disposition = headRes.headers.get("content-disposition") || "";
      let ext = ".pdf";
      if (disposition.includes(".docx")) ext = ".docx";
      else if (disposition.includes(".txt")) ext = ".txt";
      else if (contentType.includes("word")) ext = ".docx";
      else if (contentType.includes("text")) ext = ".txt";

      const localUri = FileSystem.documentDirectory + `texto_clase${ext}`;

      // Descargar con autenticación
      const result = await FileSystem.downloadAsync(url, localUri, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (result.status === 200) {
        await Sharing.shareAsync(result.uri, { mimeType: contentType || "application/pdf" });
      } else {
        Alert.alert("Error", `El servidor respondió con código ${result.status}.`);
      }
    } catch (e) {
      Alert.alert("Error", `No se pudo abrir el archivo: ${e.message}`);
    } finally {
      setDownloadingFile(false);
    }
  }

  function renderMessage({ item }) {
    const isUser = item.role === "user";
    return (
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAI]}>
        {!isUser && <Text style={styles.aiLabel}>Tutor IA</Text>}
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>
          {item.content}
        </Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={90}
    >
      {/* Botón "Ver texto" en la parte superior */}
      <TouchableOpacity
        style={styles.verTextoBar}
        onPress={handleVerTexto}
        disabled={downloadingFile}
      >
        {downloadingFile
          ? <ActivityIndicator color={colors.primary} size="small" />
          : (
            <View style={styles.verTextoContent}>
              <Ionicons name="document-text-outline" size={16} color={colors.primary} />
              <Text style={styles.verTextoText}>Ver texto de la clase</Text>
            </View>
          )
        }
      </TouchableOpacity>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      <View style={[styles.inputRow, { paddingBottom: spacing.md + insets.bottom }]}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Escribí tu respuesta..."
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={500}
          editable={!sending}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || sending) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!input.trim() || sending}
        >
          {sending
            ? <ActivityIndicator color={colors.white} size="small" />
            : <Ionicons name="send" size={18} color={colors.white} />
          }
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  verTextoBar: {
    backgroundColor: colors.white,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
    alignItems: "center",
  },
  verTextoContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  verTextoText: {
    color: colors.primary,
    fontWeight: "600",
    fontSize: 13,
  },
  messageList: {
    padding: spacing.md,
    paddingBottom: spacing.lg,
  },
  bubble: {
    maxWidth: "80%",
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
  },
  bubbleUser: {
    backgroundColor: colors.primary,
    alignSelf: "flex-end",
    borderBottomRightRadius: 4,
  },
  bubbleAI: {
    backgroundColor: colors.white,
    alignSelf: "flex-start",
    borderBottomLeftRadius: 4,
    borderWidth: 1,
    borderColor: colors.border,
  },
  aiLabel: {
    fontSize: 11,
    fontWeight: "700",
    color: colors.primary,
    marginBottom: 4,
  },
  bubbleText: { ...typography.body, lineHeight: 20 },
  bubbleTextUser: { color: colors.white },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: spacing.md,
    backgroundColor: colors.white,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: spacing.sm,
  },
  input: {
    flex: 1,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: 10,
    fontSize: 14,
    color: colors.text,
    maxHeight: 100,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: radius.full,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonDisabled: { backgroundColor: colors.border },
});
