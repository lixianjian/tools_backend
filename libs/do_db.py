#coding=utf-8

'''
这个文件里面包含数据库常用操作的一些函数
针对使用SQLite数据库
'''

import sqlite3 as sqlite
import traceback as tb
import json
import string

from public import _2unicode, objIsEmpty, _2utf8


class SqlLite:
    def __init__(self, database):
        self.database   = database
        self.conn       = None
        self.cursor     = None

    def __getattr__(self, name):
        return self.router[name]

    def __getitem__(self, name):
        return self.__getattr__(name)
    
    def force_conn(self):
        conn = None
        times = 0
        while conn is None:
            print 'begin to connect to %r'%self.database
            try:
                conn = sqlite.connect(self.database)
                print '%s is connected done'%self.database
                return conn
            except sqlite.OperationalError:
                print 'connection to db %r failed wait for retring %r, %r'%(self.database, times, tb.format_exc())
                conn = None
            times += 1
            if times >= 20:
                print 'db connection failed wait for retry later'
                return sqlite.connect(self.database)
    
    def table_exist(self, tname):
        """ 查找表是否存在 """
        self.cursor = self.conn.cursor()
        self.cursor.execute("select count(*) from sqlite_master where  type='table' and name='%s'"%tname)
        #如果表不存在
        if not self.cursor.fetchall()[0][0]:
            return False
        return True
            
    def create_table(self, name, fields):
        """ 创建表 """
        self.cursor = self.conn.cursor()
        try:
            sql = 'create table if not exists %s(%s)' % (name, string.join(fields, ','))
            self.cursor.execute(sql)
            return True
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())
            return False

    def remove(self, name, spec=None):
        self.cursor = self.conn.cursor()
        try:
            sql = 'delete from %s' % name
            if not objIsEmpty(spec):
                sql += ' where %s' % spec
            self.cursor.execute(sql)
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())
            return False
        print '%s is removed done'%name
        return True

    def drop(self, name):
        self.cursor = self.conn.cursor()
        try:
            sql = 'drop table if exists %s' % name
            self.cursor.execute(sql)
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())
            return False
        print '%s is dropped done'%(name)
        return True

    def insert(self, name, dData, fields=[]):
        if objIsEmpty(dData):
            return False
        if not isinstance(dData, list):
            dData = [dData]

        self.conn.text_factory = sqlite.OptimizedUnicode
        self.cursor = self.conn.cursor()

        if self.table_exist(name) is False:
            self.create_table(name, fields)
        
        keys   = []
        fmts   = []
        try:
            sql = 'select * from %s limit 1' % name
            self.cursor.execute(sql)
            for col in self.cursor.description:
                key = col[0]

                keys.append(key)
                fmts.append('?')

        except:
            print 'IGNORE: failed to %s, %r'%(sql, tb.format_exc())

            oneData = dData[0]
            for key in oneData.iterkeys():
                keys.append(key)
                fmts.append('?')

        manyValues = []
        for oneData in dData:
            values = []
            for key in keys:
                value = oneData.get(key)
                if value is None:
                    keyU = _2unicode(key)
                    value = oneData.get(keyU)
                if isinstance(value, list) or isinstance(value, dict):
                    save_v = json.dumps(value)
                #sqlite3.ProgrammingError:
                # You must not use 8-bit bytestrings unless you use a text_factory that can interpret 8-bit bytestrings
                # (like text_factory = str).
                # It is highly recommended that you instead just switch your application to Unicode strings.
                elif isinstance(value, basestring):
                    save_v = _2unicode(value)
                else:
                    save_v = value
                values.append(save_v)
            manyValues.append(tuple(values))

        try:
            sql = 'insert into %s values(%s)' % (name, string.join(fmts, ','))
            self.cursor.executemany(sql, manyValues)
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())
            return False

        print '%s(%d) is inserted done'%(name, len(manyValues))
        return True

    def commit(self, name):
        self.conn.commit()
        print '%s id committed done'%name
        return True

    def find(self, name, spec=None, fields=None, other=None):
        if not objIsEmpty(fields):
            fields_str = string.join(fields, ',')
        else:
            fields_str = '*'
        sql = 'select %s from %s' % (fields_str, name)
        if not objIsEmpty(spec):
            sql += ' where %s' % spec
        if not objIsEmpty(other):
            sql += ' %s' % other

        self.conn.row_factory  = sqlite.Row
        self.conn.text_factory = sqlite.OptimizedUnicode
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            colls = []
            for row in res:
                detail = dict(row)
                colls.append(detail)
            return colls
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())

        #保证返回值为list
        return []

    def find_one(self, name, fields=None, kwargs={}):
        if not objIsEmpty(fields):
            fields_str = string.join(fields, ',')
        else:
            fields_str = '*'
        sql = 'select %s from %s' % (fields_str, name)
        if not objIsEmpty(kwargs):
            conditions = []
            for k, v in kwargs.iteritems():
                condition = '%s=:%s' % (k, k)
                conditions.append(condition)
                #sqlite3.ProgrammingError:
                # You must not use 8-bit bytestrings unless you use a text_factory that can interpret 8-bit bytestrings
                # (like text_factory = str).
                # It is highly recommended that you instead just switch your application to Unicode strings.
                if isinstance(v, basestring):
                    kwargs[k] = _2unicode(v)
            conditions_str = string.join(conditions, ' and ')
            sql += ' where %s' % conditions_str

        self.conn.row_factory  = sqlite.Row
        self.conn.text_factory = sqlite.OptimizedUnicode
        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(sql, kwargs)
            row = self.cursor.fetchone()
            detail = dict(row)
            return detail
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())

    def update(self, name, spec=None, args=''):
        sql = 'update %s set %s' % (name, args)
        if not objIsEmpty(spec):
            sql += ' where %s' % spec

        self.cursor = self.conn.cursor()
        try:
            self.cursor.execute(sql)
            return True
        except:
            print 'failed to %s, %r'%(sql, tb.format_exc())
            return False

    def update_multi(self, name, spec=None, kwargs={}):
        words = []
        for key, value in kwargs.iteritems():
            if isinstance(value, list) or isinstance(value, dict):
                save_v = json.dumps(value)
                word = "%s='%s'" % (key, save_v)
            elif isinstance(value, basestring):
                save_v = _2utf8(value)
                word = "%s='%s'" % (key, save_v)
            else:
                save_v = value
                if save_v == None:
                    word = '%s=null' % key
                else:
                    word = '%s=%r' % (key, save_v)
            words.append(word)
        args = string.join(words, ',')
        return self.update(name, spec, args)

    def update_one(self, name, key, kvalue, kwargs={}):
        if isinstance(kvalue, basestring):
            spec = "%s='%s'" % (key, _2utf8(kvalue))
        else:
            spec = '%s=%r' % (key, kvalue)
        return self.update_multi(name, spec, kwargs)
    
    def disconnect(self):
        """ 关闭游标 """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


if __name__ == '__main__':
    
    sql = SqlLite(R'D:\check_data\db\test\test.db')
    sql.conn    = sql.force_conn()
    if  sql.conn is None:
        print 'connect db fail.'
    else:
#        print sql.remove('test', 'sid=5')
        print sql.insert('test2', {'sid':1, 'type':'type1', 'catalogue':'d:/test'}, ['sid integer', 'type varchar(20)', 'catalogue varchar(20)'])
        sql.commit('test2')
        print sql.find('test2', 'sid=1', ['catalogue'], "and type='type1'")
        print sql.find_one('test2', ['catalogue'], {'sid':1})
    sql.disconnect()    
    
    print 'complete'
