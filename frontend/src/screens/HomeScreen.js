import AsyncStorage from "@react-native-async-storage/async-storage";
import { Ionicons } from "@expo/vector-icons";
import React, { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Alert, FlatList, RefreshControl, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AppButton from "../components/AppButton";
import ClassCard from "../components/ClassCard";
import NotificationsModal from "../components/NotificationsModal";
import OwlMascot from "../components/OwlMascot";
import { deleteClass, getClasses, getMe, getNotifications, leaveClass, markNotificationsRead } from "../services/api";
import { colors, fontFamily } from "../styles/theme";

export default function HomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [user, setUser] = useState(null);
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [panelOpen, setPanelOpen] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [userData, classesData] = await Promise.all([getMe(), getClasses()]);
      setUser(userData);
      setClasses(classesData);
      // Las notificaciones son solo para el docente
      if (userData?.role === "teacher") {
        try {
          const notif = await getNotifications();
          setNotifications(notif.items || []);
          setUnread(notif.unread || 0);
        } catch (e) {
          // si fallan las notificaciones no rompemos la pantalla
        }
      }
    } catch (e) {
      await AsyncStorage.removeItem("token");
      navigation.replace("Login");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [navigation]);

  async function openPanel() {
    setPanelOpen(true);
    if (unread > 0) await markRead();
  }

  async function markRead() {
    try {
      await markNotificationsRead();
      setUnread(0);
    } catch (e) {
      // sin conexión: se reintenta la próxima vez
    }
  }

  useEffect(() => {
    const unsubscribe = navigation.addListener("focus", loadData);
    return unsubscribe;
  }, [navigation, loadData]);

  function handleClassPress(classroom) {
    if (user?.role === "teacher") {
      navigation.navigate("Metrics", { classId: classroom.id, className: classroom.name, joinCode: classroom.join_code });
    } else {
      navigation.navigate("Chat", { classId: classroom.id, className: classroom.name });
    }
  }

  async function handleDeleteOrLeave(classroom) {
    try {
      if (user?.role === "teacher") await deleteClass(classroom.id);
      else await leaveClass(classroom.id);
      await loadData();
    } catch (e) {
      // el Alert de la card ya dio feedback
    }
  }

  function handleLogout() {
    Alert.alert("Cerrar sesión", "¿Querés cerrar sesión?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Cerrar sesión",
        style: "destructive",
        onPress: async () => {
          await AsyncStorage.removeItem("token");
          navigation.reset({ index: 0, routes: [{ name: "Welcome" }] });
        },
      },
    ]);
  }

  const isTeacher = user?.role === "teacher";
  const firstName = user?.name?.split(" ")[0] || "";
  const noun = isTeacher ? (classes.length === 1 ? "clase" : "clases") : (classes.length === 1 ? "lectura" : "lecturas");

  return (
    <View style={[styles.container, { paddingTop: insets.top + 8 }]}>
      <View style={styles.header}>
        {/* nav bar */}
        <View style={styles.navBar}>
          <View style={styles.logoRow}>
            <OwlMascot size={30} />
            <Text style={styles.logo}>CoLearn</Text>
          </View>
          <View style={styles.navActions}>
            {isTeacher && (
              <TouchableOpacity onPress={openPanel} style={styles.iconBtn}>
                <Ionicons name="notifications-outline" size={18} color={colors.muted} />
                {unread > 0 && (
                  <View style={styles.badge}>
                    <Text style={styles.badgeText}>{unread > 9 ? "9+" : unread}</Text>
                  </View>
                )}
              </TouchableOpacity>
            )}
            <TouchableOpacity onPress={handleLogout} style={styles.iconBtn}>
              <Ionicons name="log-out-outline" size={18} color={colors.muted} />
            </TouchableOpacity>
          </View>
        </View>

        {!loading && (
          <>
            {/* greeting */}
            <View style={{ marginTop: 24 }}>
              {isTeacher ? <Text style={styles.roleBadge}>Docente</Text> : null}
              <Text style={styles.greeting}>Hola, {firstName}</Text>
              <Text style={styles.sub}>
                Tenés <Text style={styles.subStrong}>{classes.length} {noun}</Text>
                {isTeacher ? " activas." : " en curso."}
              </Text>
            </View>

            <AppButton
              title={isTeacher ? "Crear nueva clase" : "Unirse a una clase"}
              icon="add"
              onPress={() => navigation.navigate(isTeacher ? "CreateClass" : "JoinClass")}
              style={{ marginTop: 18 }}
            />

            <View style={styles.sectionHeader}>
              <Text style={styles.sectionLabel}>{isTeacher ? "Mis clases" : "Tus lecturas"}</Text>
              <Text style={styles.sectionRight}>{isTeacher ? `${classes.length} activas` : "7.º grado"}</Text>
            </View>
          </>
        )}
      </View>

      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator color={colors.primary} />
        </View>
      ) : (
        <FlatList
          data={classes}
          keyExtractor={(item) => item.id}
          renderItem={({ item, index }) => (
            <ClassCard
              classroom={item}
              isTeacher={isTeacher}
              index={index}
              onPress={() => handleClassPress(item)}
              onDelete={() => handleDeleteOrLeave(item)}
            />
          )}
          contentContainerStyle={styles.list}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadData(); }} />}
          ListEmptyComponent={
            <View style={styles.empty}>
              <Text style={styles.emptyText}>
                {isTeacher ? "Todavía no creaste ninguna clase." : "Todavía no te uniste a ninguna clase."}
              </Text>
            </View>
          }
        />
      )}

      {/* Panel de notificaciones del docente (bottom sheet) */}
      <NotificationsModal
        visible={panelOpen}
        notifications={notifications}
        onClose={() => setPanelOpen(false)}
        onMarkRead={markRead}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  header: { paddingHorizontal: 20 },
  centered: { flex: 1, alignItems: "center", justifyContent: "center" },
  navBar: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  logoRow: { flexDirection: "row", alignItems: "center", gap: 9 },
  logo: { fontFamily: fontFamily.serifSemi, fontSize: 19, color: colors.ink, letterSpacing: -0.3 },
  navActions: { flexDirection: "row", alignItems: "center", gap: 8 },
  iconBtn: { width: 38, height: 38, borderRadius: 12, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center" },
  badge: { position: "absolute", top: -5, right: -5, minWidth: 18, height: 18, borderRadius: 9, paddingHorizontal: 5, backgroundColor: colors.primary, alignItems: "center", justifyContent: "center", borderWidth: 2, borderColor: colors.bg },
  badgeText: { fontFamily: fontFamily.sansBold, fontSize: 10.5, color: "#fff" },
  roleBadge: { fontFamily: fontFamily.sansBold, fontSize: 12, color: colors.accent, textTransform: "uppercase", letterSpacing: 0.6, marginBottom: 4 },
  greeting: { fontFamily: fontFamily.serifSemi, fontSize: 30, color: colors.ink, letterSpacing: -0.6, lineHeight: 34 },
  sub: { fontFamily: fontFamily.sansRegular, fontSize: 14.5, color: colors.muted, marginTop: 6 },
  subStrong: { color: colors.primary, fontFamily: fontFamily.sansBold },
  sectionHeader: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 22, marginBottom: 11 },
  sectionLabel: { fontFamily: fontFamily.sansBold, fontSize: 11.5, color: colors.faint, letterSpacing: 1.2, textTransform: "uppercase" },
  sectionRight: { fontFamily: fontFamily.sansRegular, fontSize: 12.5, color: colors.muted },
  list: { paddingHorizontal: 20, paddingBottom: 28, gap: 13 },
  empty: { alignItems: "center", paddingTop: 40 },
  emptyText: { fontFamily: fontFamily.sansRegular, fontSize: 13, color: colors.muted, textAlign: "center" },
});
