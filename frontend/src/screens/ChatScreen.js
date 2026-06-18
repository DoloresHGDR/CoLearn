import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
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
import OwlMascot from "../components/OwlMascot";
import TopBar from "../components/TopBar";
import { BASE_URL, getChatHistory, sendMessage } from "../services/api";
import { colors, fontFamily } from "../styles/theme";

// Punto que sube y baja con retraso escalonado (animacion "pensando").
function ThinkingDot({ delay }) {
  const bounce = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.timing(bounce, { toValue: -5, duration: 300, useNativeDriver: true }),
        Animated.timing(bounce, { toValue: 0,  duration: 300, useNativeDriver: true }),
        Animated.delay(600 - delay),
      ])
    ).start();
  }, [bounce, delay]);
  return <Animated.View style={[styles.dot, { transform: [{ translateY: bounce }] }]} />;
}

function ThinkingBubble() {
  return (
    <View style={styles.aiRow}>
      <View style={styles.avatarSlot}>
        <OwlMascot size={30} animated />
      </View>
      <View>
        <Text style={styles.aiLabel}>Tutor IA</Text>
        <View style={[styles.aiBubble, styles.thinkBubble]}>
          <ThinkingDot delay={0} />
          <ThinkingDot delay={200} />
          <ThinkingDot delay={400} />
        </View>
      </View>
    </View>
  );
}

export default function ChatScreen({ route, navigation }) {
  const { classId, className } = route.params;
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [downloadingFile, setDownloadingFile] = useState(false);
  const flatListRef = useRef(null);

  useEffect(() => { initChat(); }, []);

  async function initChat() {
    try {
      const history = await getChatHistory(classId);
      if (history.length === 0) {
        setSending(true);
        const data = await sendMessage(classId, "__init__");
        setMessages([{ role: "assistant", content: data.reply, created_at: new Date().toISOString() }]);
      } else {
        setMessages(history);
      }
    } catch (e) {
      setMessages([{
        role: "assistant",
        content: "Hola! Cuando estés listo para empezar, escribime y comenzamos con las preguntas.",
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
    setMessages((prev) => [...prev, { role: "user", content: text, created_at: new Date().toISOString() }]);
    setInput("");
    setSending(true);
    try {
      const data = await sendMessage(classId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply, created_at: new Date().toISOString() }]);
    } catch (e) {
      setMessages((prev) => [...prev, {
        role: "assistant",
        content: "Hubo un error al contactar al tutor. Intentá de nuevo.",
        created_at: new Date().toISOString(),
      }]);
    } finally {
      setSending(false);
    }
  }

  async function handleVerTexto() {
    setDownloadingFile(true);
    try {
      const token = await AsyncStorage.getItem("token");
      const url = `${BASE_URL}/classes/${classId}/file`;
      const headRes = await fetch(url, { method: "GET", headers: { Authorization: `Bearer ${token}` } });
      if (!headRes.ok) {
        Alert.alert("Error", "El archivo no está disponible en el servidor.");
        return;
      }
      const contentType = headRes.headers.get("content-type") || "";
      const disposition = headRes.headers.get("content-disposition") || "";
      let ext = ".pdf";
      if (disposition.includes(".docx")) ext = ".docx";
      else if (disposition.includes(".txt")) ext = ".txt";
      else if (contentType.includes("word")) ext = ".docx";
      else if (contentType.includes("text")) ext = ".txt";
      const localUri = FileSystem.documentDirectory + `texto_clase${ext}`;
      const result = await FileSystem.downloadAsync(url, localUri, { headers: { Authorization: `Bearer ${token}` } });
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

  function renderMessage({ item, index }) {
    const isUser = item.role === "user";
    if (isUser) {
      return (
        <View style={styles.userWrap}>
          <View style={styles.userBubble}>
            <Text style={styles.userText}>{item.content}</Text>
          </View>
        </View>
      );
    }
    const prev = messages[index - 1];
    const showAvatar = !prev || prev.role === "user";
    return (
      <View style={styles.aiRow}>
        <View style={styles.avatarSlot}>{showAvatar ? <OwlMascot size={30} /> : null}</View>
        <View style={{ flex: 1 }}>
          {showAvatar ? <Text style={styles.aiLabel}>Tutor IA</Text> : null}
          <View style={styles.aiBubble}>
            <Text style={styles.aiText}>{item.content}</Text>
          </View>
        </View>
      </View>
    );
  }

  const textoChip = (
    <TouchableOpacity onPress={handleVerTexto} disabled={downloadingFile} style={styles.textoChip}>
      {downloadingFile ? (
        <ActivityIndicator color="#fff" size="small" />
      ) : (
        <>
          <Ionicons name="document-text-outline" size={15} color={colors.accent} />
          <Text style={styles.textoChipText}>Texto</Text>
        </>
      )}
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <TopBar title={className} subtitle="Tutor de comprensión lectora" onBack={() => navigation.goBack()} dark right={textoChip} />
        <View style={styles.centered}><ActivityIndicator color={colors.primary} /></View>
      </View>
    );
  }

  return (
    <KeyboardAvoidingView style={styles.container} behavior="padding" keyboardVerticalOffset={0}>
      <TopBar title={className} subtitle="Tutor de comprensión lectora" onBack={() => navigation.goBack()} dark right={textoChip} />

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListFooterComponent={sending ? <ThinkingBubble /> : null}
      />

      <View style={[styles.inputRow, { paddingBottom: 14 + insets.bottom }]}>
        <View style={styles.inputBox}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Escribí tu respuesta…"
            placeholderTextColor={colors.faint}
            multiline
            maxLength={500}
            editable={!sending}
          />
        </View>
        <TouchableOpacity
          style={[styles.sendBtn, (!input.trim() || sending) && { opacity: 0.5 }]}
          onPress={handleSend}
          disabled={!input.trim() || sending}
        >
          {sending ? <ActivityIndicator color="#fff" size="small" /> : <Ionicons name="send" size={18} color="#fff" />}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  textoChip: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 6, paddingHorizontal: 11, borderRadius: 10, backgroundColor: "rgba(255,255,255,0.16)" },
  textoChipText: { fontFamily: fontFamily.sansSemi, fontSize: 12.5, color: "#fff" },
  messageList: { padding: 16, paddingBottom: 12, gap: 14 },
  aiRow: { flexDirection: "row", gap: 9, alignItems: "flex-end", maxWidth: "88%" },
  avatarSlot: { width: 30 },
  aiLabel: { fontFamily: fontFamily.sansBold, fontSize: 11.5, color: colors.primary, marginBottom: 5 },
  aiBubble: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 18, borderTopLeftRadius: 4, paddingVertical: 11, paddingHorizontal: 14 },
  aiText: { fontFamily: fontFamily.sansRegular, fontSize: 14, lineHeight: 21, color: colors.ink },
  userWrap: { alignItems: "flex-end" },
  userBubble: { maxWidth: "82%", backgroundColor: colors.primary, borderRadius: 18, borderTopRightRadius: 4, paddingVertical: 11, paddingHorizontal: 14 },
  userText: { fontFamily: fontFamily.sansRegular, fontSize: 14, lineHeight: 21, color: "#fff" },
  inputRow: { flexDirection: "row", alignItems: "flex-end", gap: 10, paddingHorizontal: 14, paddingTop: 10, backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.line },
  inputBox: { flex: 1, minHeight: 46, maxHeight: 110, borderRadius: 23, backgroundColor: colors.bg, borderWidth: 1, borderColor: colors.border, justifyContent: "center", paddingHorizontal: 18 },
  input: { fontFamily: fontFamily.sansRegular, fontSize: 14, color: colors.ink, paddingVertical: Platform.OS === "ios" ? 12 : 8 },
  sendBtn: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center", shadowColor: colors.accent, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.33, shadowRadius: 12, elevation: 4 },
  thinkBubble: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 14 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.faint },
});
