import { Ionicons } from "@expo/vector-icons";
import * as Clipboard from "expo-clipboard";
import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import AppButton from "../components/AppButton";
import TopBar from "../components/TopBar";
import { getClassSummary, getMetrics } from "../services/api";
import { colors, fontFamily, radius } from "../styles/theme";

const DIFF = {
  easy: { label: "Fácil", color: colors.success },
  medium: { label: "Medio", color: colors.amber },
  hard: { label: "Difícil", color: colors.error },
};

function DiffChip({ levelKey, value }) {
  const d = DIFF[levelKey] || { label: levelKey, color: colors.muted };
  return (
    <View style={[styles.diffChip, { borderColor: d.color }]}>
      <Text style={[styles.diffChipLabel, { color: d.color }]}>{d.label}</Text>
      <Text style={styles.diffChipValue}>{value}</Text>
    </View>
  );
}

function Bar({ label, pct, color }) {
  return (
    <View style={styles.barRow}>
      <Text style={styles.barLabel}>{label}</Text>
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${pct}%`, backgroundColor: color }]} />
      </View>
      <Text style={styles.barPct}>{pct}%</Text>
    </View>
  );
}

export default function MetricsScreen({ route, navigation }) {
  const { classId, className, joinCode } = route.params;
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(true);

  useEffect(() => { loadMetrics(); loadSummary(); }, []);

  async function loadMetrics() {
    try { setMetrics(await getMetrics(classId)); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  async function loadSummary() {
    try { const d = await getClassSummary(classId); setSummary(d.summary); }
    catch (e) { setSummary(null); } finally { setSummaryLoading(false); }
  }
  async function handleCopyCode() {
    await Clipboard.setStringAsync(joinCode || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  }

  if (loading || error) {
    return (
      <View style={styles.container}>
        <TopBar title={className} subtitle="Panel del docente" onBack={() => navigation.goBack()} />
        <View style={styles.centered}>
          {error ? <Text style={styles.errorText}>{error}</Text> : <ActivityIndicator color={colors.primary} />}
        </View>
      </View>
    );
  }

  const allAnswers = metrics.students.flatMap((s) => s.answer_history || []);
  const total = allAnswers.length;
  const correct = allAnswers.filter((a) => a.correct === "si").length;
  const partial = allAnswers.filter((a) => a.correct === "parcial").length;
  const wrong = allAnswers.filter((a) => a.correct === "no").length;
  const participaron = metrics.students.filter((s) => s.answers_submitted > 0).length;
  const avgScore = total > 0 ? (allAnswers.reduce((s, a) => s + a.score, 0) / total).toFixed(1) : "—";
  const pct = (n) => (total > 0 ? Math.round((n / total) * 100) : 0);

  return (
    <View style={styles.container}>
      <TopBar title={className} subtitle="Panel del docente" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.content}>
        {/* code card */}
        <View style={styles.codeCard}>
          <View>
            <Text style={styles.codeLabel}>Código</Text>
            <Text style={styles.codeValue}>{joinCode}</Text>
          </View>
          <TouchableOpacity onPress={handleCopyCode} style={styles.copyBtn}>
            <Ionicons name={copied ? "checkmark" : "copy-outline"} size={16} color="#fff" />
            <Text style={styles.copyText}>{copied ? "¡Copiado!" : "Copiar"}</Text>
          </TouchableOpacity>
        </View>

        {/* stats */}
        <View style={styles.statsRow}>
          {[
            { v: String(metrics.enrolled_count), l: "inscriptos", c: colors.ink },
            { v: String(participaron), l: "participaron", c: colors.primary },
            { v: avgScore, l: "promedio", c: colors.accent },
          ].map((s) => (
            <View key={s.l} style={styles.statCard}>
              <Text style={[styles.statValue, { color: s.c }]}>{s.v}</Text>
              <Text style={styles.statLabel}>{s.l}</Text>
            </View>
          ))}
        </View>

        {/* AI summary */}
        <View style={styles.aiCard}>
          <View style={styles.aiHeader}>
            <Ionicons name="sparkles" size={15} color={colors.accent} />
            <Text style={styles.aiTitle}>Resumen de la clase</Text>
          </View>
          {summaryLoading ? (
            <View style={styles.aiLoadingRow}>
              <ActivityIndicator color={colors.primary} size="small" />
              <Text style={styles.aiLoadingText}>Analizando el desempeño…</Text>
            </View>
          ) : (
            <Text style={styles.aiText}>{summary || "Todavía no hay actividad suficiente para un resumen."}</Text>
          )}
        </View>

        {/* distribution */}
        <View style={styles.panel}>
          <Text style={styles.panelLabel}>Evaluaciones {total > 0 ? `· ${total}` : ""}</Text>
          <View style={{ gap: 10 }}>
            <Bar label="Correctas" pct={pct(correct)} color={colors.success} />
            <Bar label="Parciales" pct={pct(partial)} color={colors.amber} />
            <Bar label="Incorrectas" pct={pct(wrong)} color={colors.error} />
          </View>
        </View>

        <AppButton title="Ver preguntas generadas por la IA" variant="ghost" onPress={() => navigation.navigate("TeacherQuestions", { classId, className })} />

        {/* students */}
        <View style={styles.panel}>
          <Text style={styles.panelLabel}>Participantes</Text>
          {metrics.students.length === 0 ? (
            <Text style={styles.emptyText}>Todavía no hay alumnos inscriptos.</Text>
          ) : (
            metrics.students.map((s, i) => {
              const diffs = Object.entries(s.score_by_difficulty || {});
              const last = i === metrics.students.length - 1;
              return (
                <View key={s.student_id} style={!last ? styles.studentDivider : null}>
                  <View style={styles.studentHead}>
                    <View style={styles.avatar}>
                      <Text style={styles.avatarText}>{(s.name || "?")[0].toUpperCase()}</Text>
                    </View>
                    <View style={{ flex: 1, minWidth: 0 }}>
                      <Text style={styles.studentName} numberOfLines={1}>{s.name}</Text>
                      <Text style={styles.studentEmail} numberOfLines={1}>{s.email}</Text>
                    </View>
                    <Text style={styles.studentAvg}>{s.average_score}</Text>
                  </View>
                  {diffs.length > 0 ? (
                    <View style={styles.diffRow}>
                      {diffs.map(([k, v]) => <DiffChip key={k} levelKey={k} value={v} />)}
                    </View>
                  ) : null}
                </View>
              );
            })
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  errorText: { color: colors.error, fontFamily: fontFamily.sansRegular, textAlign: "center", padding: 20 },
  content: { padding: 16, gap: 14, paddingBottom: 28 },
  codeCard: { backgroundColor: colors.primary, borderRadius: 18, paddingVertical: 15, paddingHorizontal: 18, flexDirection: "row", alignItems: "center", justifyContent: "space-between", shadowColor: colors.primary, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.28, shadowRadius: 20, elevation: 5 },
  codeLabel: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, color: "rgba(255,255,255,0.72)", textTransform: "uppercase", letterSpacing: 0.4 },
  codeValue: { fontFamily: fontFamily.serifSemi, fontSize: 26, color: "#fff", letterSpacing: 2.5, marginTop: 2 },
  copyBtn: { flexDirection: "row", alignItems: "center", gap: 6, backgroundColor: "rgba(255,255,255,0.15)", borderRadius: 11, paddingVertical: 8, paddingHorizontal: 14 },
  copyText: { fontFamily: fontFamily.sansSemi, fontSize: 12.5, color: "#fff" },
  statsRow: { flexDirection: "row", gap: 10 },
  statCard: { flex: 1, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.lg, paddingVertical: 12, paddingHorizontal: 10, alignItems: "center" },
  statValue: { fontFamily: fontFamily.serifSemi, fontSize: 23 },
  statLabel: { fontFamily: fontFamily.sansRegular, fontSize: 11, color: colors.muted, marginTop: 2 },
  aiCard: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderLeftWidth: 3, borderLeftColor: colors.accent, borderRadius: radius.xl, padding: 15 },
  aiHeader: { flexDirection: "row", alignItems: "center", gap: 7, marginBottom: 8 },
  aiTitle: { fontFamily: fontFamily.sansBold, fontSize: 12.5, color: colors.primary },
  aiLoadingRow: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 4 },
  aiLoadingText: { fontFamily: fontFamily.sansRegular, fontSize: 13, color: colors.muted },
  aiText: { fontFamily: fontFamily.sansRegular, fontSize: 13, lineHeight: 20, color: colors.ink },
  panel: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: radius.xl, padding: 15 },
  panelLabel: { fontFamily: fontFamily.sansBold, fontSize: 11.5, color: colors.faint, letterSpacing: 1.1, textTransform: "uppercase", marginBottom: 14 },
  barRow: { flexDirection: "row", alignItems: "center", gap: 10 },
  barLabel: { fontFamily: fontFamily.sansRegular, fontSize: 12, color: colors.muted, width: 72 },
  barTrack: { flex: 1, height: 8, borderRadius: 4, backgroundColor: colors.card2, overflow: "hidden" },
  barFill: { height: "100%", borderRadius: 4 },
  barPct: { fontFamily: fontFamily.sansBold, fontSize: 12, color: colors.ink, width: 34, textAlign: "right" },
  studentDivider: { borderBottomWidth: 1, borderBottomColor: colors.line, paddingBottom: 14, marginBottom: 14 },
  studentHead: { flexDirection: "row", alignItems: "center", gap: 10, marginBottom: 10 },
  avatar: { width: 36, height: 36, borderRadius: 11, backgroundColor: colors.primarySoft, alignItems: "center", justifyContent: "center" },
  avatarText: { fontFamily: fontFamily.serifSemi, fontSize: 15, color: colors.primary },
  studentName: { fontFamily: fontFamily.sansBold, fontSize: 14, color: colors.ink },
  studentEmail: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, color: colors.muted },
  studentAvg: { fontFamily: fontFamily.serifSemi, fontSize: 20, color: colors.primary },
  diffRow: { flexDirection: "row", gap: 7, flexWrap: "wrap" },
  diffChip: { flexDirection: "row", alignItems: "center", gap: 5, borderWidth: 1.5, borderRadius: radius.chip, paddingVertical: 4, paddingHorizontal: 9 },
  diffChipLabel: { fontFamily: fontFamily.sansBold, fontSize: 10.5 },
  diffChipValue: { fontFamily: fontFamily.sansBold, fontSize: 12, color: colors.ink },
  emptyText: { fontFamily: fontFamily.sansRegular, fontSize: 13, color: colors.muted },
});
