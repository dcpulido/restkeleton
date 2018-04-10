# david.coello@ctag.com

import sys
sys.path.insert(0, './app')
import configparser
import logging
import time
from routes import flaskApp
from DAO import mysqlDAO


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


if __name__ == '__main__':
    generalconf = get_general_conf('General')
    daoconf = get_general_conf("Mysql")
    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(message)s',
        level=logging.DEBUG)
    logging.info('Little server')

    dao = mysqlDAO(daoconf)

    fl = flaskApp()
    try:
        fl.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        fl.disconnect()
