from flask import Flask, request, jsonify, make_response, render_template
from flask import Response
import json
import requests
from os import environ
import psycopg2


#INIZIO DATABASE

try:
    dbConn = psycopg2.connect(
        host     = environ.get('DATABASE_HOST'),
        database = environ.get('DATABASE_DB'),
        user     = environ.get('DATABASE_USER'),
        password = environ.get('DATABASE_PWD'),
        port     = environ.get('DATABASE_PORT')
    )

    print("Connessione al DataBase riuscita")
except:
    Response.status(503)
    print("Errore nella connessione con il DataBase")


def insertChatId(chat_id):
    try:
        cur = dbConn.cursor()
        cur.execute(f"INSERT INTO users (chat_id) VALUES ({chat_id})")
        dbConn.commit()
        print("Chat Id inserita correttamente")
        
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in insertChatId!: %s", error) 
    finally:
        cur.close()  

    return 0 

#Cambaire l'API KEY assocciata al Chat Id
def setApiKey(chat_id, api_key):
    try:
        cur = dbConn.cursor()
        cur.execute(f"UPDATE users SET api_key = \'{api_key}\' WHERE chat_id = \'{chat_id}\'")                
        dbConn.commit()
        print("API KEY settata correttamente")
               
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in setApiKey!: %s", error)  
    finally:
        cur.close()

    return 0


#FINE DATABASE

#INIZIO API

def apiAccountInfo():

    api_key = request.args.get('api_key', None)

    url = "https://api.rebrandly.com/v1/account"

    headers = {"apikey": api_key}

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        return make_response(f'APIKEY non trovata', 404)

    response = response.json()

    rId            = response.get('id')
    rUsername      = response.get('username')
    rEmail         = response.get('email')
    rFullName      = response.get('fullName')
    rType          = response.get('subscription', {}).get('category')
    rLinksUsed     = response.get('subscription', {}).get('limits', {}).get('links', {}).get('used')
    rLinksMaxLimit = response.get('subscription', {}).get('limits', {}).get('links', {}).get('included')
    rLinksBlocked  = response.get('subscription', {}).get('limits', {}).get('links', {}).get('blocked')

    #if rId and rUsername and rEmail and rFullName and rType and rLinksUsed and rLinksMaxLimit and rLinksBlocked:
    r = {
            "id": rId,
            "username": rUsername,
            "email": rEmail,
            "fullName": rFullName,
            "typeAccount": rType,
            "linksUsed": rLinksUsed,
            "maxLimitLinks": rLinksMaxLimit,
            "blockedLinks": rLinksBlocked
        }

    return make_response(jsonify(r), 200)


def apiNewLink():

    api_key = request.args.get('api_key', None)
    destUrl = request.args.get('destUrl', None)

    url = f'https://api.rebrandly.com/v1/links/new?apikey={api_key}&destination={destUrl}'

    response = requests.get(url)

    if response.status_code != 200:
        return make_response(f'Errore nel creare il link', 400)

    response = response.json()

    shortUrl = response.get('shortUrl')

    r = {
        "shortUrl": shortUrl
    }

    return make_response(jsonify(r), 200)


def apiDelLink():

    api_key = request.args.get('api_key', None)

    idLink = request.args.get('idLink', None)

    if api_key == None and idLink == None:
        return make_response(f'API KEY o l\'ID link non presenti', 404)
    
    url = f'https://api.rebrandly.com/v1/links/{idLink}?apikey={api_key}'

    response = requests.delete(url)

    if response.status_code != 200:
        return make_response(f'ID link non trovato', 404)
    
    response = response.json()

    rId       = response.get('id')
    rTitle    = response.get('title')
    rDest     = response.get('destination')
    rShortUrl = response.get('shortUrl')

    r = {
        'id': rId,
        "title": rTitle,
        "destination": rDest,
        "shortUrl": rShortUrl
    }
 
    return make_response(jsonify(r), 200)



def apiCountLink():

    api = request.args.get('api_key', None)

    url = "https://api.rebrandly.com/v1/links/count"

    headers = {"apikey": api}

    response = requests.request("GET", url, headers=headers)

    if response.status_code != 200:
        return make_response(f'Errore nell\'ottenre l\'inofrmazione', 400)

    response = response.json()

    rCount = response.get('count')

    r = {
        "count": rCount
    }

    return make_response(jsonify(r), 200)



def apiLinkInfo():

    idLink = request.args.get('idLink', None)

    api_key = request.args.get('api_key', None)

    url = f'https://api.rebrandly.com/v1/links/{idLink}?apikey={api_key}'


    response = requests.get(url)

    if response.status_code != 200:
        return make_response(f'ID link non trovato', 404)

    response = response.json()

    rId       = response.get('id')
    rTitle    = response.get('title')
    rDest     = response.get('destination')
    rShortUrl = response.get('shortUrl')
    rStatus   = response.get('status')
    rClicks   = response.get('clicks')
    rCreate   = response.get('createdAt')


    r = {
        "id": rId,
        "title": rTitle,
        "destination": rDest,
        "shortUrl": rShortUrl,
        "status": rStatus,
        "clicks": rClicks,
        "createdAt": rCreate
    }

    return make_response(jsonify(r), 200)


def apiListLink():

    api_key = request.args.get('api_key', None)


    url = f'https://api.rebrandly.com/v1/links'

    querystring = {"orderBy":"createdAt","orderDir":"desc","limit":"25"}

    headers = {"apikey": api_key}

    response = requests.request("GET", url, headers=headers, params=querystring)

    if response.status_code != 200:
        return make_response(response, 400)

    response = response.json()

    rList = []

    for item in response:
        temp = {"id":None, "title":None, "destination":None, "shortUrl":None }
        temp['id']          = item['id']
        temp['title']       = item['title']
        temp['destination'] = item['destination']
        temp['shortUrl']    = item['shortUrl']
        rList.append(temp)

    return make_response(jsonify(rList), 200)


#FINE API


#INIZIO TELEGRAM

TOKEN = environ.get('BOT_TOKEN')

def inviaMessaggio(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
    requests.post(url)
    return 0 

def index():
    if request.method == 'POST':
        req = request.get_json()
        chat_id  = req.get('message').get('chat').get('id')
        username = req.get('message').get('chat').get('first_name')
        messageText  = req.get('message').get('text')
        text = f''
        

        if messageText == '/start':
            text = (f'Ciao, {username}!\n'
                    f'Usa il comando /help per avere le informazioni sul mio funzionamento mentre usa /cmd per visualizzare i comandi disponibili.\n')
                

        elif messageText == '/help':
            text = (f'Questo Bot permette di creare dei ShortURL attraverso il sito https://rebrandly.com.\n'
                    f'Per potermi usare come prima cosa devi collegare la tua API KEY fornita dal sito attraverso il comando /collegakey (se non lo hai giÃ  fatto dovrai prima creare un account.\n'
                    f'Usa il comando /cmd per visualizzare i comandi disponibili e il loro funzionamento.')






        inviaMessaggio(chat_id, text)

    return jsonify(req)
 
#FINE TELEGRAM 





    