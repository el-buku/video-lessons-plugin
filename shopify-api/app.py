import os
from dotenv import load_dotenv
import uuid
import json
import logging

from flask import Flask, render_template, request, abort, redirect, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

from .src.twilio.twilio_api import create_room
from .src.shopify import helpers
from .src.shopify.shopify_client import ShopifyStoreClient

from .src.config import APP_SECRET_KEY, SERVER_DOMAIN, WEBHOOK_APP_UNINSTALL_URL, TWILIO_ACCOUNT_SID, \
    TWILIO_API_KEY_SID, \
    TWILIO_API_KEY_SECRET, SQLALCHEMY_DATABASE_URI, SHOPIFY_API_KEY, WEBHOOK_ORDER_CREATED_URL, DEFAULT_EMAIL_TEMPLATE, \
    EMAIL_USERNAME, EMAIL_PASS, WEBHOOK_PRODUCT_ADDED_URL+++++++++++++++++

import requests
import random
import smtplib
import datetime

twilio_account_sid = TWILIO_ACCOUNT_SID
twilio_api_key_sid = TWILIO_API_KEY_SID
twilio_api_key_secret = TWILIO_API_KEY_SECRET

ACCESS_TOKEN = None
NONCE = None
ACCESS_MODE = []  # Defaults to offline access mode if left blank or omitted. https://shopify.dev/concepts/about-apis/authentication#api-access-modes
SCOPES = ['write_inventory', 'write_orders',
          'write_script_tags, read_products, read_orders, write_products']  # https://shopify.dev/docs/admin-api/access-scopes

app = Flask(__name__)
app.config['SECRET_KEY'] = APP_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from . import models

cors = CORS(app)


# -----SHOPIFY
def token_from_db(shop):
    token = models.Shop.query.filter_by(shop_name=shop).first().shop_token
    return token


def get_shop_location(shop, token):
    headers = {
        'X-Shopify-Access-Token': token,
    }
    locations_url = f'https://{shop}/admin/api/2020-04/locations.json'

    r = requests.get(locations_url, headers=headers)
    resp = r.json()
    return resp['locations'][0]['id']


@app.route('/api/app_launched', methods=['GET'])
@helpers.verify_web_call
def app_launched():
    shop = request.args.get('shop')
    token = None
    try:
        token = token_from_db(shop)
    except:
        pass
    if not token:
        global ACCESS_TOKEN, NONCE
        if ACCESS_TOKEN:
            return redirect(f'/admin?token={ACCESS_TOKEN}&shop={shop}&apikey={SHOPIFY_API_KEY}')
        # return 'muieeee'
        # The NONCE is a single-use random value we send to Shopify so we know the next call from Shopify is valid (see #app_installed)
        #   https://en.wikipedia.org/wiki/Cryptographic_nonce
        NONCE = uuid.uuid4().hex
        redirect_url = helpers.generate_install_redirect_url(shop=shop, scopes=SCOPES, nonce=NONCE,
                                                             access_mode=ACCESS_MODE)
        return redirect(redirect_url, code=302)
    else:
        return redirect(f'/admin?token={token}&shop={shop}&apikey={SHOPIFY_API_KEY}')


@app.route('/api/app_installed', methods=['GET'])
@helpers.verify_web_call
def app_installed():
    state = request.args.get('state')
    global NONCE, ACCESS_TOKEN

    # Shopify passes our NONCE, created in #app_launched, as the `state` parameter, we need to ensure it matches!
    if state != NONCE:
        return "Invalid `state` received", 400
    NONCE = None

    # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
    # Using the `code` received from Shopify we can now generate an access token that is specific to the specified `shop` with the
    #   ACCESS_MODE and SCOPES we asked for in #app_installed
    shop = request.args.get('shop')
    code = request.args.get('code')
    ACCESS_TOKEN = ShopifyStoreClient.authenticate(shop=shop, code=code)

    # We have an access token! Now let's register a webhook so Shopify will notify us if/when the app gets uninstalled
    # NOTE This webhook will call the #app_uninstalled function defined below
    shopify_client = ShopifyStoreClient(shop=shop, access_token=ACCESS_TOKEN)
    shopify_client.create_webhook(address=WEBHOOK_APP_UNINSTALL_URL+shop, topic="app/uninstalled")
    shopify_client.create_webhook(address=WEBHOOK_PRODUCT_ADDED_URL + shop, topic="products/create")
    wh = shopify_client.create_webhook(address=WEBHOOK_ORDER_CREATED_URL + shop, topic="orders/paid")
    wh_id = wh['id']
    shop_obj = models.Shop(shop_name=shop, shop_token=ACCESS_TOKEN, webhook_id=wh_id)
    db.session.add(shop_obj)
    db.session.commit()
    # shopify_client.create_redirect(path='/video', target=SERVER_DOMAIN)
    redirect_url = helpers.generate_post_install_redirect_url(shop=shop)
    return redirect(redirect_url, code=302)


@app.route('/api/app_uninstalled/<shop>', methods=['POST'])
@helpers.verify_webhook_call
def app_uninstalled(shop):
    # https://shopify.dev/docs/admin-api/rest/reference/events/webhook?api[version]=2020-04
    # Someone uninstalled your app, clean up anything you need to
    # NOTE the shop ACCESS_TOKEN is now void!
    global ACCESS_TOKEN
    ACCESS_TOKEN = None
    webhook_topic = request.headers.get('X-Shopify-Topic')
    webhook_payload = request.get_json()
    logging.error(f"webhook call received {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")
    shop_id=models.Shop.query.filter_by(shop_name=shop).first()
    shop_id=shop_id.id
    models.Shop.query.filter_by(shop_name=shop).delete()
    models.Room.query.filter_by(shop_id=shop_id).delete()
    db.session.commit()
    return "OK"


@app.route('/api/data_removal_request', methods=['POST'])
@helpers.verify_webhook_call
def data_removal_request():
    # https://shopify.dev/tutorials/add-gdpr-webhooks-to-your-app
    # Clear all personal information you may have stored about the specified shop
    return "OK"


@app.route('/api/new_room', methods=['POST'])
def new_room():
    def reorder_variants(shop, token, product_id):
        headers = {
            'X-Shopify-Access-Token': token,
            "Content-Type": "application/json"
        }
        url = f'https://{shop}/admin/api/2020-04/products/{product_id}.json'
        r = requests.get(url, headers=headers)
        items = r.json()
        try:
            items = items['product']['variants']
        except:
            return 0
        if len(items) > 0:
            list = []
            date_list = []
            ret_list = []
            for item in items:
                try:
                    sku = item['sku']
                    room_time = datetime.datetime.strptime(sku.split('S')[0], '%Y-%m-%d-%H-%M')
                    list.append((int(item['id']), room_time))
                    date_list.append(room_time)
                except:
                    pass
            date_list.sort()
            for date in date_list:
                for item in list:
                    if item[1] == date:
                        ret_list.append({'id': item[0]})
            payload = {
                'product': {
                    'id': product_id,
                    'variants': ret_list
                }
            }
            r = requests.put(url, headers=headers, json=payload)
        else:
            pass

    shop = request.get_json(force=True).get('shop')
    shop_obj = models.Shop.query.filter_by(shop_name=shop).first()
    token = shop_obj.shop_token
    product_id = request.get_json(force=True).get('instructor')
    date = request.get_json(force=True).get('selectedDates')['end'].split('T')[0]
    date = date.split('-')
    i = date.pop(-1)
    i = str(int(i) + 1)
    date.append(i)
    date = '-'.join(date)
    hour = request.get_json(force=True).get('hour')
    minutes = request.get_json(force=True).get('minutes')
    time = hour.split(' ')[0] + ':' + str(minutes) + ' ' + hour.split(' ')[1]
    price = request.get_json(force=True).get('price')
    price = str(price)
    variant_title = date + ' ' + time
    sku = date + '-' + hour.split(' ')[0] + '-' + str(minutes) + 'SKU' + str(product_id % 1000)
    headers = {
        'X-Shopify-Access-Token': token,
        "Content-Type": "application/json"
    }
    url = f'https://{shop}/admin/api/2020-04/products/{product_id}/variants.json'
    payload = {
        "variant": {
            "option1": variant_title,
            "price": price,
            'sku': sku
        }
    }
    r = requests.post(url, headers=headers, json=payload)
    ## try:
    variant_id = r.json()['variant']['id']
    inventory_id = r.json()['variant']['inventory_item_id']
    location_id = get_shop_location(shop, token)
    url = f'https://{shop}/admin/api/2020-04/inventory_levels/adjust.json'
    payload = {
        "location_id": location_id,
        "inventory_item_id": inventory_id,
        "available_adjustment": 3
    }
    r2 = requests.post(url, headers=headers, json=payload)
    url = f'https://{shop}/admin/api/2020-04/inventory_items/{inventory_id}.json'
    payload = {
        'inventory_item': {
            'id': inventory_id,
            'requires_shipping': False
        }
    }
    r3 = requests.put(url, headers=headers, json=payload)
    room = models.Room(room_id=variant_id, instructor_id=product_id, sku=sku, variant_title=variant_title,
                       shop=shop_obj)
    if not room.can_start():
        db.session.add(room)
        db.session.commit()
        reorder_variants(shop, token, product_id)
        # except:
        #     print('passed')
        return r.json()
    else:
        abort(401)


@app.route('/api/delete_room/<room_id>')
def delete_room(room_id):
    room_id = int(room_id)
    del_room(room_id)
    return 'OK'

def del_room(room_id):
    room = models.Room.query.filter_by(room_id=room_id).first()
    instructor_id = room.instructor_id
    shop = models.Shop.query.filter_by(id=room.shop_id).first()
    token = shop.shop_token
    shop_name = shop.shop_name
    headers = {
        'X-Shopify-Access-Token': token
    }
    url = f'https://{shop_name}/admin/api/2020-04/products/{instructor_id}/variants/{room_id}.json'
    r = requests.delete(url, headers=headers)
    models.Room.query.filter_by(room_id=room_id).delete()
    db.session.commit()
    
@app.route('/api/delete_past_rooms/<instructor_id>')
def delete_past_rooms(instructor_id):
    instructor_id=int(instructor_id)
    rooms=models.Room.query.filter_by(instructor_id=int(instructor_id))
    for room in rooms:
        if room.can_start():
            del_room(room.room_id)
    return 'OK'
        
@app.route('/api/get_instructors')
def get_rooms():
    shop = request.args.get('shop')
    shop_obj=models.Shop.query.filter_by(shop_name=shop).first()
    token = shop_obj.shop_token
    headers = {
        'X-Shopify-Access-Token': token
    }
    payload = {
        'product_type': 'instructor'
    }
    url = f'https://{shop}/admin/api/2020-04/products.json'
    r = requests.get(url, headers=headers, params=payload)
    data = r.json()
    response = []
    try:
        instructors = data['products']
        for instructor in instructors:
            l = []
            l2= []
            rooms = models.Room.query.filter_by(instructor_id=int(instructor['id'])).all()
            for room in rooms:
                if not room.can_start():
                    l.append(json.loads(json.dumps(room, cls=models.AlchemyEncoder)))
                else:
                    l2.append(json.loads(json.dumps(room, cls=models.AlchemyEncoder)))
            instructor.update({'upcoming_rooms': l})
            instructor.update({'past_rooms':l2})
            response.append(instructor)
    except:
        response = {'error': 'no instructors yet'}
    return jsonify({'response': response})


@app.route('/api/delete_instructor/<instructor_id>')
def delete_instructor(instructor_id):
    instructor_id=int(instructor_id)
    shop = request.args.get('shop')
    shop_obj = models.Shop.query.filter_by(shop_name=shop).first()
    token = shop_obj.shop_token
    headers = {
        'X-Shopify-Access-Token': token
    }
    url = f'https://{shop}/admin/api/2020-04/products/{instructor_id}.json'
    r = requests.delete(url, headers=headers)
    return 'OK'

@app.route('/api/product_added/<shop>', methods=['POST'])
@helpers.verify_webhook_call
def instructor_added(shop):
    data=request.get_json()
    if not data['product_type']=='instructor':
        pass
        return 'ok'
    else:
        token=token_from_db(shop)
        id=data['id']
        payload={
            'product':{
                'id':id,
                'options':[
                    {
                        'name':'Time and Date'
                    }
                ]
            }
        }
        headers = {
            'X-Shopify-Access-Token': token,
            "Content-Type": "application/json"
        }
        url=f'https://{shop}/admin/api/2020-04/products/{id}.json'
        r=requests.put(url, headers=headers, json=payload)
        return 'ok'

@app.route('/api/order_paid/<shop>', methods=['POST'])
@helpers.verify_webhook_call
def order_paid(shop):
    def fulfill_room(id, shop, order_id, email, item_id):
        send_room_pass(id, email, shop)
        token = token_from_db(shop)
        location = get_shop_location(shop, token)
        headers = {
            'X-Shopify-Access-Token': token,
            "Content-Type": "application/json"
        }
        url = f'https://{shop}/admin/api/2020-04/orders/{order_id}/fulfillments.json'
        payload = {
            "fulfillment": {
                "location_id": location,
                "tracking_number": None,
                "notify_customer": True,
                "line_items": [{
                    "id": item_id
                }]
            }
        }
        r = requests.post(url, headers=headers, json=payload)

    def send_room_pass(id, email, shop):
        room = models.Room.query.filter_by(room_id=id).first()
        pass_list = room.user_pass_list.split(':')
        current_pass = pass_list.pop(0)
        sent_pass_list = room.sent_pass_list if room.sent_pass_list else ''
        room.sent_pass_list = sent_pass_list + current_pass + ':'
        pass_list = ':'.join(pass_list)
        room.user_pass_list = pass_list
        count=room.count
        room.count=count+1
        db.session.commit()
        send_pass(email, current_pass, room, shop)

    def send_pass(email, passw, room, shop):
        username = EMAIL_USERNAME
        password = EMAIL_PASS
        fromaddr = 'test@muie.com'
        toaddrs = email
        shop_obj = models.Shop.query.filter_by(shop_name=shop).first()
        message=shop_obj.message
        msg = message.split('///')[1]
        msg = parse_msg(msg, room, passw)
        subj = message.split('///')[0]
        html = message.split('///')[2]
        html = parse_msg(html, room, passw)
        message = 'Subject: {}\n\n{}'.format(subj, msg)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(username, password)
        server.sendmail(fromaddr, toaddrs, message)
        server.quit()
        pass

    def parse_msg(msg, room, passw):
        date = room.variant_title
        link = room.link
        msg = msg.replace('<<LINK>>', link)
        msg = msg.replace('<<DATE>>', date)
        msg = msg.replace('<<PASSWORD>>', passw)
        return msg

    data = request.get_json()
    items = data['line_items']
    for item in items:
        room_id = int(item['variant_id'])
        room = models.Room.query.filter_by(room_id=room_id).first()
        if room:
            fulfill_room(room_id, shop, data['id'], data['email'], int(item['id']))
    return "OK"


@app.route('/api/edit_message')
def edit_message():
    shop = request.args.get('shop')
    title = request.args.get('title')
    body = request.args.get('msg')
    html = request.args.get('html')
    message= title+ '///' + body + '///' + html
    shop_obj = models.Shop.query.filter_by(shop_name=shop).first()
    shop_obj.message = message
    db.session.commit()
    return "OK"


@app.route('/api/get_message')
def get_message():
    shop = request.args.get('shop')
    shop_obj = models.Shop.query.filter_by(shop_name=shop).first()
    message = shop_obj.message
    response = {
        'message': {
            'title': message.split('///')[0],
            'body': message.split('///')[1],
            'html': message.split('///')[2]
        }
    }
    return jsonify(response)


# -----TWILIO

# @app.route('/')
# def index():
#     return render_template('index.html')


@app.route('/api/token', methods=['GET'])
def token():
    username = request.args.get('identity')
    room_name = request.args.get('roomName')
    password = request.args.get('password')
    if not username or not password or not room_name:
        abort(401)

    try:
        create_room(room_name)
    except:
        pass
    room=models.Room.query.filter_by(room_name=room_name).first()
    print(room.sent_pass_list)
    try:
        if password in room.sent_pass_list:
            if room.can_start():
                token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                                    twilio_api_key_secret, identity=username)
                token.add_grant(VideoGrant(room=room_name))
                return token.to_jwt().decode()
            else:
                return jsonify({'error':'Room has not started yet.'})

        else:
            abort(401)
    except:
        if password == room.admin_pass:
            if room.can_start():
                token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                                    twilio_api_key_secret, identity=username)
                token.add_grant(VideoGrant(room=room_name))
                return token.to_jwt().decode()
            else:
                return jsonify({'error': 'Room has not started yet.'})

        else:
            abort(401)


if __name__ == '__main__':
    app.run()
