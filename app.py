from flask import Flask, request, jsonify, make_response, render_template
from flask import Response
import json
import requests
from os import environ
import psycopg2
from cryptography.fernet import Fernet



app = Flask(__name__)


FERNET_KEY = environ.get('FERNET_KEY')
f = Fernet(FERNET_KEY.encode("utf-8"))

def encrypt(text):
    bText = text.encode("utf-8")
    cText = f.encrypt(bText)

    return cText.decode("utf-8")

def decrypt(text):
    bText = text.encode("utf-8")
    cText = f.decrypt(bText)

    return cText.decode("utf-8")




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

def getApiKeyFromChatId(chat_id):
    try:
        cur = dbConn.cursor()
        cur.execute(f"SELECT api_key FROM users WHERE chat_id = \'{chat_id}\'")
                
        row = cur.fetchone()
   
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in getApiKeyfromChatId!: %s", error)
    finally:
        cur.close()

    if row: 
        return str(decrypt(row[0]))
    else:
        return -1
        

#Cambaire l'API KEY assocciata al Chat Id
def setApiKey(chat_id, api_key):
    try:
        cur = dbConn.cursor()

        api_key = encrypt(api_key)

        cur.execute(f"UPDATE users SET api_key = \'{api_key}\' WHERE chat_id = \'{chat_id}\'")                
        dbConn.commit()
        print("API KEY settata correttamente")
               
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in setApiKey!: %s", error)  
    finally:
        cur.close()

    return 0

#Dal Chat Id ottiene lo stato attuale della chat
def getStatus(chat_id):
    try:
        cur = dbConn.cursor()
        cur.execute(f"SELECT status FROM users WHERE chat_id = \'{chat_id}\'")
                
        row = cur.fetchone()      
        
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in getStatus!: %s", error)
    finally:
        cur.close()

    if row: 
        return str(row[0])
    else:
        return -1


#Cambia lo stato
def setStatus(chat_id, s):
    try:
        cur = dbConn.cursor()
        cur.execute(f"UPDATE users SET status = \'{s}\' WHERE chat_id = \'{chat_id}\'")         
        dbConn.commit()
        print("Stauts aggiornato correttamente")
        
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in setStatus!: %s", error) 
    finally:
        cur.close()  
    
    return 0


def getAuth(chat_id):
    try:
        cur = dbConn.cursor()
        cur.execute(f"SELECT auth FROM users WHERE chat_id = \'{chat_id}\'")
                
        row = cur.fetchone()
        
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in getStatus!: %s", error)
    finally:
        cur.close()

    if row: 
        return str(row[0])
    else:
        return -1

#1 - sei loggato
#0 non sei loggato
def setAuth(chat_id, s):
    try:
        cur = dbConn.cursor()
        cur.execute(f"UPDATE users SET auth = \'{s}\' WHERE chat_id = \'{chat_id}\'")         
        dbConn.commit()
        print("Autorizzazione settata correttamente")
        
    except psycopg2.Error as e:
        error = e.pgcode
        print("ERRORE in setAuth!: %s", error)   
    finally:
        cur.close()

    return 0






#FINE DATABASE

#INIZIO API


@app.route('/accountinfo')
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


@app.route('/newlink')
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


@app.route('/dellink')
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


@app.route('/countlink')
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


@app.route('/linkinfo')
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


@app.route('/listlink')
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


@app.route('/deletealllinks')
def apiDelAllLinks():
    api_key = request.args.get('api_key', None)

    url = f'https://thepdgt-bot.herokuapp.com/listlink?api_key={api_key}'

    response = requests.get(url)

    if response.status_code != 200:
        return make_response(f'Errore nel caricare la lista', 400)
    
    response = response.json()

    error = False


    for item in response:
        rId = item['id']
        print(rId)
        print(item['id'])
        url = f'https://api.rebrandly.com/v1/links/{rId}?apikey={api_key}'
        response1 = requests.delete(url)
        if response1.status_code != 200:
            error = True


    
    if error:
        r = {
            'status': f'Errore con alcuni link'
        }
        return make_response(jsonify(r),401)
    else:
        r = {
            'status': f'OK'
        }
        return make_response(jsonify(r), 200)




#FINE API


#INIZIO TELEGRAM

TOKEN = environ.get('BOT_TOKEN')

def inviaMessaggio(chat_id, text):
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={text}'
    requests.post(url)
    return 0 



@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        req = request.get_json()
        chat_id  = req.get('message').get('chat').get('id')
        username = req.get('message').get('chat').get('first_name')
        messageText  = req.get('message').get('text')
        text = f''
        
        status = getStatus(chat_id)

        if getAuth(chat_id) == f'1':


            if messageText == '/start':
                text = (f'Ciao, {username}!\n'
                        f'Usa il comando /help per avere le informazioni sul mio funzionamento mentre usa /cmd per visualizzare i comandi disponibili.\n')
                

            elif messageText == '/help':
                text = (f'Questo Bot permette di creare dei ShortURL attraverso il sito https://rebrandly.com.\n'
                        f'Per potermi usare prima devi collegare la tua API KEY fornita dal sito attraverso il comando /collegakey (per ottenerla devi prima creare un account).\n'
                        f'Usa il comando /cmd per visualizzare i comandi disponibili e il loro funzionamento.')

            
            elif messageText == '/cmd':
                text =( f'Ecco i comandi:\n'
                        f'/collegakey : Per collegare o aggiornare la tua chiave al bot\n'
                        f'/infoaccount : Per ottenere le informazioni relative al tuo account\n'
                        f'/infolink : Per ottenere le informazioni relative ad un link\n'
                        f'/newlink : Per creare un nuovo ShortLink\n'
                        f'/alllinks : Per ottenere tutti i link creati\n'
                        f'/deletelink : Per eliminare un Link\n' 
                        f'/deletealllink : Per eliminare tutti i link\n'
                        f'/countlink : Per vedere i link creati\n'
                        f'/logout : Per fare il logout dall\'account\n'
                        f'/help: Per ottenere aiuto'
                        f'/annulla : Per annullare l\'ultimo comando\n')


            elif messageText == '/collegakey':
                text = f'Okei, ora inviami la Key che vuoi associare al bot\n'
                setStatus(chat_id, f'1')

            elif (messageText == '/infoaccount' or messageText == '/annulla' or messageText == '/infolink' or messageText == '/newlink' or messageText == '/alllinks' or messageText == '/deletelink' or messageText == '/changekey' or messageText == '/countlink' or messageText == '/deletealllink' or messageText == '/logout'):

                if getApiKeyFromChatId(chat_id) != f'0':
                
                    if messageText == '/infoaccount':
                        api_key = getApiKeyFromChatId(chat_id)
                        if api_key != -1:
                            url = f'https://thepdgt-bot.herokuapp.com/accountinfo?api_key={api_key}'

                            response = requests.get(url)

                            if response.status_code != 200:
                                text = f'Errore nell\'ottenere le informazioni'
                            else:
                                
                                response = response.json()

                                rUsername      = response.get('username')
                                rEmail         = response.get('email')
                                rFullName      = response.get('fullName')
                                rType          = response.get('typeAccount')
                                rLinksUsed     = response.get('linksUsed')
                                rLinksMaxLimit = response.get('maxLimitLinks')
                                rLinksBlocked  = response.get('rLinksBlocked')

                                rId = response["id"]

                                text = f'ID Account: {rId}\nUsername: {rUsername}\nEmail: {rEmail}\nNome: {rFullName}\nLink usati: {rLinksUsed}\nLink Massimi Creabili: {rLinksMaxLimit}\nLink bloccati: {rLinksBlocked}\nTipo account: {rType}' 

                        else:
                            text = f'Account non trovato'
        
                    elif messageText == '/annulla':
                        text = f'Comando annullato\n' 
                        setStatus(chat_id, f'0')

                    elif messageText == '/logout':
                        text = f'Logout effettuato\n'
                            
                        setAuth(chat_id, f'0')
                    
                    
                    elif messageText == '/infolink':
                        text = f'Okei, ora imviami l\'ID del Link di cui vuoi visualizzare le informazioni\n'            
                        setStatus(chat_id, f'2')

                    elif messageText == '/newlink':
                        text = f'Okei, ora imviami il link che vuoi ridurre\n'
                        setStatus(chat_id, f'3')

                    elif messageText == '/alllinks':
                        api_key = getApiKeyFromChatId(chat_id)

                        if api_key != -1:
                            url = f'https://thepdgt-bot.herokuapp.com/listlink?api_key={api_key}'

                            response = requests.get(url)

                            if response.status_code != 200:
                                text = f'Errore nell\'ottenere i link'
                            else:
                                
                                response = response.json()

                                text = f'Ecco la lista link:\n'
                            
                                for item in response:
                                    rId = item['id']
                                    rTitolo = item['title']
                                    rDest = item['destination']
                                    rShortLink = item['shortUrl']

                                    temp = f'ID Link: {rId}\nTitolo: {rTitolo}\nDestinazione: {rDest}\nLink ridotto: {rShortLink}\n\n'
                                    text = text + temp
                                
                        else:
                            text = f'Account non trovato'
                    

                    elif messageText == '/deletealllink':
                        api_key = getApiKeyFromChatId(chat_id)
                        
                        url = f'https://thepdgt-bot.herokuapp.com/deletealllinks?api_key={api_key}'

                        response = requests.get(url)

                        if response.status_code != 200:
                            text = f'Errore nell\'eliminare tutti i link\n' 
                        else:
                            text = f'Link eliminati correttamente'
            

                    elif messageText == '/deletelink':
                        text = f'Okei, ora inviami l\'ID del link che vuoi eliminare\n'
                        setStatus(chat_id, f'4')

                    elif messageText == '/countlink':
                        api_key = getApiKeyFromChatId(chat_id)
                    
                        if api_key != -1:
                            url = f'https://thepdgt-bot.herokuapp.com/countlink?api_key={api_key}'

                            response = requests.get(url)

                            if response.status_code != 200:
                                text = f'Errore'
                            else:

                                response = response.json()
                            
                                count = response.get('count')

                                text = f'Numero Link usati: {count}'

                        else:
                            text = f'Account non trovato'

                else:
                    text = f'Per poter accedere al comando devi prima collegare la API KEY\n'

            elif status == '1':
                    setApiKey(chat_id, messageText)
                    setStatus(chat_id, f'0')
                    text = f'Key settata correttamente'
                    

            elif status == '2':
                    api_key = getApiKeyFromChatId(chat_id)

                    if api_key != -1:
                        
                        url = f'https://thepdgt-bot.herokuapp.com/linkinfo?idLink={messageText}&api_key={api_key}'
                    
                        response = requests.get(url)

                        if response.status_code != 200:
                            text = f'Errore nel trovare la chiave'
                        else:
                        
                            response = response.json()

                            rId         = response.get('id')
                            rTitle      = response.get('title')
                            rDest       = response.get('destination')
                            rShortUrl   = response.get('shortUrl')
                            rStatus     = response.get('status')
                            rClicks     = response.get('clicks')
                            rCreated    = response.get('createdAt')
                            
                            rCreatedD   = rCreated.split("T")[0]

                        


                            text = f'ID Link : {rId}\nTitolo: {rTitle}\nDestinazione: {rDest}\nLink ridotto: {rShortUrl}\nStato link: {rStatus}\nClicks sul link: {rClicks}\nData creazione: {rCreatedD}\n' 

                            setStatus(chat_id, f'0')
                    else:
                        text = f'Errore nel trovare la chiave'

                    

            elif status == '3':
                    api_key = getApiKeyFromChatId(chat_id)

                    if api_key != -1:

                        url = f'https://thepdgt-bot.herokuapp.com/newlink?api_key={api_key}&destUrl={messageText}'
                    
                        response = requests.get(url)

                        if response.status_code != 200:
                            text = f'Errore nel creare il link.\nCopiare tutto il link (comrpreso http[s]://)\n'
                        else:
                            response = response.json()
                            newUrl = response.get('shortUrl')
                            print(newUrl)

                            text = f'Link ridotto creato: {str(newUrl)}'

                            setStatus(chat_id, f'0')
                    else:
                        text = f'Errore nel trovare la chiave'
                    

            elif status == '4':
                    api_key = getApiKeyFromChatId(chat_id)

                    if api_key != -1:

                        url = f'https://thepdgt-bot.herokuapp.com/dellink?api_key={api_key}&idLink={messageText}'
                    
                        response = requests.get(url)

                        if response.status_code != 200:
                            text = f'Errore nell\'eliminare il link\n'

                        else: 
                            response = response.json()

                            rId         = response.get('id')
                            rTitle      = response.get('title')
                            rDest       = response.get('destination')
                            rShortUrl   = response.get('shortUrl')



                            text = f'Link eliminato.\nID Link : {rId}\nTitolo: {rTitle}\nDestinazione: {rDest}\nLink ridotto: {rShortUrl}\n' 

                            setStatus(chat_id, f'0')
                    else:
                        text = f'Errore nel trovare la chiave'
                    
            else:
                text = f'Messaggio non valido'

        else:
            if messageText == '/start':
                text = f'Ciao, {username}!\nPer usare il BOT bisogna autenticarsi!\nInviami user e password in questo formato: YOURUSER-YOURPASSWORD'
                
                if getStatus(chat_id) == -1:
                    insertChatId(chat_id)

                setStatus(chat_id, f'6')
                
        
            elif messageText == '/annulla':
                    text = f'Comando annullato\n' 
                    setStatus(chat_id, f'0')

            elif getStatus(chat_id) == '6':
                
                try:
                    user = messageText.split("-")[0]
                    pwd  = messageText.split("-")[1]

                    if user == environ.get('USER') and pwd == environ.get('PASSWORD'):

                        setAuth(chat_id, f'1')
                        setStatus(chat_id, f'0')           
                        

                        text = (f'Login effettuato correttamente\n'
                                f'Ciao, {username}!\n'
                                f'Usa il comando /help per avere le informazioni sul mio funzionamento mentre usa /cmd per visualizzare i comandi disponibili.\n')

                    else:
                        text = f'Credenziali non corrette\n'

                except: 
                    text = f'Formato stringa non corretto\n'

            else:
                text = f'Qualcosa è andato storto\n'
                    

        inviaMessaggio(chat_id,text)
 


#FINE TELEGRAM 


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get('PORT', 5000)))



    