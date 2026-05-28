import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import AppButton from "../components/AppButton";
import { getQuestions, submitAnswer } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const DIFFICULTY_LABEL = { easy: "Fácil", medium: "Media", hard: "Difícil" };
const DIFFICULTY_COLOR = { easy: "#10B981", medium: "#F59E0B", hard: "#EF4444" };
const CORRECT_LABEL = { si: "✓ Correcto", parcial: "◑ Parcial", no: "✗ Incorrecto" };
const CORRECT_COLOR = { si: colors.success, parcial: colors.warning, no: colors.error };

export default function QuestionsScreen({ route }) {
  const { classId } = route.params;
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  // Estado por pregunta: answer, submitting, result
  const [answers, setAnswers] = useState({});

  useEffect(() => {
    loadQuestions();
  }, []);

  async function loadQuestions() {
    try {
      const data = await getQuestions(classId);
      setQuestions(data);
    } finally {
      setLoading(false);
    }
  }

  function setAnswer(questionId, text) {
    setAnswers((prev) => ({ ...prev, [questionId]: { ...prev[questionId], text } }));
  }

  async function handleSubmit(question) {
    const answerText = answers[question.id]?.text?.trim();
    if (!answerText) return;

    setAnswers((prev) => ({ ...prev, [question.id]: { ...prev[question.id], submitting: true } }));
    try {
      const result = await submitAnswer(classId, question.id, answerText);
      setAnswers((prev) => ({
        ...prev,
        [question.id]: { ...prev[question.id], submitting: false, result },
      }));
    } catch (e) {
      setAnswers((prev) => ({
        ...prev,
        [question.id]: { ...prev[question.id], submitting: false, error: e.message },
      }));
    }
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Preguntas de la clase</Text>

      {questions.map((q) => {
        const state = answers[q.id] || {};
        const hasResult = !!state.result;

        return (
          <View key={q.id} style={styles.card}>
            {/* Etiqueta de dificultad */}
            <View style={[styles.difficultyBadge, { backgroundColor: DIFFICULTY_COLOR[q.difficulty] + "20" }]}>
              <Text style={[styles.difficultyText, { color: DIFFICULTY_COLOR[q.difficulty] }]}>
                {DIFFICULTY_LABEL[q.difficulty]}
              </Text>
            </View>

            <Text style={styles.questionText}>{q.question}</Text>

            {!hasResult ? (
              <>
                <TextInput
                  style={styles.answerInput}
                  placeholder="Escribí tu respuesta aquí..."
                  placeholderTextColor={colors.textMuted}
                  value={state.text || ""}
                  onChangeText={(t) => setAnswer(q.id, t)}
                  multiline
                  editable={!state.submitting}
                />
                {state.error && <Text style={styles.errorText}>{state.error}</Text>}
                <AppButton
                  title="Enviar respuesta"
                  onPress={() => handleSubmit(q)}
                  loading={state.submitting}
                  style={styles.submitButton}
                />
              </>
            ) : (
              // Mostrar resultado de la evaluación
              <View style={styles.result}>
                <View style={[styles.resultBadge, { backgroundColor: CORRECT_COLOR[state.result.correct] + "20" }]}>
                  <Text style={[styles.resultLabel, { color: CORRECT_COLOR[state.result.correct] }]}>
                    {CORRECT_LABEL[state.result.correct]}
                  </Text>
                  <Text style={[styles.resultScore, { color: CORRECT_COLOR[state.result.correct] }]}>
                    {state.result.score}/10
                  </Text>
                </View>
                <Text style={styles.feedbackText}>{state.result.feedback}</Text>
                <TouchableOpacity onPress={() => setAnswers((prev) => ({ ...prev, [q.id]: {} }))}>
                  <Text style={styles.retryLink}>Intentar de nuevo</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        );
      })}
    </ScrollView>
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
  content: {
    padding: spacing.lg,
  },
  title: {
    ...typography.title,
    marginBottom: spacing.lg,
  },
  card: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  difficultyBadge: {
    alignSelf: "flex-start",
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: radius.full,
    marginBottom: spacing.sm,
  },
  difficultyText: {
    fontSize: 11,
    fontWeight: "700",
  },
  questionText: {
    ...typography.body,
    lineHeight: 22,
    marginBottom: spacing.md,
    fontWeight: "500",
  },
  answerInput: {
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: radius.sm,
    padding: spacing.md,
    fontSize: 14,
    color: colors.text,
    minHeight: 80,
    textAlignVertical: "top",
    marginBottom: spacing.sm,
  },
  errorText: {
    color: colors.error,
    fontSize: 12,
    marginBottom: spacing.sm,
  },
  submitButton: {
    marginTop: spacing.xs,
  },
  result: {
    marginTop: spacing.xs,
  },
  resultBadge: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radius.sm,
    marginBottom: spacing.md,
  },
  resultLabel: {
    fontWeight: "700",
    fontSize: 14,
  },
  resultScore: {
    fontWeight: "700",
    fontSize: 16,
  },
  feedbackText: {
    ...typography.body,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  retryLink: {
    color: colors.primary,
    fontSize: 13,
    fontWeight: "600",
    textAlign: "right",
  },
});
