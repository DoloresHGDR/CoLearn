# -*- coding: utf-8 -*-
"""
Medicion del margen del umbral de recuperacion (3.3.1).
Mide la distancia L2 minima de cada pregunta al texto, on-topic vs off-topic,
contra el umbral SIMILARITY_THRESHOLD. No usa la IA generativa, solo embeddings.
"""
import numpy as np
from app.rag.chunker import prepare_data, model
from app.rag.indexer import create_index, SIMILARITY_THRESHOLD

TEXTO = """
La fotosintesis es el proceso mediante el cual las plantas producen su alimento.
Utilizan la luz solar, el agua y el dioxido de carbono para generar glucosa y oxigeno.
Este proceso ocurre principalmente en los cloroplastos, organulos que contienen clorofila.
La clorofila es el pigmento verde que absorbe la energia luminica.
La ecuacion general de la fotosintesis es: 6CO2 + 6H2O + luz -> C6H12O6 + 6O2.
Las plantas realizan la fotosintesis durante el dia, cuando hay luz disponible.
Sin fotosintesis, no existiria oxigeno en la atmosfera ni alimento en los ecosistemas.
La tasa de fotosintesis depende de la intensidad de la luz, la temperatura y la concentracion de CO2.
"""

ON = [
    "Que es la fotosintesis?",
    "Donde ocurre la fotosintesis dentro de la celula?",
    "Que necesitan las plantas para hacer fotosintesis?",
    "Que pigmento absorbe la luz?",
    "Que produce la fotosintesis?",
    "Por que es importante la fotosintesis para la atmosfera?",
]
OFF = [
    "Cuanto cuesta un pasaje de avion a Europa?",
    "Quien gano el ultimo mundial de futbol?",
    "Como se cambia la rueda de un auto?",
    "Cual es la capital de Francia?",
    "Que ingredientes lleva una pizza napolitana?",
    "A que hora abre el supermercado?",
]

def l2_to_cos(l2):
    return 1 - (l2 ** 2) / 2

def min_dist(q):
    qe = np.array(model.encode([q], normalize_embeddings=True)).astype("float32")
    d, _ = index.search(qe, 1)
    return float(d[0][0])

chunks, embeddings = prepare_data(TEXTO)
index = create_index(embeddings)

print(f"Chunks: {len(chunks)}  |  Umbral L2 = {SIMILARITY_THRESHOLD} (cos ~ {l2_to_cos(SIMILARITY_THRESHOLD):.2f})")
print("\n== ON-TOPIC (se espera ADMITE) ==")
on_d = []
for q in ON:
    d = min_dist(q); on_d.append(d)
    print(f"  L2={d:.3f}  cos={l2_to_cos(d):.2f}  {'ADMITE ' if d <= SIMILARITY_THRESHOLD else 'RECHAZA'}  {q}")
print("\n== OFF-TOPIC (se espera RECHAZA) ==")
off_d = []
for q in OFF:
    d = min_dist(q); off_d.append(d)
    print(f"  L2={d:.3f}  cos={l2_to_cos(d):.2f}  {'ADMITE ' if d <= SIMILARITY_THRESHOLD else 'RECHAZA'}  {q}")

print("\n== RESUMEN ==")
print(f"  on-topic : min={min(on_d):.3f}  max={max(on_d):.3f}  prom={np.mean(on_d):.3f}")
print(f"  off-topic: min={min(off_d):.3f}  max={max(off_d):.3f}  prom={np.mean(off_d):.3f}")
print(f"  peor on-topic = {max(on_d):.3f}  |  mejor off-topic = {min(off_d):.3f}  |  umbral = {SIMILARITY_THRESHOLD}")
print(f"  separacion (mejor off - peor on) = {min(off_d) - max(on_d):.3f}")
aciertos = sum(1 for d in on_d if d <= SIMILARITY_THRESHOLD) + sum(1 for d in off_d if d > SIMILARITY_THRESHOLD)
print(f"  clasificacion correcta: {aciertos}/{len(ON)+len(OFF)}")
