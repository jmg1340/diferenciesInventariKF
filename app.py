import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import pandas as pd

# Importamos las funciones de procesamiento desde nuestro módulo.
from procesador_inventario import procesar_farhos, procesar_kardex, comparar_inventarios

# --- Configuración de la Aplicación Flask ---
app = Flask(__name__)
# Clave secreta para la gestión de sesiones de usuario (necesaria para el login).
app.secret_key = 'supersecretkey'
# Carpeta donde se guardarán los ficheros subidos por el usuario.
app.config['UPLOAD_FOLDER'] = 'dadesCarregades'
# Tamaño máximo permitido para los ficheros subidos (16 MB).
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Contraseña para el acceso a la aplicación.
PASSWORD = "1234"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Gestiona el acceso a la aplicación.
    - Si el método es GET, muestra el formulario de login.
    - Si el método es POST, valida la contraseña.
    """
    # Si el usuario ya ha iniciado sesión, lo redirige a la página principal.
    if 'logged_in' in session:
        return redirect(url_for('index'))

    error = None
    # Si el usuario envía el formulario (método POST).
    if request.method == 'POST':
        # Comprueba si la contraseña es correcta.
        if request.form.get('password') == PASSWORD:
            # Inicia la sesión y muestra un mensaje de éxito.
            session['logged_in'] = True
            flash('Has iniciat sesió correctament.', 'success')
            return redirect(url_for('index'))
        else:
            # Si la contraseña es incorrecta, prepara un mensaje de error.
            error = 'Pwd incorrecte. Intenta-ho de nou.'
    
    # Muestra la plantilla de login (con o sin mensaje de error).
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """
    Cierra la sesión del usuario y lo redirige a la página de login.
    """
    # Elimina la variable de sesión 'logged_in'.
    session.pop('logged_in', None)
    flash('Has tancat la sesió.', 'success')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Página principal de la aplicación.
    - Requiere que el usuario haya iniciado sesión.
    - Si el método es GET, muestra el formulario para subir ficheros.
    - Si el método es POST, procesa los ficheros y muestra los resultados.
    """
    # Si el usuario no ha iniciado sesión, lo redirige a la página de login.
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    # Si el usuario sube los ficheros (método POST).
    if request.method == 'POST':
        # --- Validación de Ficheros ---
        if 'farhos_file' not in request.files or 'kardex_file' not in request.files:
            flash('Faltan fitxers en el formulari.', 'danger')
            return redirect(request.url)

        farhos_file = request.files['farhos_file']
        kardex_file = request.files['kardex_file']

        if farhos_file.filename == '' or kardex_file.filename == '':
            flash('Un o ambdos fitxers no han sigut seleccionats.', 'danger')
            return redirect(request.url)

        # --- Procesamiento de Ficheros ---
        if farhos_file and kardex_file:
            # Asegura que los nombres de fichero sean seguros.
            farhos_filename = secure_filename(farhos_file.filename)
            kardex_filename = secure_filename(kardex_file.filename)
            
            # Crea las rutas completas para guardar los ficheros.
            farhos_path = os.path.join(app.config['UPLOAD_FOLDER'], farhos_filename)
            kardex_path = os.path.join(app.config['UPLOAD_FOLDER'], kardex_filename)
            
            # Guarda los ficheros en el servidor.
            farhos_file.save(farhos_path)
            kardex_file.save(kardex_path)

            # --- Llamada a las Funciones de Procesamiento ---
            # Llama a las funciones del módulo 'procesador_inventario' para analizar los datos.
            df_farhos = procesar_farhos(farhos_path)
            df_kardex = procesar_kardex(kardex_path)
            df_diferencias = comparar_inventarios(df_farhos, df_kardex)

            # --- Renderizado de Resultados ---
            # Si el procesamiento fue exitoso y se generó la tabla de diferencias.
            if df_diferencias is not None:
                # Convierte los DataFrames de pandas a tablas HTML.
                tablas = {
                    'farhos': df_farhos.to_html(classes='table table-striped', index=False),
                    'kardex': df_kardex.to_html(classes='table table-striped', index=False),
                    'diferencias': df_diferencias.to_html(classes='table table-striped', index=False)
                }
                # Vuelve a mostrar la página principal, pero esta vez con los resultados.
                return render_template('index.html', resultados=True, tablas=tablas)
            else:
                # Si hubo un error en el procesamiento, muestra un mensaje genérico.
                # El error específico se habrá mostrado en la consola (ver 'procesador_inventario.py').
                flash('Hi ha hagut un error al processar els fitxers. Revisa els logs o el format dels fitxers.', 'danger')
                return redirect(request.url)

    # Si el método es GET, muestra la página principal sin resultados.
    return render_template('index.html', resultados=False)

# Punto de entrada para ejecutar la aplicación.
if __name__ == '__main__':
    # Asegura que la carpeta de subidas exista.
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    # Ejecuta la aplicación en modo debug.
    app.run(debug=True, host='0.0.0.0', port=3000)
