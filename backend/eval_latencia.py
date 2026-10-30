# -*- coding: utf-8 -*-
"""
Medicion de latencia y costo de las llamadas a la IA (MET-12): generacion de la actividad
y respuesta del tutor en el modo de evaluacion. Informa p50/p95 y el costo real que devuelve
OpenRouter por llamada, y con eso estima el costo de una actividad.

Gasta llamadas a OpenRouter. Correr desde la carpeta backend/: python eval_latencia.py [salida.json]
"""
import json
import statistics
import sys
import time
from datetime import datetime

import app.core.llm as llm
from app.core.config import OPENROUTER_MODEL
from app.services.chat_service import _generar_pista, _procesar_mensaje
from app.services.generation_service import generate_activity
from eval_evaluacion import CLASE, DATASET, TEXTO

N_GENERACIONES = 15
N_VUELTAS_CHAT = 2  # cada vuelta recorre los 16 mensajes del conjunto de evaluacion

llamadas = []  # una entrada por llamada a OpenRouter
etiqueta = ""
_post_original = llm.requests.post


def _post_medido(url, **kwargs):
    # Pide a OpenRouter el costo real de la llamada y mide el tiempo de ida y vuelta
    kwargs["json"] = {**kwargs["json"], "usage": {"include": True}}
    inicio = time.perf_counter()
    resp = _post_original(url, **kwargs)
    segundos = time.perf_counter() - inicio
    uso = resp.json().get("usage", {})
    llamadas.append({
        "tipo": etiqueta,
        "segundos": segundos,
        "tokens_entrada": uso.get("prompt_tokens", 0),
        "tokens_salida": uso.get("completion_tokens", 0),
        "costo_usd": uso.get("cost", 0.0),
    })
    return resp


llm.requests.post = _post_medido


def percentil(valores, p):
    orden = sorted(valores)
    k = (len(orden) - 1) * p / 100
    i = int(k)
    return orden[i] if i + 1 >= len(orden) else orden[i] + (orden[i + 1] - orden[i]) * (k - i)


def resumen(valores):
    return {"n": len(valores), "p50": percentil(valores, 50), "p95": percentil(valores, 95),
            "min": min(valores), "max": max(valores)}


def main():
    global etiqueta
    # 1) Generacion de la actividad (una llamada por clase)
    etiqueta = "generacion"
    for i in range(N_GENERACIONES):
        generate_activity(level="7mo grado de primaria", focuses=["Inferencia"], context=TEXTO)
        print(f"generacion {i + 1}/{N_GENERACIONES}: {llamadas[-1]['segundos']:.1f} s")

    # 2) Respuesta del tutor: evaluacion del mensaje y, si corresponde, la pista
    por_mensaje = []
    for vuelta in range(N_VUELTAS_CHAT):
        for (cid, q, diff, msg, _, _) in DATASET:
            inicio = time.perf_counter()
            etiqueta = "evaluacion"
            r = _procesar_mensaje(q, msg, TEXTO, CLASE, diff)
            if r.get("intencion") == "ayuda":
                etiqueta = "pista"
                _generar_pista(q, TEXTO)
            elif r.get("intencion") == "respuesta" and r.get("correct") == "no":
                etiqueta = "pista"
                _generar_pista(q, TEXTO, student_answer=msg)
            por_mensaje.append(time.perf_counter() - inicio)
            print(f"chat {vuelta + 1}-{cid}: {por_mensaje[-1]:.1f} s")

    def de_tipo(t, campo):
        return [c[campo] for c in llamadas if c["tipo"] == t]

    res = {
        "fecha": datetime.now().isoformat(timespec="minutes"),
        "modelo": OPENROUTER_MODEL,
        "latencia_generacion_s": resumen(de_tipo("generacion", "segundos")),
        "latencia_respuesta_tutor_s": resumen(por_mensaje),
        "latencia_por_llamada_s": {t: resumen(de_tipo(t, "segundos")) for t in ("evaluacion", "pista")},
        "costo_medio_usd": {t: statistics.mean(de_tipo(t, "costo_usd")) for t in ("generacion", "evaluacion", "pista")},
        "tokens_medios": {t: {"entrada": statistics.mean(de_tipo(t, "tokens_entrada")),
                              "salida": statistics.mean(de_tipo(t, "tokens_salida"))}
                          for t in ("generacion", "evaluacion", "pista")},
        "costo_total_usd": sum(c["costo_usd"] for c in llamadas),
        "llamadas": len(llamadas),
    }
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if len(sys.argv) > 1:
        json.dump({"resumen": res, "detalle": llamadas, "por_mensaje": por_mensaje},
                  open(sys.argv[1], "w", encoding="utf-8"), indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
