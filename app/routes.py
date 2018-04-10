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


app = Flask(__name__, template_folder="static")
app.secret_key = os.urandom(24)
# template_folder="../templates")
daoconf = get_general_conf("Mysql")
flaskconf = get_general_conf("Flask")


def ret(item): return [k.to_dict() for k in item] if type(
    item).__name__ == "list" else item.to_dict()


mysql = mysqlDAO(daoconf)


class flaskApp(threading.Thread):

    def run(self):
        app.run(threaded=True,
                host='0.0.0.0')

    def disconnect(self):
        urllib2.urlopen("http://localhost:5000/shutdown").read()


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
