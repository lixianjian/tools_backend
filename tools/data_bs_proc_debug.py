#!/usr/bin/python2.7
#coding=utf-8
'''
(1) 贸易获利总额(测试期间)
(2) 人均获利(按日统计)
(3) 人均行动力消耗(按日统计)
(4) 人均在线时长(日)


Created on 2012-7-3

@author: lixianjian@darkhutgame.net

'''

import json
import sys
from datetime import datetime, timedelta
from time import time
import operator
import urllib
import traceback as tb

from tool_local import LIBS_PATH
sys.path.append(LIBS_PATH)

from config import *
import public
from do_sqllite import SqlLite
#from achieve_file import Achieve
#from write_role import drawBaseData


class DataBackstage():
    
    def __init__(self, sid, create=False, start_day=None, end_day=None):
        """ 初始化 """
        self.sid    = sid
        #开服日期
        self.ss_date= ''    #SERVER_START_DATE[self.sid]
        self.rates  = {}
        self.yesterday  = (datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
        #新用户
        self.new_roleids= []
        self.url    = None
        #玩家当日的付费数据
        self.pay_counts = {}
        #kashen_data.db的链接
        self.data_sql= None
        #区服器配置
        self.server_info    = {}
        
#        if create:
#            self.create_roleid()
        if start_day:
            self.set_date(start_day, end_day)
    
    def create_roleid(self):
        """ 生成玩家的roleid和total_roleid文件 """
        now         = datetime.now()
        today       = now.strftime('%Y-%m-%d')
        draw_base_data = drawBaseData(self.sid)
        draw_base_data.writeRoleidTime(today, today, False, False)
    
    def set_server_info(self):
        """ 设置服务器信息 """
        msg = public.get_server_info(self.sid)
        if msg['status'] != 0:
            print 'error msg : ', msg
            return False
        else:
            self.server_info= msg['data']
            self.gl_path    = self.server_info['gl_path']
            self.ul_path    = self.server_info['ul_path']
            self.ss_date    = self.server_info['start_date']
            return True
    
    def set_date(self, p_start_date=None, p_end_date=None):
        """ 获取日期值 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        if p_start_date:
            self.start_date  = p_start_date
        else:
            self.start_date  = self.yesterday
        
        if p_end_date:
            if p_end_date > today:
                self.end_date= today
            else:
                self.end_date= p_end_date
        else:
            self.end_date    = self.yesterday
        
        if self.start_date < self.ss_date:
            self.start_date  = self.ss_date
        if self.end_date < self.ss_date:
            self.end_date    = self.ss_date
        
        if self.start_date > self.end_date:
            self.start_date  = self.end_date
    
    def get_date_value(self, p_start_date, p_end_date):
        """ 获取日期值 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        if p_start_date:
            start_date  = p_start_date
        else:
            start_date  = self.yesterday
        
        if p_end_date:
            if p_end_date > today:
                end_date= today
            else:
                end_date= p_end_date
        else:
            end_date    = self.yesterday
        
        #ss_date = SERVER_START_DATE[self.sid]
        if start_date < self.ss_date:
            start_date  = self.ss_date
        if end_date < self.ss_date:
            end_date    = self.ss_date
        
        if start_date > end_date:
            start_date  = end_date
        
        return start_date, end_date
    
    def get_data_table_info(self,condition,fields=None,table=None):
        """ 获取data数据库中table的详细信息 """
        if public.objIsEmpty(condition):
            return
        if self.data_sql is None:
            self.data_sql   = SqlLite(self.server_info['kashen_data'])
            self.data_sql.conn= self.data_sql.force_conn()
            if self.data_sql.conn is None:
                print 'connect db fail.'
                return
        #condition= {'id':captainsn}
        #如果找到则返回一个字典，否则None
        data= self.data_sql.find_one(table, fields=fields, kwargs=condition)
        #self.data_sql.disconnect()
        return data
    
    def get_pay_recordI(self, ps_date=None, pe_date=None):
        """ 获取付费玩家记录 """
        #SEA_BASE    = ROUTER_SEABASE[0][0]
        kashen_account, kashen_role, kashen_base = public.get_dbpath(self.sid)
        sql         = SqlLite(kashen_base)
        sql.conn    = sql.force_conn()
        if  sql.conn is None:
            print 'connect db fail.'
            return
        
        if ps_date is None:
            #查找所有记录
            condition   = None
        elif pe_date is None:
            #查找ps_date当天的记录
            condition   = "create_time >= '%s 00:00:00' and create_time <= '%s 23:59:59'"%(ps_date, ps_date)
        else:
            #查找ps_date到pe_date期间的记录
            condition   = "create_time >= '%s 00:00:00' and create_time <= '%s 23:59:59'"%(ps_date, pe_date)
        #付费表中字段[role_id][aid][username][tongbao][tid][time][create_time]
        payments    = sql.find('role_payment', condition, DEFAULT_PAY_FIELDSS)
        sql.disconnect()
        return payments
    
    def read_payment(self, ps_date, pe_date, roleids=None):
        """ 读取充值记录 """
        start_date  = ps_date
        end_date    = pe_date
        today   = datetime.today().strftime('%Y-%m-%d')
        datas   = []
        tids= []
        while True:
            if start_date > end_date:
                break
            log_strs= []
            if today == start_date:
                #获取玩家充值记录
                self.url= 'http://%(domain)s/index.php?controller=online_data&action=get_role_pay&roleids=%(roleids)s&fields=%(fields)s&day=%(day)s'% \
                            {'domain': self.server_info['domain'], 'roleids': urllib.quote(json.dumps(roleids)), 
                             'fields': urllib.quote(json.dumps(DEFAULT_PAY_FIELDSS)), 'day': start_date}
                pay_data= public.get_data_from_url(self.url,is_compress=True)
                if pay_data is None:
                    print 'get [%s] payment record from online server error.'%start_date
                else:
                    for d in pay_data:
                        tid = d.get('tid')
                        if tid in tids:
                            continue
                        else:
                            tids.append(tid)
                        d['cmd']= 'top_up'
                        datas.append(d)
            else:
                path    = self.server_info['kashen_pay']+'/pay_'+start_date+'.log'
                print 'path: ',path
                if os.path.exists(path):
                    log_strs= public.read_file_list(path)                    
                for log_str in log_strs:
                    if len(log_str) < 4:
                        print log_str
                        continue
                    if bool(roleids) and log_str[1] not in roleids:
                        continue
                    param   = json.loads(log_str[3])
                    tid = param.get('tid')
                    if tid in tids:
                        continue
                    else:
                        tids.append(tid)
                    param['create_time']= log_str[0]
                    param['roleid'] = log_str[1]
                    if public.objIsEmpty(log_str[2]):
                        param['cmd']= 'top_up'
                    else:
                        param['cmd']= log_str[2]
                    datas.append(param)
            start_date = public.getNextDay(start_date)
        return datas
    
    def get_pay_record(self, ps_date=None, pe_date=None, roleids=None):
        """ 获取付费玩家记录 """
#        if self.sid in ['1']:
#            return self.get_pay_recordI(ps_date, pe_date)
#        else:
        if ps_date is None:
            #查找所有记录
            start_date  = self.ss_date
            end_date    = self.yesterday
        elif pe_date is None:
            #查找ps_date当天的记录
            start_date  = ps_date
            end_date    = ps_date
        else:
            #查找ps_date到pe_date期间的记录
            start_date  = ps_date
            end_date    = pe_date
        #付费表中字段[role_id][aid][username][tongbao][tid][time][create_time]
        print 'start_date, end_date',start_date, end_date
        payments= self.read_payment(start_date, end_date, roleids=None)            
        return payments
    
    def do_pay_record(self, ps_date=None, pe_date=None):
        """ 对充值数据按照{year:{month:{day:[record...]}}}的结构进行处理 """
        pay_records = self.get_pay_record(ps_date=ps_date, pe_date=pe_date)
        records     = {'error': []}
        for record in pay_records:
            create_time = record.get('create_time', None)
            if create_time is None:
                print 'pay_record ', record,' has error'
                records['error'].append(record)
            else:
                time_obj= public.converStrToTime(create_time)
                if time_obj is None:
                    print 'pay_record ', record,'has error'
                    records['error'].append(record)
                    continue
                year    = time_obj.strftime('%Y')
                month   = time_obj.strftime('%m')
                day     = time_obj.strftime('%d')
                #time.struct_time(tm_year=2012, tm_mon=7, tm_mday=3, tm_hour=16, tm_min=17, tm_sec=1, tm_wday=1, tm_yday=185, tm_isdst=-1)
                if records.has_key(year):
                    if records[year].has_key(month):
                        if records[year][month].has_key(day):
                            records[year][month][day].append(record)
                        else:
                            records[year][month][day]   = [record]
                    else:
                        records[year][month]    = { day: [record]}
                else:
                    records[year]   = {month:{ day: [record]}}
        return records
    
    def get_payers(self, payments):
        """ 获取payments中的roleid """
        payers  = []
        if not payments:
            return payers
        for i_dict in payments:
            if i_dict.has_key('roleid'):
                roleid  = i_dict['roleid']
            elif i_dict.has_key('role_id'):
                roleid  = i_dict['role_id']
            else:
                roleid  = None
            if roleid not in payers:
                payers.append(roleid)
        return payers

    def get_player_info(self,tag='name',pstr=None,fields=None):
        """ 获取玩家信息,tag表示通过玩家的用户名、角色ID还是角色名进行查找 """
        url = 'http://%(domain)s/index.php?controller=online_data&action=%(func)s'% \
               {'domain': self.server_info['domain'],'func':'get_role_info',}
        param= {'tag': tag,'pstr': urllib.quote(json.dumps(pstr)),}
        if tag=='uid':
            param.update({'read_other': True,'other_k':'roleid','other_path':'role','other_fields': urllib.quote(json.dumps(fields))})
        elif tag=='id':
            param.update({'read_other': False,'fields': urllib.quote(json.dumps(fields))})
        elif tag=='name':
            param.update({'read_other': True,'other_k':'roleid','other_path':'role','other_fields': urllib.quote(json.dumps(fields))})
        else:
            print 'tag [%s] is unknown'%tag
            return
        return public.get_data_from_url(url, ret_field='data', is_compress=True, method='POST',values=param)
        
    def get_player_infoI(self,tag='name',pstr=None,fields=None,read_other=True,other_k='roleid',other_fields=None):
        """ 获取玩家信息,tag表示通过玩家的用户名、角色ID还是角色名进行查找 """
        url = 'http://%(domain)s/index.php?controller=online_data&action=%(func)s'% \
               {'domain': self.server_info['domain'],'func':'get_role_info',}
        param= {'tag': tag,'pstr': urllib.quote(json.dumps(pstr)),}
        if tag=='uid':
            param.update({'read_other': read_other,'fields': urllib.quote(json.dumps(fields)),'other_k':'roleid','other_path':'role','other_fields': urllib.quote(json.dumps(other_fields))})
        elif tag=='id':
            param.update({'read_other': read_other,'fields': urllib.quote(json.dumps(fields)),'other_k':'username','other_path':'account','other_fields': urllib.quote(json.dumps(other_fields))})
        elif tag=='name':
            if other_k == 'roleid':
                other_path  = 'role'
            elif other_k == 'username':
                other_path  = 'account'
            else:
                print 'other_k [%s] is unkonwn'%other_k
                return
            param.update({'read_other': read_other,'fields': urllib.quote(json.dumps(fields)),'other_k':other_k,'other_path':other_path,'other_fields': urllib.quote(json.dumps(other_fields))})
        else:
            print 'tag [%s] is unknown'%tag
            return
        return public.get_data_from_url(url, ret_field='data', is_compress=True, method='POST',values=param)
        
    #===========================================================================
    # 一    运营数据
    # 1.横向分析统计
    # 2.角色流失率统计
    # 3.等级流失率
    # 4.创建登录统计
    # 5.玩家渠道统计
    # 6.时间段流失率
    # 7.查看在线角色
    #===========================================================================
    
    def get_online_count(self,p_date):
        """读取日志server_tar_date.log文件，返回在线人数列表"""
        player_counts   = []
        fname = '%s/%s/%s%s_%s.txt'%(ONLINE_PATH, p_date, GNAME, self.sid, p_date)
        if os.path.exists(fname):
            fr = file(fname, 'r')
            while True:
                line = fr.readline()
                if len(line) == 0:
                    break            
                #将字符串中的在线人数字典分解出来
                tmp_strs = line.split('\t')
                #将字典字符串转换成字典
                if '\n' in tmp_strs[-1]:
                    tmp_strs[-1] = tmp_strs[-1][:-1]
                #print tmp_strs
                dict_str = tmp_strs[1]
                tmp_dict = json.loads(dict_str)
                
                #将在线人数添加到在线人数列表中
                if self.server_info['plat_name'] in ['hybrid']:
                    player_count = 0
                    for count in tmp_dict.values():
                        if count == -1:
                            continue
                        player_count += int(count)
                    player_counts.append(player_count)
                elif tmp_dict.has_key(self.server_info['plat_name']):
                    count   = tmp_dict.get(self.server_info['plat_name'], -1)
                    if count == -1:
                        continue
                    player_count = int(count)
                    player_counts.append(player_count)
            fr.close()
        return player_counts

    def online_top_ave(self, p_date):
        """获取到p_date这天的最高在线人数和平均在线人数"""
#        now     = datetime.now()
#        today   = now.strftime('%Y-%m-%d')
#        hour    = now.strftime('%H')
#        if today == p_date:
#            achieve     = Achieve(self.sid)
#            achieve.day = today
#            if not achieve.get_log(hour):
#                print 'can not get log [%s_%s.log]'%(p_date,hour)
        player_counts = self.get_online_count(p_date)
        sum_player  = 0
        top_player  = 0
        ave_player  = 0
        online_player   = 0
        for player_count in player_counts:
            if player_count > top_player:
                top_player = player_count
            sum_player += player_count
            online_player   = player_count
        
        if not public.objIsEmpty(player_counts):
            ave_player = sum_player/len(player_counts)
        
        return {'top_player': top_player, 'ave_player': ave_player, 'online_player': online_player}
    
    def regist_count(self, p_date):
        """ 注册数 """
        datas   = {'reg': 0, 'sum': 0}
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        #p_date当日注册人数
        acc_path    = self.server_info['kashen_account']+'/'+p_date
        if today == p_date:
            achieve     = Achieve(self.sid)
            achieve.day = today
            if not achieve.get_db('account', is_db=False):
                print 'can not get regist file [%s]'%acc_path
            else:
                datas['reg']    = len(file(acc_path, 'r').readlines())
        elif os.path.exists(acc_path):
            datas['reg']    = len(file(acc_path, 'r').readlines())
        #从开服截止p_date总的注册人数
        start_date  = self.ss_date
        while True:
            if start_date > p_date:
                break
            acc_log_path    = self.server_info['kashen_account'] + '/' + start_date
            if os.path.exists(acc_log_path):
                datas['sum']    += len(file(acc_log_path, 'r').readlines())               
            start_date = public.getNextDay(start_date)
        return datas
    
    def account_role_count(self, p_date):
        """ 玩家注册、创建角色数 """
        datas   = {'account': {'reg': 0, 'sum': 0},'role': {'cre': 0, 'sum': 0}}
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        #p_date当日注册人数
        acc_path    = self.server_info['kashen_account']+'/'+p_date
        role_path   = self.server_info['kashen_role']+'/'+p_date
        if today == p_date:
            achieve     = Achieve(self.sid)
            achieve.day = today
            if not achieve.get_db('account', is_db=False):
                print 'can not get regist file [%s]'%acc_path
            else:
                datas['account']['reg'] = len(file(acc_path, 'r').readlines())
            if not achieve.get_db('role', is_db=False):
                print 'can not get role file [%s]'%role_path
            else:
                datas['role']['cre']    = len(file(role_path, 'r').readlines())
        else:
            if os.path.exists(acc_path):
                datas['account']['reg'] = len(file(acc_path, 'r').readlines())
            if os.path.exists(role_path):
                datas['role']['cre']    = len(file(role_path, 'r').readlines())
        #从开服截止p_date总的注册人数
        start_date  = self.ss_date
        while True:
            if start_date > p_date:
                break
            acc_log_path    = self.server_info['kashen_account'] + '/' + start_date
            if os.path.exists(acc_log_path):
                datas['account']['sum'] += len(file(acc_log_path, 'r').readlines())
            role_log_path    = self.server_info['kashen_role'] + '/' + start_date
            if os.path.exists(role_log_path):
                datas['role']['sum']    += len(file(role_log_path, 'r').readlines())               
            start_date = public.getNextDay(start_date)
        return datas
    
    def get_payer_count_bak(self,pay_records,pc_date=None,pe_date=None):
        """ pay_records中的人数和金额 """
        payers  = []
        count   = 0
        low_time= '%s 00:00:00'%pc_date
        up_time = '%s 24:00:00'%pc_date
        for record in pay_records:
            create_time = record.get('create_time',None)
            tongbao = record.get('tongbao',0)
            if tongbao <= 0:
                continue
            if create_time is None:
                print 'payment record ', record,' has error'
                continue
            if pc_date:
                #当日充值                
                if create_time < low_time or create_time > up_time:
                    continue
            elif pe_date:
                #截止某天总充值 
                create_date = create_time.split(' ')[0]
                if create_date > pe_date:
                    continue
            #print record
            roleid  = record.get('roleid', None)
            count   += public.tb2rmb(tongbao,pay_time=create_time)
            if roleid not in payers:
                payers.append(roleid)
        return payers,count
        
    def pay_count_bak(self, pay_records, p_date=None, roleids=[]):
        """ 玩家从开服至今 充值 付费人数    付费金额    总付费用户数    总收入 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        start_date  = self.server_info['start_date']
        end_date    = today
        sum_pd      = 0
        days        = 0
        sum_day_arpu= 0
        datas       = {}
        while True:
            if start_date > end_date:
                break
            data    = {'payers': 0, 'pay_count': 0, 'sum_payers': 0 , 'sum_pay_count': 0}        
            if today == start_date:
                #获取玩家充值记录
                self.url= 'http://%(domain)s/index.php?controller=online_data&action=get_role_pay&roleids=%(roleids)s&fields=%(fields)s&day=%(day)s'% \
                            {'domain': self.server_info['domain'], 'roleids': urllib.quote(json.dumps(roleids)), 
                             'fields': urllib.quote(json.dumps(DEFAULT_PAY_FIELDSS)), 'day': start_date}
                pay_data= public.get_data_from_url(self.url,is_compress=True)
                if pay_data is None:
                    print 'get payment record from online server error.'
                    return data
                if pay_records is None:
                    pay_records = pay_data
                    print 'pay_data: ',pay_records
                else:
                    pay_records.extend(pay_data)
            data['payers'],data['pay_count']  = self.get_payer_count(pay_records,pc_date=start_date)
            sum_payers,data['sum_pay_count']  = self.get_payer_count(pay_records,pe_date=start_date)
            data['sum_payers']  = len(sum_payers)
            #获取当天登录角色数
            log_path= self.server_info['ul_path']+'/'+start_date+'/roleid_'+start_date+'.txt'
            if os.path.exists(log_path):
                roles   = file(log_path,'r').readlines()#len()
            else:
                print 'log file [%s] is not exist'%log_path
                roles   = []
            data['roles']   = roles
            #当日ARPU值
            day_payers  = len(data['payers'])
            day_pay_count= data['pay_count']
            if day_payers > 0:
                day_arpu= day_pay_count/day_payers
            else:
                day_arpu= 0
            data['day_arpu']= day_arpu
            #P/D:当日充值金额/当日不重复登录角色数
            if roles > 0:
                p_d = day_pay_count/roles
            else:
                p_d = 0
            data['p_d'] = p_d
            #if start_date != today:
            sum_day_arpu+= day_arpu
            sum_pd  += p_d                
            days    += 1
            datas[start_date]   = data            
            start_date = public.getNextDay(start_date)
        
        #P/D平均值,月ARPU值
        if days > 0:
            ave_pd  = '%.2f'%(sum_pd/days)
            month_arpu  = '%.2f'%(sum_day_arpu/days*30)
        else:
            ave_pd  = ''
            month_arpu  = ''
        return datas,ave_pd,month_arpu
    
    def get_payer_count(self,pay_records,data,day_roleids):
        """ pay_records中的人数和金额 """
        for roleid,record in pay_records.items():
            pay_info= record.get('top_up')
            if public.objIsEmpty(pay_info):
                continue
            day_tb  = public.tb2rmb(pay_info.get('day',0))
            pre_sum = public.tb2rmb(pay_info.get('pre_sum',0))
            if day_tb >= 0.001:
                data['payers']  += 1
                data['pay_count']   += day_tb
            data['sum_pay_count']   += day_tb + pre_sum
            data['sum_payers']  += 1
            if pre_sum == 0:
                data['new_payers']  += 1
                #print record,data['new_payers']
            elif roleid in day_roleids:
                data['podau']+= 1
        
    def pay_count(self, p_date=None, roleids=[]):
        """ 玩家从开服至今 充值 付费人数    付费金额    总付费用户数    总收入 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        start_date  = self.server_info['start_date']
        end_date    = today
        sum_pd      = 0
        days        = 0
        sum_day_arpu= 0
        datas       = {}
        while True:
            if start_date > end_date:
                break
            data    = {'payers': 0, 'pay_count': 0, 'sum_payers': 0 , 'sum_pay_count': 0,
                       'new_payers': 0, 'podau': 0}
            pay_records = {}
            if today == start_date:
                #获取玩家充值记录
                self.create_payer_count(start_date)
                pay_records = self.pay_counts
            else:
                path= '%s/payer_count_%s'%(self.server_info['payer_count'], start_date)
                if not os.path.exists(path):
                    public.print_str('path [%s] is not exist'%path)
                infos   = public.read_json_file(path)
                if public.objIsEmpty(infos):
                    public.print_str('path [%s] info is None'%path)
                else:
                    pay_records = infos[0]
            #获取当天登录角色数
            log_path= self.server_info['ul_path']+'/'+start_date+'/roleid_'+start_date+'.txt'
            day_roles   = public.getSpecialModeFieldDict(log_path, '2', 2, 1, 1).keys()
            roles   = len(day_roles)
            data['roles']   = roles
            self.get_payer_count(pay_records,data,day_roles)
            #当日ARPU值
            day_payers  = data['payers']
            day_pay_count= data['pay_count']
            if day_payers > 0:
                day_arpu= day_pay_count/day_payers
            else:
                day_arpu= 0
            data['day_arpu']= day_arpu
            #P/D:当日充值金额/当日不重复登录角色数
            if roles > 0:
                p_d = day_pay_count/roles
            else:
                p_d = 0
            data['p_d'] = p_d
            #if start_date != today:
            sum_day_arpu+= day_arpu
            sum_pd  += p_d                
            days    += 1
            datas[start_date]   = data            
            start_date = public.getNextDay(start_date)
        
        #P/D平均值,月ARPU值
        if days > 0:
            ave_pd  = '%.2f'%(sum_pd/days)
            month_arpu  = '%.2f'%(sum_day_arpu/days*30)
        else:
            ave_pd  = ''
            month_arpu  = ''
        return datas,ave_pd,month_arpu
    
    def online_pay(self):
        """ 横向分析统计 """
        #日期    注册人数    最高在线    平均在线    付费人数    付费金额    日ARPU值    总注册人数    总付费用户数    总收入    注册付费比    arpu值
        datas   = []
        start_date  = self.start_date  
        end_date    = self.end_date
        #pay_records = self.get_pay_record()
        pay_data,ave_pd,month_arpu  = self.pay_count()
        while True:
            if start_date > end_date:
                break
            #玩家注册、创建角色数
            acc_roles   = self.account_role_count(start_date)
            #datas   = {'account': {'reg': 0, 'sum': 0},'role': {'role': 0, 'sum': 0}}
            #注册数据
            reg_data    = acc_roles.get('account',{})
            #reg_data    = self.regist_count(start_date)
            #当日注册人数
            reg_roles   = reg_data.get('reg',0)
            #总注册人数
            sum_reg     = reg_data.get('sum',0)
            #建角色数据
            role_data   = acc_roles.get('role',{})
            #当日新建角色数
            new_roles   = role_data.get('cre',0)
            #在线数据
            online_data = self.online_top_ave(start_date)
            #最高在线人数
            top_player  = online_data.get('top_player',0)
            #平均在线人数
            ave_player  = online_data.get('ave_player',0)
            #在线人数
            online_player   = online_data.get('online_player',0)
            #当日付费数据
            day_pay_info= pay_data.get(start_date,{})
            #当日新登录角色数
            org_file    = '%s/%s/roleid_%s.txt'%(self.server_info['ul_path'], start_date, start_date)
            day_new_roles= public.getSpecialModeFieldDict(org_file, '0', 2, 1, 1).keys()
            day_new_roles_count = len(day_new_roles)
            #当日登陆人数
            day_roles   = day_pay_info.get('roles',0)
            #当日付费人数
            day_payers_count= day_pay_info.get('payers',0)
            #当日首充玩家和老付费登陆玩家
            pndau   = day_pay_info.get('new_payers',0)
            podau   = day_pay_info.get('podau',0)
            #当日付费金额
            day_pay_count= day_pay_info.get('pay_count',0)
            #当日ARPU值
            day_arpu    = day_pay_info.get('day_arpu',0)
            #P/D:当日充值金额/当日不重复登录角色数
            p_d         = day_pay_info.get('p_d',0)
            #总付费人数
            sum_payers  = day_pay_info.get('sum_payers',0)
            #总付费数
            sum_pay_count= day_pay_info.get('sum_pay_count',0)
            #人均ARPU值
            if sum_payers > 0:
                role_ave_arpu   = sum_pay_count/sum_payers
            else:
                role_ave_arpu   = 0
            #注册付费比
            if sum_reg > 0:
                pay_reg = sum_payers*1.0/sum_reg
            else:
                pay_reg = 0
            #登陆付费比
            if day_roles > 0:
                pay_login   = day_payers_count*1.0/day_roles
            else:
                pay_login   = 0
            tmp_list    = [start_date,reg_roles,online_player,top_player,ave_player,day_roles,day_new_roles_count,pndau,
                           day_roles-day_new_roles_count,podau,day_payers_count,'%.2f'%pay_login,'%.2f'%day_pay_count,
                           '%.2f'%day_arpu,'%.2f'%p_d,sum_reg,sum_payers,'%.2f'%sum_pay_count,'%.3f'%pay_reg,
                           '%.2f'%role_ave_arpu]
            datas.append(tmp_list)
            start_date = public.getNextDay(start_date)
        return datas,ave_pd,month_arpu
    
    def get_task_info(self,fnames,taskids=[1],hour_role=None):
        """ 获取任务接受、完成信息 """
        data    = {'accept': {}, 'complete': {}}
        for fname in fnames:
            print fname
            f = file(fname,'r')
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                if line=='\n':
                    continue
                #将读出来的字符串分解
                log_str = line.split('\t')
                #去除最后一个字段中的\n
                if '\n' in log_str[-1]:
                    log_str[-1] = log_str[-1][0:-1]
                if len(log_str) < 4:
                    print log_str
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2]
                if cmd not in MAIN_TASK_CMDS:
                    continue
                param   = json.loads(log_str[3])
                id      = param.get('id', 0)
                #不是要查找的任务
                if id not in taskids:
                    continue
                status  = param.get('status', 0)
                if status is 0:
                    print log_str, 'has error.'
                    continue
                for hour,roleids in hour_role.items():
                    if roleid in roleids:
                        key = 'accept'
                        if status > 1:
                            key = 'complete'
                        if data[key].has_key(hour):
                            if roleid not in data[key][hour]:
                                data[key][hour].append(roleid)
                        else:
                            data[key][hour] = [roleid]
                        break
            f.close()
        return data
    
    def get_task_info_bak(self,fnames,taskids=[1],hour_role=None):
        """ 获取任务接受、完成信息 """
        data    = {'accept': {}, 'complete': {}}  
        for fname in fnames:
            print fname
            log_strs    = public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    print log_str
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2]
                if cmd not in MAIN_TASK_CMDS:
                    continue
                param   = json.loads(log_str[3])
                id      = param.get('id', 0)
                #不是要查找的任务
                if id not in taskids:
                    continue
                status  = param.get('status', 0)
                if status is 0:
                    print log_str, 'has error.'
                    continue
                for hour,roleids in hour_role.items():
                    if roleid in roleids:
                        key = 'accept'
                        if status > 1:
                            key = 'complete'
                        if data[key].has_key(hour):
                            if roleid not in data[key][hour]:
                                data[key][hour].append(roleid)
                        else:
                            data[key][hour] = [roleid]
                        break
        return data
    
    def do_db_tb(self,path=None,exist_data={}):
        """ 将数据库表整理成{hour:info}格式 """
        datas   = {}
        table_datas = public.read_json_file(path)
        for data in table_datas:
            create_time = data.get('create_time', None)
            roleid      = data.get('roleid',None)
            if create_time is None:
                hour    = '24'
            else:
                hour = create_time[11:13]
            roleids = exist_data.get(hour)
            if bool(roleids) and roleid not in roleids:
                continue
            if datas.has_key(hour):
                if roleid not in datas[hour]:
                    datas[hour].append(roleid)
            else:
                datas[hour] = [roleid]
        return datas

    def role_lose_per(self, p_date):
        """ 角色流失率统计 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        tb_data = {'kashen_account':{},'kashen_role':{}}
        for table in ['account','role']:
            #如果查询日期是今天则请求在线服务器，获取今天的注册文件
            if today == p_date:
                achieve     = Achieve(self.sid)
                achieve.day = today
                if not achieve.get_db(table, is_db=False):
                    print 'can not get regist file [kashen_%s/%s]'%(table,p_date)
                
            log_path    = self.server_info['kashen_'+table] + '/' + p_date
            if os.path.exists(log_path):
                if table == 'account':
                    tb_data['kashen_'+table]  = self.do_db_tb(log_path)
                elif table == 'role':
                    tb_data['kashen_'+table]  = self.do_db_tb(log_path,tb_data.get('kashen_account',{}))

        fnames  = public.get_log_files(self.gl_path, p_date, hour='', run_hour=False)
        tk_data = self.get_task_info(fnames,taskids=[1],hour_role=tb_data['kashen_role'])
        #游戏中没有平台跳转和登陆游戏人数
        #时段   到达创建页人数    已创建角色人数    创建角色页面流失率    接第一个任务人数    游戏画面流失率    完成第一个任务人数    第一个任务流失率
        #*1.首次加载流失率=（平台跳转人数-到达创建页人数）/平台跳转人数
        #2.创建角色页面流失率=（到达创建角色页的人数-已创建角色数）/到达创建页人数
        #*3.二次加载流失率=（已创建角色数-成功登陆游戏人数）/已创建角色数
        #4.游戏画面流失率=（已创建角色数-接第一个任务人数）/已创建角色数
        #5.第一个任务流失率=（接第一个任务人数-完成第一个任务人数）/接第一个任务数
        #6.总加载流失率=（平台跳转人数-成功登陆游戏人数）/平台跳转人数
        datas   = [[]]
        #当天注册人数
        sum_accounts= 0
        #当天创建角色数
        sum_roles   = 0
        #接受第一个任务角色数
        sum_accept  = 0
        #完成第一个任务角色数
        sum_complete= 0
        for i in range(0, 24):
            if i < 10:
                hour = '0%s'%i
            else:
                hour = '%s'%i
            if not tb_data['kashen_account'].has_key(hour):
                continue
            accounts    = len(tb_data['kashen_account'].get(hour,[]))
            #print 'acccounts: ', tb_data['kashen_account'].get(hour,[])
            roles       = len(tb_data['kashen_role'].get(hour,[]))
            #print 'roles: ', tb_data['kashen_role'].get(hour,[])
            accept      = len(tk_data['accept'].get(hour,[]))
            #print 'accept: ', tk_data['accept'].get(hour,[])
            complete    = len(tk_data['complete'].get(hour,[]))
            #print 'complete: ', tk_data['complete'].get(hour,[])
            sum_accounts+= accounts 
            sum_roles   += roles
            sum_accept  += accept
            sum_complete+= complete
            tmp_list    = ['%s时'%i,accounts,roles,]
            if accounts > 0:
                tmp_list.append('%.2f%%'%((accounts-roles)*100.0/accounts))
            else:
                tmp_list.append('0.00%')
            tmp_list.append(accept)
            if roles > 0:
                tmp_list.append('%.2f%%'%((roles-accept)*100.0/roles))
            else:
                tmp_list.append('0.00%')
            tmp_list.append(complete)
            if accept > 0:
                tmp_list.append('%.2f%%'%((accept-complete)*100.0/accept))
            else:
                tmp_list.append('0.00%')
            datas.append(tmp_list)
            #datas.append([i,accounts,roles,'%.2f%'%((accounts-roles)*1.0/accounts),accept,
            #              '%.2f%'((roles-accept)*1.0/roles),complete,'.2f%'%((accept-complete)/accept)])
        datas[0]    = [u'总计',sum_accounts,sum_roles,]
        if sum_accounts > 0:
            datas[0].append('%.2f%%'%((sum_accounts-sum_roles)*100.0/sum_accounts))
        else:
            datas[0].append('0.00%')
        datas[0].append(sum_accept)
        if sum_roles > 0:
            datas[0].append('%.2f%%'%((sum_roles-sum_accept)*100.0/sum_roles))
        else:
            datas[0].append('0.00%')
        datas[0].append(sum_complete)
        if sum_accept > 0:
            datas[0].append('%.2f%%'%((sum_accept-sum_complete)*100.0/sum_accept))
        else:
            datas[0].append('0.00%')
        return datas
    
    def get_role_camp(self):
        """ 获取某段时间内玩家的角色数和阵营数据 """
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        datas   = {'camps':{}, 'roles':0}   
        start_date  = self.ss_date
        end_date    = today
        while True:
            if start_date > end_date:
                break
            role_path   = self.server_info['kashen_role']+'/'+start_date
            if today == start_date:
        #if today == start_date and not os.path.exists(role_path):
                achieve     = Achieve(self.sid)
                achieve.day = today
                if not achieve.get_db('role', is_db=False):
                    print 'can not get regist file [kashen_role/%s]'%(start_date)
            
            role_data   = public.read_json_file(role_path)
            for data in role_data:
                campid  = data.get('campid',0)
                if datas['camps'].has_key(campid):
                    datas['camps'][campid]   += 1
                else:
                    datas['camps'][campid]   = 1
            datas['roles']  += len(role_data)
            start_date = public.getNextDay(start_date)
        camps   = {}
        for campid,count in datas['camps'].items():
            camps[CAMPS.get(campid,campid)] = count
        datas['camps']  = camps
        return datas
    
    def create_login(self):
        """ 创建登录统计 """
        #日期    登陆人数    账号数    0时...24时
        datas       = []
        now     = datetime.now()
        today   = now.strftime('%Y-%m-%d')
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            tb_path = self.server_info['kashen_account'] + '/' + start_date
            if today == start_date:
            #if today == start_date and not os.path.exists(tb_path):
                achieve     = Achieve(self.sid)
                achieve.day = today
                if not achieve.get_db('account', is_db=False):
                    print 'can not get regist file [kashen_account/%s]'%(start_date)
            
            tb_data = self.do_db_tb(tb_path)
            log_path= self.server_info['ul_path']+'/'+start_date+'/roleid_'+start_date+'.txt'
            if os.path.exists(log_path):
                roles   = len(file(log_path,'r').readlines())
            else:
                print 'log file [%s] is not exist'%log_path
                roles   = 0
            tmp_list    = [start_date,roles,0]
            for i in range(0, 24):
                if i < 10:
                    hour = '0%s'%i
                else:
                    hour = '%s'%i
                count   = len(tb_data.get(hour,[]))
                tmp_list.append(count)
                tmp_list[2] += count
            datas.append(tmp_list)
            start_date = public.getNextDay(start_date)
        return datas
    
    def cmp_file(self, roleids, filename):
        ''' currentfile是要执行的当前文件，secondfile是前面的文件 
        #获取两天的roleid的重合数
        '''
        cmp_roleids = []  
        old_roleids = public.getSpecialModeFieldDict(filename, '1', 2, 1, 1).keys()
        
        for roleid in old_roleids:
            if roleid in roleids:
                cmp_roleids.append(roleid)
        print len(cmp_roleids)
        return cmp_roleids    
    
    def back_role(self, p_start_date, p_end_date):
        """ 在规定日期内返回的 """
        print '-----------------------server_%s start back_role()---------------'%self.sid
        #start_date, end_date    = self.get_date_value(p_start_date, p_end_date)
        start_date  = p_start_date
        end_date    = p_end_date
        #rates       = {}
        if not self.rates.has_key(start_date):
            org_file    = '%s/%s/roleid_%s.txt'%(self.ul_path, start_date, start_date)
            roleids     = public.getSpecialModeFieldDict(org_file, '2', 2, 1, 1).keys()
            #rates[start_date]= roleids
            #self.rates[start_date]  = rates
            self.rates[start_date]  = {start_date: roleids}
        #rates[start_date]   = self.rates[start_date][start_date]
        start_date  = public.getNextDay(start_date)
        while True:
            if start_date > end_date:
                break
            if not self.rates[p_start_date].has_key(start_date):
                last_day= public.getLastDay(start_date)
                roleids = self.rates[p_start_date][last_day]
                if len(roleids):
                    filename= '%s/%s/roleid_%s.txt'%(self.ul_path, start_date, start_date)
                    roleids = self.cmp_file(roleids, filename)
                #rates[start_date] = roleids  
                self.rates[p_start_date][start_date] = roleids                           
            start_date = public.getNextDay(start_date)                
        print '-----------------------server_%s over back_role()---------------'%self.sid
    
    def second_login(self, p_date):
        """ 二登率 """
        print '-----------------------server_%s start second_login()---------------'%self.sid
        start_date  = p_date
        if start_date < self.ss_date:
            start_date   = self.ss_date
        if start_date > self.yesterday:
            return 0.0
        end_date    = public.getNextDay(start_date)
        self.back_role(start_date, end_date)
        #二登率
        if len(self.rates[start_date][start_date]): #and len(self.rates[start_date][end_date])
            sec_login_per   = len(self.rates[start_date][end_date])*100.0/len(self.rates[start_date][start_date])
        else:
            sec_login_per   = 0.0

        print '-----------------------server_%s over second_login()---------------'%self.sid
        return sec_login_per
    
    def new_second_login(self, p_date):
        """ 新角色二登率 """
        print '-----------------------server_%s start new_second_login()---------------'%self.sid
        first_day  = p_date
        if first_day < self.ss_date:
            first_day   = self.ss_date
        if first_day > self.yesterday:
            return 0.0
        second_day  = public.getNextDay(first_day)
        first_file  = '%s/%s/roleid_%s.txt'%(self.ul_path, first_day, first_day)
        new_roleids = public.getSpecialModeFieldDict(first_file, '0', 2, 1, 1).keys()
        if not public.objIsEmpty(new_roleids):
            second_file = '%s/%s/roleid_%s.txt'%(self.ul_path, second_day, second_day)
            back_roleids= self.cmp_file(new_roleids, second_file)
            per = len(back_roleids)*100.0/len(new_roleids)
        else:
            per   = 0.0
        print '-----------------------server_%s over second_login()---------------'%self.sid
        return per
    
    def third_login(self, p_date):
        """ 三登 """
        print '-----------------------server_%s start third_login()---------------'%self.sid
        print 'p_date:', p_date
        start_date  = p_date
        if start_date < self.ss_date:
            start_date   = self.ss_date
        if start_date > self.yesterday:
            return 0.0
        end_date    = public.getNextDay(start_date, 2)
#        if not self.rates.has_key(start_date):
#            self.back_role(start_date, end_date)
        self.back_role(start_date, end_date)
        #三登率
        #third_login_per   = '%.2f%%'%(len(self.rates[start_date][p_date])*100.0/len(self.rates[start_date][start_date]))
        if len(self.rates[start_date][start_date]):
            third_login_per   = len(self.rates[start_date][end_date])*100.0/len(self.rates[start_date][start_date])
        else:
            third_login_per   = 0.0

        print '-----------------------server_%s over third_login()---------------'%self.sid
        return third_login_per
    
    def new_third_login(self, p_date):
        """ 新角色三登率 """
        print '-----------------------server_%s start new_third_login()---------------'%self.sid
        first_day  = p_date
        if first_day < self.ss_date:
            first_day   = self.ss_date
        if first_day >= self.yesterday:
            return 0.0
        second_day  = public.getNextDay(first_day)
        third_day   = public.getNextDay(first_day,2)
        first_file  = '%s/%s/roleid_%s.txt'%(self.ul_path, first_day, first_day)
        new_roleids = public.getSpecialModeFieldDict(first_file, '0', 2, 1, 1).keys()
        if not public.objIsEmpty(new_roleids):
            second_file = '%s/%s/roleid_%s.txt'%(self.ul_path, second_day, second_day)
            second_roleids= self.cmp_file(new_roleids, second_file)
            third_file  = '%s/%s/roleid_%s.txt'%(self.ul_path, third_day, third_day)
            back_roleids= self.cmp_file(second_roleids, third_file)
            per = len(back_roleids)*100.0/len(new_roleids)
        else:
            per   = 0.0
        print '-----------------------server_%s over new_third_login()---------------'%self.sid
        return per
    
    def fourth_login(self, p_date):
        """ 四登 """
        print '-----------------------server_%s start fourth_login()---------------'%self.sid
        print 'p_date:', p_date
        start_date  = p_date
        if start_date < self.ss_date:
            start_date   = self.ss_date
        if start_date > self.yesterday:
            return 0.0
        end_date    = public.getNextDay(start_date, 3)
        self.back_role(start_date, end_date)
        if len(self.rates[start_date][start_date]):
            third_login_per   = len(self.rates[start_date][end_date])*100.0/len(self.rates[start_date][start_date])
        else:
            third_login_per   = 0.0

        print '-----------------------server_%s over fourth_login()---------------'%self.sid
        return third_login_per
    
    def new_fourth_login(self, p_date):
        """ 新角色四登率 """
        print '-----------------------server_%s start new_fourth_login()---------------'%self.sid
        first_day  = p_date
        if first_day < self.ss_date:
            first_day   = self.ss_date
        if first_day >= self.yesterday:
            return 0.0
        second_day  = public.getNextDay(first_day)
        third_day   = public.getNextDay(first_day,2)
        fourth_day  = public.getNextDay(first_day,3)
        first_file  = '%s/%s/roleid_%s.txt'%(self.ul_path, first_day, first_day)
        new_roleids = public.getSpecialModeFieldDict(first_file, '0', 2, 1, 1).keys()
        if not public.objIsEmpty(new_roleids):
            second_file = '%s/%s/roleid_%s.txt'%(self.ul_path, second_day, second_day)
            second_roleids= self.cmp_file(new_roleids, second_file)
            third_file  = '%s/%s/roleid_%s.txt'%(self.ul_path, third_day, third_day)
            third_roleids= self.cmp_file(second_roleids, third_file)
            fourth_file = '%s/%s/roleid_%s.txt'%(self.ul_path, fourth_day, fourth_day)
            back_roleids = self.cmp_file(third_roleids, fourth_file)
            per = len(back_roleids)*100.0/len(new_roleids)
        else:
            per   = 0.0
        print '-----------------------server_%s over new_fourth_login()---------------'%self.sid
        return per
    
    def get_level_role(self, fname, lindex=7):
        """ 获取等级对应的玩家 """
        level_roles = {}
        if os.path.exists(fname):
            fcurrent    = file(fname,'r')        
            while True:
                line = fcurrent.readline()
                if len(line)==0:
                    break
                list_mid = line.split('\t')
                #去除最后一个字段中的\n
                if '\n' in list_mid[-1]:
                    list_mid[-1] = list_mid[-1][0:-1]
                roleid  = list_mid[0]
                level   = int(list_mid[lindex])
                if level_roles.has_key(level):
                    level_roles[level].append(roleid)
                else:
                    level_roles[level]  = [roleid]
                    
            fcurrent.close()
        return level_roles
    
    def get_level_roleI(self, fname, lindex=7, is_new=False):
        """ 获取等级对应的玩家 """
        if is_new and len(self.new_roleids):
            self.new_roleids    = []
        level_roles = {}
        if os.path.exists(fname):
            fcurrent    = file(fname,'r')        
            while True:
                line = fcurrent.readline()
                if len(line)==0:
                    break
                list_mid = line.split('\t')
                #去除最后一个字段中的\n
                if '\n' in list_mid[-1]:
                    list_mid[-1] = list_mid[-1][0:-1]
                roleid  = list_mid[0]
                if is_new:
                    new = list_mid[1]
                    if new not in ['0', '1']:
                        print 'the file[%s] field is_new is wrong.'%fname
                    elif new == '1':
                        continue
                    else:
                        self.new_roleids.append(roleid)
                elif roleid not in self.new_roleids:
                    continue  
                level   = int(list_mid[lindex])
                if level_roles.has_key(level):
                    level_roles[level].append(roleid)
                else:
                    level_roles[level]  = [roleid]
                   
            fcurrent.close()
        return level_roles
    
    def pay_percent(self, p_date):
        """ 付费转化率 """
        fname   = '%s/%s/roleid_%s.txt'%(self.ul_path, p_date, p_date)
        level_role  = self.get_level_role(fname)
        right_roleids   = 0
        for level, roleids in level_role.items():
            #取符合条件的角色作为基数
            if level < LOW_LEVEL:
                continue
            #right_roleids.extends(roleids)
            right_roleids   += len(roleids)
        try:
            payments    = self.get_pay_record(p_date)
        except Exception, e:
            print 'error: ', e
            payments    = []
        payers      = self.get_payers(payments)
        #percent = '%.2f%%'%(len(payers)*100.0/right_roleids)
        if right_roleids:
            percent = len(payers)*100.0/right_roleids
        else:
            percent = 0.0
        
        return percent
    
    def vip_second_login(self, p_date):
        """ 二登率 """
        print '-----------------------server_%s start vip_second_login()---------------'%self.sid
        start_date  = public.getLastDay(p_date)
        if start_date < self.ss_date:
            start_date   = self.ss_date
#        if p_date > self.yesterday:
#            p_date  = self.yesterday
        if not self.rates.has_key(start_date):
            self.back_role(start_date, p_date)
        try:
            payments    = self.get_pay_record(p_date)
        except Exception, e:
            print 'error: ', e
            payments    = []
        payers      = self.get_payers(payments)
        backers = []
        for roleid in payers:
            if roleid in self.rates[start_date][p_date]:
                backers.append(roleid)

        #vip二登率
        #vip_sec_login_per   = '%.2f%%'%(len(backers)*100.0/len(payers))
        if len(payers):
            vip_sec_login_per   = len(backers)*100.0/len(payers)
        else:
            vip_sec_login_per   = 0.0

        print '-----------------------server_%s over vip_second_login()---------------'%self.sid
        return vip_sec_login_per

    def vip_third_login(self, p_date):
        """ 二登率 """
        print '-----------------------server_%s start vip_third_login()---------------'%self.sid
        start_date  = public.getLastDay(p_date, 2)
        if start_date < self.ss_date:
            return 0.0
            start_date   = self.ss_date
#        if p_date > self.yesterday:
#            p_date  = self.yesterday
        if not self.rates.has_key(start_date):
            self.back_role(start_date, p_date)
        elif not self.rates[start_date].has_key(p_date):
            self.back_role(start_date, p_date)
        payments    = self.get_pay_record(start_date)
        payers      = self.get_payers(payments)
        backers = []
        for roleid in payers:
            if roleid in self.rates[start_date][p_date]:
                backers.append(roleid)

        #vip三登率
        #vip_third_login_per   = '%.2f%%'%(len(backers)*100.0/len(payers))
        if len(payers):
            vip_third_login_per   = len(backers)*100.0/len(payers)
        else:
            vip_third_login_per   = 0.0

        print '-----------------------server_%s over vip_third_login()---------------'%self.sid
        return vip_third_login_per
    
    def run_data(self):
        """ 得到登陆数据 """
        rates   = []
        sum_new_sec_per= 0.0
        sum_sce_per    = 0.0
        sum_third_per  = 0.0
        sum_new_third_per  = 0.0
        sum_fourth_per= 0.0
        sum_new_fourth_per= 0.0
        sum_pay_per    = 0.0
        sum_vip_sec_per= 0.0
        sum_vip_third_per=0.0
        days= 0

        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            
            sec_per     = self.second_login(start_date)
            new_sec_per = self.new_second_login(start_date)
            third_per   = self.third_login(start_date)
            new_third_per= self.new_third_login(start_date)
            fourth_per  = self.fourth_login(start_date)
            new_fourth_per= self.new_fourth_login(start_date)
            pay_per     = self.pay_percent(start_date)
            vip_sec_per = self.vip_second_login(start_date)
            vip_third_per= self.vip_third_login(start_date)
            
            #由于现在还没有payment表
#            pay_per     = 0.0
#            vip_sec_per = 0.0
#            vip_thir_per= 0.0
            if (sec_per + third_per + pay_per + vip_sec_per + vip_third_per) > 0.0:
                rates.append((start_date, '%.2f'%new_sec_per, '%.2f'%new_third_per, '%.2f'%new_fourth_per, 
                              '%.2f'%sec_per, '%.2f'%third_per, '%.2f'%fourth_per, 
                              '%.2f'%pay_per, '%.2f'%vip_sec_per, '%.2f'%vip_third_per))
                sum_new_sec_per += new_sec_per           
                sum_sce_per     += sec_per
                sum_third_per   += third_per
                sum_new_third_per+= new_third_per
                sum_fourth_per  += fourth_per
                sum_new_fourth_per+= new_fourth_per
                sum_pay_per     += pay_per
                sum_vip_sec_per += vip_sec_per
                sum_vip_third_per+= vip_third_per
            days    += 1
            start_date = public.getNextDay(start_date)
        
        rates.append(['average', '%.2f'%(sum_new_sec_per/days), '%.2f'%(sum_new_third_per/days), '%.2f'%(sum_new_fourth_per/days),
                      '%.2f'%(sum_sce_per/days), '%.2f'%(sum_third_per/days), '%.2f'%(sum_fourth_per/days),
                      '%.2f'%(sum_pay_per/days), '%.2f'%(sum_vip_sec_per/days), '%.2f'%(sum_vip_third_per/days)])
        return rates
    
    def level_lose(self):
        """ 等级流失 """
        start_date  = self.start_date
        end_date    = self.end_date
        levels  = []
        is_new  = True
        while True:
            if start_date > end_date:
                break
            tmp_dict    = {}
            fname   = '%s/%s/total_roleid_%s.txt'%(self.ul_path, start_date, start_date)
            lindex  = 5
            if is_new:
                fname   = '%s/%s/roleid_%s.txt'%(self.ul_path, start_date, start_date)
                lindex  = 7

            if public.is_path_exist(fname):
                print 'level_lose: ', fname
                level_role  = self.get_level_roleI(fname,lindex=lindex,is_new=is_new)
                right_roleids   = 0
                for level, roleids in level_role.items():
                    #取符合条件的角色作为基数
                    if level < 20:
                        level   = level/10*10
                    if tmp_dict.has_key(level):
                        tmp_dict[level] += len(roleids)
                    else:
                        tmp_dict[level] = len(roleids) 
#                    if level < 1:
#                        for roleid in roleids:
#                            print roleid , '\t' , level
                levels.append([start_date, tmp_dict])
            start_date = public.getNextDay(start_date)
            if is_new:
                is_new  = False
        return levels
    
    def click_cost(self):
        """ 点击数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        kashen_account, kashen_role, kashen_base = public.get_dbpath(self.sid)
        costs  = []
        while True:
            if start_date > end_date:
                break
            
            #由于数据来源未定，暂时用自定义文件格式
            cost_path   = self.gl_path + '/cost_%s.txt'%start_date
            cost_msg    = public.read_json_file(cost_path)
            cost    = {}
            if cost_msg.get('status', 1) == 0:
                cost    = cost_msg.get('data', {})
            #该天成本
            money   = cost.get('money', 0.0)
            #该天点击数        
            clicks  = cost.get('click', 1)
            
            acc_log_path    = kashen_account + '/' + start_date
            if os.path.exists(acc_log_path):
                accounts    = len(file(acc_log_path, 'r').readlines())
            else:
                accounts    = 0
            if accounts == 0:
                acc_cost    = money
            else:
                acc_cost    = money/accounts
            
            role_log_path   = kashen_role + '/' + start_date
            if os.path.exists(role_log_path):
                roles   = len(file(role_log_path, 'r').readlines())
            else:
                roles   = 0
            if roles == 0:
                role_cost   = money
            else:
                role_cost   = money/roles
            
            costs.append((start_date, money/clicks, acc_cost, role_cost))
            start_date = public.getNextDay(start_date)
        return costs
    
    #===========================================================================
    # 二    充值与RMB玩家管理
    # 1.单服充值统计
    # 2.充值日志
    # 3.玩家充值排行
    #===========================================================================
    
    def payment(self,ps_date=None, pe_date=None, p_month=None):
        """ 单服充值统计 """
        datas   = {}
        start_date  = self.start_date
        end_date    = self.end_date
        pay_records = self.get_pay_record()#ps_date=start_date, pe_date=end_date
        datas['total']= {'tongbao': 0, 'times': 0, 'roleids': [],'rmbs':0}
        for record in pay_records:
            #print record
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            tongbao = int(record.get('tongbao',0))
            cre_time= record.get('create_time','')
            rmb     = public.tb2rmb(tongbao,pay_time=cre_time)
            datas['total']['times']     += 1
            datas['total']['tongbao']   += tongbao
            datas['total']['rmbs']      += rmb
            if roleid not in datas['total']['roleids']:
                datas['total']['roleids'].append(roleid)
            day = cre_time.split(' ')[0]
            if day < start_date or day > end_date:
                continue
            if datas.has_key(day):
                datas[day]['times']   += 1
                datas[day]['tongbao'] += tongbao
                datas[day]['rmb']     += rmb
                if roleid not in datas[day]['roleids']:
                    datas[day]['roleids'].append(roleid)
            else:
                datas[day]   = {'times': 1, 'tongbao': tongbao, 'roleids': [roleid], 'rmb':rmb}
        ret_datas   = []
        while True:
            if start_date > end_date:
                break
            if datas.has_key(start_date):
                tmp_list= [start_date]
                data    = datas[start_date]
                rmb     = data.get('rmb',0)
                tmp_list.append('%.2f'%rmb)
                tmp_list.append(int(data.get('tongbao',0)))
                roles   = len(data.get('roleids',[]))
                tmp_list.append(roles)
                times   = data.get('times',0)
                tmp_list.append(times)
                if roles:
                    tmp_list.append(int(rmb/roles))
                else:
                    tmp_list.append(rmb)
                #tmp_list.append(start_date)
                ret_datas.append(tmp_list)
            else:
                ret_datas.append([start_date,'0.00',0,0,0,0])#,start_date
            start_date = public.getNextDay(start_date)
        if datas['total']['times'] > 0:
            totals  = []
            data    = datas['total']
            tongbao = int(data.get('tongbao',0))
            #totals.append('%.2f'%public.tb2rmb(tongbao))
            rmbs    = data.get('rmbs',0)
            totals.append('%.2f'%rmbs)
            totals.append(tongbao)
            roles   = len(data.get('roleids',[]))
            totals.append(roles)
            times   = data.get('times',0)
            totals.append(times)
            if bool(roles):
                totals.append(int(rmbs/roles))
            else:
                totals.append(int(rmbs))
        else:
            totals  = ['0.00',0,0,0,0]
        return totals,ret_datas
    
    def get_pay_role_info(self,records,fields=DEFAULT_ROLE_FIELDS):
        """ 获取充值记录中角色ID对应的角色信息 """
        pay_roleids = []
        for record in records:
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            if roleid is not None:
                pay_roleids.append(roleid)
        return self.get_player_info('id',pay_roleids,fields)
        
    def payment_log(self,ps_date=None,pe_date=None,roles=None,names=None):
        """ 在ps_date到pe_date期间充值日志 """
        #服务器标识    账号名    角色ID    角色名   势力    等级     订单号    金额    金币    订单处理时间
        role_infos  = {}
        if roles:
            roleids = roles
        if public.objIsEmpty(names):
            #不对roleid作限制
            roleids = None
        else:
            role_data   = self.get_player_info('name',names,DEFAULT_ROLE_FIELDS)
            if role_data is None:
                return []
            roleids = []
            for name,data in role_data.items():
                roleids.append(data['roleid'])
                role_infos[data['roleid']]= data
        start_date  = self.start_date
        end_date    = self.end_date
        pay_records = self.get_pay_record(ps_date=start_date, pe_date=end_date,roleids=roleids)
        today   = datetime.today().strftime('%Y-%m-%d')
#        if today == end_date:
#            self.url= 'http://%(domain)s/index.php?controller=online_data&action=get_role_pay&roleids=%(roleids)s&fields=%(fields)s&day=%(day)s'% \
#                        {'domain': self.server_info['domain'], 'roleids': urllib.quote(json.dumps([])), 
#                         'fields': urllib.quote(json.dumps(DEFAULT_PAY_FIELDSS)), 'day': today}
#            today_records= public.get_data_from_url(self.url,is_compress=True)
#            #print 'today_records: ', today_records
#            if today_records is None:
#                print "get current day's payment record from online server error."
#            else:
#                pay_records.extend(today_records)
        datas   = []
        tids= []
        #取出所有的付费角色ID，一次性找出所有角色信息
        if roleids is None:
            role_infos.update(self.get_pay_role_info(pay_records))
        for record in pay_records:
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            if roleids and roleid not in roleids:
                continue
            tongbao = int(record.get('tongbao',0))
            tid = record.get('tid')
            if tid in tids:
                continue
            if tongbao <= 0:
                continue            
            tmp_list= [self.server_info['name'],]
            #获取角色信息
            if not role_infos.has_key(roleid):
                role_msg= None
            else:
                role_msg= role_infos[roleid]
            #服务器标识    账号名    角色ID    角色名   势力    等级
            if role_msg is None:
                tmp_list.extend(['null',roleid,'null','null','null'])
            else:
                tmp_list.extend([role_msg.get('username','null'), roleid, role_msg.get('name','null'),
                                 CAMPS.get(role_msg.get('campid',0),'null'), role_msg.get('role_level','null')])
            #订单号    金额    金币    订单处理时间
            cre_time= record.get('create_time','')
            #print 'tongbao:',tongbao
            tmp_list.extend([record.get('tid','null'),'%.2f'%(public.tb2rmb(tongbao,pay_time=cre_time)),
                             record.get('tongbao',0),record.get('create_time','null')])
            datas.append(tmp_list)
        return datas
    
    def get_role_pay(self,pay_records):
        """ 获取玩家的充值信息 """
        role_pays   = {}
        for record in pay_records:
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            cre_time= record.get('create_time',None)
            username= record.get('username',None)
            tongbao = int(record.get('tongbao',0))
            rmb     = public.tb2rmb(tongbao,pay_time=cre_time)
            if tongbao <= 0:
                continue
            if not roleid or not cre_time or not username:
                print 'pay_record ', record,' has error'
                continue
            if role_pays.has_key(roleid):
                role_pays[roleid]['tongbao']+= tongbao
                role_pays[roleid]['last_time']= cre_time
                role_pays[roleid]['times']  += 1
                role_pays[roleid]['rmb']    += rmb
            else:
                role_pays[roleid]   = {'tongbao': tongbao, 'first_time': cre_time, 'last_time': cre_time, 
                                       'username': username, 'times': 1, 'roleid': roleid, 'rmb': rmb}
        return role_pays
    
    def get_role_payI(self,records,pcmd='top_up'):
        """ 获取玩家的充值信息 """
        datas   = {}
        for roleid,infos in records.items():
            for cmd,info in infos.items():
                if pcmd is not None and pcmd != cmd:
                    continue
                if not datas.has_key(cmd):
                    datas[cmd]  = []
                tongbao = info.get('pre_sum',0)+info.get('day',0)
                rmb = public.tb2rmb(tongbao)
                datas[cmd].append({'tongbao': tongbao, 'first_time': info.get('first_time'), 'last_time': info.get('last_time'), 
                                   'username': info.get('username'), 'times': info.get('times',1), 'roleid': roleid, 'rmb': rmb})         
        return datas
    
    def get_role_payII(self,records,pcmd='top_up',pts=['day']):
        """ 获取玩家的充值信息 """
        datas   = {}
        for roleid,infos in records.items():
            for cmd,info in infos.items():
                if pcmd is not None and pcmd != cmd:
                    continue
                if not datas.has_key(cmd):
                    datas[cmd]  = []
                tongbao = 0
                for pt in pts:
                    tongbao += info.get(pt,0)
                if tongbao < 1:
                    continue
                #tongbao = info.get('pre_sum',0)+info.get('day',0)
                rmb = public.tb2rmb(tongbao)
                datas[cmd].append({'tongbao': tongbao, 'first_time': info.get('first_time'), 'last_time': info.get('last_time'), 
                                   'username': info.get('username'), 'times': info.get('times',1), 'roleid': roleid, 'rmb': rmb})         
        return datas
        
    def pay_sort(self,ps_date=None, pe_date=None):
        """ 玩家充值排行 """
        #服务器标识    账号名    角色ID    角色名   势力    等级     剩余金币    注册时间    公会    充值总额RMB(%)    充值次数    平均充值        停充天数        首充时间    最后登陆时间
        if self.end_date > self.yesterday:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.yesterday)
        else:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.end_date)
        if os.path.exists(path):
            infos   = public.read_json_file(path)
            if not public.objIsEmpty(infos):
                rets= self.get_role_payI(infos[0],pcmd='top_up')
                role_records= rets.get('top_up',[])
            else:
                role_records= []
        else:
            pay_records = self.get_pay_record()
            role_pays   = self.get_role_pay(pay_records)
            role_records= role_pays.values()
        #将返回的字典转换成列表进行排序        
        #tmp_list    = []
        #for roleid,info in role_pays.items():
        #    tmp_list.append(info)
        public.print_str('---------sorted start len:%s'%len(role_records))
        sort_record = sorted(role_records, key=operator.itemgetter('tongbao'), reverse=True)
        public.print_str('---------sorted end')
        datas       = []
        fields  = DEFAULT_ROLE_FIELDS
        fields.extend(['guildname'])
        role_infos  = self.get_pay_role_info(sort_record,fields=fields)
        public.print_str('---------get_pay_role_info end')
        for record in sort_record:
            tmp_list= [self.server_info['name'],]
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            if not role_infos.has_key(roleid):
                #获取玩家信息
                role_msg= None
            else:
                role_msg= role_infos[roleid]            
            #账号名    角色ID    角色名   势力    等级     剩余金币    注册时间
            if role_msg is None:
                tmp_list.extend(['null',roleid,'null','null','null','null','null','null'])
                role_msg= {}
            else:
                tmp_list.extend([role_msg.get('username','null'), roleid, role_msg.get('name','null'),
                                 CAMPS.get(role_msg.get('campid',0),'null'), role_msg.get('role_level','null'),
                                 role_msg.get('tongbao',0), role_msg.get('create_time','null'),
                                 role_msg.get('guildname','null'),])
            #充值总额RMB(%)    充值次数    平均充值        停充天数    首充时间    最后登陆时间
            RMB     = record.get('rmb')
            times   = record.get('times',1)
            cre_date= record.get('last_time',self.ss_date).split(' ')[0]
            tmp_list.extend(['%.2f'%RMB,times,'%.2f'%(RMB/times),public.getDays(cre_date, self.yesterday)+1,
                             record.get('first_time','null'),role_msg.get('logintime','null')])
            datas.append(tmp_list)
        public.print_str('---------pay_sort end')
        return datas
    
    def pay_sortI(self,ps_date=None, pe_date=None):
        """ 玩家充值排行 """
        #服务器标识    账号名    角色ID    角色名   势力    等级     剩余金币    注册时间    充值总额RMB(%)    充值次数    平均充值        停充天数        首充时间    最后登陆时间
        pay_records = self.get_pay_record()
        role_pays   = self.get_role_pay(pay_records)
        #将返回的字典转换成列表进行排序        
        tmp_list    = []
        for roleid,info in role_pays.items():
            tmp_list.append(info)
        sort_record = sorted(tmp_list, key=operator.itemgetter('tongbao'), reverse=True)
        datas       = []
        role_infos  = self.get_pay_role_info(sort_record)
        for record in sort_record:
            tmp_list= [self.server_info['name'],]
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            if not role_infos.has_key(roleid):
                #获取玩家信息
                role_msg= None
            else:
                role_msg= role_infos[roleid]            
            #账号名    角色ID    角色名   势力    等级     剩余金币    注册时间
            if role_msg is None:
                tmp_list.extend(['null',roleid,'null','null','null','null','null',])
                role_msg= {}
            else:
                tmp_list.extend([role_msg.get('username','null'), roleid, role_msg.get('name','null'),
                                 CAMPS.get(role_msg.get('campid',0),'null'), role_msg.get('role_level','null'),
                                 role_msg.get('tongbao',0), role_msg.get('create_time','null')])
            #充值总额RMB(%)    充值次数    平均充值        停充天数    首充时间    最后登陆时间
            RMB     = record.get('rmb')
            times   = record.get('times',1)
            cre_date= record.get('last_time',self.ss_date).split(' ')[0]
            tmp_list.extend(['%.2f'%RMB,times,'%.2f'%(RMB/times),public.getDays(cre_date, self.yesterday)+1,
                             record.get('first_time','null'),role_msg.get('logintime','null')])
            datas.append(tmp_list)
        return datas
    
    #===========================================================================
    # 三    金币与银币管理
    # 1.库存统计
    # 2.金币获得及使用记录
    # 3.银币获得及使用记录
    # 4.玩家剩余记录
    # 5.礼金获得及使用记录
    #===========================================================================
    
    def do_pay(self, fnames):
        """ 处理付费行为 """
        data    = {}
        default = {'count': 0, 'roles': [], 'roles_count': 0}
        #d_sum   = {'feiqian': default, 'money': default, 'tongbao': default}
        d_sum   = {}
        #print 'data: ', data
        for fname in fnames:
            print 'do_pay:',fname
            log_strs    = public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    print log_str
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2]
                if cmd not in COST_CMDS.keys():
                    continue
                param   = json.loads(log_str[3])
                if cmd == 'BuyDirect':
                    if param.has_key('itemlist'):
                        cmd = 'BuyDirect_item'
                    elif param.has_key('shipsn'):
                        cmd = 'BuyDirect_ship'
                feiqian = param.get('cost_feiqian', 0)
                tongbao = param.get('cost_tongbao', 0)
                money   = param.get('cost_money', 0)
                tmp_dict= {'feiqian': feiqian, 'money': money, 'tongbao': tongbao}
                if data.has_key(cmd):
                    for k,v in tmp_dict.items():
                        data[cmd][k]['count']   += v
                        if v > 0 and roleid not in data[cmd][k]['roles']:
                            data[cmd][k]['roles'].append(roleid)
                else:
                    data[cmd]   = {}
                    for k,v in tmp_dict.items():
                        if v > 0:
                            data[cmd][k]    = {'count': v, 'roles': [roleid]}
                        else:
                            data[cmd][k]    = {'count': v, 'roles': []}
                
                for k,v in tmp_dict.items():
                    if d_sum.has_key(k):
                        if v > 0:
                            d_sum[k]['count']   += v
                            if roleid not in d_sum[k]['roles']:
                                d_sum[k]['roles'].append(roleid)
                                d_sum[k]['roles_count'] += 1
                    else:
                        if v > 0:
                            d_sum[k]    = {'count': v, 'roles_count': 1, 'roles': [roleid]}
                        else:
                            d_sum[k]    = {'count': v, 'roles_count': 0, 'roles': []}

        return {'status' : 0, 'data' : data, 'sum': d_sum}
    
    def _do_money_log(self,param,roleid,cmd,data,d_sum,is_cost=True):
        """ 处理与钱相关的记录 """
        if is_cost:
            feiqian = param.get('cost_feiqian', 0)
            tongbao = param.get('cost_tongbao', 0)
            money   = param.get('cost_money', 0)
        else:
            feiqian = param.get('add_feiqian', 0)
            tongbao = param.get('add_tongbao', 0)
            money   = param.get('add_money', 0)
        tmp_dict= {'feiqian': feiqian, 'money': money, 'tongbao': tongbao}
        if data.has_key(cmd):
            for k,v in tmp_dict.items():
                data[cmd][k]['count']   += v
                if v > 0 and roleid not in data[cmd][k]['roles']:
                    data[cmd][k]['roles'].append(roleid)
        else:
            data[cmd]   = {}
            for k,v in tmp_dict.items():
                if v > 0:
                    data[cmd][k]    = {'count': v, 'roles': [roleid]}
                else:
                    data[cmd][k]    = {'count': v, 'roles': []}
        
        for k,v in tmp_dict.items():
            if d_sum.has_key(k):
                if v > 0:
                    d_sum[k]['count']   += v
                    if roleid not in d_sum[k]['roles']:
                        d_sum[k]['roles'].append(roleid)
                        d_sum[k]['roles_count'] += 1
            else:
                if v > 0:
                    d_sum[k]    = {'count': v, 'roles_count': 1, 'roles': [roleid]}
                else:
                    d_sum[k]    = {'count': v, 'roles_count': 0, 'roles': []}
        return data,d_sum
    
    def do_cost_earn(self, fnames, cost=False, earn=False):
        """ 处理付费行为 """
        if not cost and not earn:
            print 'warmming: parameter cost and earn are both False'
            return {'status': 1,'tips': 'warmming: parameter cost and earn are both False'}
        cost_data    = {}
        cost_d_sum   = {}
        earn_data    = {}
        earn_d_sum   = {}
        #print 'data: ', data
        for fname in fnames:
            print 'do_cost_earn do file: ',fname
            log_strs    = public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    print log_str
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2]
                try:
                    param   = json.loads(log_str[3])
                except:
                    public.print_str('error line %s'%log_str)
                    continue
                if cost and cmd in COST_CMDS.keys():
                    if cmd == 'BuyDirect':
                        if param.has_key('itemlist'):
                            cmd = 'BuyDirect_item'
                        elif param.has_key('shipsn'):
                            cmd = 'BuyDirect_ship'
                    self._do_money_log(param,roleid,cmd,cost_data,cost_d_sum,is_cost=True)
                if earn and cmd in EARN_CMDS.keys():
                    self._do_money_log(param,roleid,cmd,earn_data,earn_d_sum,is_cost=False)

        return {'status' : 0, 'cost_data' : cost_data, 'cost_sum': cost_d_sum,
                'earn_data': earn_data, 'earn_sum': earn_d_sum
                }
    
    def write_cost_earn(self,mod='w'):
        """ 写消费与获利数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            fnames  = public.get_log_files(self.gl_path, start_date, '', False)
            msg = self.do_cost_earn(fnames, cost=True, earn=True)
            if msg['status'] == 0:
                path= self.server_info['cost_earn']+'/'+start_date
                public.write_json_file(path, msg)
            else:
                print start_date,' do_cost_earn error'
            start_date = public.getNextDay(start_date)
    
    def read_cost_earn(self):
        """ 读消费与获利数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        datas   = {}
        while True:
            if start_date > end_date:
                break
            path= self.server_info['cost_earn']+'/'+start_date
            if not os.path.exists(path):
                fnames  = public.get_log_files(self.gl_path, start_date, '', False)
                msg = self.do_cost_earn(fnames, cost=True, earn=True)
                if msg['status'] != 0:
                    print start_date,' do_cost_earn error'
            else:
                ds  = public.read_json_file(path)
                if len(ds) <= 0:
                    print start_date,' do_cost_earn error'
                    msg = {}
                else:
                    msg = ds[0]
            public.merge_dict(datas,msg)
            start_date = public.getNextDay(start_date)
        return datas
    
    def cost(self,key=None):
        """ 金币获得及使用记录、银币获得及使用记录、礼金获得及使用记录 """
        if key is None:
            print 'parameter key is None'
            return []
        money_keys  = ['money', 'feiqian', 'tongbao']
        msg     = self.read_cost_earn()
        if msg['status'] == 0:
            cost_data= msg['cost_data']
            cost_sum = msg['cost_sum']
            earn_data= msg['earn_data']
            earn_sum = msg['earn_sum']
            tmp_dict = {} 
            for data_type in ['earn','cost']:
                if data_type == 'earn':
                    ec_data  = self.do_ec_data(key,tmp_dict,data=earn_data,sum=earn_sum,e_or_c='earn')
                elif data_type == 'cost':
                    ec_data  = self.do_ec_data(key,tmp_dict,data=cost_data,sum=cost_sum,e_or_c='cost')
                if ec_data is None:
                    print 'warmming: do_ec_data return value is None'
                else:
                    tmp_dict= ec_data
            #将字典数据格式化成列表
            datas   = []
            for t_name, value in tmp_dict.items():
                datas.extend(value)
            datas.append(['',u'收入总值',earn_sum.get(key,{}).get('count',0), '', len(earn_sum.get(key,{}).get('roles',[])), ''])
            datas.append(['',u'消耗总值',cost_sum.get(key,{}).get('count',0), '', len(cost_sum.get(key,{}).get('roles',[])), ''])
            return datas
        else:
            return []
    
    def do_ec_data(self,key,datas={},data={},sum={},e_or_c='cost'):
        """ data是传入的收入或消耗数据，e_or_c表示传入数据的类型 """
        if e_or_c == 'cost':
            cmd_config  = COST_CMDS 
            sign    = '-'
        elif e_or_c == 'earn':
            cmd_config  = EARN_CMDS
            sign    = '+'
        else:
            print 'parameter e_or_c [%s] error'%e_or_c
            return
        for cmd, value in data.items():
            cmd_info    = cmd_config.get(cmd)
            if cmd_info is None:
                print '[%s] cmd is not in config'%e_or_c
                return
            #如果该命令的使用货币中内中不包含查询的货币则跳过
            if key not in cmd_info['money_type']:
                continue
            t_name  = cmd_info['type_name']
            tmp_list= [t_name,cmd_info['name']]
            k_v     = value[key]
            k_count = k_v['count']
            k_roles = len(k_v['roles'])
            sum_count   = sum.get(key,{}).get('count',0)
            sum_rcount  = len(sum.get(key,{}).get('roles',[1]))
            #sum_rcount  = sum.get(key,{}).get('roles_count',0)
            if (sum_count + sum_rcount) > 0:
                tmp_list.extend(['%s%s'%(sign,k_count), '%.2f%%'%(k_count*100.0/sum_count),
                                  k_roles, '%.2f%%'%(k_roles*100.0/sum_rcount)])
            else:
                tmp_list.extend(['%s%s'%(sign,k_count), '0.00%', k_roles, '0.00%'])
            #该命令所属类型
            if datas.has_key(t_name):
                datas[t_name].append(tmp_list)
            else:
                datas[t_name]   = [tmp_list]
        return datas
    
    def exist_log(self,names):
        """ 玩家剩余记录 """
        #获取玩家信息
        role_data   = self.get_player_info('name',names,DEFAULT_ROLE_FIELDS)
        if role_data is None:
            return None
        else:
            datas   = []
            roleids = []
            for name,info in role_data.items():
                roleids.append(info['roleid'])
            #获取玩家充值记录
            start_date  = self.ss_date
            end_date    = self.yesterday
            pay_records = self.get_pay_record(ps_date=start_date, pe_date=end_date)
            today   = datetime.today().strftime('%Y-%m-%d')
            self.url= 'http://%(domain)s/index.php?controller=online_data&action=get_role_pay&roleids=%(roleids)s&fields=%(fields)s&day=%(day)s'% \
                        {'domain': self.server_info['domain'], 'roleids': urllib.quote(json.dumps(roleids)), 
                         'fields': urllib.quote(json.dumps(DEFAULT_PAY_FIELDSS)), 'day': today}
            today_records= public.get_data_from_url(self.url,is_compress=True)
            print 'today_records: ', today_records
            if today_records is None:
                print "get current day's payment record from online server error."
            else:
                pay_records.extend(today_records)
            datas       = []
            for name,info in role_data.items():
                roleid  = info['roleid']
                #records = pay_data.get(roleid,None)
                tmp_list= [info['name'],info['username'],info['roleid'],CAMPS[info['campid']],SEXS[info['sex']],
                                  info['role_level'],info['tongbao'],info['money'],info['feiqian']]
                #角色ID    账号名    角色名    势力    性别    等级    金币    银币    礼金    消耗金币    充值RMB    最后充值时间    最后充值金额RMB
                #todo:由于消耗必须读取日志文件才能准确的计算得出，而且有可能出现消耗+剩余>充值的情况，所以暂时取消掉
                if not bool(pay_records):
                    tmp_list.extend(['','',''])
                else:
                    rmbs        = 0
                    last_time   = ''
                    last_rmb    = 0
                    for record in pay_records:
                        if record.has_key('roleid'):
                            roleid  = record.get('roleid',None)
                        elif record.has_key('role_id'):
                            roleid  = record.get('role_id',None)
                        else:
                            roleid  = None
                        if roleid is None or roleid not in roleids:
                            continue
                        tongbao = int(record.get('tongbao',0))
                        last_time= record.get('create_time','')
                        last_rmb= public.tb2rmb(tongbao,pay_time=last_time)
                        rmbs    += last_rmb
                    tmp_list.extend(['%.2f'%rmbs,last_time,'%.2f'%last_rmb])
                print 'tmp_list: ',tmp_list
                datas.append(tmp_list)
            return datas
    
    def exist_count(self):
        """ 库存统计 """
        #统计日期    新增礼金    消耗礼金    库存礼金    新增银币    消耗银币    库存银币
        money_keys  = ['money', 'feiqian']
        start_date  = self.start_date
        end_date    = self.end_date
        datas   = []
        while True:
            if start_date > end_date:
                break
            fnames  = public.get_log_files(self.gl_path, start_date, '', False)
            #获取消费和获利的数据
            msg = self.do_cost_earn(fnames, cost=True, earn=True)
            if msg['status'] == 0:
                tmp_list    = [start_date]
                for k in money_keys:
                    cost    = msg['cost_sum'].get(k,{}).get('count',0)
                    earn    = msg['earn_sum'].get(k,{}).get('count',0)
                    exist   = earn-cost
                    tmp_list.extend([earn,cost,exist])
                datas.append(tmp_list)
            start_date = public.getNextDay(start_date)
        return datas
    
    def payer_area(self,min_count=0,max_count=100000000,roleids=None,mod='a'):
        """ 大付费玩家区域分布 """
        if self.end_date > self.yesterday:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.yesterday)
        else:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.end_date)
        if os.path.exists(path):
            infos   = public.read_json_file(path)
            if not public.objIsEmpty(infos):
                rets= public.get_person_countI(infos[0],k='username',pcmd='top_up')
                persons = rets.get('top_up',{})
            else:
                persons = {}
        else:
            records = public.get_pay_record(self.sid,ps_date=self.start_date,pe_date=self.end_date,ppath=self.server_info['kashen_pay'],roleids=roleids)
            print len(records)
            persons = public.get_person_count(records,k='username')
        big_payers  = {}
        for username, rmb in persons.items():
            if rmb < min_count or rmb > max_count:
                continue
            big_payers[username]  = rmb
            #print '%s\t%s'%(username,rmb)
        acc_infos   = self.get_player_infoI(tag='uid',pstr=big_payers.keys(),fields=['ip','roleid'],read_other=False)
        #连接IP区域数据库
        data_sql= SqlLite(IP_AREA_DATA_PATH)
        data_sql.conn   = data_sql.force_conn()
        if data_sql.conn is None:
            print 'connect db fail'
            return
        ret_msg = public.read_json_file(USERNAME_IP_PATH)
        if public.objIsEmpty(ret_msg):
            username_ips= {}
        else:
            username_ips= ret_msg[0]
        #以city_id为键值，大付费玩家区域信息
        datas   = {}
        for username,rmb in big_payers.items():
            acc_info= acc_infos.get(username)
            if public.objIsEmpty(acc_info):
                continue
            if username_ips.has_key(username):
                ip  = username_ips[username]
            else:
                ip  = acc_info.get('ip')
                username_ips[username]  = ip
            roleid  = acc_info.get('roleid',username)
            if public.objIsEmpty(ip):
                print 'cannot get username [',username,"]'s ip info"
                city_id = '-2' 
                info= {'region_id':'-2','region':'未知'}
            else:
                info= public.ip2area(ip,data_sql=data_sql)
                if info is None:
                    region_id= '-2'
                    info= {'region_id':'-2','region':'未知'}
                else:
                    region_id = info['region_id']
                    if region_id == '-1':
                        area_id = info['area_id']
                        if area_id == '-1':
                            region_id = info['country_id']+'-1-1'
                            region    = info['country']
                        else:
                            region_id = info['area_id']+'-1'
                            region    = info['area']
                        info['region_id'] = region_id
                        info['region']    = region
            if datas.has_key(region_id):
                if username not in datas[region_id]['usernames']:
                    datas[region_id]['usernames'].append(username)
                datas[region_id]['roleids'].append(roleid)
                datas[region_id]['rmb']   += rmb
                datas[region_id]['count'] += 1
            else:
                info.update({'usernames':[username],'roleids':[roleid],'rmb':rmb,'sname':self.server_info['name'],
                             'count':1,'sid': self.sid})
                datas[region_id]  = info
        result_path = self.server_info['payer_area']+u'/payer_area_%s_%s.txt'%(min_count,self.end_date)
        public.write_json_file(result_path, datas.values(), mod='a', end='\n')
        print result_path
        #提交数据&关闭数据库连接
        #data_sql.commit('ip_area')
        data_sql.disconnect()
        #写用户名与IP的对照文件
        public.write_json_file(USERNAME_IP_PATH+'.tmp',username_ips)
        os.rename(USERNAME_IP_PATH+'.tmp', USERNAME_IP_PATH)
    
    def get_payer_area_info(self,min_count=0):
        """ 获取大付费玩家分布数据 """
        #money_keys  = ['money', 'feiqian']
        start_date  = self.start_date
        end_date    = self.end_date
        pay_infos   = []
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['payer_area']+u'/payer_area_%s_%s.txt'%(min_count,self.start_date)
            public.print_str('do payer area file: %s'%fname)
            pay_infos.extend(public.read_json_file(fname))
            start_date = public.getNextDay(start_date)
        datas   = {}
        sum_rmb = 0
        sum_count= 0
        print 'len of pay_infos: ',len(pay_infos)
        plats   = {}
        for pay_info in pay_infos:
            region_id = pay_info['region_id']
            #print pay_info['rmb']
            sum_rmb += pay_info['rmb']
            sum_count+= pay_info['count']
            if datas.has_key(region_id):
                public.merge_dict(datas[region_id],pay_info,add_str=False)
            else:
                datas[region_id]  = pay_info
            plat_name   = GS_INFO.get(pay_info['sid'],{}).get('plat_name','unknown')
            if plats.has_key(plat_name):
                plats[plat_name]['rmb'] += pay_info['rmb']
            else:
                plats[plat_name]= {'rmb': pay_info['rmb'], 'name': PLAT_NAMES.get(plat_name,'未知')}
        sort_record = sorted(datas.values(), key=operator.itemgetter('rmb'), reverse=True)
        if sum_rmb == 0:
            sum_rmb = 1
        if sum_count == 0:
            sum_count= 1
        infos   = []
        index   = 1
        for data in sort_record:
            infos.append([index,data.get('country',''),data.get('area',''),data.get('region',''),
                           data['count'],'%.2f%%'%(data['count']*100.0/sum_count),
                           data['rmb'],'%.2f%%'%(data['rmb']*100.0/sum_rmb)])
            index   += 1
        infos.append(['','总和','','',sum_count,'',sum_rmb,''])
        #print 'infos: ',infos
        return infos,plats.values()
    
    def count_DAU(self,day):
        """ 统计当天在线总人数 """
        count   = 0
        for server in SERVERS:
            try:
                sid = server['sid']   
                spname      = '/kashen_%s'%sid
                #日志存放目录        
                log_path    = USERLOG_PATH + spname+'/'+day+'/'+'roleid_'+day+'.txt'
                if os.path.exists(log_path):
                    count   += len(file(log_path).readlines())
                else:
                    print log_path,'\t不存在'
            except:
                print public.get_now2str(),'\t%r'%tb.format_exc()
                count   = -1
                break
        return count
    
    def do_cardbag(self, fnames, cost=False, earn=False):
        """ 处理付费行为 """
        datas   = {}
        for fname in fnames:
            print 'do_cardbag: ',fname
            log_strs= public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2].lower()
                try:
                    param   = json.loads(log_str[3])
                except:
                    public.print_str('error line %s'%log_str)
                    return
                items   = []
                if cmd not in ['opencardbag','shopbuy']:
                    continue
                if not datas.has_key(cmd):
                    if cmd == 'opencardbag':
                        datas[cmd]  = {'cost_feiqian':0,'cost_tongbao':0}
                    else:
                        datas[cmd]  = {}
                cost_feiqian= param.get('cost_feiqian', 0)
                cost_tongbao= param.get('cost_tongbao', 0)
                if (cost_feiqian+cost_tongbao) <= 0:
                    continue
                if cmd == 'opencardbag':
                    itemlist= param.get('itemlist',[])
                    for item in itemlist:
                        itemsn  = item['itemsn']
                        count   = item['count']
                        if datas[cmd].has_key(itemsn):
                            datas[cmd][itemsn]['count'] += count
                        else:
                            datas[cmd][itemsn]  = {'count': count}
                    datas[cmd]['cost_feiqian'] += cost_feiqian
                    datas[cmd]['cost_tongbao'] += cost_tongbao
                else:
                    itemsn  = param.get('id',0)
                    count   = param.get('count',0)
                    if not CARDS.has_key(itemsn):
                        continue
                    if datas[cmd].has_key(itemsn):
                        datas[cmd][itemsn]['count'] += count
                        datas[cmd][itemsn]['cost_feiqian']  += cost_feiqian
                        datas[cmd][itemsn]['cost_tongbao']  += cost_tongbao
                    else:
                        datas[cmd][itemsn]  = {'count': count,'cost_feiqian': cost_feiqian,'cost_tongbao': cost_tongbao}
        return datas
    
    def write_cardbag(self):
        """ 写卡包数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            fnames  = public.get_log_files(self.gl_path, start_date, '', False)
            datas   = self.do_cardbag(fnames, cost=True, earn=True)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            datas['sid']= self.sid
            des_path= self.server_info['cardbag']+'/cardbag_'+start_date
            public.write_json_file(des_path, datas, mod='a', end='\n')
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_cardbag_info(self):
        """ 获取卡包数据 """
        start_date  = self.start_date
        end_date= self.end_date
        datas   = []
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['cardbag']+u'/cardbag_%s'%start_date
            ret_msg = public.read_json_file(fname)
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            tmp = [start_date,0,0,0,0,0,0]
            for d in ret_msg:
                #日期,合成礼金,合成金币,商城礼金,商城金币,礼金总量,金币总量
                for cmd,info in d.items():
                    if cmd not in ['opencardbag','shopbuy']:
                        continue
                    else:
                        if cmd == 'opencardbag':
                            tmp[1]  += info.get('cost_feiqian',0)
                            tmp[2]  += info.get('cost_tongbao',0)
                            tmp[5]  += info.get('cost_feiqian',0)
                            tmp[6]  += info.get('cost_tongbao',0)
                        else:
                            for shopbuyinfo in info.values():
                                tmp[3]  += shopbuyinfo.get('cost_feiqian',0)
                                tmp[4]  += shopbuyinfo.get('cost_tongbao',0)
                                tmp[5]  += shopbuyinfo.get('cost_feiqian',0)
                                tmp[6]  += shopbuyinfo.get('cost_tongbao',0)
            datas.append(tmp)
            start_date = public.getNextDay(start_date)
        return datas
    
    def rewrite_cardbag_info(self):
        """ 整理卡包数据 """
        start_date  = self.start_date
        end_date= self.end_date
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['cardbag']+u'/cardbag_%s'%start_date
            ret_msg = public.read_json_file(fname)
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            datas   = []
            for d in ret_msg:
                #日期,合成礼金,合成金币,商城礼金,商城金币,礼金总量,金币总量
                for cmd,info in d.items():
                    if cmd == 'shopbuy':
                        for itemsn,shopbuyinfo in info.items():
                            if not CARDS.has_key(int(itemsn)):
                                d[cmd].pop(itemsn)
                        if public.objIsEmpty(d[cmd]):
                            d.pop(cmd)
                datas.append(d)
            des_path= self.server_info['cardbag']+'/cardbag_'+start_date
            public.write_json_file(des_path, datas, mod='w', end='\n')
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
        
    def do_payer_info(self, ps_date=None, pe_date=None):
        """ 对充值数据按照{year:{month:{day:[record...]}}}的结构进行处理 """
        datas   = {}
        records = self.get_pay_record(ps_date=ps_date, pe_date=pe_date)
        for record in records:
            if record.has_key('roleid'):
                roleid  = record['roleid']
            elif record.has_key('role_id'):
                roleid  = record['role_id']
            else:
                public.print_str('eroor_record, %s'%record)
                continue
            tongbao = record.get('tongbao')
            create_time = record.get('create_time')
            cmd = record.get('cmd')
            username= record.get('username')
            if tongbao is None or create_time is None or cmd is None:
                public.print_str('eroor_record, %s'%record)
                continue
            elif tongbao <= 0:
                continue
            if not datas.has_key(roleid):
                datas[roleid]   = {}
            if datas[roleid].has_key(cmd):
                datas[roleid][cmd]['tongbao']+= tongbao
                datas[roleid][cmd]['cur_time']= create_time
                datas[roleid][cmd]['times']+= 1
            else:
                datas[roleid][cmd]  = {'tongbao': tongbao, 'cur_time': create_time, 'first_time': create_time,
                                       'username':username, 'times': 1,'first_pay': tongbao}
        return datas
    
    def create_payer_count(self,p_date):
        """ 生成p_date的payer_count数据字典 """
        pre_day = public.getLastDay(p_date)
        #前一天的payer_count文件
        pre_file= '%s/payer_count_%s'%(self.server_info['payer_count'], pre_day)
        if public.objIsEmpty(self.pay_counts):
            #检查前一天的文件是否存在，存在就读取文件
            counts  = public.read_json_file(pre_file)
            if not public.objIsEmpty(counts):
                self.pay_counts = counts[0]
            else:
                self.pay_counts = {}
        for roleid,info in self.pay_counts.items():
            for cmd,cmd_info in info.items():
                self.pay_counts[roleid][cmd]['pre_sum'] += self.pay_counts[roleid][cmd]['day']
                self.pay_counts[roleid][cmd]['day'] = 0
        infos   = self.do_payer_info(p_date, p_date)
        for roleid,info in infos.items():
            if not self.pay_counts.has_key(roleid):
                self.pay_counts[roleid] = {}
            for cmd,cmd_info in info.items():
                if self.pay_counts[roleid].has_key(cmd):
                    #self.pay_counts[roleid][cmd]['pre_sum'] += self.pay_counts[roleid][cmd]['day']
                    self.pay_counts[roleid][cmd]['day'] = cmd_info['tongbao']
                    self.pay_counts[roleid][cmd]['last_time']   = cmd_info['cur_time']
                    self.pay_counts[roleid][cmd]['times']   += cmd_info['times']
                else:
                    self.pay_counts[roleid][cmd]= {'pre_sum': 0, 'day': cmd_info['tongbao'], 'first_time': cmd_info['first_time'],
                                                   'last_time': cmd_info['cur_time'],'username':cmd_info['username'],
                                                   'times': cmd_info['times'], 'first_pay': cmd_info['first_pay']}
    
    def write_payer_info(self):
        """ 写玩家付费信息 """
        start_date  = self.start_date
        end_date= self.end_date
        while True:
            if start_date > end_date:
                break
            self.create_payer_count(start_date)
            des_path= self.server_info['payer_count']+'/payer_count_'+start_date
            if os.path.exists('/root'):
                public.write_json_file(public._2utf8(des_path), self.pay_counts)
            else:
                public.write_json_file(des_path, self.pay_counts)
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
            
    def write_richman_info(self,min_count=0.01,max_count=100000000,roleids=None,mod='a'):
        """ 大付费玩家名单,min_count和max_count是游戏币的数量 """
        if self.end_date > self.yesterday:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.yesterday)
        else:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.end_date)
        if not os.path.exists(path):
            public.print_str('path [%s] is not exist'%path)
            return
        infos   = public.read_json_file(path)
        if public.objIsEmpty(infos):
            public.print_str('path [%s] info is None'%path)
            return
        rets= public.get_person_countII(infos[0],k='roleid',pcmd='top_up',min_count=min_count,max_count=max_count)
        persons = rets.get('top_up',{})
        if public.objIsEmpty(persons):
            public.print_str('server [%s] has no data in range %s-%s'%(self.sid,min_count,max_count))
            return
        datas   = []
        role_infos  = self.get_player_info('id',persons.keys(),DEFAULT_ROLE_FIELDS)
        #role_infos  = {}
        for roleid,info in persons.items():
            tmp_dict= {'sname': self.server_info['name'],'serverid': self.sid}
            #账号名    角色ID    角色名   势力    等级     剩余金币    注册时间
            if not role_infos.has_key(roleid):
                tmp_dict.update({'username': '', 'roleid': roleid, 'rolename': '', 'campid': '', 'role_level': '', 
                                 'tongbao': '', 'create_time': ''})
                logintime   = self.ss_date
                create_time = self.ss_date
            else:
                role_msg= role_infos[roleid]
                if public.objIsEmpty(role_msg):
                    print 'can not get roleid[%s] info'%roleid,info
                    continue
                logintime   = role_msg.get('logintime',self.ss_date)
                create_time = role_msg.get('create_time',self.ss_date)
                tmp_dict.update(role_msg)
            #充值总额RMB(%)    充值次数    平均充值        停充天数    首充时间    最后登陆时间    是否新满足条件    在规定时间内未登录
            is_new  = False
            is_nologin  = False
            pre_sum = info.get('pre_sum',0)
            if pre_sum < min_count:
                is_new  = True
            pre_rmb = public.tb2rmb(info.get('pre_sum',0))
            rmb     = public.tb2rmb(info.get('day',0))
            RMB     = pre_rmb+rmb
            times   = info.get('times',1)
            #最近未登录天数
            last_time   = info.get('last_time',create_time)
            nopay_days  = public.getDays(last_time[:10], self.yesterday)
            nologin_days= public.getDays(logintime[:10], self.yesterday)
            #在规定时间内未登录
            if nologin_days >= 3 and nologin_days <= 10:
                is_nologin  = True
            tmp_dict.update({'sum_rmb': RMB, 'pay_times': times, 'avg_rmb': '%.2f'%(RMB/times), 
                             'nopay_days': nopay_days, 'first_time': info.get('first_time',''), 
                             'logintime': logintime, 'is_new': is_new, 'is_nologin': is_nologin,
                             'last_time': last_time})
            datas.append(tmp_dict)
        result_path = self.server_info['richman']+u'/richman_%s_%s.txt'%(min_count,self.end_date)
        public.write_json_file(result_path, datas, mod='a', end='\n')
        print result_path
    
    def write_richman_info_bak(self,min_count=0.01,max_count=100000000,roleids=None,mod='a'):
        """ 大付费玩家名单,min_count和max_count是游戏币的数量 """
        if self.end_date > self.yesterday:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.yesterday)
        else:
            path= '%s/payer_count_%s'%(self.server_info['payer_count'], self.end_date)
        if not os.path.exists(path):
            public.print_str('path [%s] is not exist'%path)
            return
        infos   = public.read_json_file(path)
        if public.objIsEmpty(infos):
            public.print_str('path [%s] info is None'%path)
            return
        rets= public.get_person_countII(infos[0],k='roleid',pcmd='top_up',min_count=min_count,max_count=max_count)
        persons = rets.get('top_up',{})
        if public.objIsEmpty(persons):
            public.print_str('server [%s] has no data in range %s-%s'%(self.sid,min_count,max_count))
            return
        datas   = []
        role_infos  = self.get_player_info('id',persons.keys(),DEFAULT_ROLE_FIELDS)
        #role_infos  = {}
        for roleid,info in persons.items():
            tmp_list= [self.server_info['name'],]
            #账号名    角色ID    角色名   势力    等级     剩余金币    注册时间
            if not role_infos.has_key(roleid):
                tmp_list.extend(['',roleid,'','','','','',])
                logintime   = self.ss_date
            else:
                role_msg= role_infos[roleid]
                logintime   = role_msg.get('logintime',self.ss_date)
                tmp_list.extend([role_msg.get('username',''), roleid, role_msg.get('name',''),
                                 CAMPS.get(role_msg.get('campid',0),''), role_msg.get('role_level',''),
                                 role_msg.get('tongbao',0), role_msg.get('create_time','')])
            #充值总额RMB(%)    充值次数    平均充值        停充天数    首充时间    最后登陆时间
            is_new  = False
            is_nologin  = False
            pre_sum = info.get('pre_sum',0)
            if pre_sum < min_count:
                is_new  = True
            pre_rmb = public.tb2rmb(info.get('pre_sum',0))
            rmb     = public.tb2rmb(info.get('day',0))
            RMB     = pre_rmb+rmb
            times   = info.get('times',1)
            nopay_days  = public.getDays(info.get('last_time',self.ss_date)[:10], self.yesterday)#+1
            nologin_days= public.getDays(logintime[:10], self.yesterday)#+1
            if nologin_days >= 3 and nologin_days <= 10:
                is_nologin  = True
            tmp_list.extend(['%.2f'%RMB,times,'%.2f'%(RMB/times),nopay_days,info.get('first_time',''),
                             logintime,is_new,is_nologin])
            datas.append(tmp_list)
        result_path = self.server_info['richman']+u'/richman_%s_%s.txt'%(min_count,self.end_date)
        public.write_json_file(result_path, datas, mod='a', end='\n')
        print result_path
    
    def get_richman_info(self,min_count=0,start_date=None, end_date=None):
        """ 获取大付费玩家名单数据 """
        #start_date  = self.start_date
        #end_date    = self.end_date
        infos   = []
        while True:
            if start_date > end_date:
                break
            infos.extend(public.read_json_file(self.server_info['richman']+u'/richman_%s_%s.txt'%(min_count,self.start_date)))
            start_date = public.getNextDay(start_date)
        return infos
    
    def do_fireworks(self,fnames):
        """ 处理付费行为 """
        datas   = {}
        for fname in fnames:
            print 'do_playfireworks: ',fname
            log_strs= public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    continue
                roleid  = log_str[1]
                cmd     = log_str[2].lower()
                if cmd not in ['playfireworks']:
                    continue
                try:
                    param   = json.loads(log_str[3])
                except:
                    public.print_str('error line %s'%log_str)
                    continue
                cost_feiqian= param.get('cost_feiqian', 0)
                cost_tongbao= param.get('cost_tongbao', 0)
                if (cost_feiqian+cost_tongbao) <= 0:
                    continue
                datalist= param.get('datalist',[])
                for data in datalist:
                    fid = data.get('id',0)
                    if datas.has_key(fid):
                        datas[fid]['cost_feiqian']  += cost_feiqian
                        datas[fid]['cost_tongbao']  += cost_tongbao
                        datas[fid]['count'] += 1
                        if roleid not in datas[fid]['roleids']:
                            datas[fid]['roleids'].append(roleid)
                    else:
                        ret_msg = self.get_data_table_info({'id':fid},fields=['name'],table='fireworks')
                        if public.objIsEmpty(ret_msg):
                            fwname  = fid
                        else:
                            fwname  = ret_msg.get('name',fid)                        
                        datas[fid]  = {'cost_tongbao': cost_tongbao, 'cost_feiqian': cost_feiqian, 'count': 1,
                                       'name': fwname, 'id': fid, 'sid': self.sid, 'sname': self.server_info['name'],
                                       'roleids':[roleid]}
        return datas
    
    def write_fireworks(self):
        """ 写烟火数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            fnames  = public.get_log_files(self.gl_path, start_date, '', False)
            datas   = self.do_fireworks(fnames)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            des_path= self.server_info['fireworks']+'/fireworks_'+start_date
            public.write_json_file(des_path, datas.values(), mod='a', end='\n')
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def merge_list(self,l1,l2):
        """ 合并列表 """
        if public.objIsEmpty(l1):
            return l2
        for v in l2:
            if v not in l1:
                l1.append(v)
        return l1
    
    def get_fireworks_info(self):
        """ 获取烟火数据 """
        start_date  = self.start_date
        end_date= self.end_date
        datas   = {}
        sum_count   = 0
        sum_tongbao = 0
        sum_feiqian = 0
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['fireworks']+u'/fireworks_%s'%start_date
            ret_msg = public.read_json_file(fname)
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            for d in ret_msg:
                fid = d.get('id',0)
                cost_feiqian= d.get('cost_feiqian',0)
                cost_tongbao= d.get('cost_tongbao',0)
                count   = d.get('count',0)
                roleids = d.get('roleids',[])
                if datas.has_key(fid):
                    datas[fid]['cost_feiqian']   += cost_feiqian
                    datas[fid]['cost_tongbao']   += cost_tongbao
                    datas[fid]['count']  += count
                    if self.start_date == self.end_date:
                        datas[fid]['roleids'].extend(roleids)
                    else:
                        datas[fid]['roleids']   = self.merge_list(datas[fid]['roleids'],roleids)
                else:
                    datas[fid]  = {'cost_tongbao': cost_tongbao, 'cost_feiqian': cost_feiqian, 'count': count,
                                   'name': d.get('name',fid), 'id': fid, 'roleids': roleids}
                sum_count   += count
                sum_tongbao += cost_tongbao
                sum_feiqian += cost_feiqian
            start_date = public.getNextDay(start_date)
        infos   = []
        for fid,info in datas.items():
            persons = len(info.get('roleids',[]))
            count   = info.get('count',0)            
            if persons < 1 or count < 1:
                buy_per = 0
            else:
                buy_per = count*1.0/persons
            cost_tongbao= info.get('cost_tongbao',0)
            cost_feiqian= info.get('cost_feiqian',0)
            if cost_tongbao < 1 or sum_tongbao < 1:
                tb_per  = 0
            else:
                tb_per  = cost_tongbao*1.0/sum_tongbao
            if cost_feiqian < 1 or sum_feiqian < 1:
                fq_per  = 0
            else:
                fq_per  = cost_feiqian*1.0/sum_feiqian
            infos.append([info['name'],count,persons,'%.2f'%buy_per,cost_tongbao,'%.2f'%tb_per,cost_feiqian,'%.2f'%fq_per])
        infos.append(['总和',sum_count,'','',sum_tongbao,'',sum_feiqian,''])
        return infos
    
    def write_platonline(self):
        """ 平台横向分析统计 """
        #日期    注册人数    最高在线    平均在线    付费人数    付费金额    日ARPU值    总注册人数    总付费用户数    总收入    注册付费比    arpu值
        start_date  = self.start_date  
        end_date    = self.end_date
        pay_data,ave_pd,month_arpu  = self.pay_count()
        while True:
            if start_date > end_date:
                break
            if start_date > self.yesterday:
                start_date = public.getNextDay(start_date)
                continue
            #玩家注册、创建角色数
            acc_roles   = self.account_role_count(start_date)
            #datas   = {'account': {'reg': 0, 'sum': 0},'role': {'role': 0, 'sum': 0}}
            #注册数据
            reg_data    = acc_roles.get('account',{})
            #reg_data    = self.regist_count(start_date)
            #当日注册人数
            reg_roles   = reg_data.get('reg',0)
            #总注册人数
            sum_reg     = reg_data.get('sum',0)
            #建角色数据
            role_data   = acc_roles.get('role',{})
            #当日新建角色数
            new_roles   = role_data.get('cre',0)
            #当日创建角色数
            sum_roles   = role_data.get('sum',0)
            #在线数据
            online_data = self.online_top_ave(start_date)
            #最高在线人数
            top_player  = online_data.get('top_player',0)
            #平均在线人数
            ave_player  = online_data.get('ave_player',0)
            #在线人数
            online_player   = online_data.get('online_player',0)
            #当日付费数据
            day_pay_info= pay_data.get(start_date,{})
            #当日登陆人数
            day_roles   = day_pay_info.get('roles',0)
            #当日新登录角色数
            org_file    = '%s/%s/roleid_%s.txt'%(self.server_info['ul_path'], start_date, start_date)
            day_new_roles= len(public.getSpecialModeFieldDict(org_file, '0', 2, 1, 1).keys())
            #当日付费人数
            day_payers  = day_pay_info.get('payers',0)
            #当日付费数
            day_pay_count= day_pay_info.get('pay_count',0)
            #当日首充玩家和老付费登陆玩家
            pndau   = day_pay_info.get('new_payers',0)
            podau   = day_pay_info.get('podau',0)
            #当日ARPU值
            day_arpu    = day_pay_info.get('day_arpu',0)
            #P/D:当日充值金额/当日不重复登录角色数
            p_d         = day_pay_info.get('p_d',0)
            #总付费人数
            sum_payers  = day_pay_info.get('sum_payers',0)
            #总付费数
            sum_pay_count= day_pay_info.get('sum_pay_count',0)
            #人均ARPU值
            if sum_payers > 0:
                role_ave_arpu   = sum_pay_count/sum_payers
            else:
                role_ave_arpu   = 0
            #注册付费比
            if sum_reg > 0:
                pay_reg = sum_payers*1.0/sum_reg
            else:
                pay_reg = 0
            #登陆付费比
            if day_roles > 0:
                pay_login   = day_payers*1.0/day_roles
            else:
                pay_login   = 0
            data= {'reg_roles':reg_roles,'online_player':online_player, 'top_player':top_player, 'ave_player':ave_player, 'day_roles':day_roles, 
                   'day_new_roles':day_new_roles,'pndau':pndau,'odau':(day_roles-day_new_roles),'podau':podau,'day_payers': day_payers,
                   'pay_login':pay_login,'day_pay_count':day_pay_count, 'day_arpu':day_arpu, 'p_d':p_d,'sum_roles':sum_roles, 'sum_reg':sum_reg, 
                   'sum_payers':sum_payers, 'sum_pay_count':sum_pay_count, 'pay_reg':pay_reg, 'role_ave_arpu':role_ave_arpu,
                   'plat_name':self.server_info['plat_name'],'sid': self.sid} 
            des_path= self.server_info['horizontal']+'/horizontal_'+start_date
            public.write_json_file(des_path, data, mod='a', end='\n')
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
        
    def get_platonline_info(self,start_date=None,end_date=None,plat_id='all',plat_ids=[],user='all'):
        """ 获取平台横向分析统计数据 """
        #start_date  = self.start_date
        #end_date= self.end_date
        infos   = []
        plats   = {'all':[u'所有平台',False]}
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['horizontal']+u'/horizontal_%s'%start_date
            ret_msg = public.read_json_file(fname)
            #print 'fname,ret_msg:',fname,ret_msg
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            datas   = {}
            for d in ret_msg:
                plat_name   = d.get('plat_name','unknown')
#                pay_reg = d.get('pay_reg',0)
#                if pay_reg > 0.1:
#                    continue
                #开服日期
                serverid= d.get('sid','-1')
                sstart_date  = GS_INFO.get(serverid,{}).get('start_date','')
                if public.objIsEmpty(sstart_date) or sstart_date > start_date:
                    public.print_str('[%s] server start date [%s] is none or later than search date [%s]'%(serverid,sstart_date,start_date))
                    continue
                if datas.has_key(plat_name):
                    for k,v in d.items():
                        if k in ['plat_name','sid']:
                            continue
                        datas[plat_name][k] += v
                    datas[plat_name]['count']   +=1
                else:
                    d['count']  = 1
                    datas[plat_name]= d
            if user not in ['winson']:
                plat_ids= datas.keys()
            for plat_name,info in datas.items():
                count   = info.get('count',1)
                if count < 1:
                    count = 1
                platname= PLAT_NAMES.get(plat_name,plat_name)
                if plat_name not in plat_ids:
                    continue 
                if not plats.has_key(plat_name):
                    plats[plat_name]= [platname,False]
                if plat_id not in ['all'] and plat_name != plat_id:
                    continue
                infos.append([start_date,PLAT_NAMES.get(plat_name,plat_name), info.get('reg_roles',0), info.get('top_player',0), 
                              info.get('ave_player',0), info.get('day_roles',0), info.get('day_new_roles',0),info.get('pndau',0), 
                              info.get('odau',0),info.get('podau',0),info.get('day_payers',0),'%.2f'%(info.get('pay_login',0)/count),
                              '%.2f'%info.get('day_pay_count',0),'%.2f'%(info.get('day_arpu',0)/count), '%.2f'%(info.get('p_d',0)/count), 
                              info.get('sum_roles',0),info.get('sum_reg',0),info.get('sum_payers',0),'%.2f'%info.get('sum_pay_count',0), 
                              '%.3f'%(info.get('pay_reg',0)/count), '%.2f'%(info.get('role_ave_arpu',0)/count)])
            start_date = public.getNextDay(start_date)
        if plats.has_key(plat_id):
            plats[plat_id][1]   = True
        else:
            plats['all'][1] = True
        return infos,plats
    
    def get_horizontal_info(self,start_date=None,end_date=None,sids=[],platids='all'):
        """ 获取横向分析统计数据 """
        datas   = []
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['horizontal']+u'/horizontal_%s'%start_date
            ret_msg = public.read_json_file(fname)
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            for info in ret_msg:
                serverid= info.get('sid','-1')
#                plat_name = info.get('plat_name','unknown')
#                if plat_name == 'pengyou':
#                    print serverid,'\t','%.2f'%info.get('day_pay_count',0)
                #开服日期
                sstart_date  = GS_INFO.get(serverid,{}).get('start_date','')
                if public.objIsEmpty(sstart_date) or sstart_date > start_date:
                    public.print_str('[%s] server start date [%s] is none or later than search date [%s]'%(serverid,sstart_date,start_date))
                    continue
#                pay_reg = info.get('pay_reg',0)
#                if pay_reg > 0.1:
#                    continue
                if serverid not in sids:
                    continue
                #if platids != 'all' and plat_id not in platids:
                #    continue
                datas.append([start_date,
                              GS_INFO.get(serverid,{}).get('name',serverid),
                              info.get('reg_roles',0),
                              info.get('top_player',0), 
                              info.get('ave_player',0),
                              info.get('day_roles',0),
                              info.get('day_new_roles',0),
                              info.get('pndau',0), 
                              info.get('odau',0),
                              info.get('podau',0),
                              info.get('day_payers',0),
                              '%.2f'%(info.get('pay_login',0)),
                              '%.2f'%info.get('day_pay_count',0),
                              '%.2f'%(info.get('day_arpu',0)),
                              '%.2f'%(info.get('p_d',0)), 
                              info.get('sum_roles',0),
                              info.get('sum_reg',0),
                              info.get('sum_payers',0),
                              '%.2f'%info.get('sum_pay_count',0),
                              '%.3f'%(info.get('pay_reg',0)), 
                              '%.2f'%(info.get('role_ave_arpu',0))
                              ])
            start_date = public.getNextDay(start_date)
        return datas
    
    def pay_sortII(self,ps_date=None, pe_date=None):
        """ 玩家充值排行,某段时间内的数据 """
        #服务器标识    账号名    角色ID    角色名   势力    等级     剩余金币    注册时间    公会    充值总额RMB(%)    充值次数    平均充值        停充天数        首充时间    最后登陆时间
        if public.objIsEmpty(ps_date):
            ps_date = self.yesterday
        path= '%s/payer_count_%s'%(self.server_info['payer_count'], ps_date)
        if os.path.exists(path):
            infos   = public.read_json_file(path)
            if not public.objIsEmpty(infos):
                rets= self.get_role_payII(infos[0],pcmd='top_up',ptr=['day'])
                role_records= rets.get('top_up',[])
            else:
                role_records= []
        else:
            pay_records = self.get_pay_record(ps_date=ps_date, pe_date=ps_date)
            role_pays   = self.get_role_pay(pay_records)
            role_records= role_pays.values()
        #将返回的字典转换成列表进行排序
        #tmp_list    = []
        #for roleid,info in role_pays.items():
        #    tmp_list.append(info)
        public.print_str('---------sorted start len:%s'%len(role_records))
        sort_record = sorted(role_records, key=operator.itemgetter('tongbao'), reverse=True)
        public.print_str('---------sorted end')
        datas   = []
        fields  = DEFAULT_ROLE_FIELDS
        fields.extend(['guildname'])
        role_infos  = self.get_pay_role_info(sort_record,fields=fields)
        public.print_str('---------get_pay_role_info end')
        for record in sort_record:
            tmp_list= [self.server_info['name'],]
            if record.has_key('roleid'):
                roleid  = record.get('roleid',None)
            elif record.has_key('role_id'):
                roleid  = record.get('role_id',None)
            else:
                roleid  = None
            if not role_infos.has_key(roleid):
                #获取玩家信息
                role_msg= None
            else:
                role_msg= role_infos[roleid]            
            #账号名    角色ID    角色名   势力    等级     剩余金币    注册时间
            if role_msg is None:
                tmp_list.extend(['null',roleid,'null','null','null','null','null','null'])
                role_msg= {}
            else:
                tmp_list.extend([role_msg.get('username','null'), roleid, role_msg.get('name','null'),
                                 CAMPS.get(role_msg.get('campid',0),'null'), role_msg.get('role_level','null'),
                                 role_msg.get('tongbao',0), role_msg.get('create_time','null'),
                                 role_msg.get('guildname','null'),])
            #充值总额RMB(%)    充值次数    平均充值        停充天数    首充时间    最后登陆时间
            RMB     = record.get('rmb')
            times   = record.get('times',1)
            cre_date= record.get('last_time',self.ss_date).split(' ')[0]
            tmp_list.extend(['%.2f'%RMB,times,'%.2f'%(RMB/times),public.getDays(cre_date, self.yesterday)+1,
                             record.get('first_time','null'),role_msg.get('logintime','null')])
            datas.append(tmp_list)
        public.print_str('---------pay_sort end')
        return datas

    def read_jlb_kashen_cost(self):
        """ 读取加勒比海消费数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        datas   = {}
        while True:
            if start_date > end_date:
                break
            for server in SERVERS:
                sid = server['sid']
                path= DB_PATH + '/kashen_%s/cost_earn/'%sid+start_date
                if not os.path.exists(path):
                    public.print_str(path+' is not exist')
                    continue
                ds  = public.read_json_file(path)
                if public.objIsEmpty(ds):
                    public.print_str(path+' is none')
                    continue
                if not datas.has_key(sid):
                    datas[sid]  = {}
                tmp_data= {}
                cost_data   = ds[0].get('cost_data',{})
                for cmd,v in cost_data.items():
                    if cmd not in JLB_CMDS:
                        continue
                    tmp_data[cmd]   = v
                if public.objIsFull(tmp_data):
                    public.merge_dict(datas[sid],tmp_data)
            start_date  = public.getNextDay(start_date)
        return datas
    
    def get_jlb_kashen_info(self):
        """ 获取加勒比海消费数据 """
        datas   = {}
        sum_tongbao = 0
        sum_feiqian = 0
        #读取加勒比海消费数据
        costs   = self.read_jlb_kashen_cost()
        for cost_data in costs.values():
            for cmd,d in cost_data.items():
                feiqian = d['feiqian']
                tongbao = d['tongbao']
                cost_feiqian= feiqian['count']
                cost_tongbao= tongbao['count']
                if (cost_feiqian+cost_tongbao) < 1:
                    continue
                if not datas.has_key(cmd):
                    datas[cmd]  = {'feiqian':0,'tongbao':0,'roles':0}
                datas[cmd]['feiqian']   += cost_feiqian
                datas[cmd]['tongbao']   += cost_tongbao
                datas[cmd]['roles'] += len(self.merge_list(feiqian['roles'], tongbao['roles']))
                sum_feiqian += cost_feiqian
                sum_tongbao += cost_tongbao
        infos   = []
        for cmd,info in datas.items():
            cost_tongbao= info['tongbao']
            cost_feiqian= info['feiqian']
            if cost_tongbao < 1 or sum_tongbao < 1:
                tb_per  = 0
            else:
                tb_per  = cost_tongbao*1.0/sum_tongbao
            if cost_feiqian < 1 or sum_feiqian < 1:
                fq_per  = 0
            else:
                fq_per  = cost_feiqian*1.0/sum_feiqian
            infos.append([COST_CMDS.get(cmd,{}).get('name',cmd),info['roles'],cost_tongbao,'%.3f'%tb_per,cost_feiqian,'%.3f'%fq_per])
        infos.append(['总和','',sum_tongbao,'',sum_feiqian,''])
        return infos
    
    def do_jlb_card(self,fnames):
        """ 处理付费行为 """        
        keys= JLB_CARD_CMDS.keys()
        datas   = {}
        for fname in fnames:
            print 'do_jlb_card: ',fname
            log_strs= public.read_file_list(fname)
            for log_str in log_strs:
                if len(log_str) < 4:
                    continue
                cmd = log_str[2]
                if cmd not in keys:
                    continue
                param   = json.loads(log_str[3])
                #server_id   = param.get('server_id', self.sid)
                itemlist= param.get('itemlist',[])
                if cmd == 'THunt':
                    gradeid = param.get('id',0)
                    cmd = cmd+'%s'%gradeid
                    if cmd not in keys:
                        continue
                for item in itemlist:
                    itemsn  = item.get('itemsn',0)
                    count   = item.get('count',0)
                    if itemsn == 0:
                        public.print_str('wrong record: %r'%log_str)
                    if datas.has_key(itemsn):
                        if datas[itemsn].has_key(cmd):
                            datas[itemsn][cmd]  += count
                        else:
                            datas[itemsn][cmd]  = count
                        datas[itemsn]['count']  += count
                    else:
                        datas[itemsn]  = {cmd: count,'sid': self.sid,'count':count}
        return datas
    
    def write_jlb_cards(self):
        """ 写加勒比掉落卡片数据 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            fnames  = public.get_log_files(self.gl_path, start_date, '', False)
            datas   = self.do_jlb_card(fnames)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            des_path= self.server_info['jlb_cards']+'/jlb_cards_'+start_date
            public.write_json_file(des_path, datas, mod='a', end='\n')
            public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_jlb_card_info(self):
        """ 获取加勒比掉落卡片数据 """
        start_date  = self.start_date
        end_date= self.end_date
        datas   = {}
        sum_count   = 0
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['jlb_cards']+u'/jlb_cards_%s'%start_date
            ret_msg = public.read_json_file(fname)
            if public.objIsEmpty(ret_msg):
                start_date = public.getNextDay(start_date)
                continue
            for d in ret_msg:
                for itemsn,info in d.items():
                    count   = info.get('count',0)
                    if count < 1:
                        continue
                    sum_count   += count
                    if datas.has_key(itemsn):
                        public.merge_dict(datas[itemsn], info, add_str=False)
                    else:
                        datas[itemsn]  = info
            start_date = public.getNextDay(start_date)
        infos   = []
        keys    = ['THunt1','THunt2','THunt3','THunt4','CaribWabao','rare_boss']
        for itemsn,info in datas.items():
            ret_msg = self.get_data_table_info({'id':int(itemsn)},fields=['name'],table='backend_item')
            if public.objIsEmpty(ret_msg):
                itemname= itemsn
            else:
                itemname= ret_msg.get('name',itemsn)
            #sname   = GS_INFO[info.get('sid',self.sid)]['name']
            count   = info.get('count',0)
            if count < 1:
                per = 0
            else:
                per = count*1.0/sum_count
            tmp_list= [itemname,count,'%.3f'%per]
            for key in keys:
                if info.has_key(key):
                    tmp_list.append(info[key])
                else:
                    tmp_list.append(0)
            infos.append(tmp_list)
        infos.append(['总和',sum_count,'','','','','','',''])
        return infos
    
    def do_ex_sell_profit(self,records):
        """ 处理卖出货物获利 """
        datas   = {}
        for record in records:
            if len(record) < 4:
                continue
            roleid  = record[1]
#            if roleid == '465da3f2-d38e-4373-6768-7f32d31f6e3c':
#                print record
            param   = json.loads(record[3])
            add_profit  = param.get('add_profit',0)
            if datas.has_key(roleid):
                datas[roleid]   += add_profit
            else:
                datas[roleid]   = add_profit
        return datas
    
    def write_ex_sell(self):
        """ 写卖出货物获利 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            msg,records = public.get_log_records(bpath=self.server_info['gl_path'],start_day=start_date,end_day=start_date,run_hour=False,include=['ExSell'])
            if msg:
                print 'error:',msg
            else:
                datas   = self.do_ex_sell_profit(records)
                if public.objIsFull(datas):
                    des_path= self.server_info['ex_sell_profit']+'/ex_sell_profit_'+start_date
                    public.write_json_file(des_path, datas, mod='w', end='\n')
                    public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_ex_sell_info(self):
        """ 获取卖出货物获利 """
        start_date  = self.start_date
        end_date= self.end_date
        infos   = []
#        sum_persons = 0
        sum_profit  = 0
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['ex_sell_profit']+'/ex_sell_profit_'+start_date
            datas   = public.read_json_file(fname)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            d1  = datas[0]
            persons = len(d1.keys())
#            sum_persons += persons
            profit  = 0
            for p in d1.values():
                profit  += p
            sum_profit  += profit
            ave = '0.0'
            if persons:
                ave = '%.2f'%(profit*1.0/persons)
            infos.append([start_date,persons,profit,ave])
            start_date = public.getNextDay(start_date)
#        sum_ave = '0.0'
#        if sum_persons:
#            sum_ave = '%.2f'%(sum_profit*1.0/sum_persons)       
        infos.append(['总和','',sum_profit,''])
        return infos
    
    def do_cost_ap(self,records):
        """ 处理行动力消耗 """
        datas   = {}
        for record in records:
            if len(record) < 4:
                continue
            roleid  = record[1]
            param   = json.loads(record[3])
            cost_ap = param.get('cost_ap',0)
            if not cost_ap:
                continue
            if datas.has_key(roleid):
                datas[roleid]   += cost_ap
            else:
                datas[roleid]   = cost_ap
        return datas
    
    def write_cost_ap(self):
        """ 写行动力消耗 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
#            卖出货物ExSell
#            攻击Rob
#            立即到达ArriveNow
#            立即完成任务TaskCompleteNow
#            访问拓扑TopoVisit
#            抽卡PkDrawCard
#            刷新玩家拓扑结构RefreshPlayerTopo
            msg,records = public.get_log_records(bpath=self.server_info['gl_path'],start_day=start_date,end_day=start_date,run_hour=False,
                                                 include=['ExSell','Rob','ArriveNow','TaskCompleteNow','TopoVisit','PkDrawCard','RefreshPlayerTopo'])
            if msg:
                print 'error:',msg
            else:
                datas   = self.do_cost_ap(records)
                if public.objIsFull(datas):
                    des_path= self.server_info['cost_ap']+'/'+start_date
                    public.write_json_file(des_path, datas, mod='w', end='\n')
                    public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_cost_ap_info(self):
        """ 获取动力消耗 """
        start_date  = self.start_date
        end_date= self.end_date
        infos   = []
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['cost_ap']+'/'+start_date
            datas   = public.read_json_file(fname)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            d1  = datas[0]
            persons = len(d1.keys())
            ap  = 0
            for p in d1.values():
                ap  += p
            ave = '0.0'
            if persons:
                ave = '%.2f'%(ap*1.0/persons)
            infos.append([start_date,persons,ap,ave])
            start_date = public.getNextDay(start_date)
        return infos
    
    def do_online_time(self,records):
        """ 处理在线时长 """
        #单个角色登入登出记录
        datas   = {}
        for record in records:
            if len(record) < 4:
                continue
            cmd = record[2]
            param   = json.loads(record[3])
            today   = int(param.get('today',0))
#            if not today and cmd == 'Logout':
#                continue
            roleid  = record[1]
#            if roleid == 'e116e7c2-f90c-469b-5f14-72c039a21e3c':
#                print record
            if cmd == 'PlayGame':
                #记录时间戳
                t1  = record[0]
                today   += public.getSeconds2(t1,t1[:11]+'23:59:59')
            datas[roleid]   = today
            #today   = param.get('today',0)
            #if not today:
            #    continue
            #if datas.has_key(roleid):
            #    datas[roleid][1]= record
            #else:
            #    datas[roleid]   = [record,[]]
            #datas[roleid]= record
#        #角色在线时长
#        d2  = {}
#        for roleid, r1 in d2.items():
#            
        return datas
    
    def write_online_time(self):
        """ 写在线时长 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
#            上线PlayGame
#            下线Logout
#                 today：今天在线时长（单位秒）
#                 lastday：昨天在线时长（单位秒）
            msg,records = public.get_log_records(bpath=self.server_info['gl_path'],start_day=start_date,end_day=start_date,run_hour=False,
                                                 include=['PlayGame','Logout'])
            if msg:
                print 'error:',msg
            else:
                datas   = self.do_online_time(records)
                if public.objIsFull(datas):
                    des_path= self.server_info['online_time']+'/'+start_date
                    public.write_json_file(des_path, datas, mod='w', end='\n')
                    public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_online_time_info(self):
        """ 获取在线时长 """
        start_date  = self.start_date
        end_date= self.end_date
        infos   = []
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['online_time']+'/'+start_date
            datas   = public.read_json_file(fname)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            d1  = datas[0]
            persons = len(d1.keys())
            t1  = 0
            for t2 in d1.values():
                t1  += t2
            ave = '0.0'
            if persons:
                ave = '%.2f'%(ap*1.0/persons)
            infos.append([start_date,persons,ap,ave])
            start_date = public.getNextDay(start_date)
        return infos
    
    def do_cost_money(self,records):
        """ 处理行银币消耗 """
        datas   = {}
        for record in records:
            if len(record) < 4:
                continue
            roleid  = record[1]
            cmd = record[2]
            param   = record[3]
            if not param:
                continue
            try:
                param   = json.loads(param)
            except:
                print record
                continue
            cost_money = param.get('cost_money',0)
            if not cost_money:
                continue
            if datas.has_key(roleid):
                if datas[roleid].has_key(cmd):
                    datas[roleid][cmd]  += cost_money
                else:
                    datas[roleid][cmd]  = cost_money
            else:
                datas[roleid]   = {cmd: cost_money}
        return datas
    
    def write_cost_money(self):
        """ 写行银币消耗 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            msg,records = public.get_log_records(bpath=self.server_info['gl_path'],start_day=start_date,end_day=start_date,run_hour=False,
                                                 include=[])
            if msg:
                print 'error:',msg
            else:
                datas   = self.do_cost_money(records)
                if public.objIsFull(datas):
                    des_path= self.server_info['cost_money']+'/'+start_date
                    public.write_json_file(des_path, datas, mod='w', end='\n')
                    public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_cost_money_info(self,roleids=[]):
        """ 获取银币消耗 """
        start_date  = self.start_date
        end_date= self.end_date
        infos   = [['日期','雇佣','选择地图随机元件','交易所-解锁货物','合成','界面B/点击任务选项/任务接受','交易所-买']]
        if not roleids:
            return infos
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['cost_money']+'/'+start_date
            datas   = public.read_json_file(fname)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            d1  = datas[0]
            d2  = {}
            for roleid,v in d1.items():
                if roleid not in roleids:
                    continue
                for cmd, money in v.items():
                    if d2.has_key(cmd):
                        d2[cmd]  += money
                    else:
                        d2[cmd]  = money
            tmp = [start_date]
            for cmd in ['Hire','TopoChoose','ExUnlock','Combo','TaskAccept','ExBuy']:
                tmp.append(d2.get(cmd,0))
            infos.append(tmp)
            start_date = public.getNextDay(start_date)
        return infos
    
    def do_ex_sell_profitI(self,records):
        """ 处理卖出货物获利&次数 """
        datas   = {}
        for record in records:
            if len(record) < 4:
                continue
            roleid  = record[1]
#            if roleid == '465da3f2-d38e-4373-6768-7f32d31f6e3c':
#                print record
            param   = json.loads(record[3])
            add_profit  = param.get('add_profit',0)
            if datas.has_key(roleid):
                datas[roleid]['add_profit'] += add_profit
                datas[roleid]['count']  += 1
            else:
                datas[roleid]   = {'add_profit': add_profit, 'count': 1}
        return datas
    
    def write_ex_sellI(self):
        """ 写卖出货物获利&次数 """
        start_date  = self.start_date
        end_date    = self.end_date
        while True:
            if start_date > end_date:
                break
            msg,records = public.get_log_records(bpath=self.server_info['gl_path'],start_day=start_date,end_day=start_date,run_hour=False,include=['ExSell'])
            if msg:
                print 'error:',msg
            else:
                datas   = self.do_ex_sell_profitI(records)
                if public.objIsFull(datas):
                    des_path= self.server_info['ex_sell_profitI']+'/ex_sell_profit_'+start_date
                    public.write_json_file(des_path, datas, mod='w', end='\n')
                    public.print_str('result path',des_path)
            start_date = public.getNextDay(start_date)
    
    def get_ex_sell_infoI(self,roleids=[]):
        """ 获取卖出货物获利，某些玩家数据 """
        start_date  = self.start_date
        end_date= self.end_date
        infos   = []
        if not roleids:
            return infos
#        sum_persons = 0
        sum_profit  = 0
        while True:
            if start_date > end_date:
                break
            fname   = self.server_info['ex_sell_profitI']+'/ex_sell_profit_'+start_date
            datas   = public.read_json_file(fname)
            if public.objIsEmpty(datas):
                start_date = public.getNextDay(start_date)
                continue
            d1  = datas[0]
            persons = 0
            profit  = 0
            count   = 0
            for roleid,v1 in d1.items():
                if roleid not in roleids:
                    continue
                profit  += v1['add_profit']
                count   += v1['count']
                persons += 1
            sum_profit  += profit
            ave = '0.0'
            if persons:
                ave = '%.2f'%(profit*1.0/persons)
            infos.append([start_date,persons,profit,ave,count])
            start_date = public.getNextDay(start_date)
#        sum_ave = '0.0'
#        if sum_persons:
#            sum_ave = '%.2f'%(sum_profit*1.0/sum_persons)    
        infos.append(['总和','',sum_profit,'',''])
        return infos
    
def do_plat_pay_info(sid,start_day,end_day):
    """ 计算区服在某段时间内的充值 """
    tongbao = 0
    obj = DataBackstage(sid, create=False)
    obj.set_date(p_start_date=start_day,p_end_date=start_day)
    records = obj.get_pay_record(ps_date=obj.start_date, pe_date=obj.end_date, roleids=None)
    for record in records:
        #tb  = record.get('tongbao',0)
        #print sid,'\t',tb
        tongbao += record.get('tongbao',0)
    return tongbao
    
def get_plat_pay_info(start_day,end_day):
    """ 获取平台充值数据 """
    datas   = {}
    for server in SERVERS:
        sid = server.get('sid')
        plat_id = server['plat_name']
        #腾讯是以玩家在游戏中的消费计算的，所以不能用充值数据来计算
        if plat_id in ['pengyou']:
            continue
        start_date  = server.get('start_date','')
        if start_date > end_day:
            print 'server[%s] start date later than %s'%(sid,end_day)
            continue
        #玩家付费数据,以游戏币进行计算
        rmb = public.tb2rmb(do_plat_pay_info(sid,start_day,end_day))
        if datas.has_key(plat_id):
            datas[plat_id]['rmb']   += rmb
        else:
            datas[plat_id]  = {'rmb':rmb,'platname':PLAT_NAMES[plat_id]}
    return datas

def timing():
    """ 定时执行 """
    mod = 'w'
    for server in SERVERS:
        try:
            sid = server['sid']
            if sid not in ['16001','16002']:
                continue
            start_date  = server['start_date']
            #sname= server['name']
            obj = DataBackstage(sid, create=False)
            obj.set_date(p_start_date='2013-06-15',p_end_date='2013-06-16')
#            #写消费与获利数据
#            obj.write_cost_earn()
            #obj.set_date(p_start_date=GS_INFO[sid]['start_date'])
            #obj.set_date(p_start_date=start_date)
            #写玩家付费信息
            obj.write_payer_info()
#            #写卡包数据
#            obj.write_cardbag()
#            #大付费玩家名单
#            obj.write_richman_info(min_count=30000)
#            #写烟火数据
#            obj.write_fireworks()
#            #平台横向分析统计
#            obj.write_platonline()
#            #付费玩家区域分布
#            obj.payer_area()
#            #付费500RMB以上玩家区域分布
#            obj.payer_area(min_count=500)
        except:
            print public.print_str('server [%s] \t%r'%(server,tb.format_exc()))
    
def timing_debug():
    """ 定时执行调试入口 """
    print public.get_now2str(),'\tstart'
    t1= time()
    #for sid,info in GS_INFO.items():
    for sid,sname in SERVERS:
        try:
            if GS_INFO[sid]['plat_name'] not in ['pengyou','qzone','tencent']:
                print public.get_now2str(),'\t%s is not tencent server'%sid
                continue
            print public.get_now2str(),'\t%s is excutting'%sid 
            obj = DataBackstage(sid, create=False)
            obj.set_date(p_start_date=GS_INFO[sid]['start_date'])
            #写消费与获利数据
            #obj.write_cost_earn()
            #大付费玩家区域分布
            #obj.payer_area()
            #付费500RMB以上玩家区域分布
            obj.payer_area(min_count=500)
        except:
            print public.get_now2str(),'\t%r'%tb.format_exc()
    print public.get_now2str(),'\tend\ttimestamp\t',time()-t1
    
if __name__ == "__main__":
    
    #执行正式模块
    EXCUTE_PROCESS  = False
    #执行测试模块
    EXCUTE_TEST     = True
    #执行测试模块2
    EXCUTE_TEST2    = False
    if EXCUTE_PROCESS:
        timing()
        #timing_debug()
    elif EXCUTE_TEST:
        for sid in ['1']:
#        for server in SERVERS:
#            try:
#                sid = server['sid']
#                print '-----------------------server id [%s]'%sid
#                start_date  = server['start_date']
                obj = DataBackstage(sid, create=False)
                obj.set_server_info()
                if not obj.server_info:
                    continue
#                if not obj.set_server_info():
#                    print '初始化区服数据失败'
#                    continue
                obj.set_date(p_start_date='2014-04-30', p_end_date='2014-05-28')
#                #print obj.get_player_infoI(tag='uid',pstr=['64346BC930535FA6B004A49CB1CC6710'],fields=['ip','roleid'],read_other=False)
#                #付费玩家区域分布
#                obj.payer_area()
#                #付费500RMB以上玩家区域分布
#                obj.payer_area(min_count=500)
#                #obj.write_cost_earn()
#                #充值日志
#                datas = obj.payment_log(names=['白发拜伦'])
#                #横向分析统计
#                datas,ave_pd,month_arpu= obj.online_pay()
#                #角色流失率统计
#                datas   = obj.role_lose_per('2012-08-12')
#                infos   = ['时段\t到达创建页人数\t已创建角色人数\t创建角色页面流失率\t接第一个任务人数\t游戏画面流失率\t完成第一个任务人数\t第一个任务流失率']  
#                data_bs = DataBackstage(sid, create=False)
#                datas   = data_bs.role_lose_per('2013-03-04') 
#                for data in datas:
#                    #print data
#                    tmp_str = ''
#                    for v in data:
#                        tmp_str += '%s\t'%v
#                    tmp_str.rstrip('\t')
#                    infos.append(tmp_str+'\n')
#                result_path = obj.server_info['activity']+u'/2013-03-04/role_lose_per_2013-03-04.txt'
#                public.write_json_file(result_path, infos, mod='a',is_json=False)
#                print result_path
#                #创建登录统计
#                datas   = obj.create_login()        
#                totals,datas = obj.payment()
#                print 'totals: ', totals
#                #充值日志
#                datas   = obj.payment_log()        
#                #库存统计
#                datas   = obj.exist_count()        
#                datas   = obj.exist_log(['血玫瑰问萍'])        
#                datas   = obj.payment_log()#names=['血玫瑰问萍']
#                #获取某段时间内玩家的角色数和阵营数据
#                datas   = obj.get_role_camp()
#                for k,v in datas.items():
#                    print 'k,v: ', k,'\t',v
#                #金币、礼金和银币的消耗与活力        
#                datas = obj.cost(key='tongbao')        
#                #新手二登        
#                print obj.new_second_login('2012-08-03')
#                dates = obj.run_data()
#                #写卡包数据
#                obj.write_cardbag()
#                #获取卡包数据
#                datas   = obj.get_cardbag_info()
#                #整理卡包数据
#                obj.rewrite_cardbag_info()
#                #写玩家付费信息
#                obj.write_payer_info()
#                datas   = obj.get_payer_area_info()
#                #充值排行
#                datas   = obj.pay_sort()
#                #大付费玩家名单
#                obj.write_richman_info(min_count=6500)
#                infos   = ['日期\t注册人数\t最高在线\t平均在线\tDAU\tNDAU\tODAU\t付费人数\t付费金额\t日ARPU值\tP/D\t总注册人数\t总付费用户数\t总收入\t注册付费比\t人均arpu值\n']
#                #写烟火数据
#                obj.write_fireworks()
#                #平台横向分析统计
#                obj.write_platonline()
#                #获取加勒比海消费数据
#                infos   = obj.get_jlb_kashen_info()
#                for info in infos:
#                    print info
#                #写加勒比掉落卡片数据
#                obj.write_jlb_cards()
#                #获取加勒比掉落卡片数据
#                datas   = obj.get_jlb_card_info()
#                for data in datas:
#                    tmp_str = ''
#                    for v in data:
#                        tmp_str += '%s\t'%v
#                    print tmp_str
#                #写卖出货物获利
#                obj.write_ex_sell()
#                #写行动力消耗
#                obj.write_cost_ap()
#                #写在线时长
#                obj.write_online_time()
#                #写行银币消耗
#                obj.write_cost_money()
#                #获取银币消耗
#                for v1 in obj.get_cost_money_info(roleids=['3e4d140e-03e4-4e2e-6792-f666e29855b7']):
#                    tmp = '%s'%v1[0]
#                    for v2 in v1[1:]:
#                        tmp += '\t%s'%v2
#                    print tmp
#                #写卖出货物获利&次数
#                obj.write_ex_sellI()
                #个人获取银币数量
                for r in obj.get_ex_sell_infoI(roleids=['3e4d140e-03e4-4e2e-6792-f666e29855b7']):
                    tmp = '%s'%r[0]
                    for v in r[1:]:
                        tmp += '\t%s'%v
                    print tmp
#            except:
#                print public.print_str('server [%s] \t%r'%(sid,tb.format_exc()))
        
    elif EXCUTE_TEST2:
        #获取平台充值数据
        public.print_str('---------- start ')
        t1  = time()
        #datas   = get_plat_pay_info('2013-04-01','2013-04-30')
        datas   = {'qidian': {'rmb': 708722.0, 'platname': u'\u8d77\u70b9'}, '2133': {'rmb': 120622.0, 'platname': '2133'}, 
                   'kaixin': {'rmb': 218328.0, 'platname': '\xe5\xbc\x80\xe5\xbf\x83\xe7\xbd\x91'}, 
                   '37wan': {'rmb': 739025.0, 'platname': '37wan'}, 'self': {'rmb': 31464.3, 'platname': u'\u81ea\u6709\u670d'}, 
                   'pptv': {'rmb': 16560.0, 'platname': 'PPTV'}, 'yaowan': {'rmb': 2525.1, 'platname': '\xe8\xa6\x81\xe7\x8e\xa9'}, 
                   'pps': {'rmb': 28119.0, 'platname': 'PPS'}, 'pengyou': {'rmb': 733246.2000000002, 'platname': u'\u817e\u8baf'}, 
                   '2144': {'rmb': 21978.0, 'platname': '2144'}, '1377': {'rmb': 1101.0, 'platname': '1377'}, 
                   '37ww': {'rmb': 48074.0, 'platname': '37\xe7\x8e\xa9\xe7\x8e\xa9'}, 'xba': {'rmb': 7303.0, 'platname': u'XBA'}, 
                   '360': {'rmb': 789872.0, 'platname': '360\xe5\x8d\xab\xe5\xa3\xab'}, 'sina': {'rmb': 315720.0, 'platname': u'\u65b0\u6d6a'}}
        for data in datas.values():
            print '%(platname)s\t%(rmb)s'%data
        t2  = time()
        public.print_str('---------- end %s'%(t2-t1))
        
    print 'complete'
