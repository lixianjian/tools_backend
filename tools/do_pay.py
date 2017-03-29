#!/usr/bin/env python2.7
#coding=utf-8
'''
获取在线服务器上的数据，如日志、数据库信息等
该脚本放在中央服务器上

Created on 2012-05-16

@author: lixianjian@darkhutgame.com
'''

import urllib2
import os
from datetime import datetime, timedelta
import traceback as tb
import json

from libs.config import DOWNLOAD_PATH,BASE_DATA_PATH,PROGRAM_PATH,BS_DB_NAME
from libs import public
from libs.game_server import get_gs_from_db
from libs.do_sqllite import SqlLite

def url_download(url, despath):
    """ URL下载数据 """
    try:
        #使用urllib.urlretrieve直接下载文件，但是该方法有个缺点就是当文件不存在的时候返回的是网页错误源码，而且程序无法得知
        #response    = urllib.urlretrieve(url,despath)
        #该方法有一个好处就是能够获取到网页返回的状态码，从而判断下载是否报错
        req         = urllib2.Request(url)
        response    = urllib2.urlopen(req)
    except urllib2.HTTPError,e:
        print 'error code: %s'% e.code
        #print 'achieve pay log fail. %s'%tb.format_exc()
    else:
        status  = response.code 
        if status == 200:
            with open(despath, "wb") as fhandler:     
                fhandler.write(response.read())
                fhandler.close()
        else:
            print 'achieve pay log fail. response status: %s'%status

def download_pay_log(svr_info={}, day=None, path=DOWNLOAD_PATH):
    """ 下载充值数据库 """
    recordid= svr_info.get('id')
    domain  = svr_info.get('domain')
    svrid   = svr_info.get('svrid')
    program = svr_info.get('program')
    if not domain:
        print 'record id [%s], domain is none'%recordid
    elif not svrid:
        print 'record id [%s], server id is none'%recordid
    elif not program:
        print 'record id [%s], program is none'%recordid
    else:
        fname   = 'pay_'+ day+'.log'
        url= 'http://%s/pay_log/%s' %(domain, fname)
        pay_path= os.path.join(BASE_DATA_PATH,program+'%s/pay'%svrid)
        print 'pay_path: ',pay_path
        public._mkdir(pay_path)
        despath = pay_path + '/' + fname
        url_download(url, despath)
    

def read_payment(bpath, day, cmds=['TopUp', 'delivery']):
    """ 读取充值记录 """
    #金币数量
    datas   = {'tongbao': 0, 'rmb': 0}
    tids= []
    log_strs= []
    path    = bpath + '/pay_' + day + '.log'
    print 'path: ',path
    if os.path.exists(path):
        log_strs= public.read_file_list(path)                    
    for log_str in log_strs:
        if len(log_str) < 4:
            print log_str
            continue
        #不是条件记录
        if log_str[2] not in cmds:
            continue
        param   = json.loads(log_str[3])
        #重复订单
        tid = param.get('tid')
        if tid in tids:
            continue
        else:
            tids.append(tid)
        for k in ['tongbao', 'rmb']:
            datas[k]    += param.get(k,0)
#        param['createtime'] = log_str[0]
#        param['roleid'] = log_str[1]
#        param['cmd']= cmd
#        datas.append(param)        
    return datas

def write_payer_info(svr_info, start_day, end_day):
    """ 写玩家付费信息 """
    #链接数据库
    db_path = os.path.join(PROGRAM_PATH,BS_DB_NAME)
    sql = SqlLite(db_path)
    sql.conn    = sql.force_conn()
    if not sql.conn:
        print 'connect db [%s] fail.'%db_path
        return
    recordid= svr_info.get('id')
    svrid   = svr_info.get('svrid')
    program = svr_info.get('program')
    if not svrid:
        print 'record id [%s], server id is none'%recordid
    elif not program:
        print 'record id [%s], program is none'%recordid
    else:
        pay_path= os.path.join(BASE_DATA_PATH,program+'%s/pay'%svrid)
        print 'pay_path: ',pay_path
        public._mkdir(pay_path)
        while True:
            if start_day > end_day:
                break
            #计算充值数据，并写入数据库
            pdatas  = read_payment(pay_path, start_day)
            #添加\修改逻辑服日、月充值记录
            for k in ['logic','logic_month']:
                table   = 'amazon_%s_recharge'%k
                day = start_day
                prev_day= public.getLastDay(day)
                if k == 'logic_month':
                    day = start_day[:8]+'01'
#                    print 'day', day
                    prev_day= public.get_prev_month(day)
#                print k,'day, prev_day:',day,prev_day
                pre_data= sql.find_one(table, kwargs={'logic_id': recordid, 'day': prev_day})
                rdatas  = {'logic_id': recordid, 'day': day, 'create': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'operator_id': 9, 'deleted': 0, 
                           'coins': pdatas['tongbao'], 'sum_coins': pdatas['tongbao'], 'money': pdatas['rmb'], 'sum_money': pdatas['rmb']}
                if pre_data:
                    rdatas['sum_coins'] += pre_data.get('sum_coins', 0)
                    rdatas['sum_money'] += pre_data.get('sum_money', 0)
                #检查当前日期数据是否已存在
                record  = sql.find_one(table, kwargs={'logic_id': recordid, 'day': day})
#                print day,'record',record
                if record:
                    #存在则更新数据
                    print 'update record data %s'%rdatas
                    print 'update result: %s'%sql.update_multi(table, 'logic_id=%s and day="%s"'%(recordid, day), rdatas)
                else:
                    #插入数据记录
                    print 'insert record data %s'%rdatas
                    print 'insert result: %s'%sql.insert(table, rdatas)
                sql.commit(table)
            #日期向后移
            start_day = public.getNextDay(start_day)
    sql.disconnect()

def timing():
    """ 定时执行 """
    #获取日期
    servers = get_gs_from_db()
    day = public.get_yesterday(days=1)
    for server in servers:
        print server
        try:
            #下载充值数据库
            download_pay_log(server,day)
            #写玩家付费信息
            write_payer_info(server, day, day)
        except:
            public.print_str('serverid [%s] \t %r'%(server.get('svrid','0'),tb.format_exc()))


if __name__ == "__main__":
        
    #执行正式模块
    EXCUTE_PROCESS  = False
    #执行测试模块
    EXCUTE_TEST     = True
    if EXCUTE_PROCESS:
        timing()
        #timing_debug()
    elif EXCUTE_TEST:
#        achieve = Achieve('2')
        svr_info    = {'program': 'kashen', 'domain': '230.kashen.darkhutgame.net', 'svrid': 1, 'id': 1}
#        #下载充值数据库
#        download_pay_log(svr_info=svr_info, day='2015-03-09', path=DOWNLOAD_PATH)
        #写玩家付费信息
        write_payer_info(svr_info, '2015-03-04', '2015-03-10')