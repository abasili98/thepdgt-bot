from flask import Flask, request, jsonify, make_response, render_template
from flask import Response
import json
import requests


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