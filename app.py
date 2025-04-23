from flask import Flask, render_template, request, redirect, url_for, session
import json, random, time, os

app = Flask(__name__)
app.secret_key = 'clave_secreta_para_sesiones'

RESULTADOS_FILE = 'resultados.json'

def cargar_preguntas():
    with open("questions.json", "r", encoding="utf-8") as file:
        preguntas = json.load(file)
    random.shuffle(preguntas)
    return preguntas[:6]

def calcular_puntaje(preguntas, respuestas_usuario):
    puntaje_total = 0
    resultados = []
    for i, pregunta in enumerate(preguntas):
        correcta = pregunta["respuesta"]
        seleccionada = respuestas_usuario.get(f"pregunta_{i}")
        es_correcta = (seleccionada == correcta)
        puntaje = pregunta.get("dificultad", 1) if es_correcta else 0
        puntaje_total += puntaje
        resultados.append({
            "pregunta": pregunta["pregunta"],
            "correcta": correcta,
            "seleccionada": seleccionada,
            "es_correcta": es_correcta,
            "categoria": pregunta.get("categoria", "General"),
            "puntaje": puntaje,
            "dificultad": pregunta.get("dificultad", 1)
        })
    return puntaje_total, resultados

def guardar_resultado(nombre, puntaje, tiempo):
    if not os.path.exists(RESULTADOS_FILE):
        with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    with open(RESULTADOS_FILE, "r", encoding="utf-8") as f:
        datos = json.load(f)
    datos.append({"nombre": nombre, "puntaje": puntaje, "tiempo": tiempo})
    datos = sorted(datos, key=lambda x: (-x['puntaje'], x['tiempo']))[:10]  # Top 10
    with open(RESULTADOS_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=4)

def obtener_clasificacion():
    if not os.path.exists(RESULTADOS_FILE):
        return []
    
    with open(RESULTADOS_FILE, "r", encoding="utf-8") as f:
        clasificacion = json.load(f)
    
    # Filtrar solo los jugadores que han respondido todas las preguntas correctamente
    clasificacion = [jugador for jugador in clasificacion if jugador['puntaje'] == 11]

    # Ordenar por puntaje (descendente) y luego por tiempo (ascendente)
    clasificacion = sorted(clasificacion, key=lambda x: (-x['puntaje'], x['tiempo']))

    # Si hay menos de 10 jugadores, llenar con los mejores disponibles
    return clasificacion[:10]  # Limitar a los primeros 10 jugadores

@app.route("/", methods=["GET", "POST"])
def quiz():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        if not nombre:
            return redirect(url_for('quiz'))
        preguntas = cargar_preguntas()
        session['preguntas'] = preguntas
        session['nombre'] = nombre
        session['inicio'] = time.time()
        return render_template("quiz.html", preguntas=preguntas, nombre=nombre, enumerate=enumerate)
    return render_template("inicio.html")

@app.route("/resultado", methods=["POST"])
def resultado():
    preguntas = session.get('preguntas')
    nombre = session.get('nombre')
    inicio = session.get('inicio')
    if not preguntas or not nombre or not inicio:
        return redirect(url_for('quiz'))
    respuestas_usuario = request.form
    puntaje, resultados = calcular_puntaje(preguntas, respuestas_usuario)
    tiempo_total = round(time.time() - inicio, 2)
    guardar_resultado(nombre, puntaje, tiempo_total)
    clasificacion = obtener_clasificacion()
    return render_template("resultado.html", resultados=resultados, puntaje=puntaje, tiempo=tiempo_total, clasificacion=clasificacion, nombre=nombre)

@app.route("/clasificacion")
def clasificacion():
    datos = obtener_clasificacion()
    return render_template("clasificacion.html", clasificacion=datos)

@app.route("/jugar_de_nuevo")
def jugar_de_nuevo():
    nombre = request.args.get("nombre", "Jugador")
    return redirect(url_for("quiz", nombre=nombre))

if __name__ == "__main__":
    app.run(debug=True)