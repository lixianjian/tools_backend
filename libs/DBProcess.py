#!/usr/bin/env python2.7
#coding=utf-8
'''
定时 读取逻辑服务器的某些信息
'''

from pymongo.connection import Connection 
import json
from datetime import datetime, timedelta
import sys
import urllib

from config import *


class DBProcess():
    """数据库访问操作"""
    def __init__(self):
        """初始化"""
        pass


    def connectDB(self, sid, table_name):
        """根据传入的sid(服务器ID)、db_name(数据库名)和
        table_name(表名)返回数据库连接实例"""        
        #连接该服务器的制定数据库
        mgdb = Connection(dbhost, 27417)
        dt_name = 'dt_base_%s'%sid
        datadb = mgdb[dt_name][table_name]
        #返回数据库的连接实例
        return datadb, mgdb
    
    
    def get_aid(self, sid, roleid):
        """根据传入的sid和roleid获取该roleid所在的区服"""
#        mgdb    = Connection('10.23.0.223', 27417)
#        dt_name = 'dt_base_%s'%sid    
#        datadb  = mgdb[dt_name]['role']
        datadb, mgdb = self.connectDB(sid, 'role')

        aid = ''
        try:
            dataDict = datadb.find_one({'roleid':roleid},{'aid':1})
            aid      = dataDict.get('aid', '')
        except:
            pass

        if aid == '':
            print 'roleid[%s] 对应的aid为空'%roleid
        
        mgdb.disconnect()
        return aid
    
    
    def get_server_nameI(self, sid, aid):
        """"""
        return 'qidian'
    
    
    def get_server_name(self, sid, aid):
        """根据传入的sid和roleid获取该roleid所在的区服"""
#        mgdb    = Connection('10.23.0.223', 27417)
#        dt_name = 'dt_base_%s'%sid    
#        datadb  = mgdb[dt_name]['account']
        datadb, mgdb = self.connectDB(sid, 'account')
        
        server_name = ''
        try:
            dataDict = datadb.find_one({'aid':aid},{'source_name':1})
            server_name = dataDict.get('source_name', '')
            if server_name == '':
                print 'aid[%s] 对应的source_name为空'%aid
        except:
            server_name = 'unknown'
        mgdb.disconnect()
        return server_name
    
    
    def get_plat_roleids(self, sid, plat_aids):
        """根据传入的sid和roleid获取该roleid所在的区服"""
#        mgdb    = Connection('10.23.0.223', 27417)
#        dt_name = 'dt_base_%s'%sid    
#        datadb  = mgdb[dt_name]['role']
        datadb, mgdb = self.connectDB(sid, 'role')
        
        roleids = []
        for dataDict in datadb.find({'aid':{'$in':plat_aids}},{'roleid':1}):
            roleid = dataDict.get('roleid', '')
            if roleid == '':
                print 'aid[%s] 对应的roleid为空'%aid
            roleids.append(roleid)
        
        mgdb.disconnect()
        print len(roleids)
        return roleids 
    
    
    def get_plat_aids(self, sid, plat_server):
        """"""
        datadb, mgdb = self.connectDB(sid, 'account')
        
        aids = []
        for dataDict in datadb.find({},{'aid':1}):
            aid = dataDict.get('aid', '')
            if aid == '':
                continue
            aids.append(aid)
        
        mgdb.disconnect()
#        print len(aids)
#        print sys.getsizeof(aids[0])
#        print sys.getsizeof(aids[2:5])
#        print sys.getsizeof(aids)
        return aids
    
    
    def get_plat_aidsI(self, sid, plat_server):
        """根据传入的sid和roleid获取该roleid所在的区服"""
#        mgdb    = Connection('10.23.0.223', 27417)
#        dt_name = 'dt_base_%s'%sid    
#        datadb  = mgdb[dt_name]['account']
        datadb, mgdb = self.connectDB(sid, 'account')
        
        aids = []
        for dataDict in datadb.find({'server_name':plat_server},{'aid':1}):
            aid = dataDict.get('aid', '')
            if aid == '':
                continue
            aids.append(aid)
        
        mgdb.disconnect()
        return aids


    def get_item_name(self, gamelog_dir, sid):    
        ''' 传入gamelog_path和sid得到item和name对应关系 '''
        datadb, mgdb = self.connectDB(sid, 'dt_data', 'item')
#        mgdb = Connection('10.23.0.216', 27418)    
#        datadb = mgdb['dt_data']['item']
        
        fname = '../tmp_files/item_name.txt'
        fp = open(fname, 'w')
        
        i=0
        for data in datadb.find({}, {'itemsn':1,'name':1}):
            i += 1
            fp.write('%s\t%s\t\n'%(data['itemsn'],data['name']))   
        fp.close()    
        
        mgdb.disconnect() 
        print ('get_item_name - item number [%s]'%i)
        
    
    
    def get_roleid_item(self, sid):    
        ''' 传入sid得到item对应的银两值 '''
        datadb, mgdb = self.connectDB(sid, 'role_item')
        
        dict = {}
        #当前的roleid和silver值
        current_roleid = ''
        current_silver = 0
        result_list = []
        print '连接数据库成功，开始读取数据'
        for data in datadb.find({'sub_type': '29'}, 
                                {'roleid':1, 'count':1}):
            if dict.has_key(data['roleid']):
                dict[data['roleid']] += data['count']
            else:
                dict[data['roleid']] = data['count']
            if dict[data['roleid']] > current_silver:
                current_roleid = data['roleid']
                current_silver = dict[data['roleid']]
                result_list = []
                result_list.append([current_roleid, current_silver])
            elif dict[data['roleid']] == current_silver:
                result_list.append([data['roleid'], dict[data['roleid']]])
        print '读取数据成功，返回所需数据'
        mgdb.disconnect()
        return current_roleid, current_silver
    
    
    def get_top_muscle(self, sid):    
        ''' 传入sid得到天龙镖师的对应关系 '''
        datadb, mgdb = self.connectDB(sid, 'role_muscle')
        dict = {}
        for data in datadb.find({'quality':'5', 'capacity':'0'}, 
                                {'muscleid':1, 'name':1}):
            if dict.has_key(data['muscleid']) ==False:
                dict[data['muscleid']] = data['name']
        for key,value in dict.items():
            print key,value
        print '获取天龙镖师字典结束'
        return dict
    
    
    def get_guildid_roleid(self, sid, guildid):    
        ''' 得到镖盟盟主的name '''
        datadb, mgdb = self.connectDB(sid, 'guild_member')
        name = ''
        print '连接数据库成功，开始读取数据'
        for data in datadb.find({'guildid': guildid,'job': '50'}, 
                                {'name':1}):
            name = data['name']
        print '读取数据成功，返回所需数据'
        mgdb.disconnect()
        if name != '':
            return name
        else:
            return ''
    
    
    def get_roleid_task_package(self, sid, date_time):    
        ''' 传入sid和date_time 得到  每个roleid使用任务包的次数 '''
        datadb, mgdb = self.connectDB(sid, 'role_task_package')  
        #获取昨天的日期
        yesterday = datetime.now() - timedelta(days=1)
        if date_time == '':
            date_time = yesterday.strftime('%Y-%m-%d')
        date2 = '%s 24:00:00'%date_time
        dict = {}
        for data in datadb.find({'status':'1', 'create_time':{'$lt':date2}}, 
                                {'roleid':1, 'name':1}):
            if dict.has_key(data['roleid']):
                dict[data['roleid']] += 1
            else:
                dict[data['roleid']] = 1
        return dict
    
    
    def get_roleid_task_packageI(self, sid, date_time):    
        ''' 传入sid和date_time 得到 那些 roleid 使用过'大唐行镖' 这个任务包 返回列表'''
        print '-----------%s server start get_roleid_task_packageI------------'%sid
        roleids = []
        datadb, mgdb = self.connectDB(sid, 'role_task_package')  
        #获取昨天的日期
        yesterday = datetime.now() - timedelta(days=1)
        if date_time == '':
            date_time = yesterday.strftime('%Y-%m-%d')
        date2 = '%s 24:00:00'%date_time
    
        for data in datadb.find({'name':'大唐行镖', 'create_time':{'$lt':date2}}, 
                                {'roleid':1}):
            roleid = data.get('roleid', '')
            if roleid not in roleids:
                roleids.append(roleid)
        
        print '-----------%s server over get_roleid_task_packageI------------'%sid
        return roleids
    
    
    def get_roleid_muscle(self, sid):    
        ''' 传入sid 得到 有结义镖师的roleid，返回roleid列表'''
        roleids = []
        datadb, mgdb = self.connectDB(sid, 'role_muscle')  
    
        for data in datadb.find({'capacity':'2'}, {'roleid':1}):
            roleid = data.get('roleid', '')
            if roleid not in roleids:
                roleids.append(roleid)
            
        return roleids
    
    #任务状态说明
    #TASKSTATUS_IDLE     = '0'  #已刷新，任务未接受
    #TASKSTATUS_UNDONE   = '1'  #进行中，任务已接受但未完成
    #TASKSTATUS_DONE     = '2'  #已完成，任务已完成但未提交
    #TASKSTATUS_SUBMIT   = '3'  #已交付，任务已提交
    #TASKSTATUS_OVERTIME = '9'  #超时失败
    #TASKSTATUS_WAITING  = '99' #等待中，任务未接受（任务包任务未刷新）
    
    TASKS_STATUS = {'0':'已刷新，任务未接受',
                    '1':'进行中，任务已接受但未完成',
                     '2':'已完成，任务已完成但未提交',
                      '3':'已交付，任务已提交',
                       '9':'超时失败',
                        '99':'等待中，任务未接受(任务包任务未刷新)',
                         '':'未接触任务'}
    
    
    def get_role_task_table(self, sid, date_time, task_status = TASKS_STATUS):
        ''' 传入sid 该服务器上roleid 完成第一个成长任务的情况   返回相应dict'''
        print '-----------%s server start get_role_task_table------------'%sid
        
        datadb, mgdb = self.connectDB(sid, 'role_task')
        
        date_time = '%s 24:00:00'%date_time
        dict = {}    
        for data in datadb.find({'taskdbid':'17b5637d-c77e-406f-87e7-b041c52e96ee',
                                  'jointime':{'$lt':date_time}}, 
                                {'roleid':1,'status':1}):
            roleid = data.get('roleid', '')
            status = data.get('status', '')
            
    #        if not dict.has_key(roleid) and status != '':
            if status != '':
                dict[roleid] = status
        
        mgdb.disconnect()     
        print '-----------%s server over get_role_task_table------------'%sid
    
        return dict 
    
    
    def get_guild_name(self, sid):    
        ''' 得到有镖盟的 roleid和相应的guild_name , 返回相应dict'''
        print '-----------%s server start get_guild_name-----------'%sid
        
        guild_dict      = {} 
        datadb, mgdb    = self.connectDB(sid, 'guild') 
    
        for data in datadb.find({'guildname':{'$ne':'新手训练营'}, 'guildid':{'$ne':'0'}}, 
                                {'guildid':1, 'guildname':1}):
            guildid     = data.get('guildid', '')
            guild_name  = data.get('guildname', '')
            if guildid == '' or guild_name == '':
                continue
            guild_dict[guildid] = guild_name
    
        mgdb.disconnect()
        print '-----------%s server over get_guild_name------------'%sid
        
        return guild_dict
    
    
    def get_guild_roleid(self, sid, end_date):    
        ''' 得到有镖盟的 roleid和相应的guild_name , 返回相应dict'''
        print '-----------%s server start get_guild_roleid------------'%sid
        
        role_dict       = {} 
        datadb, mgdb    = self.connectDB(sid, 'guild_member') 
        guildid_name    = get_guild_name(sid) 
        
        i = 0
        end_time = '%s 24:00:00'%end_date    
        for data in datadb.find({'jointime':{'$lt':end_time}, 'guildid':{'$ne':'0'}, 'passed':'2'}, 
                                {'guildid':1, 'roleid':1}):
            roleid      = data.get('roleid', '')
            guildid     = data.get('guildid', '')
    
            if not guildid_name.has_key(guildid):
                continue
            guild_name = guildid_name[guildid]
            
            role_dict[roleid] = guild_name
            i += 1
        
        mgdb.disconnect()
        print '-----------%s server over get_guild_roleid\tsum is %s------------'%(sid, i)
        
        return role_dict
    
    
    FIELDS_LIST = ['function_id','func_name','role_id', 
                    'score', 'func_start_time', 'mod']  
        
    
    def get_role_resident(self, sid, gamelog_dir, fields_list = FIELDS_LIST):    
        ''' 传入sid 从role_resident表中得到小游戏相关的字段，并将获取的字段写入
        role_resident.txt文件中 '''
        datadb, mgdb = self.connectDB(sid, 'role_resident')
        fname = gamelog_dir + '/role_resident.txt'
        fp = open(fname, 'w')
        fp.write('function_id\tfunc_name\trole_id\tscore\tfunc_start_time\tmod\t\n')
        i=0
        yesterday = datetime.now() - timedelta(days=1)
        for data in datadb.find({}, 
                                {'func_name':1,'func_start_time':1, 
                                 'function_id':1, 'mod':1, 
                                 'role_id':1, 'score':1 }):
            if yesterday.strftime('%Y-%m-%d') not in data['func_start_time']:
                continue
            i += 1
            string = ''
            for item in fields_list:
                value = data.get(item, 0)
                fp.write('%s\t'%value) 
            fp.write('\n')
        fp.close()    
        mgdb.disconnect()
        print ('role_resident - item number [%s]'%i)
    
        
    def get_mongo_config(self, sid = '5'):
        """ 根据服务器组id  返回数据库的配置文件   """
        for dict in GameServerList:
            if dict[gkServerID] == sid:
                return dict[gkMongoConfig]
        return {}


    #任务状态说明
    #TASKSTATUS_IDLE     = '0'  #已刷新，任务未接受
    #TASKSTATUS_UNDONE   = '1'  #进行中，任务已接受但未完成
    #TASKSTATUS_DONE     = '2'  #已完成，任务已完成但未提交
    #TASKSTATUS_SUBMIT   = '3'  #已交付，任务已提交
    #TASKSTATUS_OVERTIME = '9'  #超时失败
    #TASKSTATUS_WAITING  = '99' #等待中，任务未接受（任务包任务未刷新）
    #
    #第一个任务      '17b5637d-c77e-406f-87e7-b041c52e96ee'
    #第一次出镖      'c2d90e6e-879e-4942-b365-447b9cc12f1e'
    #开杭州镖局      'e3f69af6-fb60-4639-a2f9-26c0a8641d3b'


    def get_role_task_info(self, sid, roleids, taskids = []):
        ''' 传入sid 返回指定roleid 在指定数据库中  对指定任务的完成情况   '''
        datadb, mgdb = self.connectDB(sid, 'role_task')
        
        dict = {}    
        for data in datadb.find({'roleid':roleid, 'taskdbid':{'$in':task_list}}, 
                                {'roleid':1,'status':1, 'taskdbid':1}):
            tid = data['taskdbid']
            sta = data['status']
            dict[tid] = sta
            
        mgdb.disconnect() 
        return dict
    
    
    FLESH_TASK_LIST = ['17b5637d-c77e-406f-87e7-b041c52e96ee',
                 'da459743-557f-4d34-9f4b-8983c6e8eb79','2d26f1bc-b77a-4a49-937f-b8cbbf38c4a9',
                 '2362c503-2cd6-74a2-b3a6-e469dda59a41','c2d90e6e-879e-4942-b365-447b9cc12f1e',
                 '83e2c56a-363c-4d44-8441-e23ca4ed3bb4','9001bd02-526c-4525-b6cf-7d8b4f9aaf39',
                 '53c7faee-2925-45b0-870f-8109d0fd8f07','e3f69af6-fb60-4639-a2f9-26c0a8641d3b',
                 'b175423b-acdf-48d6-8bb7-7ee63d58d2a7','cfb8a650-8b09-454f-8ec0-eed1c1b55a59',
                 'decae2f4-cb89-1858-f7d3-4d87befa816b']
    
    def write_role_task_info(self, userlog_path, sid):
        ''' 传入sid 返回指定roleid 在指定数据库中  对指定任务的完成情况   '''
        print '写入玩家任务信息开始'
        datadb, mgdb = self.connectDB(sid, 'role_task')
        
        fp  = file('%s/reference/server%s_role_task_info.txt'%(userlog_path, sid), 'w')
        fp.write('roleid\taccepttime\tstatus\ttaskid\t\n')
    
        for data in datadb.find({'taskdbid':{'$in':FLESH_TASK_LIST}}, 
                                {'roleid':1,'status':1, 'taskdbid':1, 'accepttime':1}):
            roleid  = data.get('roleid', '')
            taskid  = data.get('taskdbid', '')
            if roleid == '' or taskid == '':
                continue
            
            fp.write('%s\t%s\t%s\t'%(roleid, data.get('accepttime', ''), taskid, data.get('status', '')))
            
        mgdb.disconnect() 
        fp.close()
        print '写入玩家任务信息结束'
        
    
    def get_role_task_dict(self, sid, roleids, date_time, taskids = [], b_day = '1'):
        ''' 传入sid为服务器的ID编号，
                                当b_day='1'时，返回指定roleid 在指定数据库中 date_time这一天taskids中任务的完成情况
                                当b_day='2'时，返回指定roleid 在指定数据库中 date_time这一天之前taskids中任务的完成情况  
        '''
        datadb, mgdb = self.connectDB(sid, 'role_task')
        
        role_task_dict = {}
        #查找某一天的任务完成情况
        if b_day == '1':
            quiry = {'roleid':{'$in':roleids}, 'taskdbid':{'$in':taskids},
                      'accepttime':{'$gte':'%s 00:00:00'%date_time, '$lte':'%s 23:59:59'%date_time}}
        #查找date_time这一天之前的任务完成情况
        elif b_day == '2':
            quiry = {'roleid':{'$in':roleids}, 'taskdbid':{'$in':taskids},
                      'accepttime':{'$lte':'%s 23:59:59'%date_time}}
        
        for data in datadb.find(quiry,{'roleid':1,'status':1, 'taskdbid':1}):
            roleid  = data.get('roleid', '')
            tid     = data.get('taskdbid', '')
            sta     = data.get('status', '')
            
            if roleid == '' or tid == '' or sta == '':
                continue
            
            if role_task_dict.has_key(roleid):
                role_task_dict[roleid][tid] = sta
            else:
                role_task_dict[roleid] = {tid:sta}
            
        mgdb.disconnect() 
        return role_task_dict
    
    
    def get_tongbao_info(sid, userlog_path):    
        ''' 传入sid 得到该  数据库 所有通宝充值记录 '''
        datadb, mgdb = self.connectDB(sid, 'role_payment')
        
        tongbao_dict = {}
    
        for data in datadb.find({}, {'role_id':1, 'tongbao':1, 'create_time':1}):
            roleid      = data.get('role_id', '') 
            tongbao     = data.get('tongbao', 0)
            create_time = data.get('create_time', '')
            if create_time != '':
                date_time = create_time.split(' ')[0]
            
            if tongbao_dict.has_key(date_time):
                if tongbao_dict[date_time].has_key(roleid):
                    tongbao_dict[date_time][roleid] += tongbao
                else:
                    tongbao_dict[date_time][roleid] = tongbao
            else:
                tongbao_dict[date_time] = {roleid:tongbao}
        
        for date_time, v_dict in tongbao_dict.items():         
            f = file('%s/reference/%s_tongbao.txt'%(userlog_path, date_time), 'w')
            f.write('roleid\ttongbao\t\n')  
            
            for roleid, tongbao in v_dict.items():
                  f.write('%s\t%s\t\n'%(roleid, tongbao))
            f.close()
        
        mgdb.disconnect() 
    
    
    def get_iden_func_ids(self, sid):
        """ 获取名将镖师状态 """
        datadb, mgdb = self.connectDB(sid, 'role_resident')
    #    mgdb = Connection(dbhost, 27423)    
    #    datadb = mgdb['dt_base']['role_resident']
    
        iden_func_ids = {}
        for dataDict in datadb.find({'mod':5}, {'function_id':1, 'func_name':1}):
            func_id = dataDict.get('function_id', 'unknown')
            if func_id == 'unknown':
                continue
    #        commando_dict[muscleid] = {'muscleid':muscleid, 'status':dataDict.get('status', 'unknown')} 
            iden_func_ids[func_id] = dataDict.get('func_name', 'unknown') 
        
        mgdb.disconnect() 
        return iden_func_ids 
    
    
    def getGMRoleids(self, sid):
        """读取roleid_aid.txt，取出aid放入到aid_lists中进行返回"""  
        role_gms    = []  
        datadb, mgdb = self.connectDB(sid, 'role')
    #    mgdb = Connection(dbhost, 27423)    
    #    datadb = mgdb['dt_base']['role_resident']

        for dataDict in datadb.find({'gamemaster':True}, {'roleid':1}):
            roleid = dataDict.get('roleid', '')
            if roleid == '':
                continue
            role_gms.append(roleid) 
        
        mgdb.disconnect()   
        return role_gms

    
    
    def write_roid_aid_info_to_file(self):
        ''' 将roid aid 对应关系  all_aid信息写入文件中 '''
        for [db_config, gamelog_dir, sid] in get_server_mongo_info():
            if sid != '3':
                continue
    
            #获取roleid和aid对应关系
            get_roleid_aidI(sid, gamelog_dir)
                    
            #获取所有aid对应关系
            get_account(sid, gamelog_dir)
    
            #获取item_name对应关系
    #        get_item_name(db_config, gamelog_dir)
            
            #获取小游戏的相关字段(给小游戏排名用的)
    #        get_role_resident(db_config, gamelog_dir)
            print '\n'
    
    
    def get_leitai(self):    
        ''' 传入sid 从role_resident表中得到小游戏相关的字段，并将获取的字段写入
        role_resident.txt文件中 '''
        for [db_config, gamelog_dir, sid] in get_server_mongo_info():
            if sid != '4':
                continue
            datadb, mgdb = connectDB(sid, 'dt_base', 'role_resident')
            fname = gamelog_dir + '/role_resident_leitai.txt'
            fp = open(fname, 'w')
            fp.write('function_id\tfunc_name\tfunc_start_time\tmod\t\n')
            i=0
            yesterday = datetime.now() - timedelta(days=1)
            for data in datadb.find({'func_start_time':{'$gt':'2011-08-19 00:00:00'}}, 
                                    {'func_name':1,'func_start_time':1, 
                                     'function_id':1, 'mod':1}):
                
                string = ''
                for item in ['function_id', 'func_name', 'func_start_time', 'mod']:
                    value = data.get(item, 0)
                    fp.write('%s\t'%value) 
                fp.write('\n')
            fp.close()    
            mgdb.disconnect()


    def getItemName(self):
        """读取item_name.txt文件返回item_name的对应字典"""
        item_names  = {}  
        datadb, mgdb = self.connectDB('3', 'item')
        
        for dataDict in datadb.find({},{'itemsn':1, 'name':1}):
            itemsn  = dataDict.get('itemsn', '')
            name    = dataDict.get('name', '')
            
            if itemsn == '' or name == '':
                continue
            
            item_names[itemsn]  = name
            item_names[name]    = itemsn
        
        return item_names


def HttpMongoQuery(DBInfo, key, value):
    """ 用IP访问远程主机php页面，返回相关的数据库信息, 其中key与value包含多个字段是以‘|’分隔
        DBInfo={'dbhost':'', 'dt_name':'', 'dt_port':0, 'dt_table':''}
    """
    if not DBInfo:
        TheAllText = 'None'
        return TheAllText
    
    dbhost  = DBInfo['dbhost']
    dt_name = DBInfo['dt_name']
    dt_port = DBInfo['dt_port']
    dt_table= DBInfo['dt_table']
#    ParamsKey = Key
#    ParamsValue = Value
   
    '''
    url = 'http://%s/index.php?controller=playerinfo&action=index&database=%s&port=%s&'%(dbhost,dt_name,dt_port)
    url+= 'coll=%s&paramkey=%s&paramvalue=%s'%(dt_table,ParamsKey,ParamsValue)
    logger.info("%s URL:%s!",Today,url)
    '''
    ParamsValueDict = {'paramvalue':change2utf8(value)}
    ParamsValueUrlString = urllib.urlencode(ParamsValueDict)
    url = 'http://%s/index.php?controller=playerinfo&action=index&database=%s&port=%s&'%(dbhost, dt_name, dt_port)
    url+= 'coll=%s&paramkey=%s&'%(dt_table, key)
    url+=  ParamsValueUrlString
    #print url
    #logger.info("%s URL:%s!",Today,url)
    
    #发送http请求，得到返回页面内容
    filehandle = urllib.urlopen(url)
    try:
        TheAllText = filehandle.read()
    finally:
        filehandle.close()
    #TempDict = {object_id:info_dict}
    #print TheAllText
    TempDict = json.loads(TheAllText)
    ReturnDatas  = []
    if isinstance(TempDict, dict):        
        for object_id, info_dict in TempDict.items():
            ReturnDatas.append(info_dict)
    
    return ReturnDatas



if __name__ == '__main__':
    """ 从逻辑数据读取mongo数据库中数据 """
    if 0:
        #获取roleid和aid对应文件，all_aid文件，item_name对应表文件
        write_roid_aid_info_to_file()
    
    
    if 1:
        """获取道具信息"""
        aids = ['cc2d4b83-2592-7663-e57b-f73e5619373a']
        db_process = DBProcess()
        #print db_process.get_plat_roleids('3', aids)
        db_process.get_plat_aids('3')
        
    print 'complete'









