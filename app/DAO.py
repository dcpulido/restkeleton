import sys
sys.path.insert(0, '../models')
import json
import logging
import mysql.connector
from mysql.connector import errorcode
from instance import Instance


class mysqlDAO:

    def __init__(self,
                 conf):
        self.conf = conf
        self._spec = {}
        self.connect_to_database()
        self.get_schema()

    def connect_to_database(self):
        try:
            self.cnx = mysql.connector.connect(user=self.conf["user"],
                                               password=self.conf["password"],
                                               host=self.conf["host"],
                                               database=self.conf["database"],
                                               port=3306)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logging.info(
                    "Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logging.info("Database does not exist")
            else:
                logging.info(err)

    def insert(self,
               ob):
        keys = ""
        values = "VALUES ("
        for k in ob.to_dict().keys():
            if k != "idUser":
                def ret(x): return '%(' + k + ')s, ' \
                    if type(x).__name__ == "str" \
                    or type(x).__name__ == "unicode" \
                    else '%('+str(x)+')s, '
                values += ret(k)
                keys += k + \
                    ", "
        values = values[:len(values)-2] + ")"
        keys = keys[:len(keys)-2] + ") "
        query = "INSERT INTO " + \
            ob.__class__.__name__ + \
            " (" + \
            keys + \
            values
        try:
            cursor = self.cnx.cursor()
            cursor.execute(query, ob.to_dict())
            lsid = cursor.lastrowid
            self.cnx.commit()
            cursor.close()
            return lsid
        except Exception, e:
            logging.info(e)
            return None

    def get_by_id(self,
                  id,
                  module_name):
        instance = Instance()
        instance.__class__.__name__ = module_name

        def ret(x): return '"'+x+'"' \
            if type(x).__name__ == "str" \
            or type(x).__name__ == "unicode" \
            else str(x)
        ids = ""
        for kk in self._spec[module_name]:
            if kk in id.keys():
                ids += kk + \
                    "=" +\
                    ret(id[kk]) + \
                    " AND "
        ids = ids[:len(ids)-5]
        query = "SELECT * " + \
            ", ".join(instance.to_dict().keys()) + \
            " FROM " + \
            module_name + \
            " WHERE " + \
            ids
        try:
            cursor = self.cnx.cursor(dictionary=True)
            cursor.execute(query)
            toret = []
            for c in cursor:
                if c is not None:
                    instance = Instance()
                    instance.__class__.__name__ = module_name
                    instance.set_by_dic(c)
                    toret.append(instance)
            cursor.close()
            if len(toret) == 1:
                return toret[0]
            else:
                return toret
        except Exception, e:
            logging.info(e)
            logging.info("error in get by id returning []")
            return []

    def get_all(self,
                module_name):
        query = "SELECT  * FROM " + \
                module_name
        try:
            cursor = self.cnx.cursor(dictionary=True)
            cursor.execute(query)
            toret = []
            for c in cursor:
                instance = None
                if c is not None:
                    instance = Instance()
                    instance.__class__.__name__ = module_name
                    instance.set_by_dic(c)
                    toret.append(instance)
            cursor.close()
            return toret
        except Exception, e:
            logging.info(e)
            logging.info("error in get all returning []")
            return []

    def delete(self,
               id,
               module_name):
        def ret(x): return '"'+x+'"' \
            if type(x).__name__ == "str" \
            or type(x).__name__ == "unicode" \
            else str(x)
        ids = ""
        for kk in id.keys():
            ids += kk + \
                "=" +\
                ret(id[kk]) + \
                " AND "
        ids = ids[:len(ids)-5]

        query = "DELETE FROM " + \
                module_name + \
                " WHERE " + \
                ids
        try:
            cursor = self.cnx.cursor()
            cursor.execute(query)
            self.cnx.commit()
            cursor.close()
        except Exception, e:
            self.connect_to_database()
            self.delete(id, module_name)
            raise

    def update(self,
               ob):
        def ret(x): return '"'+x+'"' \
            if type(x).__name__ == "str" \
            or type(x).__name__ == "unicode" \
            else str(x)
        ww = " WHERE "
        for k in self._spec[ob.__class__.__name__]:
            ww += k + \
                "=" + \
                ret(ob.to_dict()[k]) + \
                " AND "
        ww = ww[:len(ww)-5]
        sets = " SET "
        for k in ob.to_dict().keys():
            sets += k +\
                "=%s, "
        sets = sets[:len(sets)-2]
        query = "UPDATE " + \
                ob.__class__.__name__ + \
                sets + \
                ww
        try:
            cursor = self.cnx.cursor()
            cursor.execute(query,
                           ob.to_dict().values())
            self.cnx.commit()
            cursor.close()
        except Exception, e:
            logging.info(e)

    def get_schema(self):
        try:
            cursor = self.cnx.cursor(dictionary=True)
            query = 'select * ' + \
                'from INFORMATION_SCHEMA.COLUMNS ' + \
                ' where table_schema="' + \
                self.conf["database"] + \
                '";'
            cursor.execute(query)
            tt = {}
            for att in cursor:
                if att["COLUMN_KEY"] == "PRI":
                    if att["TABLE_NAME"] in self._spec:
                        self._spec[att["TABLE_NAME"]].append(
                            att["COLUMN_NAME"])
                    else:
                        self._spec[att["TABLE_NAME"]] = [att["COLUMN_NAME"]]
            cursor.close()
        except Exception, e:
            logging.info(e)

    def disconnect(self):
        self.cnx.close()


if __name__ == "__main__":
    dao = mysqlDAO()
