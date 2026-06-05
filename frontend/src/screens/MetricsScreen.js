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
import { getMetrics } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

const TREND_CONFIG = {
  mejorando: { label: "📈 Mejorando", color: colors.success },
  estable:   { label: "➡️ Estable",   color: colors.warning },
  bajando:   { label: "📉 Bajando",   color: colors.error },
  "sin datos": { label: "—", color: colors.textMuted },
};

export default function MetricsScreen({ route, navigation }) {
  const { classId, className, joinCode } = route.params;
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => { loadMetrics(); }, []);

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

      {/* Botón a pantalla de preguntas */}
      <TouchableOpacity
        style={styles.questionsButton}
        onPress={() => navigation.navigate("TeacherQuestions", { classId, className })}
      >
        <Text style={styles.questionsButtonText}>📋 Ver preguntas generadas por la IA</Text>
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
          const trend = TREND_CONFIG[student.score_trend] || TREND_CONFIG["sin datos"];
          return (
            <View key={student.student_id} style={styles.studentCard}>
              <View style={styles.studentHeader}>
                <View>
                  <Text style={styles.studentName}>{student.name}</Text>
                  <Text style={styles.studentEmail}>{student.email}</Text>
                </View>
                <Text style={[styles.trendBadge, { color: trend.color }]}>{trend.label}</Text>
              </View>
              <View style={styles.statsRow}>
                <StatChip label="Mensajes" value={student.message_count} />
                <StatChip label="Respuestas" value={student.answers_submitted} />
                <StatChip label="Promedio" value={`${student.average_score}/10`} highlight />
              </View>
            </View>
          );
        })
      )}

      {/* Métricas de desarrollador — título fuera de la card */}
      <Text style={styles.title}>Métricas de desarrollador</Text>
      <View style={styles.devSection}>
        <Text style={styles.devSubtitle}>
          Confiabilidad del evaluador IA — {total} {total === 1 ? "evaluacion registrada" : "evaluaciones registradas"}
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
          Basado en Evaluation Framework for AI Tutoring Systems (VanLehn, 2011).
          La efectividad se mide por la tasa de respuestas correctas y la progresion del puntaje promedio.
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
  trendBadge: { fontSize: 12, fontWeight: "600" },
  statsRow: { flexDirection: "row", gap: spacing.sm },
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
