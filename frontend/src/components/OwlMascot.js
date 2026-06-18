import React, { useEffect, useRef } from "react";
import { Animated } from "react-native";
import Svg, { Path, Circle } from "react-native-svg";
import { colors } from "../styles/theme";

// Mascota buho tutor IA.
// onDark: invierte colores para fondos oscuros.
// animated: activa flotado suave + alas.
export default function OwlMascot({ size = 34, onDark = false, animated = false }) {
  const body  = onDark ? colors.surface   : colors.primary;
  const belly = onDark ? colors.accent    : colors.accentSoft;
  const pupil = onDark ? colors.primaryDeep : colors.ink;
  const beak  = colors.accent;
  const hi    = "#fff";

  const floatY = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!animated) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(floatY, { toValue: -4, duration: 900, useNativeDriver: true }),
        Animated.timing(floatY, { toValue:  0, duration: 900, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [animated, floatY]);

  const svg = (
    <Svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      {/* alas (solo en version animada) */}
      {animated && <Path d="M14 14 C6 15, 4.5 24, 10 28 C12.5 24, 13 19, 16.5 16.5 Z" fill={body} />}
      {animated && <Path d="M26 14 C34 15, 35.5 24, 30 28 C27.5 24, 27 19, 23.5 16.5 Z" fill={body} />}
      {/* orejas */}
      <Path d="M12 10L14.5 4.5L18 10.5Z" fill={body} />
      <Path d="M28 10L25.5 4.5L22 10.5Z" fill={body} />
      {/* cuerpo */}
      <Path d="M20 7c7.2 0 11.5 5.4 11.5 13S26.8 34 20 34 8.5 27.6 8.5 20 12.8 7 20 7Z" fill={body} />
      {/* panza */}
      <Path d="M20 18c3.6 0 6 2.6 6 6.4 0 4-2.7 6.8-6 6.8s-6-2.8-6-6.8c0-3.8 2.4-6.4 6-6.4Z" fill={belly} />
      {/* ojos */}
      <Circle cx="14.7" cy="18"   r="5.1" fill={hi} />
      <Circle cx="25.3" cy="18"   r="5.1" fill={hi} />
      <Circle cx="14.7" cy="18.4" r="2.3" fill={pupil} />
      <Circle cx="25.3" cy="18.4" r="2.3" fill={pupil} />
      <Circle cx="15.5" cy="17.5" r="0.7" fill={hi} />
      <Circle cx="26.1" cy="17.5" r="0.7" fill={hi} />
      {/* pico */}
      <Path d="M20 21.2l-2.4 2.8h4.8z" fill={beak} />
    </Svg>
  );

  if (!animated) return svg;

  return (
    <Animated.View style={{ transform: [{ translateY: floatY }] }}>
      {svg}
    </Animated.View>
  );
}
