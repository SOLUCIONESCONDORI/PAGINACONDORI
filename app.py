from flask import Flask, render_template, request, send_file, jsonify
import os

app = Flask(__name__)

# Ruta a la carpeta donde están los archivos (directorio raíz: macros)
CARPETA_ARCHIVOS = os.path.join(app.root_path, 'macros')

@app.route("/")
def inicio():
    return render_template("index.html")

@app.route("/buscar")
def buscar():
    q = request.args.get("q", "").lower()
    archivos = []

    for carpeta_actual, _, archivos_en_carpeta in os.walk(CARPETA_ARCHIVOS):
        for archivo in archivos_en_carpeta:
            if archivo.lower().endswith(".xlsx"):
                ruta_relativa = os.path.relpath(os.path.join(carpeta_actual, archivo), CARPETA_ARCHIVOS)
                if q in ruta_relativa.lower():
                    archivos.append(ruta_relativa.replace("\\", "/"))  # Windows safe

    return jsonify(archivos)

@app.route("/descargar/<path:archivo_relativo>")
def descargar(archivo_relativo):
    ruta_archivo = os.path.join(CARPETA_ARCHIVOS, archivo_relativo)
    if os.path.isfile(ruta_archivo):
        return send_file(ruta_archivo, as_attachment=True)
    return "Archivo no encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)

