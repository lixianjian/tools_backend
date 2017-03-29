#!/usr/bin/env python2.7
#coding=utf-8
'''
获取在线服务器上的数据，如日志、数据库信息等
该脚本放在中央服务器上

Created on 2015-03-10

@author: lixianjian@darkhutgame.com
'''

import urllib2
import os
from datetime import datetime, timedelta
import traceback as tb
import json
import time

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
    

def read_payment(bpath, day, cmds=['TopUp', 'delivery', 'top_up'], rate=10):
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
        detail  = param.get('detail', {})
        for k in ['tongbao', 'rmb']:
            datas[k]    += float(detail.get(k,0))
#        param['createtime'] = log_str[0]
#        param['roleid'] = log_str[1]
#        param['cmd']= cmd
#        datas.append(param)
    if datas['tongbao'] > 0.01 and datas['rmb'] < 0.001:
        datas['rmb']    += datas['tongbao']*1.0/rate
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
        #获取逻辑服的信息
        logic   = sql.find_one('amazon_logic', kwargs={'id': recordid})
        partner = logic['partner_id']
        #我方分账比例，1-合作方分账比例
        proportion  = 1- sql.find_one('amazon_partner_program_country', kwargs={'partner_id': partner})['proportion']
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
            #插入资金流水记录
            insert_logic_bill(sql, 'amazon_logic_bill', start_day, recordid, partner, reason=3, money=pdatas['rmb']*proportion)
            #日期向后移
            start_day = public.getNextDay(start_day)
    sql.disconnect()

def insert_logic_bill(sql, table, day, recordid, partner, reason=2, duration=5, money=0):
    """ 插入资金流水记录 """
    #检查当前日期数据是否已存在
    record  = sql.find_one(table, kwargs={'logic_id': recordid, 'day': day, 'reason_id': reason})
    if not record:
        #服务器一天的扣费
        rdatas  = {'logic_id': recordid, 
                   'reason_id': reason,                                     #默认服务器续费
                   'partner_id': partner,
                   'duration_id': duration,                                 #默认按天扣费
                   'money': money,
                   'tid': datetime.now().strftime('%Y%m%d%H%M%S'),
                   'day': day, 
                   'create': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                   'operator_id': 9,                                        #管理员
                   'deleted': 0, 
                   }
        #插入数据记录
        print 'insert record data %s'%rdatas
        print 'insert result: %s'%sql.insert(table, rdatas)
        sql.commit(table)
        time.sleep(1)

def write_server_use_cost(svr_info, start_day, end_day):
    """ 写服务器使用费用 """
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
        #获取逻辑服的信息
        logic   = sql.find_one('amazon_logic', kwargs={'id': recordid})
        while True:
            if start_day > end_day:
                break
            day = start_day
            #插入资金流水记录
            insert_logic_bill(sql, 'amazon_logic_bill', day, recordid, logic['partner_id'], money=logic['price'])
#            #检查当前日期数据是否已存在
#            record  = sql.find_one(table, kwargs={'logic_id': recordid, 'day': day})
#            if not record:
#                #服务器一天的扣费
#                rdatas  = {'logic_id': recordid, 
#                           'reason_id': 2,                                          #服务器续费
#                           'partner_id': logic['partner_id'],
#                           'duration_id': 5,                                        #按天扣费
#                           'money': logic['price'],
#                           'tid': datetime.now().strftime('%Y%m%d%H%M%S'),
#                           'day': day, 
#                           'create': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
#                           'operator_id': 9,                                        #管理员
#                           'deleted': 0, 
#                           }
#                #插入数据记录
#                print 'insert record data %s'%rdatas
#                print 'insert result: %s'%sql.insert(table, rdatas)
#                sql.commit(table)
#                time.sleep(1)
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
#        download_pay_log(svr_info=svr_info, day='2015-05-29', path=DOWNLOAD_PATH)
        #写玩家付费信息
        write_payer_info(svr_info, '2015-05-29', '2015-05-29')
#        #写服务器使用费用
#        write_server_use_cost(svr_info, '2015-05-29', '2015-05-29')