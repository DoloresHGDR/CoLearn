import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { getTeacherQuestions } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const DIFFICULTY_LABEL = { easy: "Fácil", medium: "Media", hard: "Difícil" };
const DIFFICULTY_COLOR = { easy: "#10B981", medium: "#F59E0B", hard: "#EF4444" };

export default function TeacherQuestionsScreen({ route }) {
  const { classId } = route.params;
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => { loadQuestions(); }, []);

  async function loadQuestions() {
    try {
      const data = await getTeacherQuestions(classId);
      setQuestions(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  if (loading) return <View style={styles.centered}><ActivityIndicator color={colors.primary} /></View>;
  if (error) return <View style={styles.centered}><Text style={styles.error}>{error}</Text></View>;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Preguntas generadas por la IA</Text>
      <Text style={styles.subtitle}>
        Estas preguntas fueron creadas automáticamente según la Taxonomía de Bloom (1956)
        al procesar el texto de la clase.
      </Text>

      {questions.length === 0 ? (
        <Text style={styles.empty}>No hay preguntas registradas para esta clase.</Text>
      ) : (
        questions.map((q, i) => (
          <View key={q.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.num}>{i + 1}</Text>
              <View style={[styles.badge, { backgroundColor: DIFFICULTY_COLOR[q.difficulty] + "20" }]}>
                <Text style={[styles.badgeText, { color: DIFFICULTY_COLOR[q.difficulty] }]}>
                  {DIFFICULTY_LABEL[q.difficulty]}
                </Text>
              </View>
            </View>
            <Text style={styles.question}>{q.question}</Text>
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.lg },
  title: { ...typography.title, marginBottom: spacing.xs },
  subtitle: { ...typography.muted, marginBottom: spacing.lg, lineHeight: 18 },
  empty: { ...typography.muted, textAlign: "center", marginTop: spacing.xl },
  error: { color: colors.error, textAlign: "center" },
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  num: {
    width: 24,
    height: 24,
    borderRadius: radius.full,
    backgroundColor: colors.primaryLight,
    textAlign: "center",
    lineHeight: 24,
    fontSize: 12,
    fontWeight: "700",
    color: colors.primary,
  },
  badge: {
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.full,
  },
  badgeText: { fontSize: 11, fontWeight: "700" },
  question: { ...typography.body, lineHeight: 22 },
});
