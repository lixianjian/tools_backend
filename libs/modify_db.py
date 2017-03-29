#!/usr/bin/python2.7
#coding=utf-8
'''
修改数据库
Created on 2012-7-26

@author: lixianjian@darkhutgame.net

'''

import json
#import os
import sys
import re

from do_sqllite import SqlLite

def modify_card(path):
	""" 修改商卡 """
	data_sql   = SqlLite(path)
	data_sql.conn= data_sql.force_conn()
	if data_sql.conn is None:
	    print 'connect db fail.'
	    return
	for data in data_sql.find('card', spec='deleted=0', fields=['id','intro','intro2','intro3']):
		if not bool(data):
		    break
		for k in ['intro','intro2','intro3']:
			for k2 in ['prop-tongbao','prop-aMetal','prop-dMetal','prop-aWood','prop-dWood','prop-aWater','prop-dWater','prop-aFire',
					'prop-dFire','prop-aEarth','prop-dEarth','prop-life','prop-aSpd','prop-crit','prop-resi','prop-hit','prop-dodge',
					'prop-xMetal','prop-xWood','prop-xWater','prop-xFire','prop-xEarth','prop-value','prop-duration','prop-aStr','prop-block']:
				if k2 in data[k]:
					data[k]	= data[k].replace(k2,'['+k2+']')
		data_sql.update_multi('card','id=%s'%data['id'],data)
	data_sql.disconnect()
	
	
if __name__ == '__main__':
	#modify_card(R'D:\Jean\program\support\tools_backend\tools_backend.db')
	s1	= 'dfasl'
	s1	= s1.replace('df', '1')
	print s1
