import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from "react-native";
import { getMetrics } from "../services/api";
import { colors, radius, spacing, typography } from "../styles/theme";

export default function MetricsScreen({ route }) {
  const { classId, className } = route.params;
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadMetrics();
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

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.centered}>
        <Text style={styles.errorText}>{error}</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>Métricas de participación</Text>

      {/* Resumen general */}
      <View style={styles.summaryCard}>
        <View style={styles.statItem}>
          <Text style={styles.statNumber}>{metrics.enrolled_count}</Text>
          <Text style={styles.statLabel}>Alumnos inscriptos</Text>
        </View>
      </View>

      {/* Tabla de alumnos */}
      {metrics.students.length === 0 ? (
        <Text style={styles.emptyText}>Todavía no hay alumnos inscriptos en esta clase.</Text>
      ) : (
        metrics.students.map((student) => (
          <View key={student.student_id} style={styles.studentCard}>
            <Text style={styles.studentName}>{student.name}</Text>
            <Text style={styles.studentEmail}>{student.email}</Text>
            <View style={styles.statsRow}>
              <StatChip label="Mensajes" value={student.message_count} />
              <StatChip label="Respuestas" value={student.answers_submitted} />
              <StatChip label="Promedio" value={`${student.average_score}/10`} highlight />
            </View>
          </View>
        ))
      )}
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

const chipStyles = StyleSheet.create({
  chip: {
    flex: 1,
    alignItems: "center",
    backgroundColor: colors.background,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
  },
  chipHighlight: {
    backgroundColor: colors.primaryLight,
  },
  value: {
    ...typography.subtitle,
    fontSize: 18,
    color: colors.text,
  },
  valueHighlight: {
    color: colors.primary,
  },
  label: {
    ...typography.muted,
    fontSize: 11,
    marginTop: 2,
  },
});

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
  summaryCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.lg,
    marginBottom: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
  },
  statItem: {
    alignItems: "center",
  },
  statNumber: {
    fontSize: 40,
    fontWeight: "700",
    color: colors.primary,
  },
  statLabel: {
    ...typography.muted,
    marginTop: 4,
  },
  studentCard: {
    backgroundColor: colors.white,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  studentName: {
    ...typography.subtitle,
    marginBottom: 2,
  },
  studentEmail: {
    ...typography.muted,
    marginBottom: spacing.md,
  },
  statsRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  emptyText: {
    ...typography.muted,
    textAlign: "center",
    marginTop: spacing.xl,
  },
  errorText: {
    color: colors.error,
    textAlign: "center",
    padding: spacing.lg,
  },
});
