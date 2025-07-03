from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import uuid
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Rutas
CARPETA_ARCHIVOS = os.path.join(app.root_path, 'macros')
CARPETA_TICKETS = os.path.join(app.root_path, 'tickets')
CARPETA_COMPROBANTES = os.path.join(app.root_path, 'comprobantes')

# Crear carpetas si no existen
os.makedirs(CARPETA_TICKETS, exist_ok=True)
os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)


@app.route("/")
def inicio():
    precios = {}
    try:
        with open("precios.json", "r", encoding="utf-8") as f:
            precios = json.load(f)
    except Exception as e:
        print("No se pudo cargar precios:", e)

    return render_template("index.html", precios=precios)


@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").lower()
    archivos = []
    if os.path.exists(CARPETA_ARCHIVOS):
        for archivo in os.listdir(CARPETA_ARCHIVOS):
            if q in archivo.lower():
                archivos.append(archivo)
    return jsonify(archivos)


@app.route("/solicitar-descarga", methods=["POST"])
def solicitar_descarga():
    archivo = request.form.get("archivo")
    imagen = request.files.get("comprobante")

    if not archivo or not imagen:
        return "Faltan datos", 400

    ticket = str(uuid.uuid4())
    ruta_comprobante = os.path.join(CARPETA_COMPROBANTES, f"{ticket}.jpg")
    imagen.save(ruta_comprobante)

    info = {
        "archivo": archivo,
        "estado": "pendiente",
        "descargado": False
    }

    with open(os.path.join(CARPETA_TICKETS, f"{ticket}.json"), "w") as f:
        json.dump(info, f)

    return jsonify({"ticket": ticket})


@app.route("/autorizaciones", methods=["GET", "POST"])
def autorizaciones():
    tickets = []
    for nombre_archivo in os.listdir(CARPETA_TICKETS):
        if nombre_archivo.endswith(".json"):
            ruta = os.path.join(CARPETA_TICKETS, nombre_archivo)
            with open(ruta, "r") as f:
                data = json.load(f)
            ticket_id = nombre_archivo.replace(".json", "")
            tickets.append({"ticket": ticket_id, **data})

    if request.method == "POST":
        ticket = request.form.get("ticket")
        accion = request.form.get("accion")
        ruta_ticket = os.path.join(CARPETA_TICKETS, f"{ticket}.json")
        if os.path.exists(ruta_ticket):
            with open(ruta_ticket, "r") as f:
                info = json.load(f)
            info["estado"] = "autorizado" if accion == "autorizar" else "rechazado"
            with open(ruta_ticket, "w") as f:
                json.dump(info, f)

    return render_template("autorizaciones.html", tickets=tickets)


@app.route("/descargar/<ticket>")
def descargar_archivo_autorizado(ticket):
    ruta_ticket = os.path.join(CARPETA_TICKETS, f"{ticket}.json")
    if not os.path.exists(ruta_ticket):
        return "Ticket no válido.", 404

    with open(ruta_ticket, 'r') as f:
        info = json.load(f)

    if info["estado"] != "autorizado":
        return "Este ticket no está autorizado.", 403

    if info.get("descargado", False):
        return "Este enlace ya ha sido utilizado. Para descargar nuevamente, realiza un nuevo pago.", 403

    # Marcar como descargado
    info["descargado"] = True
    with open(ruta_ticket, 'w') as f:
        json.dump(info, f)

    return send_from_directory(CARPETA_ARCHIVOS, info["archivo"], as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)




