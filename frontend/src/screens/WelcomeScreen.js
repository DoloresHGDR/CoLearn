import React, { useEffect, useRef, useState } from "react";
import { AccessibilityInfo, Animated, Easing, StyleSheet, Text, View } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import AppButton from "../components/AppButton";
import OwlMascot from "../components/OwlMascot";
import { colors, fontFamily } from "../styles/theme";

// Anillo pulsante que se expande y desvanece desde el circulo del buho ("IA activa").
function OwlRing({ delay }) {
  const anim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const timeout = setTimeout(() => {
      Animated.loop(
        Animated.timing(anim, {
          toValue: 1,
          duration: 4200,
          easing: Easing.bezier(0.16, 0.8, 0.4, 1),
          useNativeDriver: true,
        })
      ).start();
    }, delay);
    return () => clearTimeout(timeout);
  }, [anim, delay]);

  const scale   = anim.interpolate({ inputRange: [0, 1], outputRange: [0.96, 1.75] });
  const opacity = anim.interpolate({ inputRange: [0, 0.7, 1], outputRange: [0.32, 0, 0] });

  return <Animated.View style={[styles.ring, { opacity, transform: [{ scale }] }]} />;
}

export default function WelcomeScreen({ navigation }) {
  const insets = useSafeAreaInsets();
  const [reduceMotion, setReduceMotion] = useState(false);

  useEffect(() => {
    let mounted = true;
    AccessibilityInfo.isReduceMotionEnabled().then((v) => { if (mounted) setReduceMotion(v); });
    return () => { mounted = false; };
  }, []);

  return (
    <View style={styles.container}>
      {/* Hero */}
      <View style={[styles.hero, { paddingTop: insets.top + 40 }]}>
        {/* Escenario del buho: los anillos se posicionan absolutamente sobre el circulo */}
        <View style={styles.owlStage}>
          {!reduceMotion && <OwlRing delay={1100} />}
          {!reduceMotion && <OwlRing delay={2500} />}
          {!reduceMotion && <OwlRing delay={3900} />}
          <View style={styles.owlCircle}>
            <OwlMascot size={68} onDark intro reduceMotion={reduceMotion} />
          </View>
        </View>

        <View style={{ alignItems: "center" }}>
          <Text style={styles.title}>CoLearn</Text>
          <Text style={styles.tagline}>Comprensión lectora con guía de IA</Text>
        </View>
      </View>

      {/* Caption */}
      <View style={styles.caption}>
        <Text style={styles.captionText}>
          Tu tutor inteligente te guía con preguntas para que comprendas cada texto en profundidad.
        </Text>
      </View>

      {/* Acciones */}
      <View style={[styles.actions, { paddingBottom: insets.bottom + 28 }]}>
        <AppButton title="Ingresar" onPress={() => navigation.navigate("Login")} />
        <AppButton title="Crear una cuenta" variant="ghost" onPress={() => navigation.navigate("Register")} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  hero: {
    backgroundColor: colors.primarySoft,
    borderBottomLeftRadius: 52,
    borderBottomRightRadius: 52,
    paddingBottom: 44,
    alignItems: "center",
    gap: 22,
  },
  owlStage: {
    width: 108,
    height: 108,
    alignItems: "center",
    justifyContent: "center",
  },
  ring: {
    position: "absolute",
    width: 108,
    height: 108,
    borderRadius: 54,
    borderWidth: 1.5,
    borderColor: colors.primary,
  },
  owlCircle: {
    width: 108,
    height: 108,
    borderRadius: 54,
    backgroundColor: colors.primary,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: colors.primary,
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.32,
    shadowRadius: 24,
    elevation: 8,
  },
  title: { fontFamily: fontFamily.serifSemi, fontSize: 38, color: colors.ink, letterSpacing: -1 },
  tagline: { fontFamily: fontFamily.sansRegular, fontSize: 15, color: colors.muted, marginTop: 8 },
  caption: { flex: 1, alignItems: "center", justifyContent: "center", paddingHorizontal: 36 },
  captionText: { textAlign: "center", fontFamily: fontFamily.sansRegular, fontSize: 14.5, lineHeight: 22, color: colors.muted },
  actions: { paddingHorizontal: 24, gap: 12 },
});
