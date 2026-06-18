import { Ionicons } from "@expo/vector-icons";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import TopBar from "../components/TopBar";
import { getTeacherQuestions } from "../services/api";
import { colors, fontFamily, radius } from "../styles/theme";

const DIFF = {
  easy: { label: "Fácil", color: colors.success },
  medium: { label: "Medio", color: colors.amber },
  hard: { label: "Difícil", color: colors.error },
};

export default function TeacherQuestionsScreen({ route, navigation }) {
  const { classId, className } = route.params;
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { load(); }, []);
  async function load() {
    try { setQuestions(await getTeacherQuestions(classId)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  if (loading || error) {
    return (
      <View style={styles.container}>
        <TopBar title="Preguntas generadas" subtitle={className} onBack={() => navigation.goBack()} />
        <View style={styles.centered}>
          {error ? <Text style={styles.errorText}>{error}</Text> : <ActivityIndicator color={colors.primary} />}
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <TopBar title="Preguntas generadas" subtitle={className} onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.content}>
        <View style={styles.banner}>
          <Ionicons name="sparkles" size={15} color={colors.accent} style={{ marginTop: 1 }} />
          <Text style={styles.bannerText}>
            La IA generó {questions.length} preguntas de comprensión con dificultad progresiva a partir del texto de la clase.
          </Text>
        </View>

        {questions.length === 0 ? (
          <Text style={styles.empty}>No hay preguntas registradas para esta clase.</Text>
        ) : (
          questions.map((q, i) => {
            const d = DIFF[q.difficulty] || { label: q.difficulty, color: colors.muted };
            return (
              <View key={q.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.num}>#{i + 1}</Text>
                  <View style={[styles.diffChip, { borderColor: d.color }]}>
                    <Text style={[styles.diffChipLabel, { color: d.color }]}>{d.label}</Text>
                  </View>
                </View>
                <Text style={styles.question}>{q.question}</Text>
              </View>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: colors.error, fontFamily: fontFamily.sansRegular, textAlign: "center", padding: 20 },
  content: { padding: 16, gap: 13, paddingBottom: 28 },
  banner: { flexDirection: "row", gap: 10, alignItems: "flex-start", backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.lg, paddingVertical: 12, paddingHorizontal: 14 },
  bannerText: { flex: 1, fontFamily: fontFamily.sansRegular, fontSize: 13, color: colors.muted, lineHeight: 19 },
  card: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 16, padding: 15 },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10 },
  num: { fontFamily: fontFamily.serifSemi, fontSize: 13, color: colors.faint },
  diffChip: { borderWidth: 1.5, borderRadius: radius.chip, paddingVertical: 3, paddingHorizontal: 9 },
  diffChipLabel: { fontFamily: fontFamily.sansBold, fontSize: 10.5 },
  question: { fontFamily: fontFamily.serifMedium, fontSize: 15, lineHeight: 23, color: colors.ink },
  empty: { fontFamily: fontFamily.sansRegular, fontSize: 13, color: colors.muted, textAlign: "center", marginTop: 20 },
});
