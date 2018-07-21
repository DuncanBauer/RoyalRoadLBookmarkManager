import MySQLdb


class DB:
    def __init__(self):
        self.conn = None
        self.host = None
        self.user = None
        self.passwd = None
        self.db = None
        self.charset = None

    def connect(self, _host, _user, _passwd, _db, _charset):
        self.conn = MySQLdb.connect(host=_host, user=_user, passwd=_passwd, db=_db, charset=_charset)
        self.host = _host
        self.user = _user
        self.passwd = _passwd
        self.db = _db
        self.charset = _charset

    def reconnect(self):
        self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.db, charset=self.charset)

    def query(self, sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql[0],sql[1])
            self.conn.commit()
        except (AttributeError, MySQLdb.OperationalError):
            self.reconnect()
            cursor = self.conn.cursor()
            cursor.execute(sql[0],sql[1])
            self.conn.commit()
        return cursor

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
