import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { getChatHistory, sendMessage } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

export default function ChatScreen({ route }) {
  const { classId, className } = route.params;
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const flatListRef = useRef(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const history = await getChatHistory(classId);
      setMessages(history);
    } catch (e) {
      // Si falla, empezamos con chat vacío
    } finally {
      setLoading(false);
    }
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    // Mostrar el mensaje del alumno inmediatamente
    const userMsg = { role: "user", content: text, created_at: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSending(true);

    try {
      const data = await sendMessage(classId, text);
      const aiMsg = { role: "assistant", content: data.reply, created_at: new Date().toISOString() };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      const errMsg = { role: "assistant", content: "Hubo un error al contactar al tutor. Intentá de nuevo.", created_at: new Date().toISOString() };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  }

  function renderMessage({ item }) {
    const isUser = item.role === "user";
    return (
      <View style={[styles.bubble, isUser ? styles.bubbleUser : styles.bubbleAI]}>
        {!isUser && <Text style={styles.aiLabel}>Tutor IA</Text>}
        <Text style={[styles.bubbleText, isUser && styles.bubbleTextUser]}>{item.content}</Text>
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
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListEmptyComponent={
          <Text style={styles.emptyChat}>
            Empezá la conversación haciendo una pregunta sobre el texto de la clase.
          </Text>
        }
      />

      <View style={styles.inputRow}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Escribí tu pregunta..."
          placeholderTextColor={colors.textMuted}
          multiline
          maxLength={500}
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || sending) && styles.sendButtonDisabled]}
          onPress={handleSend}
          disabled={!input.trim() || sending}
        >
          {sending
            ? <ActivityIndicator color={colors.white} size="small" />
            : <Text style={styles.sendIcon}>➤</Text>
          }
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
  centered: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
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
  bubbleText: {
    ...typography.body,
    lineHeight: 20,
  },
  bubbleTextUser: {
    color: colors.white,
  },
  emptyChat: {
    ...typography.muted,
    textAlign: "center",
    marginTop: spacing.xl,
    paddingHorizontal: spacing.lg,
  },
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
  sendButtonDisabled: {
    backgroundColor: colors.border,
  },
  sendIcon: {
    color: colors.white,
    fontSize: 16,
  },
});
