from flask import Flask, render_template, send_from_directory, request, jsonify
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/logo'

# Carpeta donde están los archivos Excel
CARPETA_MACROS = "macros"

@app.route('/')
def inicio():
    archivos = os.listdir(CARPETA_MACROS)
    archivos = [f for f in archivos if f.endswith(('.xls', '.xlsx', '.xlsm'))]
    return render_template("index.html", archivos=archivos)

@app.route('/descargar/<nombre_archivo>')
def descargar(nombre_archivo):
    return send_from_directory(CARPETA_MACROS, nombre_archivo, as_attachment=True)

@app.route('/buscar')
def buscar():
    consulta = request.args.get('q', '').lower()
    archivos = os.listdir(CARPETA_MACROS)
    resultados = [f for f in archivos if consulta in f.lower()]
    return jsonify(resultados)

if __name__ == '__main__':
    app.run(debug=True)
