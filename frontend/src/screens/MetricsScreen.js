import { Ionicons } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { getClassSummary, getMetrics } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const DIFFICULTY_LABELS = { easy: "Fácil", medium: "Medio", hard: "Difícil" };
const DIFFICULTY_COLORS = { easy: colors.success, medium: colors.warning, hard: colors.error };

export default function MetricsScreen({ route, navigation }) {
  const { classId, className, joinCode } = route.params;
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  useEffect(() => {
    loadMetrics();
    loadSummary();
  }, []);

  async function loadMetrics() {
    try {
      const data = await getMetrics(classId);
      setMetrics(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  // Resumen generado por IA — se carga solo al entrar (el backend lo cachea)
  async function loadSummary() {
    try {
      const data = await getClassSummary(classId);
      setSummary(data.summary);
    } catch (e) {
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }

  async function handleCopyCode() {
    await Clipboard.setStringAsync(joinCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (loading) return <View style={styles.centered}><ActivityIndicator color={colors.primary} /></View>;
  if (error) return <View style={styles.centered}><Text style={styles.errorText}>{error}</Text></View>;

  // Calcular métricas de desarrollador
  const allAnswers = metrics.students.flatMap((s) => s.answer_history || []);
  const total = allAnswers.length;
  const correct = allAnswers.filter((a) => a.correct === "si").length;
  const partial = allAnswers.filter((a) => a.correct === "parcial").length;
  const wrong = allAnswers.filter((a) => a.correct === "no").length;
  const avgScore = total > 0 ? (allAnswers.reduce((s, a) => s + a.score, 0) / total).toFixed(1) : "—";
  const pct = (n) => total > 0 ? `${Math.round((n / total) * 100)}%` : "—";

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>

      {/* Código de clase copiable */}
      <TouchableOpacity style={styles.codeCard} onPress={handleCopyCode} activeOpacity={0.8}>
        <Text style={styles.codeLabel}>Código de la clase</Text>
        <Text style={styles.codeValue}>{joinCode}</Text>
        <Text style={styles.codeTip}>{copied ? "Copiado!" : "Toca para copiar"}</Text>
      </TouchableOpacity>

      {/* Resumen de desempeño generado por IA */}
      <View style={styles.aiCard}>
        <View style={styles.aiHeader}>
          <Ionicons name="sparkles-outline" size={16} color={colors.primary} />
          <Text style={styles.aiTitle}>Resumen de la clase</Text>
        </View>
        {summaryLoading ? (
          <View style={styles.aiLoadingRow}>
            <ActivityIndicator color={colors.primary} size="small" />
            <Text style={styles.aiLoadingText}>Analizando el desempeño...</Text>
          </View>
        ) : (
          <Text style={styles.aiText}>
            {summary || "No se pudo generar el resumen en este momento."}
          </Text>
        )}
      </View>

      {/* Botón a pantalla de preguntas */}
      <TouchableOpacity
        style={styles.questionsButton}
        onPress={() => navigation.navigate("TeacherQuestions", { classId, className })}
      >
        <Text style={styles.questionsButtonText}>Ver preguntas generadas por la IA</Text>
      </TouchableOpacity>

      <Text style={styles.title}>Métricas de participación</Text>

      {/* Resumen */}
      <View style={styles.summaryCard}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{metrics.enrolled_count}</Text>
          <Text style={styles.statLabel}>Alumnos inscriptos</Text>
        </View>
      </View>

      {/* Alumnos */}
      {metrics.students.length > 0 && (
        metrics.students.map((student) => {
          const diffEntries = Object.entries(student.score_by_difficulty || {});
          return (
            <View key={student.student_id} style={styles.studentCard}>
              <View style={styles.studentHeader}>
                <View>
                  <Text style={styles.studentName}>{student.name}</Text>
                  <Text style={styles.studentEmail}>{student.email}</Text>
                </View>
              </View>
              <View style={styles.statsRow}>
                <StatChip label="Mensajes" value={student.message_count} />
                <StatChip label="Respuestas" value={student.answers_submitted} />
                <StatChip label="Promedio" value={`${student.average_score}/10`} highlight />
              </View>
              {diffEntries.length > 0 && (
                <View style={styles.diffRow}>
                  <Text style={styles.diffTitle}>Puntaje por nivel:</Text>
                  <View style={styles.diffChips}>
                    {diffEntries.map(([level, avg]) => (
                      <View key={level} style={[styles.diffChip, { borderColor: DIFFICULTY_COLORS[level] }]}>
                        <Text style={[styles.diffChipLabel, { color: DIFFICULTY_COLORS[level] }]}>
                          {DIFFICULTY_LABELS[level] || level}
                        </Text>
                        <Text style={styles.diffChipValue}>{avg}/10</Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}
            </View>
          );
        })
      )}

      {/* Métricas de desarrollador — título fuera de la card */}
      <Text style={styles.title}>Métricas de desarrollador</Text>
      <View style={styles.devSection}>
        <Text style={styles.devSubtitle}>
          Distribución de evaluaciones — {total} {total === 1 ? "evaluacion registrada" : "evaluaciones registradas"}
        </Text>

        <View style={styles.devGrid}>
          <DevMetric label="Correctas" value={pct(correct)} count={correct} color={colors.success} />
          <DevMetric label="Parciales" value={pct(partial)} count={partial} color={colors.warning} />
          <DevMetric label="Incorrectas" value={pct(wrong)} count={wrong} color={colors.error} />
        </View>

        <View style={styles.devRow}>
          <Text style={styles.devRowLabel}>Puntaje promedio global</Text>
          <Text style={styles.devRowValue}>{total > 0 ? `${avgScore}/10` : "Sin datos aun"}</Text>
        </View>
        <View style={styles.devRow}>
          <Text style={styles.devRowLabel}>Total de evaluaciones</Text>
          <Text style={styles.devRowValue}>{total}</Text>
        </View>
        <Text style={styles.devNote}>
          Distribución de resultados del evaluador IA por categoría (VanLehn, 2011).
          Permite observar el balance entre respuestas correctas, parciales e incorrectas en la clase.
        </Text>
      </View>

    </ScrollView>
  );
}

function StatChip({ label, value, highlight }) {
  return (
    <View style={[chipStyles.chip, highlight && chipStyles.chipHighlight]}>
      <Text style={[chipStyles.value, highlight && chipStyles.valueHighlight]}>{value}</Text>
      <Text style={chipStyles.label}>{label}</Text>
    </View>
  );
}

function DevMetric({ label, value, count, color }) {
  return (
    <View style={[devStyles.box, { borderColor: color }]}>
      <Text style={[devStyles.pct, { color }]}>{value}</Text>
      <Text style={devStyles.label}>{label}</Text>
      <Text style={devStyles.count}>{count} resp.</Text>
    </View>
  );
}

const devStyles = StyleSheet.create({
  box: {
    flex: 1,
    alignItems: "center",
    borderWidth: 1.5,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
    backgroundColor: colors.white,
  },
  pct: { fontSize: 20, fontWeight: "700" },
  label: { fontSize: 11, color: colors.textMuted, textAlign: "center", marginTop: 2 },
  count: { fontSize: 11, color: colors.textMuted },
});

const chipStyles = StyleSheet.create({
  chip: {
    flex: 1,
    alignItems: "center",
    backgroundColor: colors.background,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
  },
  chipHighlight: { backgroundColor: colors.primaryLight },
  value: { ...typography.subtitle, fontSize: 18, color: colors.text },
  valueHighlight: { color: colors.primary },
  label: { ...typography.muted, fontSize: 11, marginTop: 2 },
});

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  content: { padding: spacing.lg },
  codeCard: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    padding: spacing.lg,
    alignItems: "center",
    marginBottom: spacing.md,
  },
  codeLabel: { color: "rgba(255,255,255,0.8)", fontSize: 12, marginBottom: 4 },
  codeValue: { color: colors.white, fontSize: 28, fontWeight: "700", letterSpacing: 3 },
  codeTip: { color: "rgba(255,255,255,0.7)", fontSize: 12, marginTop: 4 },
  aiCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.primary,
  },
  aiHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginBottom: spacing.sm,
  },
  aiTitle: {
    fontSize: 13,
    fontWeight: "700",
    color: colors.primary,
  },
  aiLoadingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.sm,
  },
  aiLoadingText: {
    ...typography.muted,
    fontSize: 13,
  },
  aiText: {
    ...typography.body,
    fontSize: 14,
    lineHeight: 20,
    color: colors.text,
  },
  questionsButton: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    alignItems: "center",
    borderWidth: 1.5,
    borderColor: colors.primary,
    marginBottom: spacing.lg,
  },
  questionsButtonText: { color: colors.primary, fontWeight: "600", fontSize: 14 },
  title: { ...typography.title, marginBottom: spacing.lg },
  summaryCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
  },
  statItem: { alignItems: "center" },
  statNumber: { fontSize: 40, fontWeight: "700", color: colors.primary },
  statLabel: { ...typography.muted, marginTop: 4 },
  studentCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  studentHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: spacing.md,
  },
  studentName: { ...typography.subtitle, marginBottom: 2 },
  studentEmail: { ...typography.muted },
  statsRow: { flexDirection: "row", gap: spacing.sm },
  diffRow: { marginTop: spacing.sm, paddingTop: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border },
  diffTitle: { ...typography.muted, fontSize: 11, marginBottom: spacing.xs },
  diffChips: { flexDirection: "row", gap: spacing.sm, flexWrap: "wrap" },
  diffChip: { borderWidth: 1.5, borderRadius: radius.sm, paddingHorizontal: spacing.sm, paddingVertical: 4, alignItems: "center" },
  diffChipLabel: { fontSize: 11, fontWeight: "600" },
  diffChipValue: { fontSize: 13, fontWeight: "700", color: colors.text },
  emptyText: { ...typography.muted, textAlign: "center", marginTop: spacing.xl },
  errorText: { color: colors.error, textAlign: "center", padding: spacing.lg },
  devSection: {
    marginTop: spacing.xl,
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  devTitle: { ...typography.subtitle, marginBottom: 4 },
  devSubtitle: { ...typography.muted, marginBottom: spacing.md },
  devGrid: { flexDirection: "row", gap: spacing.sm, marginBottom: spacing.md },
  devRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  devRowLabel: { ...typography.muted },
  devRowValue: { fontWeight: "600", color: colors.text },
  devNote: {
    ...typography.muted,
    fontSize: 11,
    marginTop: spacing.md,
    fontStyle: "italic",
    lineHeight: 16,
  },
});
