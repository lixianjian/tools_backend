#!/usr/bin/python2.7
#coding=utf-8
"""
服务器配置信息
"""
from do_sqllite import SqlLite
import os
#import operator

def get_gs_from_db(status=[5,6]):
    """ 从数据库中获取 """
    ctf = os.path.dirname(os.path.abspath(__file__))
#    datas   = {}
    servers = []
    if os.path.exists(ctf + '/libs_local.py'):
        from libs_local import PROGRAM_PATH,BS_DB_NAME
        sql = SqlLite(os.path.join(PROGRAM_PATH,BS_DB_NAME))
        sql.conn= sql.force_conn()
        infos   = sql.find('amazon_logic')
        for info in infos:
            #不在选定状态内
            if info.get('status_id',0) not in status:
                continue
#            sid = info['sid']
#            datas[sid]  = info
            servers.append(info)
        sql.disconnect()
    #服务器配置排序    
    #sort_servers= sorted(servers, key=operator.itemgetter('start_date'))
    return servers

#SERVERS = get_gs_from_db()
#for server in get_gs_from_db():
#    print server
