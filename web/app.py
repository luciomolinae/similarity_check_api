from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from pymongo import MongoClient
import bcrypt
import spacy

app = Flask(__name__)
api = Api(app)

client = MongoClient("mongodb://db:27017")
db = client.SimilarityDB
users = db["Users"]


def UserExist(username):
    if users.count_documents({"Username": username}) == 0:
        return False
    else:
        return True
    

class Register(Resource):
    def post(self):

        postedData = request.get_json()
        
        username = postedData["username"]
        password = postedData["password"]

        if UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Usuario Invalido"
            }
            return jsonify(retJson)
        
        hashed_pw = bcrypt.hashpw(password.encode('utf8'), bcrypt.gensalt())

        users.insert_one({
            "Username": username,
            "Password" : hashed_pw,
            "Tokens": 6
        })

        retJson = {
            "status" : 200,
            "msg" : "Inscripcion Exitosa!"
        }

        return jsonify(retJson)


def verifyPw(username, password):
    if not UserExist(username):
        return False
    
    hashed_pw = users.find({
        "Username" : username
    }) [0]["Password"] # accedemos al usuario y luego a su contraseña

    if bcrypt.hashpw(password.encode('utf8'), hashed_pw) == hashed_pw:
        return True
    else:
        return False

def countTokens(username):
    tokens = users.find({
        "Username" : username
    })[0]["Tokens"]
    return tokens

class Detect(Resource):
    def post(self):

        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["password"]
        text1 = postedData["text1"]
        text2 = postedData["text2"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Usuario no valido"
            }
            return jsonify(retJson)
        
        correct_pw = verifyPw(username, password)

        if not correct_pw:
             retJson = {
                "status" : 302,
                "msg" : "Contraseña no valida"
            }
            
        num_tokens = countTokens(username)

        if num_tokens <= 0:
            retJson = {
                "status" : 303,
                "msg" : "Te quedaste sin Tokens, por favor recargalos "
            }
            return jsonify(retJson)
        

        nlp = spacy.load('en_core_web_sm')

        text1 = nlp(text1)
        text2 = nlp(text2)

        # Ratio es un numero entre 0 y 1, mientras mas cercano sea a 1 mas iguales son los textos
        ratio = text1.similarity(text2)

        retJson = {
            "status" : 200,
            "similarity" : ratio,
            "msg" : "Test de similitud completado"
        }

        current_tokens = countTokens(username)

        users.update_one({
            "Username": username,
        }, {
            "$set":{
                "Tokens": current_tokens - 1
            }
        })

        return jsonify(retJson)
    
class Refill(Resource):
    def post(self):
        postedData = request.get_json()

        username = postedData["username"]
        password = postedData["admin_pw"]
        refill_amount = postedData["refill"]

        if not UserExist(username):
            retJson = {
                "status" : 301,
                "msg" : "Usuario no valido"
            }
            return jsonify(retJson)
        
        correct_pw = "abc123"
        if not password == correct_pw:
            retJson = {
                "status" : 304,
                "msg" : "ADMIN PASSWORD Incorrecta"
            }
            return jsonify(retJson)
        
        users.update_one({
            "Username" : username
        }, {
            "$set":{
                "Tokens" : refill_amount
            }
        })

        retJson = {
            "status" : 200,
            "msg" : "Recarga de Tokens completada"
        }
        return jsonify(retJson)
    
api.add_resource(Register, '/register')
api.add_resource(Detect, '/detect')
api.add_resource(Refill, '/refill')

if __name__ == "__main__":
    app.run(host='0.0.0.0')




