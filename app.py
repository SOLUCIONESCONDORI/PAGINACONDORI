from flask import Flask, render_template, request, send_from_directory, jsonify
import os

app = Flask(__name__)

# Ruta a la carpeta donde están los archivos Excel
CARPETA_ARCHIVOS = os.path.join(app.root_path, 'archivos')

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").lower()
    archivos = []
    if os.path.exists(CARPETA_ARCHIVOS):
        for archivo in os.listdir(CARPETA_ARCHIVOS):
            if archivo.lower().endswith(".xlsx") and q in archivo.lower():
                archivos.append(archivo)
    return jsonify(archivos)

@app.route("/descargar/<nombre>")
def descargar(nombre):
    return send_from_directory(CARPETA_ARCHIVOS, nombre, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
