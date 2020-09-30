from .app import db, DEFAULT_EMAIL_TEMPLATE, SERVER_DOMAIN

import string
import random
import datetime
from sqlalchemy.ext.declarative import DeclarativeMeta
import json



class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
                data = obj.__getattribute__(field)
                try:
                    json.dumps(data) # this will fail on non-encodable values, like other classes
                    fields[field] = data
                except TypeError:
                    fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)

class Shop(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    shop_name=db.Column(db.String, nullable=False)
    shop_token=db.Column(db.String, nullable=False)
    webhook_id=db.Column(db.Integer, nullable=False)
    message=db.Column(db.String, default=DEFAULT_EMAIL_TEMPLATE)
    rooms=db.relationship('Room', backref='shop', lazy='dynamic')

class Room(db.Model):

    id=db.Column(db.Integer, primary_key=True)
    room_id=db.Column(db.Integer, nullable=False)
    room_name=db.Column(db.String)
    instructor_id=db.Column(db.Integer, nullable=False)
    # instructor_name=db.Column(db.String, nullable=False)
    sku=db.Column(db.String, nullable=False)
    variant_title=db.Column(db.String, nullable=False)
    # hour=db.Column(db.String, nullable=False)
    # minutes=db.Column(db.Integer, nullable=False)
    user_pass_list=db.Column(db.String)
    admin_pass=db.Column(db.String)
    sent_pass_list=db.Column(db.String)
    started=db.Column(db.Boolean, nullable=False, default=False)
    link=db.Column(db.String)
    count=db.Column(db.Integer, nullable=False, default=False)
    shop_id=db.Column(db.Integer, db.ForeignKey('shop.id'))

    def __init__(self, **kwargs):
        super(Room, self).__init__(**kwargs)
        self.room_name=self.gen_room_name()
        passlist=self.gen_pass_list()
        admin=passlist.pop(0)
        self.admin_pass=admin
        self.user_pass_list=':'.join(passlist)
        self.started=self.can_start()
        self.link = SERVER_DOMAIN + '/room/' + self.room_name

    def gen_room_name(self):
        size = 6
        allowed = string.ascii_letters+string.digits  # add any other allowed characters here
        random_string = ''.join([allowed[random.randint(0, len(allowed) - 1)] for x in range(size)])
        if not self.query.filter_by(room_name=random_string).all():
            return random_string
        else:
            return self.gen_room_name()

    def gen_pass_list(self):
        size = 6  # or whatever lenght you want your random string to be
        allowed = string.ascii_letters + string.digits # add any other allowed characters here
        l=[]
        for i in range(4):
            randomstring = ''.join([allowed[random.randint(0, len(allowed) - 1)] for x in range(size)])
            l.append(randomstring)
        return l

    def can_start(self):
        room_time=datetime.datetime.strptime(self.sku.split('S')[0], '%Y-%m-%d-%H-%M')
        est_time=datetime.datetime.utcnow()-datetime.timedelta(hours=4, minutes=10)
        if room_time<est_time:
            return True
        else:
            return False