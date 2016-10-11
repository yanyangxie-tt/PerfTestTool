# -*- coding=utf-8 -*-
# author: yanyang.xie@gmail.com

import sys
import MySQLdb
from MySQLdb.cursors import DictCursor

class MySQLConnection(object):
    conn = ''
    cursor = ''
    def __init__(self, host, user, passwd, db=None, charset='utf8', port=3306, cursorclass=DictCursor):
        """MySQL Database initialization """
        try:
            if db is None:
                self.conn = MySQLdb.connect(host, user, passwd, port=port, cursorclass=cursorclass)
            else:
                self.conn = MySQLdb.connect(host, user, passwd, db, port=port, cursorclass=cursorclass)
        except MySQLdb.Error, e:
            errormsg = 'Cannot connect to server\nERROR (%s): %s' % (e.args[0], e.args[1])
            print errormsg
            sys.exit(1)

        self.cursor = self.conn.cursor()

    def use_db(self, db):
        self.conn.select_db(db)

    def execute(self, sql_string):
        """  Execute SQL statement """
        #insert into user values('Tom','1321');
        try:
            if type(sql_string) in [list, set, tuple]:
                for q in sql_string:
                    self.cursor.execute(q)
            else:
                
                self.cursor.execute(sql_string)
            self.conn.commit()
        except Exception, e:
            print 'Failed to execute sql.\nERROR (%s): %s' % (e.args[0], e.args[1])
            self.conn.rollback()
    
    def execute_with_values(self, sql_string, values):
        """  Batch execute SQL statement """
        #insert into user values(%s,%s), [('Joke', '2234'), ('Alice', '3334'),]
        if type(sql_string) is not str:
            print 'Sql must be string'
        
        try:
            if type(values) in [list, set, tuple]:
                '''
                sql = "insert into person(name, age, telephone) values(%s, %s, %s)"
                tmp = (('ninini', 89, '888999'), ('koko', 900, '999999'))
                conn.executemany(sql, tmp)
                '''
                self.cursor.executemany(sql_string, values)
            else:
                self.cursor.execute(sql_string, values)
            self.conn.commit()
        except Exception, e:
            print 'Failed to execute sql.\nERROR (%s): %s' % (e.args[0], e.args[1])
            self.conn.rollback()
    
    def count(self):
        ''' Return the count by previous SQL'''
        return self.cursor.rowcount
    
    def find_one(self):
        """ Return the first result after executing SQL statement """
        return self.cursor.fetchone()
    
    def find_all(self):
        """ Return the results after executing SQL statement """
        return self.cursor.fetchall()
              
    def __del__(self):
        """ Terminate the connection """
        self.conn.close()
        self.cursor.close()

if __name__ == '__main__':
    db='addtest'
    connect = MySQLConnection(host='localhost', user='root', passwd='111111', charset='utf8', port=3306)
    connect.execute('create database %s' %(db))
    connect.use_db(db)
    connect.execute("CREATE TABLE  user (name VARCHAR(20),password VARCHAR(200));")
    connect.execute("insert into user values('Tom','1321');")
    connect.execute_with_values("insert into user values(%s,%s)", [('Joke', '2234'), ('Alice', '3334'),])
    
    import json
    json_data = json.dumps({"c": 0, "b": 0, "a": 0})
    connect.execute_with_values("insert into user values(%s,%s)", [('json', json_data),])
    
    print '#' * 100
    connect.execute("select * from user;")
    print connect.count()
    query_data = connect.find_all()
    print query_data
    
    for data in query_data:
        if data['name'] == 'json':
            print json.loads(data['password'])
            print type(json.loads(data['password']))
    
    connect.execute('drop database %s' %(db))
