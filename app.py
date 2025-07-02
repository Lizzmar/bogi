from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
import json
import os

app =Flask(__name__)
#Configruación de la base de datos SQLITE-test
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///metapython.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
#end

#Modelo de la tabla log
class Log(db.Model):
    id=db.Column(db.Integer, primary_key = True)
    fecha_y_hora = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    texto = db.Column (db.TEXT)
#end

#Crear la tabla si no existe
with app.app_context():
    db.create_all()
#end

#Funcion para ordenar los registros por fecha y hora
def ordenar_por_fecha_y_hora(registros):
    return sorted(registros, key=lambda x: x.fecha_y_hora,reverse=True)
#end

@app.route('/')
def home():
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html', registros=registros_ordenados)

@app.route('/politica-de-privacidad')
def privacidad():
    return render_template('politica-de-privacidad.html')

@app.route('/terminos-y-condiciones')
def terminos():
    return render_template('terminos-y-condiciones.html')

@app.route('/templates/<path:filename>')
def custom_static(filename):
    return send_from_directory('templates', filename)

mensajes_log =  []

#Funciones para agregar mensajes y guardar en la base de datos
def agregar_mensajes_log(texto):
    mensajes_log.append(texto)
    if isinstance(texto, dict):
        texto = json.dumps(texto)

    #Guardar el mensaje en la base de datos
    nuevo_registro = Log(texto=texto)
    db.session.add(nuevo_registro)
    db.session.commit()
    #end

#Token de verificación para la configuración
TOKEN_GAMLP = "GAMLP"

@app.route('/webhook', methods=['GET','POST'])
def webhook():
    if request.method == 'GET':
        challenge = verificar_token(request)
        return challenge
    elif request.method == 'POST':
        reponse = recibir_mensajes(request)
        return reponse

def verificar_token(req):
    token = req.args.get('hub.verify_token')
    challenge = req.args.get('hub.challenge')

    if challenge and token == TOKEN_GAMLP:
        return challenge
    else:
        return jsonify({'error':'Token Invalido'}),401

def recibir_mensajes(req):
    try:
        req = request.get_json()
        entry = req['entry'][0]
        changes = entry['changes'][0]
        value = changes ['value']
        objeto_mensaje = value['messages']

        if objeto_mensaje:
            messages = objeto_mensaje[0]

            if "type" in messages:
                tipo = messages["type"]
                #Guardar log en la BD
                agregar_mensajes_log(json.dumps(messages))

                if tipo == "interactive":
                    tipo_interactive = messages["interactive"]["type"]
                                    
                    if tipo_interactive == "button_reply":
                        text = messages["interactive"]["button_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatsapp(text,numero)
                    
                    elif tipo_interactive == "list_reply":
                        text = messages["interactive"]["list_reply"]["id"]
                        numero = messages["from"]

                        enviar_mensaje_whatsapp(text,numero)

                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    enviar_mensaje_whatsapp(text,numero)

                    #Guardar log en la BD
                    agregar_mensajes_log(json.dumps(messages))

        return jsonify({'message':'EVENT_RECEIVED'})
    except Exception as e:
        return jsonify({'message':'EVENT_RECEIVED'})
#end
    
#funcion para enviar mensajes a whatsapp
def enviar_mensaje_whatsapp(texto,number):
    texto =texto.lower()

    if "hola" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, ¿Como estás? Bienvenido."
            }
        }
    elif "1" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, opcion 1"
            }
        }
    elif "2" in texto:
        data = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "location",
            "location": {
                "latitude": "-16.517906810963066",
                "longitude": "-68.06603843725476",
                "name": "CA",
                "address": "1 Hacker Way",   
            }, 
        }
    elif "boton" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body":{
                    "text":"¿Confirmas tu registro?"
                },
                "footer":{
                    "text":"Selecciona una opción"
                },
                "action":{
                    "buttons":[
                        {
                            "type":"reply",
                            "reply":{
                                "title":"Si",
                                "id":"btnsi"
                            }
                        },
                        {
                            "type":"reply",
                            "reply":{
                                "title":"No",
                                "id":"btnno"
                            }
                        },
                        {
                            "type":"reply",
                            "reply":{
                                "title":"Tal vez",
                                "id":"btntalvez"
                            }
                        }
                    ]
                }
            }
        }
    elif "btnsi" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Muchas gracias por aceptar"
            }
        }
    elif "btnno" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Es una lastima"
            }
        }
    elif "lista" in texto:
        data ={
            "messaging_product": "whatsapp",
            "to": number,
            "type": "interactive",
            "interactive":{
                "type" : "list",
                "body": {
                    "text": "Selecciona Alguna Opción"
                },
                "footer": {
                    "text": "Selecciona una de las opciones para poder ayudarte"
                },
                "action":{
                    "button":"Ver Opciones",
                    "sections":[
                        {
                            "title":"Compra y Venta",
                            "rows":[
                                {
                                    "id":"btncompra",
                                    "title" : "Comprar",
                                    "description": "Compra los mejores articulos de tecnologia"
                                },
                                {
                                    "id":"btnvender",
                                    "title" : "Vender",
                                    "description": "Vende lo que ya no estes usando"
                                }
                            ]
                        },{
                            "title":"Distribución y Entrega",
                            "rows":[
                                {
                                    "id":"btndireccion",
                                    "title" : "Local",
                                    "description": "Puedes visitar nuestro local."
                                },
                                {
                                    "id":"btnentrega",
                                    "title" : "Entrega",
                                    "description": "La entrega se realiza todos los dias."
                                }
                            ]
                        }
                    ]
                }
            }
        }
    elif "btncompra" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Los mejores articulos de tecnologia"
            }
        }
    elif "btnvender" in texto:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "Excelente, vende lo que ya no estes usando"
            }
        }     
    else:
        data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": number,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": "🚀 Hola, visita mi web anderson-bastidas.com para más información.\n \n📌Por favor, ingresa un número #️⃣ para recibir información.\n \n1️⃣. Información del Curso. ❔\n2️⃣. Ubicación del local. 📍\n3️⃣. Enviar temario en PDF. 📄\n4️⃣. Audio explicando curso. 🎧\n5️⃣. Video de Introducción. ⏯️\n6️⃣. Hablar con AnderCode. 🙋‍♂️\n7️⃣. Horario de Atención. 🕜 \n0️⃣. Regresar al Menú. 🕜"
            }
        }

    #Convertir el diccionaria a formato JSON
    data=json.dumps(data)
    
    #Los Header para la conexión desde la API de Facebook
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer EAAU1xePd7pgBOyysJK7Lb5wrMTr16Sv09adBYJAcwHm5606jaO7Bv4HDQWJeQAzbQDUM0Qpmh9gknsmZA8CyvrSpgCId9jSwdJp6yZCQIDJyzDkZCvI4QaDgNlWo7ZA8jsW85EJGxZAr1HZAYEEFlclypKkjBqTQE2xlzdedpp7SYhjNZCZB8g6uJu7csfAVPrr4VP9e7HQhgcwZB9ob7xrT2Q5WNiphJFY8m8MQTcb0tcnZBMcOFl9hMzO1S1XMXl"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")
    try:
        connection.request("POST","/v20.0/680860005112615/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)