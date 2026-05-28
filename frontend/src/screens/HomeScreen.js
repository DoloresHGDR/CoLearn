import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { useCallback, useEffect, useState } from "react";
import { FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import AppButton from "../components/AppButton";
import ClassCard from "../components/ClassCard";
import { getClasses, getMe } from "../services/api";
import { colors, spacing, typography } from "../styles/theme";

export default function HomeScreen({ navigation }) {
  const [user, setUser] = useState(null);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [userData, classesData] = await Promise.all([getMe(), getClasses()]);
      setUser(userData);
      setClasses(classesData);
    } catch (e) {
      // Si el token expiró, volver al login
      await AsyncStorage.removeItem("token");
      navigation.replace("Login");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [navigation]);

  useEffect(() => {
    const unsubscribe = navigation.addListener("focus", loadData);
    return unsubscribe;
  }, [navigation, loadData]);

  function handleClassPress(classroom) {
    if (user?.role === "teacher") {
      navigation.navigate("Metrics", { classId: classroom.id, className: classroom.name });
    } else {
      navigation.navigate("Chat", { classId: classroom.id, className: classroom.name });
    }
  }

  function handleQuestionsPress(classroom) {
    navigation.navigate("Questions", { classId: classroom.id, className: classroom.name });
  }

  if (loading) {
    return (
      <View style={styles.centered}>
        <Text style={typography.muted}>Cargando...</Text>
      </View>
    );
  }

  const isTeacher = user?.role === "teacher";

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Hola, {user?.name?.split(" ")[0]} 👋</Text>
          <Text style={styles.role}>{isTeacher ? "Docente" : "Alumno"}</Text>
        </View>
        <AppButton
          title={isTeacher ? "Nueva clase" : "Unirse"}
          onPress={() => navigation.navigate(isTeacher ? "CreateClass" : "JoinClass")}
          style={styles.headerButton}
        />
      </View>

      <FlatList
        data={classes}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <ClassCard
            classroom={item}
            onPress={() => handleClassPress(item)}
            onQuestionsPress={user?.role === "student" ? () => handleQuestionsPress(item) : null}
          />
        )}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>
              {isTeacher ? "Todavía no creaste ninguna clase." : "Todavía no te uniste a ninguna clase."}
            </Text>
          </View>
        }
      />
    </View>
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
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.lg,
    paddingBottom: spacing.md,
    backgroundColor: colors.white,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  greeting: {
    ...typography.subtitle,
    fontSize: 18,
  },
  role: {
    ...typography.muted,
    marginTop: 2,
  },
  headerButton: {
    paddingVertical: 10,
    paddingHorizontal: spacing.md,
  },
  list: {
    padding: spacing.lg,
  },
  empty: {
    alignItems: "center",
    paddingTop: spacing.xl,
  },
  emptyText: {
    ...typography.muted,
    textAlign: "center",
  },
});
