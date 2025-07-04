from flask import Flask, render_template, request, send_from_directory, jsonify, session, redirect, url_for
import os
import uuid
import json
from werkzeug.utils import secure_filename
from PIL import Image
import io

app = Flask(__name__)
app.secret_key = 'clave-secreta-muy-segura'  # Cambiar por una clave segura

USUARIO_ADMIN = "admin"
CLAVE_ADMIN = "1234"

# Seguridad: límite de tamaño de subida a 5 MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024

# Extensiones permitidas
EXTENSIONES_PERMITIDAS = {'jpg', 'jpeg', 'png'}

def extension_valida(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS

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

    if not extension_valida(imagen.filename):
        return "Extensión de archivo no permitida", 400

    try:
        imagen_bytes = imagen.read()
        Image.open(io.BytesIO(imagen_bytes)).verify()
        imagen.stream.seek(0)
    except Exception:
        return "El archivo no es una imagen válida", 400

    ticket = str(uuid.uuid4())
    nombre_archivo = secure_filename(imagen.filename)
    extension = os.path.splitext(nombre_archivo)[1].lower()
    nombre_comprobante = f"{ticket}{extension}"
    ruta_comprobante = os.path.join(CARPETA_COMPROBANTES, nombre_comprobante)
    imagen.save(ruta_comprobante)

    info = {
        "ticket": ticket,
        "archivo": archivo,
        "estado": "pendiente",
        "descargado": False,
        "comprobante": nombre_comprobante
    }

    with open(os.path.join(CARPETA_TICKETS, f"{ticket}.json"), "w", encoding="utf-8") as f:
        json.dump(info, f)

    return jsonify({"ticket": ticket})

@app.route("/autorizaciones", methods=["GET", "POST"])
def autorizaciones():
    if not session.get("autenticado"):
        return redirect(url_for("login"))

    tickets = []
    for nombre_archivo in os.listdir(CARPETA_TICKETS):
        if nombre_archivo.endswith(".json"):
            ruta = os.path.join(CARPETA_TICKETS, nombre_archivo)
            with open(ruta, "r", encoding="utf-8") as f:
                data = json.load(f)
            ticket_id = nombre_archivo.replace(".json", "")
            tickets.append({"ticket": ticket_id, **data})

    if request.method == "POST":
        ticket = request.form.get("ticket")
        accion = request.form.get("accion")
        ruta_ticket = os.path.join(CARPETA_TICKETS, f"{ticket}.json")
        if os.path.exists(ruta_ticket):
            with open(ruta_ticket, "r", encoding="utf-8") as f:
                info = json.load(f)
            info["estado"] = "autorizado" if accion == "autorizar" else "rechazado"
            with open(ruta_ticket, "w", encoding="utf-8") as f:
                json.dump(info, f)

    return render_template("autorizaciones.html", tickets=tickets)

@app.route("/descargar/<ticket>")
def descargar_archivo_autorizado(ticket):
    ruta_ticket = os.path.join(CARPETA_TICKETS, f"{ticket}.json")
    if not os.path.exists(ruta_ticket):
        return "Ticket no válido.", 404

    with open(ruta_ticket, 'r', encoding='utf-8') as f:
        info = json.load(f)

    if info["estado"] != "autorizado":
        return "Este ticket no está autorizado.", 403

    if info.get("descargado", False):
        return "Este enlace ya ha sido utilizado. Para descargar nuevamente, realiza un nuevo pago.", 403

    info["descargado"] = True
    with open(ruta_ticket, 'w', encoding='utf-8') as f:
        json.dump(info, f)

    return send_from_directory(CARPETA_ARCHIVOS, info["archivo"], as_attachment=True)

@app.route("/comprobantes/<nombre>")
def ver_comprobante(nombre):
    return send_from_directory(CARPETA_COMPROBANTES, nombre)

@app.route("/consultar", methods=["GET", "POST"])
def consultar():
    mensaje = ""
    info = None

    if request.method == "POST":
        ticket = request.form.get("ticket")
        ruta_ticket = os.path.join(CARPETA_TICKETS, f"{ticket}.json")
        if os.path.exists(ruta_ticket):
            with open(ruta_ticket, "r", encoding="utf-8") as f:
                info = json.load(f)
            info["ticket"] = ticket
        else:
            mensaje = "Ticket no encontrado."

    return render_template("consultar.html", info=info, mensaje=mensaje)

@app.route("/precios.json")
def obtener_precios():
    return send_from_directory(".", "precios.json")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        usuario = request.form.get("usuario")
        clave = request.form.get("clave")
        if usuario == USUARIO_ADMIN and clave == CLAVE_ADMIN:
            session["autenticado"] = True
            return redirect(url_for("autorizaciones"))
        else:
            error = "Credenciales inválidas"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop("autenticado", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)



