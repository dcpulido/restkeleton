#!/usr/bin/python
# # rutas se pueden generalizar todavia mas
# es recomendable??

import threading
import os
import sys
sys.path.insert(0, './models')
sys.path.insert(0, './')
from instance import Instance
from functools import wraps

from flask import render_template
from flask import Flask
from flask import request
from flask import redirect
from flask import session,  url_for, escape
import configparser

import urllib2

from DAO import mysqlDAO
import json
import base64
import datetime

from redis import Redis
ONLINE_LAST_MINUTES = 5

def logged():
    def logged_decorator(func):
        @wraps(func)
        def wrapped_function(*args,
                             **kwargs):
            aux = func(*args,
                       **kwargs)
            print "check log"
            if 'username' in session:
                return aux
            else:
                return redirect(url_for('index'))
        return wrapped_function
    return logged_decorator

def ConfigSectionMap(section, Config):
    dict1 = {}
    options = Config.options(section)
    for option in options:
        try:
            dict1[option] = Config.get(section, option)
            if dict1[option] == -1:
                logging.info('skip: %s' % option)
        except:
            logging.info('exception on %s!' % option)
            dict1[option] = None
    return dict1


def get_general_conf(name):
    Config = configparser.ConfigParser()
    Config.read('./conf/config.conf')
    myprior = {}
    for sec in Config.sections():
        if sec == name:
            myprior = ConfigSectionMap(sec, Config)
    return myprior


redis = Redis()
app = Flask(__name__, template_folder="static")
app.secret_key = os.urandom(24)
# template_folder="../templates")
daoconf = get_general_conf("Mysql")
flaskconf = get_general_conf("Flask")

def mark_online(user_id):
    now = int(time.time())
    expires = now + (ONLINE_LAST_MINUTES * 60) + 10
    all_users_key = 'online-users/%d' % (now // 60)
    user_key = 'user-activity/%s' % user_id
    p = redis.pipeline()
    p.sadd(all_users_key, user_id)
    p.set(user_key, now)
    p.expireat(all_users_key, expires)
    p.expireat(user_key, expires)
    p.execute()

def get_user_last_activity(user_id):
    last_active = redis.get('user-activity/%s' % user_id)
    if last_active is None:
        return None
    return datetime.utcfromtimestamp(int(last_active))

def get_online_users():
    current = int(time.time()) // 60
    minutes = xrange(ONLINE_LAST_MINUTES)
    return redis.sunion(['online-users/%d' % (current - x)
                         for x in minutes])

def ret(item): return [k.to_dict() for k in item] if type(
    item).__name__ == "list" else item.to_dict()


mysql = mysqlDAO(daoconf)


class flaskApp(threading.Thread):

    def run(self):
        app.run(threaded=True,
                host='0.0.0.0')

    def disconnect(self):
        urllib2.urlopen("http://localhost:5000/shutdown").read()

#cross side allow
@app.after_request
def sthtest(response):
    if request.headers.get('Origin'):
        response.headers["Access-Control-Allow-Origin"] = request.headers.get(
            'Origin')
    else:
        response.headers["Access-Control-Allow-Origin"] = request.remote_addr
    return response

#online users
@app.before_request
def mark_current_user_online():
    mark_online(request.remote_addr)



@app.route("/current",
           methods=['GET'])
@logged()
def current_time():
    now = datetime.datetime.now()
    return json.dumps(dict(
        year=now.year,
        month=now.month,
        day=now.day,
        hour=now.hour,
        minute=now.minute,
        second=now.second,
        weekday=datetime.datetime.today().weekday()
    ))

@app.route('/')
def index():
    if 'username' in session:
        return 'Logged in as %s' % escape(session['username'])
    return 'You are not logged in'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        return redirect(url_for('index'))
    return '''
        <form method="post">
            <p><input type=text name=username>
            <p><input type=submit value=Login>
        </form>
    '''


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))


@app.route("/something",
           methods=['POST', 'GET'])
def fet_something():
    if request.method == 'GET':
        something = mysql.get_all("something")
        toret = []
        for som in something:
            toret.append(som)
        return json.dumps(ret(toret))


@app.route('/shutdown',
           methods=['GET', 'POST'])
def shutdown():
    stop_flask()
    return 'Server shutting down...'


def stop_flask():
    func = request.environ.get("werkzeug.server.shutdown")
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def get_last(items):
    fl = True
    last = None
    if type(items).__name__ == "list":
        for it in items:
            if fl:
                last = it
                fl = False
            else:
                if it.date > last.date:
                    last = it
        return last
    else:
        return items


def encode_image(item):
    with open(item.image, "rw") as image:
        item.image = base64.b64encode(image.read())
    return item
