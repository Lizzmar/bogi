from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import http.client
import json

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
def index():
    #obtener todos los registros de la base de datos
    registros = Log.query.all()
    registros_ordenados = ordenar_por_fecha_y_hora(registros)
    return render_template('index.html',registros=registros_ordenados)

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

                if tipo == "interactive":
                    return 0

                if "text" in messages:
                    text = messages["text"]["body"]
                    numero = messages["from"]

                    enviar_mensaje_whatsapp(text,numero)
                    # agregar_mensajes_log(json.dumps(text))
                    # agregar_mensajes_log(json.dumps(numero))

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
        "Authorization" : "Bearer EAAHjoggR6icBO4c9pwSZBjUf7SV3aYcXijGztW0fIxAiEgThisWhqbnVYTZAFjGm7eqPMK4LUZCH7DHChnyEmzZCWxgza9USB6uMlMcWBPbt14lqTnecVqN5yr6SZCOzjsqPZATM25kdT6g2gpCO0Ou4JkpU8aAuJyDtzla7Ir70rxEKDNc6BRzERrAJFkNzX9pTRdHaIdhbkEvIXgt3WuNlnn"
    }
    connection = http.client.HTTPSConnection("graph.facebook.com")
    try:
        connection.request("POST","/v20.0/450708958127799/messages", data, headers)
        response = connection.getresponse()
        print(response.status, response.reason)
    except Exception as e:
        agregar_mensajes_log(json.dumps(e))
    finally:
        connection.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)