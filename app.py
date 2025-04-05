# Librerias a usar
from flask import Flask, request, render_template, redirect, url_for, flash, session, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from email.message import EmailMessage
from email.mime.image import MIMEImage
import smtplib
import os
import random
import string
from google_auth_oauthlib.flow import Flow
from datetime import datetime, timedelta  # Importamos datetime
import requests
import stripe
import time

# Función para generar un PIN aleatorio de 6 dígitos
def generar_pin():
    return ''.join(random.choices(string.digits, k=6))

def cargar_y_modificar_html(ruta_html, pin):
    """
    Carga un archivo HTML, reemplaza las variables globales del usuario, el PIN y el tiempo de validez.
    
    :param ruta_html: Ruta del archivo HTML a cargar.
    :param pin: Código PIN generado.
    :return: HTML modificado como string o None si hay un error.
    """
    global nombre_usuario, correo_usuario, PIN_EXPIRATION_SECONDS  # Asegurar que usa las variables globales

    try:
        # Leer el contenido del archivo HTML
        with open(ruta_html, "r", encoding="utf-8") as archivo:
            contenido_html = archivo.read()
        
        # Diccionario con los valores a reemplazar en la plantilla HTML
        reemplazos = {
            "[Nombre]": nombre_usuario if nombre_usuario else "Usuario",
            "[Código]": pin,
            "[Tiempo de validez]": str(PIN_EXPIRATION_SECONDS // 60)  # Convertir segundos a minutos
        }

        # Reemplazar cada variable en el HTML
        for clave, valor in reemplazos.items():
            contenido_html = contenido_html.replace(clave, valor)

        return contenido_html

    except FileNotFoundError:
        print(f"Error: No se encontró el archivo HTML en {ruta_html}.")
        return None

    except Exception as e:
        print(f"Error al procesar el HTML: {e}")
        return None

def enviar_correo(remitente, contraseña, destino, asunto, mensaje):
    """
    Envía un correo electrónico con HTML modificado.
    """
    try:
        email = EmailMessage()
        email["From"] = remitente
        email["To"] = destino
        email["Subject"] = asunto
        email.set_content(mensaje, subtype='html')  # HTML como cuerpo del correo

        # Configurar SMTP
        stmp = smtplib.SMTP_SSL("smtp.gmail.com")
        stmp.login(remitente, contraseña)
        stmp.sendmail(remitente, destino, email.as_string())
        stmp.quit()

        print(f"Correo enviado exitosamente a {destino}.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")

# Crear un archivo con variables y tomarlas de aqui
# Configuración de la base de datos
DB_CONFIG = {
    "host": "bovqplubijydcjcfchpc-mysql.services.clever-cloud.com",
    "port": 3306,
    "user": "udwxzfcpj17kawho",
    "password": "1qO6vuO4sfHYS6WPeU2y",
    "database": "bovqplubijydcjcfchpc"
}

# Variable para el uso de autenticacion de google
state_global = None

id_usuario_global = None
correo_usuario_global = None
nombre_usuario_global = None
nombre_usuario = None
correo_usuario = None
pin = None
pin_timestamp = None  # Tiempo en que se generó el PIN
PIN_EXPIRATION_SECONDS = 300  # Por ejemplo, 5 minutos

# banderas
usuario_google = False
usuario_normal = False
primera_compra = False
paquete_adquirido = False

# Inicializar la aplicación Flask
app = Flask(__name__)
app.secret_key = 'clave-secreta-unica-y-segura' # cambiar por una llave

# Para la pasarela de pago
app.config['STRIPE_PUBLIC_KEY'] = 'pk_test_51IJ6UsBRC8zXI5uuDPPTI5tM2lvMQG7w9deejuUdb1zFvib6bGtAPCyXU9w4rkqRVQ85etNIAtE7Y0sPCUqUNcZB00pUjb7jeU'
app.config['STRIPE_SECRET_KEY'] = 'sk_test_51IJ6UsBRC8zXI5uuxqtNsH7OWnemGw9thmFmvsiZmReW3z3RlbXl8Hfpuftm3mg472GT6NS8K6jmnPB0CqTUtVj500Hj4shzyU'
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Ruta donde está la plantilla HTML
RUTA_CARPETA = "templates"  
ARCHIVO_HTML = "Codigo_verificacion.html"
LOGO_PATH = "static/imagen/Logo_Valkin_9.png"

# Configuración del remitente y contraseña de donde se va enviar los correos
REMITENTE = "hernadezken123@gmail.com"
CONTRASEÑA = "dirw juhp hoxc bugb"  # Reemplaza esto por la contraseña de aplicación de Google

# Crear conexión global a la base de datos
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print("Error al conectar a la base de datos:", e)
        return None

# Ruta de Login
@app.route('/', methods=['GET', 'POST'])
def login():
    global id_usuario_global, usuario_normal, nombre_usuario
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True, buffered=True)
                query = "SELECT * FROM Usuarios WHERE correo = %s LIMIT 1"
                cursor.execute(query, (email,))
                user = cursor.fetchone()

                if user and user['contrasena'] and check_password_hash(user['contrasena'], password):
                    session['user_id'] = user['id_usuario']  # Guarda solo el ID en la sesión
                    id_usuario_global = user['id_usuario']
                    nombre_usuario = user['nombre']

                    usuario_normal = True
                    usuario_google = False
                    print(nombre_usuario)
                    print(usuario_normal)
                    print(usuario_google)
                    if request.headers.get('Accept') == 'application/json':
                        return jsonify({
                            "status": "success",
                            "message": "Bienvenido",
                            "user": nombre_usuario
                        })
                    else:
                        return redirect(url_for('home'))
                else:
                    flash("Correo o contraseña incorrectos", "error")
                    return redirect(url_for('login'))
            except mysql.connector.Error as err:
                print(f"Error en la consulta: {err}")
                flash("Error interno del servidor", "error")
                return redirect(url_for('login'))
            finally:
                cursor.close()
                connection.close()
        else:
            flash("Error al conectar a la base de datos", "error")
            return redirect(url_for('login'))

    return render_template('Login.html')
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función de registro de usuario a la página
@app.route('/registro', methods=['GET', 'POST'])
def register():
    global nombre_usuario, correo_usuario

    if request.method == 'POST':
        # Capturar datos del formulario
        email = request.form.get('email')
        nombre = request.form.get('nombre')
        terms_conditions = request.form.get('terms_conditions')
        privacy_policy = request.form.get('privacy_policy')

        # Validar que no haya campos vacíos
        if not email or not nombre:
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for('register'))

        # Verificar que el usuario haya aceptado los términos y el aviso de privacidad
        if not terms_conditions or not privacy_policy:
            flash("Debes aceptar los términos y condiciones y el aviso de privacidad.", "error")
            return redirect(url_for('register'))

        try:
            # Conectar a la base de datos
            connection = get_db_connection()
            if connection is None:
                flash("Error al conectar a la base de datos", "error")
                return redirect(url_for('register'))

            cursor = connection.cursor(dictionary=True)

            # Verificar si el correo ya existe en alguna de las tablas (Usuarios o Usuarios_Google)
            cursor.execute("""
                SELECT 'Usuarios' AS source FROM Usuarios WHERE correo = %s 
                UNION ALL 
                SELECT 'Usuarios_Google' AS source FROM Usuarios_Google WHERE correo = %s
            """, (email, email))

            usuario_existente = cursor.fetchone()

            if usuario_existente:
                if usuario_existente["source"] == "Usuarios":
                    flash("El correo ya está registrado como usuario normal.", "error")
                elif usuario_existente["source"] == "Usuarios_Google":
                    flash("El correo ya está registrado con Google. Inicia sesión con Google.", "error")
                return redirect(url_for('register'))  # Evita continuar con el registro

            # Solo si el usuario NO existe, se asignan las variables globales y se envía el PIN
            correo_usuario = email
            nombre_usuario = nombre

            flash("Registro exitoso. Se ha enviado un PIN a tu correo.", "success")
            return envio_pin()

        except mysql.connector.Error as e:
            print(f"Error al verificar usuario: {e}")
            flash("Error en el registro. Intenta nuevamente.", "error")
            return redirect(url_for('register'))

        finally:
            if cursor:
                cursor.fetchall()  # Evita errores con cursores abiertos
                cursor.close()
            if connection:
                connection.close()

    return render_template('Register.html')

# Ruta para terminos y condiciones
@app.route('/terminos', methods=['GET', 'POST'])
def terminos():
      return render_template('Terminos_Condiciones.html')

# Ruta para aviso de privacidad
@app.route('/privacidad', methods=['GET', 'POST'])
def privacidad():
    return render_template('Aviso_Privacidad.html')

@app.route('/envio_pin', methods=['POST'])
def envio_pin():
    global pin, pin_timestamp, correo_usuario  # Asegurar que usa las variables globales

    if not correo_usuario:
        return jsonify({"error": "Correo no proporcionado"}), 400

    pin = generar_pin()  # Generar el PIN
    pin_timestamp = time.time()  # Guardar el tiempo de generación del PIN

    # Cargar y modificar el HTML con el PIN
    ruta_html = os.path.join(RUTA_CARPETA, ARCHIVO_HTML)
    html_modificado = cargar_y_modificar_html(ruta_html, pin)

    if html_modificado:
        enviar_correo(REMITENTE, CONTRASEÑA, correo_usuario, "Código de Verificación", html_modificado)
        return redirect(url_for('validacion', correo=correo_usuario))
    else:
        return jsonify({"error": "No se pudo cargar la plantilla HTML"}), 500

# Funcion de reenvio de PIN por si no le llego, pero es mas para cuando puso mal el correo
@app.route('/reenvio/<destino>', methods=['GET','POST'])
def reenvio():
    global pin, pin_timestamp, correo_usuario  # Asegurar que usa las variables globales

    if not correo_usuario:
        return jsonify({"error": "Correo no proporcionado"}), 400

    pin = generar_pin()  # Generar el PIN
    pin_timestamp = time.time()  # Guardar el tiempo de generación del PIN

    # Cargar y modificar el HTML con el PIN
    ruta_html = os.path.join(RUTA_CARPETA, ARCHIVO_HTML)
    html_modificado = cargar_y_modificar_html(ruta_html, pin)

    if html_modificado:
        enviar_correo(REMITENTE, CONTRASEÑA, correo_usuario, "Código de Verificación", html_modificado)
        return redirect(url_for('validacion', correo=correo_usuario))
    else:
        return jsonify({"error": "No se pudo cargar la plantilla HTML"}), 500

# Funcion para la validacion del PIN
@app.route('/validacion', methods=['GET', 'POST'])
def validacion():
    global pin, pin_timestamp
    
    correo = request.args.get('correo')  # Obtener el correo desde los parámetros de la URL
    
    if not correo:  # Verificar si no se recibe el correo
        flash("Correo no proporcionado.", "error")
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        pin_ingresado = request.form.get('pin')  # Captura el PIN ingresado

        # Validar que el PIN no esté vacío
        if not pin_ingresado:
            flash("Por favor ingrese el PIN.", "error")
            return redirect(url_for('validacion', correo=correo))
        
        # Verificar si el PIN es correcto y aún no ha expirado
        if pin_ingresado == pin and (time.time() - pin_timestamp) <= PIN_EXPIRATION_SECONDS:
            return redirect(url_for('contrasena', correo=correo))
        else:
            flash("PIN incorrecto o expirado.", "error")
        
    return render_template('Validacion.html', correo=correo)

# Funcion para colocar la contraseña de acceso del usuario
# Modificar para que sea mas simple
@app.route('/contrasena', methods=['GET', 'POST'])
def contrasena():
    global nombre_usuario, correo_usuario  # Usamos las variables globales para el nombre y correo
    # Verificar que el nombre y el correo no sean None (asegúrate de que están definidos previamente)
    if not nombre_usuario or not correo_usuario:
        print("Nombre o correo no proporcionado")
        message = "Nombre o correo no proporcionado"
        message_color = "red"
        return render_template('Password.html', message=message, message_color=message_color)

    print(f"Correo recibido: {correo_usuario}, Nombre recibido: {nombre_usuario}")
    
    cursor = None
    connection = None
    if request.method == 'POST':
        # Capturar la nueva contraseña y la confirmación
        nueva_contrasena = request.form.get('password')
        confirmar_contrasena = request.form.get('confirm-password')

        print(f"Contraseña nueva: {nueva_contrasena}")
        print(f"Confirmar contraseña: {confirmar_contrasena}")

        # Validar que las contraseñas coincidan
        if nueva_contrasena != confirmar_contrasena:
            print("Las contraseñas no coinciden")
            message = "Las contraseñas no coinciden"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        # Validar que la contraseña cumpla con los requisitos
        if len(nueva_contrasena) < 8:
            print("La contraseña no cumple con el requisito de longitud")
            message = "La contraseña debe tener al menos 8 caracteres"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        # Aquí puedes agregar más validaciones si es necesario

        try:
            # Generar el hash de la nueva contraseña
            hashed_password = generate_password_hash(nueva_contrasena)
            print(f"Contraseña hasheada: {hashed_password}")

            # Conectar a la base de datos
            connection = mysql.connector.connect(**DB_CONFIG)
            cursor = connection.cursor()

            print("Conexión a la base de datos establecida")

            # Insertar usuario con valores NULL en los campos opcionales
            query_insert = """
                INSERT INTO Usuarios (foto_perfil, nombre, apellidos, correo, contrasena, telefono, direccion, fecha_nacimiento, tipo_perfil, horas_adquiridas, horas_usadas, institucion, id_dispositivo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            valores = (
                None, nombre_usuario, None, correo_usuario, hashed_password, None, None, None, 
                "usuario", 0, 0, None, None
            )
            cursor.execute(query_insert, valores)
            connection.commit()

            print(f"{cursor.rowcount} filas afectadas por la inserción")

            # Verificar si la inserción fue exitosa
            if cursor.rowcount > 0:
                message = "Usuario registrado y contraseña actualizada con éxito"
                message_color = "green"
                # Redirigir al login ("/")
                return redirect('/', code=302)  # Redirige al login con código de redirección permanente

            else:
                message = "No se pudo registrar al usuario. Intenta nuevamente."
                message_color = "red"

            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        except mysql.connector.Error as err:
            # Manejar errores de base de datos
            print(f"Error en la base de datos: {err}")
            message = f"Error en la base de datos: {err}"
            message_color = "red"
            return render_template('Password.html', correo=correo_usuario, message=message, message_color=message_color)

        finally:
            # Cerrar la conexión y el cursor de la base de datos
            if cursor:
                cursor.close()
                print("Cursor cerrado")
            if connection:
                connection.close()
                print("Conexión cerrada")

    # Si la solicitud es GET, renderizar el formulario con el correo
    print("Método GET, mostrando formulario con correo")
    return render_template('Password.html', correo=correo_usuario)

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para el olvido de contraseña y se quiere restablecer
@app.route("/olvido", methods=['GET', 'POST'])
def olvido():
    global correo_usuario  # Asegurar que usa la variable global

    if request.method == 'POST':
        correo_usuario = request.form.get('email')

        if not correo_usuario:
            return jsonify({"error": "Correo no proporcionado"}), 400

        return envio_pin()  # Llama a la función existente para enviar el PIN

    # Si es GET, mostrar el formulario para ingresar el correo
    return render_template('olvido.html')


# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Función para entrar al home de la página
# ver la forma de tomar las reservaciones y cambiar lo de microsft tanto nombre como imagen
@app.route('/home', methods=['GET', 'POST'])
def home():
    global nombre_usuario, usuario_google, usuario_normal, id_usuario_global

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # 🔹 Determinar filtro según tipo de usuario
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
            valor_usuario = id_usuario_global
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
            valor_usuario = id_usuario_global
        else:
            return jsonify({"status": "error", "message": "Usuario no identificado"}), 400

        # 🔹 Actualizar reservas vencidas (solo si la fecha_reserva es menor a la fecha actual)
        cursor.execute(f"""
            UPDATE Reservas
            SET estado_reserva = 'inactivo'
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo'
            AND DATE(fecha_reserva) < CURDATE()
        """, (valor_usuario,))
        connection.commit()

        # 🔹 Obtener la suma total de horas utilizadas (Horas Activas)
        cursor.execute(f"""
            SELECT COALESCE(SUM(horas_utilizadas), 0) AS horas_activas 
            FROM HorasPaquete 
            WHERE {filtro_usuario}
        """, (valor_usuario,))
        horas_activas = cursor.fetchone()["horas_activas"]

        # 🔹 Calcular el promedio de horas utilizadas en la última semana
        cursor.execute(f"""
            SELECT COALESCE(ROUND(AVG(horas_utilizadas), 1), 0) AS promedio_horas
            FROM HorasPaquete
            WHERE {filtro_usuario} 
            AND fecha_pago >= NOW() - INTERVAL 7 DAY
        """, (valor_usuario,))
        promedio_horas = cursor.fetchone()["promedio_horas"]

    except mysql.connector.Error as e:
        print(f"Error en la base de datos: {e}")
        horas_activas, promedio_horas = 0, 0

    finally:
        cursor.close()
        connection.close()

    # Si la solicitud es JSON, devolver los datos
    if request.headers.get('Accept') == 'application/json':
        return jsonify({
            "status": "success",
            "message": "Bienvenido",
            "user": nombre_usuario,
            "horas_activas": horas_activas,
            "promedio_horas": promedio_horas
        })

    # Si la solicitud es normal (desde un navegador), renderizar el HTML
    return render_template('Home.html', user=nombre_usuario, horas_activas=horas_activas, promedio_horas=promedio_horas)

# Funcion de los productos de la tienda
@app.route('/tienda', methods=['POST','GET'])
def tienda():
    return render_template('tienda.html')

@app.route('/paquetes', methods=['GET'])
def paquetes():
    global primera_compra, id_usuario_global, usuario_google, usuario_normal, paquete_adquirido

    if not id_usuario_global:
        return redirect(url_for('login'))

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Verificar si el usuario ha comprado antes
        if usuario_google:
            cursor.execute("""
                SELECT EXISTS(SELECT 1 FROM Pagos WHERE id_usuario_google = %s) AS ha_comprado
            """, (id_usuario_global,))
        elif usuario_normal:
            cursor.execute("""
                SELECT EXISTS(SELECT 1 FROM Pagos WHERE id_usuario = %s) AS ha_comprado
            """, (id_usuario_global,))
        else:
            return redirect(url_for('login'))

        resultado = cursor.fetchone()
        primera_compra = not bool(resultado['ha_comprado'])

        # Buscar un paquete activo
        cursor.execute("""
            SELECT id_pago, id_paquete 
            FROM Pagos 
            WHERE (id_usuario = %s OR id_usuario_google = %s) 
            AND estado = 'paid' 
            AND estado_paquete = 'no consumido'
        """, (id_usuario_global, id_usuario_global))

        pago = cursor.fetchone()
        paquete_adquirido = bool(pago)

        return render_template('paquetes.html', 
                               primera_compra=primera_compra, 
                               paquete_adquirido=paquete_adquirido)

    except mysql.connector.Error as e:
        print(f"Error en la base de datos: {e}")
        return jsonify({"error": f"Error en la base de datos: {e}"}), 500
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# Funcion para las reservaciones cambiar
# Cambiar para que distinga entre usuario normal y google y verifique disponibilidad de fecha y hora
# Cambiar para que acepte el forma de fecha y hora del frontend
@app.route('/reservacion', methods=['GET', 'POST'])
def reservacion():
    global usuario_normal, usuario_google, primera_compra, id_usuario_global

    if request.method == 'POST':
        # 📌 Verificar autenticación del usuario
        if not (usuario_normal or usuario_google):
            return jsonify({"success": False, "error": "Debes iniciar sesión"}), 400

        # 📌 Capturar datos del formulario
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')  # Puede venir como "14" en lugar de "14:00"
        duracion = request.form.get('duracion')

        print(f"📥 Recibido → Fecha: {fecha}, Hora: {hora}, Duración: {duracion}")

        if not fecha or not hora or not duracion:
            return jsonify({"success": False, "error": "Todos los campos son obligatorios"}), 400

        try:
            duracion = int(duracion)  # Convertir duración a entero
            
            # 🕒 Normalizar la hora (asegurarse de que tenga formato HH:MM:SS)
            if ":" not in hora:
                hora = f"{hora}:00"

            # 📌 Unir fecha y hora en un formato válido
            fecha_reserva = f"{fecha} {hora}:00"
            fecha_reserva = datetime.strptime(fecha_reserva, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")

            print(f"✅ Fecha de reserva final: {fecha_reserva}")

        except ValueError as e:
            print(f"❌ Error en conversión de fecha/hora: {e}")
            return jsonify({"success": False, "error": "Formato de fecha u hora inválido"}), 400

        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            # 🔹 1️⃣ Determinar filtro según tipo de usuario
            if usuario_normal:
                filtro_usuario = "id_usuario = %s"
                valor_usuario = id_usuario_global
            elif usuario_google:
                filtro_usuario = "id_usuario_google = %s"
                valor_usuario = id_usuario_global
            else:
                return jsonify({"success": False, "error": "Usuario no identificado"}), 400

            # 🔹 2️⃣ Verificar si la fecha y hora ya están ocupadas
            horas_ocupadas = set()
            cursor.execute("""
                SELECT HOUR(fecha_reserva) as hora_inicio, duracion 
                FROM Reservas 
                WHERE DATE(fecha_reserva) = %s AND estado_reserva = 'Activo'
            """, (fecha,))

            reservas = cursor.fetchall()
            for r in reservas:
                for h in range(r['hora_inicio'], r['hora_inicio'] + r['duracion']):
                    if 0 <= h < 24:
                        horas_ocupadas.add(h)

            hora_inicio = int(hora.split(':')[0])
            for h in range(hora_inicio, hora_inicio + duracion):
                if h in horas_ocupadas:
                    return jsonify({"success": False, "error": "La hora seleccionada y las siguientes están ocupadas"}), 400

            # 🔹 3️⃣ Buscar un pago válido
            cursor.execute(f"""
                SELECT id_pago, id_paquete, fecha_pago FROM Pagos 
                WHERE estado = 'paid' AND estado_paquete = 'no consumido'
                AND {filtro_usuario}
                LIMIT 1
            """, (valor_usuario,))

            pago = cursor.fetchone()
            if not pago:
                return jsonify({"success": False, "error": "No tienes un pago válido"}), 400

            id_pago = pago['id_pago']
            id_paquete = pago['id_paquete']
            fecha_pago = pago['fecha_pago']

            # 🔹 4️⃣ Verificar horas restantes en `HorasPaquete`
            cursor.execute("SELECT horas_restantes FROM HorasPaquete WHERE id_pago = %s", (id_pago,))
            horas_paquete = cursor.fetchone()

            if horas_paquete:
                horas_restantes = horas_paquete['horas_restantes']
                if duracion > horas_restantes:
                    return jsonify({"success": False, "error": f"No hay suficientes horas disponibles. Tienes {horas_restantes} horas."}), 400

                # Actualizar las horas utilizadas
                cursor.execute("""
                    UPDATE HorasPaquete 
                    SET horas_utilizadas = horas_utilizadas + %s 
                    WHERE id_pago = %s
                """, (duracion, id_pago))
            else:
                # 🔹 5️⃣ Si no hay registro en `HorasPaquete`, buscar horas en `Paquetes`
                cursor.execute("SELECT horas FROM Paquetes WHERE id_paquete = %s", (id_paquete,))
                paquete = cursor.fetchone()

                if not paquete:
                    return jsonify({"success": False, "error": "El paquete no existe"}), 400

                horas_totales = paquete['horas']
                if duracion > horas_totales:
                    return jsonify({"success": False, "error": f"No hay suficientes horas disponibles. Tienes {horas_totales} horas."}), 400

                # Insertar en `HorasPaquete`
                cursor.execute("""
                    INSERT INTO HorasPaquete (id_pago, id_usuario, id_usuario_google, horas_totales, horas_utilizadas, fecha_pago, fecha_caducidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (id_pago, valor_usuario if usuario_normal else None, valor_usuario if usuario_google else None, horas_totales, duracion, fecha_pago, fecha_reserva))

            # 🔹 6️⃣ Insertar la reserva en la base de datos
            cursor.execute("""
                INSERT INTO Reservas (tiempo_solicitado, fecha_reserva, duracion, id_paquete, id_pago, id_usuario, id_usuario_google, estado_reserva) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (duracion, fecha_reserva, duracion, id_paquete, id_pago, valor_usuario if usuario_normal else None, valor_usuario if usuario_google else None, "Activo"))

            connection.commit()
            print("✅ ¡Reservación realizada con éxito!")
            return jsonify({"success": True, "message": "¡Reservación realizada con éxito!"}), 200

        except mysql.connector.Error as e:
            print(f"❌ Error en la base de datos: {e}")
            return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500
        finally:
            cursor.close()
            connection.close()

    return render_template('reservacion.html', primera_compra=primera_compra)

@app.route('/verificar_disponibilidad', methods=['POST'])
def verificar_disponibilidad():
    fecha = request.json.get('fecha')

    if not fecha:
        return jsonify({"success": False, "error": "Fecha no proporcionada"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Obtener todas las reservas activas para la fecha dada
        cursor.execute("""
            SELECT HOUR(fecha_reserva) as hora_inicio, duracion 
            FROM Reservas 
            WHERE DATE(fecha_reserva) = %s AND estado_reserva = 'Activo'
        """, (fecha,))

        reservas = cursor.fetchall()
        horas_ocupadas = set()

        # Calcular todas las horas ocupadas basadas en la duración de cada reserva
        for r in reservas:
            hora_inicio = r['hora_inicio']
            duracion = r['duracion']

            for h in range(hora_inicio, hora_inicio + duracion):  
                if 0 <= h < 24:  # Asegurar que no exceda el rango de horas del día
                    horas_ocupadas.add(h)

        # Crear la lista de disponibilidad
        disponibilidad = []
        for hora in range(0, 24):
            if hora in horas_ocupadas:
                disponibilidad.append({"hora": hora, "estado": "ocupado"})  # 🔴 Rojo
            else:
                disponibilidad.append({"hora": hora, "estado": "disponible"})  # 🟢 Verde

        # Definir el color general del día
        if len(horas_ocupadas) == 24:
            color = "rojo"  # 🔴 Sin disponibilidad
        elif len(horas_ocupadas) > 0:
            color = "amarillo"  # 🟡 Algunas horas ocupadas
        else:
            color = "verde"  # 🟢 Totalmente disponible

        return jsonify({"success": True, "disponibilidad": disponibilidad, "color": color})

    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/horas_disponibles', methods=['GET'])
def horas_disponibles():
    global usuario_normal, usuario_google, id_usuario_global

    if not (usuario_normal or usuario_google):
        return jsonify({"success": False, "error": "Usuario no autenticado"}), 400

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # 🔹 1️⃣ Determinar filtro según tipo de usuario
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
            valor_usuario = id_usuario_global
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
            valor_usuario = id_usuario_global
        else:
            return jsonify({"success": False, "error": "Usuario no identificado"}), 400

        # 🔹 2️⃣ Buscar ID de pago con estado 'paid' y 'no consumido'
        cursor.execute(f"""
            SELECT id_pago, id_paquete FROM Pagos 
            WHERE estado = 'paid' AND estado_paquete = 'no consumido'
            AND {filtro_usuario}
            LIMIT 1
        """, (valor_usuario,))

        pago = cursor.fetchone()
        if not pago:
            return jsonify({"success": False, "error": "No tienes horas disponibles. Ve a la sección de paquetes."}), 400

        id_pago = pago['id_pago']
        id_paquete = pago['id_paquete']

        # 🔹 3️⃣ Buscar horas restantes en HorasPaquete
        cursor.execute("SELECT horas_restantes FROM HorasPaquete WHERE id_pago = %s", (id_pago,))
        horas_paquete = cursor.fetchone()

        if horas_paquete:
            horas_restantes = horas_paquete['horas_restantes']

            # 🔹 4️⃣ Si horas_restantes es 0, marcar el pago como 'consumido'
            if horas_restantes == 0:
                cursor.execute("UPDATE Pagos SET estado_paquete = 'consumido' WHERE id_pago = %s", (id_pago,))
                connection.commit()
                return jsonify({"success": False, "error": "No tienes horas disponibles. Ve a la sección de paquetes."}), 400

            return jsonify({"success": True, "horas_restantes": horas_restantes})

        # 🔹 5️⃣ Si no hay registro en HorasPaquete, obtener horas del paquete
        cursor.execute("SELECT horas FROM Paquetes WHERE id_paquete = %s", (id_paquete,))
        paquete = cursor.fetchone()

        if paquete:
            return jsonify({"success": True, "horas_restantes": paquete['horas']})

        return jsonify({"success": False, "error": "No tienes horas disponibles. Ve a la sección de paquetes."}), 400

    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Error en BD: {e}"}), 500
    finally:
        cursor.close()
        connection.close()

@app.route("/reservas_cercanas", methods=["GET"])
def obtener_reservas_cercanas():
    global id_usuario_global, usuario_normal, usuario_google  # Variables globales dentro de la función

    connection = get_db_connection()  
    if connection is None:
        return jsonify({"success": False, "error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # 📌 Determinar el tipo de usuario y aplicar filtro
        if usuario_normal:
            filtro_usuario = "id_usuario = %s"
        elif usuario_google:
            filtro_usuario = "id_usuario_google = %s"
        else:
            return jsonify({"success": False, "error": "Usuario no identificado"}), 400

        # 🕒 Obtener fecha y hora actual
        fecha_actual = datetime.now()

        print(f"🔍 Consultando reservas para usuario ID: {id_usuario_global} - Fecha actual: {fecha_actual}")

        # 1️⃣ CONTAR RESERVAS A CAMBIAR A "inactivo"
        cursor.execute(f"""
            SELECT COUNT(*) as total_cambio
            FROM Reservas 
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            AND DATE_ADD(fecha_reserva, INTERVAL duracion HOUR) < %s
        """, (id_usuario_global, fecha_actual))
        total_cambio = cursor.fetchone()["total_cambio"]

        print(f"⚠️ Reservas cambiadas a 'inactivo': {total_cambio}")

        # 2️⃣ ACTUALIZAR RESERVAS VENCIDAS A "inactivo"
        cursor.execute(f"""
            UPDATE Reservas 
            SET estado_reserva = 'inactivo' 
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            AND DATE_ADD(fecha_reserva, INTERVAL duracion HOUR) < %s
        """, (id_usuario_global, fecha_actual))
        connection.commit()
        print("✅ Reservas vencidas actualizadas correctamente.")

        # 3️⃣ OBTENER LAS 3 RESERVAS MÁS CERCANAS
        cursor.execute(f"""
            SELECT fecha_reserva, duracion, 
                DATE_FORMAT(fecha_reserva, '%d/%m/%Y') AS fecha_formateada,
                DATE_FORMAT(fecha_reserva, '%I:%i %p') AS hora_inicio,
                DATE_FORMAT(DATE_ADD(fecha_reserva, INTERVAL duracion HOUR), '%I:%i %p') AS hora_fin
            FROM Reservas
            WHERE {filtro_usuario} 
            AND estado_reserva = 'activo' 
            ORDER BY fecha_reserva ASC 
            LIMIT 3
        """, (id_usuario_global,))
        
        reservas = cursor.fetchall()

        print("📌 Próximas 3 reservas activas:")
        for reserva in reservas:
            print(f"📅 {reserva['fecha_formateada']} ⏰ {reserva['hora_inicio']} - {reserva['hora_fin']}")

        return jsonify({"success": True, "reservas": reservas, "cambiadas": total_cambio})

    except mysql.connector.Error as e:
        print(f"❌ Error en la base de datos: {e}")
        return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500

    finally:
        cursor.close()
        connection.close()
        print("🔌 Conexión cerrada.")

# Funcion para modificar perfil
@app.route('/perfil')
def perfil():
    return render_template('editar_perfil.html')

# Funcion para salir de la sesion
@app.route('/logout')
def logout():
    # Eliminar la sesión del usuario
    session.pop('user_id', None)
    session.pop('email', None)
    session.clear()
    # Redirigir al login
    return redirect(url_for('login'))

# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para el pago de paquetes
# Ruta para el pago
@app.route('/stripe_pay', methods=['POST'])
def stripe_pay():
    # Verificar si estamos en modo de prueba o producción
    stripe_secret_key = app.config.get('STRIPE_SECRET_KEY', '')
    if 'test' in stripe_secret_key:
        print("Modo de prueba de Stripe")
    else:
        print("Modo de producción de Stripe")

    # Obtener los datos enviados desde el frontend
    data = request.json
    horas = data.get("horas")
    precio = data.get("precio")

    # Imprimir los datos recibidos para depuración
    print(f"Datos recibidos - Horas: {horas}, Precio: {precio}")

    if not horas or not precio:
        return jsonify({"error": "Faltan parámetros de horas o precio"}), 400

    try:
        # Conexión a la base de datos
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)

        # Realizar la consulta para obtener el stripe_price_id basado en el precio
        cursor.execute("SELECT stripe_precio_id FROM Paquetes WHERE precio = %s", (precio,))
        producto = cursor.fetchone()

        # Imprimir el resultado de la consulta para depuración
        print(f"Resultado de la consulta a la base de datos: {producto}")

        if not producto:
            return jsonify({"error": f"No se encontró un paquete con precio {precio}"}), 404

        # Si se encuentra el stripe_price_id, continuar con la creación de la sesión de Stripe
        stripe_precio_id = producto["stripe_precio_id"]
        print(f"stripe_precio_id encontrado: {stripe_precio_id}")

        # Crear la sesión de pago en Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': stripe_precio_id,
                'quantity': 1
            }],
            mode='payment',  # Modo de pago único
            success_url=url_for('thanks', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('tienda', _external=True),
        )

        # Devolver la sesión de pago a la aplicación frontend
        return jsonify({
            'checkout_session_id': session['id'],
            'checkout_public_key': app.config['STRIPE_PUBLIC_KEY']
        })

    except mysql.connector.Error as db_error:
        print(f"Error en la base de datos: {db_error}")
        return jsonify({"error": f"Error en la base de datos: {str(db_error)}"}), 500

    except stripe.error.StripeError as stripe_error:
        # Manejamos los errores de Stripe específicamente
        print(f"Error de Stripe: {stripe_error}")
        return jsonify({"error": f"Error de Stripe: {str(stripe_error)}"}), 500

    except Exception as e:
        print(f"Error al generar la sesión de pago: {str(e)}")
        return jsonify({"error": f"Error al generar la sesión de pago: {str(e)}"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Ruta para confirmar el pago y asociarlo a la reserva
@app.route('/thanks')
def thanks():
    global usuario_google, usuario_normal, id_usuario_global
    session_id = request.args.get('session_id')

    if not session_id:
        return jsonify({"error": "Falta el parámetro session_id"}), 400

    try:
        # Recuperar la sesión de pago de Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        # Verificar si el pago fue exitoso
        if session.payment_status != 'paid':
            return jsonify({"error": "El pago no fue completado correctamente"}), 400

        # Obtener detalles del pago
        amount_total = session.get('amount_total', None)
        amount_total = amount_total / 100 if amount_total else None
        status = session.get('payment_status', None)
        customer_email = session.get('customer_email', 'No disponible')
        customer_name = session.get('customer_details', {}).get('name', 'No disponible')

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # Buscar el id_paquete basado en el precio (monto pagado)
        cursor.execute("SELECT id_paquete FROM Paquetes WHERE precio = %s", (amount_total,))
        paquete = cursor.fetchone()

        if not paquete:
            return jsonify({"error": "No se encontró un paquete con ese monto"}), 404

        id_paquete = paquete["id_paquete"]

        # Determinar qué ID de usuario almacenar
        id_usuario = id_usuario_global
        print(id_usuario)

        # Insertar el pago en la tabla 'Pagos'
        print(f"Usuario Google: {usuario_google}, Usuario Normal: {usuario_normal}")
        if usuario_google:
            cursor.execute(""" INSERT INTO Pagos (monto, fecha_pago, estado, id_paquete, id_usuario, id_usuario_google, estado_paquete) VALUES (%s, CURDATE(), %s, %s, NULL, %s, %s) """, (amount_total, status, id_paquete, id_usuario, "no consumido"))  # Usa id_usuario_global como id_usuario_google
        elif usuario_normal:
            cursor.execute("""INSERT INTO Pagos (monto, fecha_pago, estado, id_paquete, id_usuario, id_usuario_google, estado_paquete) VALUES (%s, CURDATE(), %s, %s, %s, NULL, %s) """, (amount_total, status, id_paquete, id_usuario, "no consumido"))  # Usa id_usuario_global como id_usuario normal
        else:
            print("⚠️ Error: No se ha detectado si es usuario normal o de Google.")
        
        connection.commit()
        id_pago = cursor.lastrowid  # Obtener el ID del pago recién insertado

        return render_template('thanks.html', 
                               customer_email=customer_email,
                               amount_total=amount_total if amount_total else 0,
                               currency='USD',
                               status=status if status else 'Desconocido',
                               customer_name=customer_name,
                               payment_id=id_pago if id_pago else 'N/A')

    except mysql.connector.Error as db_error:
        return jsonify({"error": f"Error en la base de datos: {str(db_error)}"}), 500
    except stripe.error.StripeError as stripe_error:
        return jsonify({"error": f"Error de Stripe: {str(stripe_error)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500
    finally:
        cursor.close()
        connection.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcion para autenticacion de google
@app.route("/verificacion_google", methods=['POST', 'GET'])
def verificacion_google():
    global state_global, usuario_google, usuario_normal
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],  # Scope actualizado
        redirect_uri='https://localhost:5000/callback'
    )
    # Generamos la URL de autorización y el estado
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    # Guardamos el estado en la variable global
    state_global = state
    usuario_google = True
    usuario_normal = False
    return redirect(authorization_url)

# Ruta de callback, donde Google redirige después de la autenticación
@app.route('/callback')
def callback():
    global nombre_usuario
    try:
        global state_global
        if not state_global:
            return 'Error: No se pudo recuperar el estado de la sesión.', 400

        flow = Flow.from_client_secrets_file(
            'client_secrets.json',
            scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
            state=state_global,
            redirect_uri='https://localhost:5000/callback'
        )

        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        user_info = obtener_informacion_usuario(credentials)  # Obtenemos los datos de Google

        if user_info:
            insertar_usuario_en_db(user_info)  # Insertar usuario en la BD si no existe

            session['user'] = {
                "id": user_info.get("sub"),
                "nombre": user_info.get("name", "Usuario de Google"),
                "email": user_info.get("email"),
                "avatar": user_info.get("picture", "static/image/default-avatar.png")
            }

            # Redirigir según el tipo de solicitud
            if request.headers.get('Accept') == 'application/json':
                print(usuario_normal)
                print(usuario_google)
                return jsonify({
                    "status": "success",
                    "message": "Bienvenido",
                    "user": "usuario google"
                })
            else:
                return redirect(url_for('home'))  
        else:
            return 'Error: No se pudo obtener la información del usuario.', 400
    except Exception as e:
        return f'Error en el callback: {str(e)}', 400

# Función para obtener la información del usuario usando el token de acceso
def obtener_informacion_usuario(credentials):
    access_token = credentials.token
    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    print(f"Respuesta de la API de Google: {response.status_code} - {response.json()}")  # Ver respuesta
    if response.status_code == 200:
        return response.json()  # Retorna la información del usuario (nombre, correo electrónico, etc.)
    else:
        print(f"Error al obtener la información del usuario: {response.status_code}")
        return None

# Función para insertar los datos del usuario en la base de datos si no existe
def insertar_usuario_en_db(user_info):
    global id_usuario_global  # Asegurar que usamos la variable global

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Obtener la fecha actual para el registro
        fecha_registro = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        hd = user_info.get('hd', 'No tiene hd')

        # Verificar si el usuario ya está registrado
        cursor.execute("SELECT id_usuario_google FROM Usuarios_Google WHERE correo = %s", (user_info['email'],))
        existing_user = cursor.fetchone()

        if existing_user:
            id_usuario_global = existing_user[0]  # Asignar ID si ya existe
            print(f"El usuario ya existe con ID: {id_usuario_global}")
        else:
            # Insertar el usuario si no existe
            query = """
            INSERT INTO Usuarios_Google (imagen, correo, correo_verificado, fecha_registro, dominio)
            VALUES (%s, %s, %s, %s, %s)
            """
            data = (
                user_info.get('picture', 'static/image/default-avatar.png'),
                user_info['email'], 
                user_info.get('email_verified', False),
                fecha_registro,
                hd
            )
            cursor.execute(query, data)
            conn.commit()
            
            # Obtener el ID generado por la BD
            id_usuario_global = cursor.lastrowid
            print(f"Usuario {user_info['email']} insertado en la BD con ID: {id_usuario_global}")

        return id_usuario_global  # Retornar el ID del usuario

    except mysql.connector.Error as err:
        print(f"⚠️ Error al interactuar con la BD: {err}")
        return None
    finally:
        cursor.close()
        conn.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
@app.route('/administrador')
def administrador():
    return render_template('administrador.html')

@app.route('/datos_dashboard', methods=['GET'])
def datos_dashboard():
    connection = get_db_connection()
    if connection is None:
        return jsonify({"success": False, "error": "No se pudo conectar a la base de datos"}), 500

    cursor = connection.cursor(dictionary=True)

    try:
        # 📌 Total de Usuarios
        cursor.execute("SELECT COUNT(*) AS total_usuarios FROM Usuarios")
        total_usuarios = cursor.fetchone()["total_usuarios"]

        cursor.execute("SELECT COUNT(*) AS total_usuarios_google FROM Usuarios_Google")
        total_usuarios_google = cursor.fetchone()["total_usuarios_google"]

        total_general_usuarios = total_usuarios + total_usuarios_google

        # 📌 Total de Pagos
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS normales_consumidos,
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS normales_no_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS google_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS google_no_consumidos
            FROM Pagos
        """)
        pagos_totales = cursor.fetchone()
        total_pagos = sum(pagos_totales.values())

        # 📌 Total de Reservas
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN id_usuario IS NOT NULL THEN 1 ELSE 0 END) AS normales_reservas,
                SUM(CASE WHEN id_usuario_google IS NOT NULL THEN 1 ELSE 0 END) AS google_reservas
            FROM Reservas
        """)
        reservas_totales = cursor.fetchone()
        total_reservas = reservas_totales["normales_reservas"] + reservas_totales["google_reservas"]

        # 📌 Obtener datos de Usuarios y Usuarios_Google
        cursor.execute("""
            SELECT DATE(fecha_registro) AS fecha, COUNT(*) AS total_usuarios
            FROM Usuarios
            GROUP BY DATE(fecha_registro)
            ORDER BY fecha ASC
        """)
        usuarios = cursor.fetchall()

        cursor.execute("""
            SELECT DATE(fecha_registro) AS fecha, COUNT(*) AS total_usuarios_google
            FROM Usuarios_Google
            GROUP BY DATE(fecha_registro)
            ORDER BY fecha ASC
        """)
        usuarios_google = cursor.fetchall()

        # 📌 Obtener datos de Pagos
        cursor.execute("""
            SELECT DATE(fecha_pago) AS fecha, 
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS normales_consumidos,
                SUM(CASE WHEN id_usuario IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS normales_no_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'consumido' THEN 1 ELSE 0 END) AS google_consumidos,
                SUM(CASE WHEN id_usuario_google IS NOT NULL AND estado_paquete = 'no_consumido' THEN 1 ELSE 0 END) AS google_no_consumidos
            FROM Pagos
            GROUP BY DATE(fecha_pago)
            ORDER BY fecha ASC
        """)
        pagos = cursor.fetchall()

        # 📌 Obtener datos de Reservas usando fecha_reserva y ordenadas
        cursor.execute("""
            SELECT 
                DATE(fecha_reserva) AS fecha,
                estado_reserva,
                SUM(CASE WHEN id_usuario IS NOT NULL THEN 1 ELSE 0 END) AS usuarios_normales,
                SUM(CASE WHEN id_usuario_google IS NOT NULL THEN 1 ELSE 0 END) AS usuarios_google
            FROM Reservas
            GROUP BY fecha, estado_reserva
            ORDER BY fecha ASC
        """)
        reservas = cursor.fetchall()

        # 📌 Formatear datos en JSON para el frontend
        return jsonify({
            "success": True,
            "totales": {
                "usuarios": {"total": total_general_usuarios, "normales": total_usuarios, "google": total_usuarios_google},
                "pagos": {
                    "total": total_pagos,
                    "normales_consumidos": pagos_totales["normales_consumidos"],
                    "normales_no_consumidos": pagos_totales["normales_no_consumidos"],
                    "google_consumidos": pagos_totales["google_consumidos"],
                    "google_no_consumidos": pagos_totales["google_no_consumidos"]
                },
                "reservas": {
                    "total": total_reservas,
                    "normales": reservas_totales["normales_reservas"],
                    "google": reservas_totales["google_reservas"]
                }
            },
            "usuarios": usuarios,
            "usuarios_google": usuarios_google,
            "pagos": pagos,
            "reservas": reservas
        })

    except mysql.connector.Error as e:
        return jsonify({"success": False, "error": f"Error en la base de datos: {e}"}), 500

    finally:
        cursor.close()
        connection.close()
# -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Rutas temporales
@app.route('/carga', methods=['GET', 'POST'])
def carga():
    return render_template('carga.html')

@app.route('/acceso_token', methods=['GET', 'POST'])
def acceso_token():
    return render_template('acceso_token.html')

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Funcionar la API
if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', ssl_context='adhoc') # El ssl es para crear un HTTPS, el adhoc es para hacerlo sin la necesidad de credenciales