import React, { useEffect, useRef } from "react";
import { Animated, Easing } from "react-native";
import Svg, { Path, Circle, G } from "react-native-svg";
import { colors } from "../styles/theme";

const AnimatedG      = Animated.createAnimatedComponent(G);
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

// Mascota buho tutor IA.
// onDark: invierte colores para fondos oscuros.
// animated: flotado suave + parpadeo (avatar del chat).
// intro: vuelo de entrada diagonal + aleteo de alas + respiracion + parpadeo (pantalla Welcome).
// reduceMotion: muestra el estado final sin animar.
export default function OwlMascot({ size = 34, onDark = false, animated = false, intro = false, reduceMotion = false }) {
  const body  = onDark ? colors.surface     : colors.primary;
  const belly = onDark ? colors.accent      : colors.accentSoft;
  const pupil = onDark ? colors.primaryDeep : colors.ink;
  const beak  = colors.accent;
  const hi    = "#fff";

  const playIntro = intro && !reduceMotion;
  const alive     = (animated || intro) && !reduceMotion;

  const floatY  = useRef(new Animated.Value(0)).current;
  const tx      = useRef(new Animated.Value(playIntro ? -110 : 0)).current;
  const ty      = useRef(new Animated.Value(playIntro ? -95  : 0)).current;
  const wingY   = useRef(new Animated.Value(0)).current;   // sube/baja las alas
  const scaleV  = useRef(new Animated.Value(playIntro ? 0.55 : 1)).current;
  const opacity = useRef(new Animated.Value(playIntro ? 0 : 1)).current;
  // lid: 0 = ojos abiertos, 1 = ojos cerrados (circulo del color del cuerpo cubre el ojo)
  const lid     = useRef(new Animated.Value(0)).current;

  // Respiracion en valores SEPARADOS del vuelo (no comparten translateY/scale),
  // asi la respiracion nunca "vuelve a volar" al buho.
  const breatheY     = useRef(new Animated.Value(0)).current;
  const breatheScale = useRef(new Animated.Value(1)).current;

  // translateY final = ty (posicion/aterrizaje) + wingY (aleteo) + breatheY (respiracion)
  const combinedY     = useRef(Animated.add(Animated.add(ty, wingY), breatheY)).current;
  // scale final = scaleV (entrada) * breatheScale (respiracion)
  const combinedScale = useRef(Animated.multiply(scaleV, breatheScale)).current;

  // Candado: la entrada se reproduce UNA sola vez por montaje, nunca en loop.
  const hasPlayed = useRef(false);

  // Flotado suave del avatar del chat (modo animated puro)
  useEffect(() => {
    if (!animated || intro || reduceMotion) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(floatY, { toValue: -4, duration: 900, useNativeDriver: true }),
        Animated.timing(floatY, { toValue:  0, duration: 900, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [animated, intro, reduceMotion, floatY]);

  // Vuelo de entrada: el buho vuela desde arriba-izquierda mientras las alas aletean.
  // El aleteo se hace con wingY (bounce vertical de las alas), sin rotar el buho entero,
  // para evitar que el rotate del padre interfiera con los transforms internos del SVG.
  useEffect(() => {
    if (!playIntro) return;
    if (hasPlayed.current) return;  // ya voló una vez: no repetir nunca
    hasPlayed.current = true;
    const bezier = Easing.bezier(0.16, 0.7, 0.3, 1);

    // Punto de partida del vuelo (arriba-izquierda, chico y transparente)
    tx.setValue(-110);
    ty.setValue(-95);
    wingY.setValue(0);
    scaleV.setValue(0.55);
    opacity.setValue(0);

    // 5 ciclos de aleteo (sube/baja), 220ms cada uno → 1100ms total
    const flap = Animated.sequence(
      Array.from({ length: 5 }).flatMap(() => [
        Animated.timing(wingY, { toValue: -5, duration: 110, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(wingY, { toValue:  0, duration: 110, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ])
    );

    let breatheLoopY;
    let breatheLoopScale;

    const entrance = Animated.parallel([
      Animated.timing(opacity, { toValue: 1,    duration:  280, useNativeDriver: true }),
      Animated.timing(tx,      { toValue: 0,    duration: 1200, easing: bezier, useNativeDriver: true }),
      Animated.timing(ty,      { toValue: 0,    duration: 1200, easing: bezier, useNativeDriver: true }),
      Animated.timing(scaleV,  { toValue: 1,    duration: 1200, easing: bezier, useNativeDriver: true }),
      flap,
    ]);

    entrance.start(({ finished }) => {
      if (!finished) return;
      // Respiracion suave en loop tras aterrizar. Anima valores APARTE del vuelo:
      // breatheY (-2px) y breatheScale (1.025), ciclo lento de 4.8s (2400ms x 2).
      breatheLoopY = Animated.loop(
        Animated.sequence([
          Animated.timing(breatheY, { toValue: -2, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          Animated.timing(breatheY, { toValue:  0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        ])
      );
      breatheLoopScale = Animated.loop(
        Animated.sequence([
          Animated.timing(breatheScale, { toValue: 1.025, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
          Animated.timing(breatheScale, { toValue: 1,     duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        ])
      );
      breatheLoopY.start();
      breatheLoopScale.start();
    });

    // Detener todo al desmontar (no deja loops sueltos)
    return () => {
      entrance.stop();
      breatheLoopY && breatheLoopY.stop();
      breatheLoopScale && breatheLoopScale.stop();
      tx.stopAnimation();
      ty.stopAnimation();
      wingY.stopAnimation();
      scaleV.stopAnimation();
      opacity.stopAnimation();
      breatheY.stopAnimation();
      breatheScale.stopAnimation();
    };
  }, [playIntro]);

  // Parpadeo doble natural. El "parpado" es un AnimatedCircle del color del cuerpo
  // que tapa el ojo con opacity: evita el problema de pivot que tenia scaleY en AnimatedG.
  useEffect(() => {
    if (!alive) return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.delay(1100),
        Animated.timing(lid, { toValue: 1, duration: 55, useNativeDriver: false }),
        Animated.timing(lid, { toValue: 0, duration: 55, useNativeDriver: false }),
        Animated.timing(lid, { toValue: 1, duration: 55, useNativeDriver: false }),
        Animated.timing(lid, { toValue: 0, duration: 55, useNativeDriver: false }),
        Animated.delay(2200),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [alive, lid]);

  // AnimatedG para las alas: sube/baja con wingY durante el aleteo de entrada
  const wingTranslate = wingY.interpolate({ inputRange: [-5, 0], outputRange: [-5, 0] });

  const svg = (
    <Svg width={size} height={size} viewBox="0 0 40 40" fill="none">
      {/* alas animadas (solo en animated/intro) */}
      {(animated || intro) ? (
        <AnimatedG style={{ transform: [{ translateY: wingTranslate }] }}>
          <Path d="M14 14 C6 15, 4.5 24, 10 28 C12.5 24, 13 19, 16.5 16.5 Z" fill={body} />
          <Path d="M26 14 C34 15, 35.5 24, 30 28 C27.5 24, 27 19, 23.5 16.5 Z" fill={body} />
        </AnimatedG>
      ) : null}
      {/* orejas */}
      <Path d="M12 10L14.5 4.5L18 10.5Z" fill={body} />
      <Path d="M28 10L25.5 4.5L22 10.5Z" fill={body} />
      {/* cuerpo */}
      <Path d="M20 7c7.2 0 11.5 5.4 11.5 13S26.8 34 20 34 8.5 27.6 8.5 20 12.8 7 20 7Z" fill={body} />
      {/* panza */}
      <Path d="M20 18c3.6 0 6 2.6 6 6.4 0 4-2.7 6.8-6 6.8s-6-2.8-6-6.8c0-3.8 2.4-6.4 6-6.4Z" fill={belly} />
      {/* ojo izquierdo */}
      <Circle cx="14.7" cy="18"   r="5.1" fill={hi} />
      <Circle cx="14.7" cy="18.4" r="2.3" fill={pupil} />
      <Circle cx="15.5" cy="17.5" r="0.7" fill={hi} />
      {/* ojo derecho */}
      <Circle cx="25.3" cy="18"   r="5.1" fill={hi} />
      <Circle cx="25.3" cy="18.4" r="2.3" fill={pupil} />
      <Circle cx="26.1" cy="17.5" r="0.7" fill={hi} />
      {/* parpados: circulos del color del cuerpo que cubren los ojos al parpadear.
          Quedan encima de los ojos (orden SVG) y su opacity se anima de 0 a 1. */}
      <AnimatedCircle cx="14.7" cy="18" r="5.1" fill={body} opacity={lid} />
      <AnimatedCircle cx="25.3" cy="18" r="5.1" fill={body} opacity={lid} />
      {/* pico */}
      <Path d="M20 21.2l-2.4 2.8h4.8z" fill={beak} />
    </Svg>
  );

  if (intro) {
    return (
      <Animated.View style={{ opacity, transform: [{ translateX: tx }, { translateY: combinedY }, { scale: combinedScale }] }}>
        {svg}
      </Animated.View>
    );
  }

  if (!animated) return svg;

  return (
    <Animated.View style={{ transform: [{ translateY: floatY }] }}>
      {svg}
    </Animated.View>
  );
}
