import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
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
import { BASE_URL, getChatHistory, getProgress, sendMessage, submitFeedback } from "../services/api";
import { colors, fontFamily } from "../styles/theme";

// Punto que sube y baja con retraso escalonado (animacion "pensando").
function ThinkingDot({ delay }) {
  const bounce = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    // Periodo total constante (1200 ms) para que los tres puntos queden sincronizados.
    Animated.loop(
      Animated.sequence([
        Animated.delay(delay),
        Animated.timing(bounce, { toValue: -4, duration: 300, useNativeDriver: true }),
        Animated.timing(bounce, { toValue: 0,  duration: 300, useNativeDriver: true }),
        Animated.delay(600 - delay),
      ])
    ).start();
  }, [bounce, delay]);
  return <Animated.View style={[styles.dot, { transform: [{ translateY: bounce }] }]} />;
}

// Burbuja "pensando". Si la espera se hace larga, muestra un aviso para que el alumno no crea que se colgo.
function ThinkingBubble({ slow }) {
  return (
    <MessageIn>
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
          {slow ? <Text style={styles.slowText}>Pensando un poco más…</Text> : null}
        </View>
      </View>
    </MessageIn>
  );
}

// Envuelve cada burbuja con una entrada suave (fade + leve subida) al montarse.
function MessageIn({ children }) {
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    Animated.timing(anim, {
      toValue: 1,
      duration: 260,
      easing: Easing.bezier(0.2, 0.7, 0.3, 1),
      useNativeDriver: true,
    }).start();
  }, [anim]);
  const translateY = anim.interpolate({ inputRange: [0, 1], outputRange: [8, 0] });
  return (
    <Animated.View style={{ opacity: anim, transform: [{ translateY }] }}>
      {children}
    </Animated.View>
  );
}

// Barra de avance bajo el TopBar: el ancho refleja preguntas cerradas / total.
// Cuando el avance sube, un destello breve refuerza la sensacion de progreso.
function ProgressBar({ ratio }) {
  const w = useRef(new Animated.Value(ratio)).current;
  const glow = useRef(new Animated.Value(0)).current;
  const prev = useRef(ratio);
  useEffect(() => {
    Animated.timing(w, { toValue: ratio, duration: 400, easing: Easing.out(Easing.ease), useNativeDriver: false }).start();
    if (ratio > prev.current) {
      Animated.sequence([
        Animated.timing(glow, { toValue: 0.7, duration: 160, useNativeDriver: false }),
        Animated.timing(glow, { toValue: 0,   duration: 520, useNativeDriver: false }),
      ]).start();
    }
    prev.current = ratio;
  }, [ratio, w, glow]);
  const width = w.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] });
  return (
    <View style={styles.progressTrack}>
      <Animated.View style={[styles.progressFill, { width }]} />
      <Animated.View style={[styles.progressGlow, { width, opacity: glow }]} />
    </View>
  );
}

const makeId = () => `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

export default function ChatScreen({ route, navigation }) {
  const { classId, className } = route.params;
  const insets = useSafeAreaInsets();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [slowWait, setSlowWait] = useState(false);
  const [downloadingFile, setDownloadingFile] = useState(false);
  const [progress, setProgress] = useState({ answered: 0, total: 0 });
  const [showComplete, setShowComplete] = useState(false);
  const [feedbackVoted, setFeedbackVoted] = useState(false);
  const [connError, setConnError] = useState(false);
  const flatListRef = useRef(null);

  async function handleVote(helpful) {
    setFeedbackVoted(true); // optimista: el voto no es crítico
    try {
      await submitFeedback(classId, helpful);
    } catch (e) {
      // si falla, no molestamos al alumno con un error por una encuesta
    }
  }
  const prevAnsweredRef = useRef(null); // null = aún no inicializado

  useEffect(() => { initChat(); }, []);

  async function loadProgress() {
    try {
      const p = await getProgress(classId);
      setProgress(p);
      const prevA = prevAnsweredRef.current;
      // Mostrar el festejo solo cuando se CRUZA al total en esta sesion,
      // no al abrir una actividad que ya estaba terminada.
      if (prevA !== null && p.total > 0 && p.answered === p.total && prevA < p.total) {
        setShowComplete(true);
      }
      prevAnsweredRef.current = p.answered;
    } catch (e) {
      // si falla, la barra simplemente no se actualiza
    }
  }

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
      setConnError(false);
      loadProgress();
    } catch (e) {
      setConnError(true);
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

  // Envia un mensaje nuevo, o reintenta uno que habia fallado (retryMsg).
  async function handleSend(retryMsg) {
    const text = (retryMsg ? retryMsg.content : input).trim();
    if (!text || sending) return;

    let msgId;
    if (retryMsg) {
      msgId = retryMsg.id;
      setMessages((prev) => prev.map((m) => (m.id === msgId ? { ...m, failed: false } : m)));
    } else {
      msgId = makeId();
      setMessages((prev) => [...prev, { role: "user", content: text, created_at: new Date().toISOString(), id: msgId, failed: false }]);
      setInput("");
    }

    setSending(true);
    const slowTimer = setTimeout(() => setSlowWait(true), 8000);
    try {
      const data = await sendMessage(classId, text);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply, created_at: new Date().toISOString() }]);
      setConnError(false);
      loadProgress();
    } catch (e) {
      // No perdemos el mensaje del alumno: queda marcado para reintentar.
      setConnError(true);
      setMessages((prev) => prev.map((m) => (m.id === msgId ? { ...m, failed: true } : m)));
    } finally {
      clearTimeout(slowTimer);
      setSlowWait(false);
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
        <MessageIn>
          <View style={styles.userWrap}>
            <View style={[styles.userBubble, item.failed && styles.userBubbleFailed]}>
              <Text style={styles.userText}>{item.content}</Text>
            </View>
            {item.failed ? (
              <TouchableOpacity style={styles.retryRow} onPress={() => handleSend(item)} disabled={sending}>
                <Ionicons name="refresh" size={13} color={colors.error} />
                <Text style={styles.retryText}>No se envió · Reintentar</Text>
              </TouchableOpacity>
            ) : null}
          </View>
        </MessageIn>
      );
    }
    const prev = messages[index - 1];
    const showAvatar = !prev || prev.role === "user";
    return (
      <MessageIn>
        <View style={styles.aiRow}>
          <View style={styles.avatarSlot}>{showAvatar ? <OwlMascot size={30} /> : null}</View>
          <View style={{ flex: 1 }}>
            {showAvatar ? <Text style={styles.aiLabel}>Tutor IA</Text> : null}
            <View style={styles.aiBubble}>
              <Text style={styles.aiText}>{item.content}</Text>
            </View>
          </View>
        </View>
      </MessageIn>
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

      {connError ? (
        <View style={styles.offlineBanner}>
          <Ionicons name="cloud-offline-outline" size={14} color="#fff" />
          <Text style={styles.offlineText}>Sin conexión. Revisá tu internet e intentá de nuevo.</Text>
        </View>
      ) : null}

      {progress.total > 0 && <ProgressBar ratio={Math.max(0, Math.min(1, progress.answered / progress.total))} />}

      {progress.current_question ? (
        <View style={styles.currentQ}>
          <Ionicons name="bookmark" size={14} color={colors.primary} style={{ marginTop: 1 }} />
          <View style={{ flex: 1 }}>
            <Text style={styles.currentQLabel}>Pregunta actual</Text>
            <Text style={styles.currentQText} numberOfLines={3}>{progress.current_question}</Text>
          </View>
        </View>
      ) : null}

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(_, i) => String(i)}
        renderItem={renderMessage}
        contentContainerStyle={styles.messageList}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
        ListFooterComponent={sending ? <ThinkingBubble slow={slowWait} /> : null}
      />

      {input.length > 400 ? (
        <Text style={styles.counter}>{input.length}/500</Text>
      ) : null}

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
          onPress={() => handleSend()}
          disabled={!input.trim() || sending}
        >
          {sending ? <ActivityIndicator color="#fff" size="small" /> : <Ionicons name="send" size={18} color="#fff" />}
        </TouchableOpacity>
      </View>

      {showComplete ? (
        <View style={styles.completeOverlay}>
          <MessageIn>
            <View style={styles.completeCard}>
              <OwlMascot size={84} animated />
              <Text style={styles.completeTitle}>¡Lo lograste!</Text>
              <Text style={styles.completeText}>
                Completaste todas las preguntas. ¡Gran trabajo! Desde ahora pasás al modo de charla libre: preguntame lo que quieras sobre el texto y ya no afecta tu nota.
              </Text>
              {feedbackVoted ? (
                <Text style={styles.completeThanks}>¡Gracias por tu opinión! 🙌</Text>
              ) : (
                <View style={styles.voteBlock}>
                  <Text style={styles.voteQ}>¿Te resultó clara la ayuda del tutor?</Text>
                  <View style={styles.voteRow}>
                    <TouchableOpacity style={styles.voteBtn} onPress={() => handleVote(true)} activeOpacity={0.7}>
                      <Text style={styles.voteEmoji}>👍</Text>
                      <Text style={styles.voteLabel}>Sí</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={styles.voteBtn} onPress={() => handleVote(false)} activeOpacity={0.7}>
                      <Text style={styles.voteEmoji}>👎</Text>
                      <Text style={styles.voteLabel}>No</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              )}
              <TouchableOpacity style={styles.completeBtn} onPress={() => setShowComplete(false)}>
                <Text style={styles.completeBtnText}>Seguir</Text>
              </TouchableOpacity>
            </View>
          </MessageIn>
        </View>
      ) : null}
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
  slowText: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, color: colors.faint, marginTop: 5, fontStyle: "italic" },
  userWrap: { alignItems: "flex-end" },
  userBubble: { maxWidth: "82%", backgroundColor: colors.primary, borderRadius: 18, borderTopRightRadius: 4, paddingVertical: 11, paddingHorizontal: 14 },
  userBubbleFailed: { borderWidth: 1.5, borderColor: colors.error },
  userText: { fontFamily: fontFamily.sansRegular, fontSize: 14, lineHeight: 21, color: "#fff" },
  retryRow: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 4, paddingRight: 2 },
  retryText: { fontFamily: fontFamily.sansSemi, fontSize: 11.5, color: colors.error },
  inputRow: { flexDirection: "row", alignItems: "flex-end", gap: 10, paddingHorizontal: 14, paddingTop: 10, backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.line },
  inputBox: { flex: 1, minHeight: 46, maxHeight: 110, borderRadius: 23, backgroundColor: colors.bg, borderWidth: 1, borderColor: colors.border, justifyContent: "center", paddingHorizontal: 18 },
  input: { fontFamily: fontFamily.sansRegular, fontSize: 14, color: colors.ink, paddingVertical: Platform.OS === "ios" ? 12 : 8 },
  counter: { alignSelf: "flex-end", paddingHorizontal: 20, paddingBottom: 4, fontFamily: fontFamily.sansRegular, fontSize: 11, color: colors.faint },
  sendBtn: { width: 46, height: 46, borderRadius: 23, backgroundColor: colors.accent, alignItems: "center", justifyContent: "center", shadowColor: colors.accent, shadowOffset: { width: 0, height: 6 }, shadowOpacity: 0.33, shadowRadius: 12, elevation: 4 },
  thinkBubble: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 14 },
  dot: { width: 7, height: 7, borderRadius: 4, backgroundColor: colors.faint },
  offlineBanner: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, backgroundColor: colors.error, paddingVertical: 6, paddingHorizontal: 12 },
  offlineText: { fontFamily: fontFamily.sansSemi, fontSize: 12, color: "#fff" },
  currentQ: { flexDirection: "row", alignItems: "flex-start", gap: 8, paddingHorizontal: 16, paddingVertical: 9, backgroundColor: colors.primarySoft, borderBottomWidth: 1, borderBottomColor: colors.line },
  currentQLabel: { fontFamily: fontFamily.sansBold, fontSize: 10, color: colors.primary, textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 2 },
  currentQText: { fontFamily: fontFamily.sansSemi, fontSize: 13, lineHeight: 18, color: colors.ink },
  progressTrack: { height: 3, width: "100%", backgroundColor: colors.card2 },
  progressFill: { height: 3, backgroundColor: colors.accent },
  progressGlow: { position: "absolute", left: 0, top: 0, height: 3, backgroundColor: "#fff" },
  completeOverlay: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, backgroundColor: "rgba(0,0,0,0.45)", alignItems: "center", justifyContent: "center", padding: 28 },
  completeCard: { backgroundColor: colors.surface, borderRadius: 24, padding: 26, alignItems: "center", gap: 12, width: "100%", maxWidth: 340, shadowColor: "#000", shadowOffset: { width: 0, height: 12 }, shadowOpacity: 0.2, shadowRadius: 24, elevation: 10 },
  completeTitle: { fontFamily: fontFamily.serifSemi, fontSize: 24, color: colors.primary, marginTop: 4 },
  completeText: { fontFamily: fontFamily.sansRegular, fontSize: 14, lineHeight: 21, color: colors.muted, textAlign: "center" },
  completeBtn: { marginTop: 6, backgroundColor: colors.primary, borderRadius: 14, paddingVertical: 12, paddingHorizontal: 30 },
  completeBtnText: { fontFamily: fontFamily.sansBold, fontSize: 15, color: "#fff" },
  voteBlock: { alignItems: "center", gap: 10, marginTop: 2 },
  voteQ: { fontFamily: fontFamily.sansSemi, fontSize: 13.5, color: colors.ink, textAlign: "center" },
  voteRow: { flexDirection: "row", gap: 14 },
  voteBtn: { alignItems: "center", gap: 3, backgroundColor: colors.bg, borderWidth: 1, borderColor: colors.border, borderRadius: 14, paddingVertical: 10, paddingHorizontal: 22 },
  voteEmoji: { fontSize: 24 },
  voteLabel: { fontFamily: fontFamily.sansSemi, fontSize: 12, color: colors.muted },
  completeThanks: { fontFamily: fontFamily.sansSemi, fontSize: 14, color: colors.primary, marginTop: 2 },
});
