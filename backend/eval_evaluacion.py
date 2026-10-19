# -*- coding: utf-8 -*-
"""
Medicion de la calidad de la IA (Hueco 1): clasificacion de intencion y evaluacion
de respuestas, contra una referencia humana. Cada item lleva la intencion esperada
y, si es respuesta, el veredicto esperado (si/parcial/no).

Gasta llamadas a OpenRouter (una por item). Correr desde la carpeta backend/.
"""
from app.services.chat_service import _procesar_mensaje

TEXTO = (
    "Las ballenas grises realizan una de las migraciones mas largas de todos los mamiferos. "
    "Cada ano viajan unos 16.000 kilometros entre las aguas frias del Artico, donde se alimentan "
    "durante el verano, y las lagunas calidas de Mexico, donde nacen sus crias en invierno. "
    "Durante el viaje casi no comen: viven de la grasa que acumularon en el verano. Las crias nacen "
    "en las lagunas mexicanas porque el agua es tibia y poco profunda, lo que las protege de las "
    "orcas, sus principales depredadores. Una vez que las crias crecen lo suficiente, las ballenas "
    "emprenden el regreso hacia el norte. Estas ballenas se comunican mediante sonidos graves que "
    "viajan largas distancias bajo el agua. Durante muchos anos fueron cazadas casi hasta su "
    "desaparicion, pero gracias a los acuerdos de proteccion su poblacion se recupero en gran parte."
)
CLASE = "Las ballenas grises"

Q_EASY = "Cuantos kilometros recorren las ballenas grises cada ano en su migracion?"
Q_MED = "Por que las ballenas grises tienen sus crias en las lagunas de Mexico y no en el Artico?"
Q_HARD = "Te parece importante que existan acuerdos para proteger a las ballenas? Por que?"

# Cada item: (id, pregunta, dificultad, mensaje_del_alumno, intencion_esperada, correcto_esperado)
# correcto_esperado solo aplica si la intencion esperada es "respuesta".
DATASET = [
    ("E1", Q_EASY, "easy", "Recorren como 16.000 kilometros.", "respuesta", "si"),
    ("E2", Q_EASY, "easy", "16 mil km nadando desde el artico hasta mexico", "respuesta", "si"),
    ("E3", Q_EASY, "easy", "Viajan un monton, miles de kilometros.", "respuesta", "parcial"),
    ("E4", Q_EASY, "easy", "Como 500 kilometros.", "respuesta", "no"),
    ("E5", Q_EASY, "easy", "No me acuerdo, me das una pista?", "ayuda", None),
    ("E6", Q_EASY, "easy", "Viste la pelicula de Buscando a Nemo?", "fuera_de_tema", None),

    ("M1", Q_MED, "medium", "Porque el agua es tibia y poco profunda, asi las crias estan protegidas de las orcas.", "respuesta", "si"),
    ("M2", Q_MED, "medium", "Porque ahi hace mas calor.", "respuesta", "parcial"),
    ("M3", Q_MED, "medium", "Porque en el Artico hay mucha comida.", "respuesta", "no"),
    ("M4", Q_MED, "medium", "no se", "ayuda", None),
    ("M5", Q_MED, "medium", "no se si sera porque ahi no estan las orcas", "respuesta", "si"),

    ("H1", Q_HARD, "hard", "Si, porque casi se extinguen por la caza y hay que cuidarlas para que no desaparezcan.", "respuesta", "si"),
    ("H2", Q_HARD, "hard", "Si.", "respuesta", "parcial"),
    ("H3", Q_HARD, "hard", "No, total las ballenas no sirven para nada.", "respuesta", "si"),
    ("H4", Q_HARD, "hard", "asdf jajaja", "respuesta", "no"),
    ("H5", Q_HARD, "hard", "A que hora termina la clase?", "fuera_de_tema", None),
]


def main():
    int_ok = 0
    eval_total = 0
    eval_ok = 0
    print(f"{'ID':<4}{'esp.int':<14}{'got.int':<14}{'esp.corr':<10}{'got.corr':<10}{'OK':<4} mensaje")
    print("-" * 100)
    for (cid, q, diff, msg, exp_int, exp_corr) in DATASET:
        r = _procesar_mensaje(q, msg, TEXTO, CLASE, diff)
        got_int = r.get("intencion")
        got_corr = r.get("correct") if got_int == "respuesta" else None
        int_match = got_int == exp_int
        if int_match:
            int_ok += 1
        corr_mark = ""
        if exp_int == "respuesta":
            eval_total += 1
            if int_match and got_corr == exp_corr:
                eval_ok += 1
                corr_mark = "ok"
            else:
                corr_mark = "X"
        flag = "ok" if int_match else "X"
        print(f"{cid:<4}{exp_int:<14}{str(got_int):<14}{str(exp_corr):<10}{str(got_corr):<10}{flag:<4} {msg[:40]}")

    print("-" * 100)
    print(f"Intencion: {int_ok}/{len(DATASET)} correctas")
    print(f"Evaluacion (solo respuestas): {eval_ok}/{eval_total} coinciden con la referencia")


if __name__ == "__main__":
    main()
