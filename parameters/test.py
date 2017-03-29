#coding=utf-8
'''
Created on 2013-9-3

@author: lixianjian
'''
#
#import json
#s1  = '[[12, 3,4, 54,56 ] ,[3 , 243, 545,532,56]]'
#print json.loads(s1.replace(' ', '').replace(',', ', '))

#from libs.do_sqllite import SqlLite
#
#src_data_sql= SqlLite(R'D:\Jean\program\support\tools_backend\tools_backend_2013-11-22_12_06.db.bak')
#src_data_sql.conn  = src_data_sql.force_conn()
#records = src_data_sql.find('card')
#for record in records:
#    record['wuxing']    = [record['wuxing']]
#src_data_sql.disconnect()
#
#dst_data_sql= SqlLite(R'D:\Jean\program\support\tools_backend\tools_backend.db')
#dst_data_sql.conn  = dst_data_sql.force_conn()
#dst_data_sql.insert('card',records)
#dst_data_sql.commit('card')
#dst_data_sql.disconnect()
d1  = {'key': 'value'}
#print d1.key
s2  = ''
print 'test: ',s2[:8]


class Test():
    def __init__(self):
        self.output = 'test class'
    
    def put(self):
        print self.output

print Test()
t1 = Test()
print t1

def foo(l):
    for i in l:
        yield i+1

l=[1,2,3,4]
for x in foo(l):
    print x