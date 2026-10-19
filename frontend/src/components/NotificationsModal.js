import { Ionicons } from "@expo/vector-icons";
import React, { useEffect, useRef } from "react";
import { Animated, Easing, FlatList, Modal, Pressable, StyleSheet, Text, TouchableOpacity, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { colors, fontFamily } from "../styles/theme";

// Convierte una fecha ISO en un texto relativo corto ("hace 5 min", "ayer", etc.)
function timeAgo(iso) {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const diff = Math.max(0, Date.now() - then);
  const min = Math.floor(diff / 60000);
  if (min < 1) return "recién";
  if (min < 60) return `hace ${min} min`;
  const hours = Math.floor(min / 60);
  if (hours < 24) return `hace ${hours} h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return "ayer";
  return `hace ${days} días`;
}

// Bottom sheet de notificaciones del docente. Datos reales (alumno se unió / salió).
export default function NotificationsModal({ visible, notifications, onClose, onMarkRead }) {
  const insets = useSafeAreaInsets();
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (visible) {
      anim.setValue(0);
      Animated.timing(anim, {
        toValue: 1,
        duration: 320,
        easing: Easing.bezier(0.22, 1, 0.36, 1),
        useNativeDriver: true,
      }).start();
    }
  }, [visible, anim]);

  // Cierra animando el sheet hacia abajo antes de desmontar.
  function requestClose() {
    Animated.timing(anim, {
      toValue: 0,
      duration: 220,
      easing: Easing.in(Easing.ease),
      useNativeDriver: true,
    }).start(({ finished }) => {
      if (finished) onClose();
    });
  }

  const overlayStyle = { opacity: anim };
  const sheetStyle = { transform: [{ translateY: anim.interpolate({ inputRange: [0, 1], outputRange: [700, 0] }) }] };
  const hasItems = notifications.length > 0;

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={requestClose}>
      <Pressable style={styles.overlayPress} onPress={requestClose}>
        <Animated.View style={[styles.overlay, overlayStyle]} />
      </Pressable>

      <Animated.View
        style={[styles.sheet, { paddingBottom: insets.bottom + 16 }, sheetStyle]}
      >
        {/* Grabber */}
        <View style={styles.grabber} />

        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Ionicons name="notifications" size={19} color={colors.primary} />
            <Text style={styles.title}>Notificaciones</Text>
          </View>
          {hasItems && (
            <TouchableOpacity onPress={onMarkRead} hitSlop={8}>
              <Text style={styles.markRead}>Marcar leídas</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Lista */}
        {!hasItems ? (
          <View style={styles.empty}>
            <Ionicons name="notifications-off-outline" size={28} color={colors.faint} />
            <Text style={styles.emptyText}>No tenés notificaciones todavía.</Text>
          </View>
        ) : (
          <FlatList
            data={notifications}
            keyExtractor={(item) => String(item.id)}
            style={{ maxHeight: 420 }}
            contentContainerStyle={{ paddingBottom: 12 }}
            renderItem={({ item }) => {
              const joined = item.event_type === "join";
              const unread = !item.is_read;
              return (
                <View style={[styles.row, unread && styles.rowUnread]}>
                  {unread && <View style={styles.unreadDot} />}
                  <View style={styles.rowIcon}>
                    <Ionicons
                      name={joined ? "person-add" : "exit-outline"}
                      size={16}
                      color={joined ? colors.primary : colors.muted}
                    />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.rowText}>
                      <Text style={styles.rowName}>{item.student_name}</Text>
                      {joined ? " se unió a " : " salió de "}
                      <Text style={styles.rowClass}>{item.class_name}</Text>
                    </Text>
                    <View style={styles.timeRow}>
                      <Ionicons name="time-outline" size={12} color={colors.faint} />
                      <Text style={styles.time}>{timeAgo(item.created_at)}</Text>
                    </View>
                  </View>
                </View>
              );
            }}
            ItemSeparatorComponent={() => <View style={styles.sep} />}
          />
        )}
      </Animated.View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlayPress: { ...StyleSheet.absoluteFillObject },
  overlay: { flex: 1, backgroundColor: "rgba(58,33,26,0.32)" },
  sheet: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    maxHeight: "78%",
    backgroundColor: colors.bg,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    paddingTop: 10,
    shadowColor: "#3A211A",
    shadowOffset: { width: 0, height: -12 },
    shadowOpacity: 0.18,
    shadowRadius: 40,
    elevation: 16,
  },
  grabber: { alignSelf: "center", width: 38, height: 4, borderRadius: 2, backgroundColor: colors.border, marginBottom: 6 },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 20, paddingTop: 12, paddingBottom: 14, borderBottomWidth: 1, borderBottomColor: colors.line },
  headerLeft: { flexDirection: "row", alignItems: "center", gap: 9 },
  title: { fontFamily: fontFamily.serifSemi, fontSize: 19, color: colors.ink },
  markRead: { fontFamily: fontFamily.sansSemi, fontSize: 13, color: colors.primary },
  empty: { alignItems: "center", paddingVertical: 40, gap: 10 },
  emptyText: { fontFamily: fontFamily.sansRegular, fontSize: 13.5, color: colors.muted },
  row: { flexDirection: "row", alignItems: "flex-start", gap: 13, paddingVertical: 13, paddingHorizontal: 20 },
  rowUnread: { backgroundColor: colors.primarySoft + "55" },
  unreadDot: { position: "absolute", left: 8, top: 22, width: 6, height: 6, borderRadius: 3, backgroundColor: colors.primary },
  rowIcon: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, alignItems: "center", justifyContent: "center" },
  rowText: { fontFamily: fontFamily.sansRegular, fontSize: 13.5, color: colors.muted, lineHeight: 19 },
  rowName: { fontFamily: fontFamily.sansBold, color: colors.ink },
  rowClass: { fontFamily: fontFamily.sansSemi, color: colors.primary },
  timeRow: { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 3 },
  time: { fontFamily: fontFamily.sansRegular, fontSize: 11.5, color: colors.faint },
  sep: { height: 1, backgroundColor: colors.line, marginLeft: 73 },
});
