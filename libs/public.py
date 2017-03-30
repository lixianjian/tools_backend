#!/usr/bin/env python2.7
# coding=utf-8
#
#    将一些公用模块放入其中
#
#
#

from datetime import datetime, timedelta, date
from time import strptime, sleep
import time
import json
import zlib
import urllib
import urllib2
import traceback as tb
import codecs

from config import *
from do_sqllite import SqlLite

#import sys
# reload(sys)
# sys.setdefaultencoding('utf-8')

#---------------------------------------------------------------------------
#    判断对象
#---------------------------------------------------------------------------


def objIsEmpty(obj=None):
    '''判断对象为空'''
    return not bool(obj)


def objIsFull(obj=None):
    '''判断对象不为空'''
    return bool(obj)


def objsIsEmpty(objs=None):
    '''判断对象为空'''
    if not isinstance(objs, list):
        objs = [objs]
    for obj in objs:
        if not bool(obj):
            return True
    return False
#---------------------------------------------------------------------------
#    编码
#---------------------------------------------------------------------------


def _2unicode(obj):
    '''将对象转换为UNICODE字符串'''
    if isinstance(obj, unicode):
        return obj
    else:
        return unicode(obj, 'utf-8')


def _2utf8(obj):
    '''将对象转换为UTF-8字符串'''
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    else:
        obj = _2unicode(obj)
        return obj.encode('utf-8')
    return obj


def _struct2unicode(obj):
    """将数据结构转换成unicode编码"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            obj.pop(key)
            key = key.decode('utf-8')
            obj[key] = value

    elif isinstance(obj, list):
        for item in value:
            obj.pop(item)
            item = item.decode('utf-8')
            obj.append(item)

    return obj


def _2ascii(obj):
    '''将对象转换为UNICODE字符串'''
    return obj.decode('gb2312', 'ignore')

#---------------------------------------------------------------------------
#    时间、日期
#---------------------------------------------------------------------------


def getSeconds(first_time, second_time):
    """传入的时间格式为 'h:m:s'，返回值为秒，second_time减去
    first_time, 如果有一个以上参数为空则返回为-1"""
    if first_time == '' or second_time == '':
        return -1
    days = 0
    if ' ' in first_time:
        tmp_date1 = first_time.split(' ')[0]
        first_time = first_time.split(' ')[1]
        tmp_date2 = second_time.split(' ')[0]
        second_time = second_time.split(' ')[1]
        days = getDays(tmp_date1, tmp_date2)

    first_time_list = first_time.split(':')
    second_time_list = second_time.split(':')
    result_seconds = ((int(second_time_list[0]) - int(first_time_list[0])) * 3600 +
                      (int(second_time_list[1]) - int(first_time_list[1])) * 60 +
                      (int(second_time_list[2]) - int(first_time_list[2])) +
                      days * 86400)
    return abs(result_seconds)


def converStrToDate(cstr):
    """   
    Convert str to date   
    cstr parameter must be the str of   
    Return value of the date   
    """
    fdate = None
    try:
        fdate = date(*strptime(cstr, '%Y-%m-%d')[0:3])
    except:
        raise ValueError
    return fdate


def converStrToTime(cstr):
    """   
    Convert str to time   
    cstr parameter must be the str of   
    Return value of the time   
    """
    dtime = None
    try:
        if len(cstr) > 19:
            cstr = cstr[:19]
        dtime = datetime(*strptime(cstr, '%Y-%m-%d %H:%M:%S')[:6])
    except:
        #raise ValueError
        print '%r' % tb.format_exc()
        return None
    return dtime


def getLastDay(pstr, p_days=1):
    """根据传入的字符串，返回前p_days天的时间字符串"""
    date_time = converStrToDate(pstr)
    yesterday = date_time - timedelta(p_days)
    return yesterday.strftime('%Y-%m-%d')


def getNextDay(pstr, p_days=1):
    """根据传入的字符串，返回后p_days天的时间字符串"""
    date_time = converStrToDate(pstr)
    tomorrow = date_time + timedelta(p_days)
    return tomorrow.strftime('%Y-%m-%d')


def getDays(str1, str2):
    """计算str1到str2之间相隔几天"""
    day1 = converStrToDate(str1)
    day2 = converStrToDate(str2)
    p_days = (day2 - day1).days
    return p_days


def getNextMonth(pstr, p_month=1):
    """计算str的后p_month个月，返回时间字符串"""
    date_time = converStrToDate(pstr)
    #next_month = date_time + timedelta(months = p_month)
    month = date_time.month
    year = date_time.year
    month += p_month
    if month > 12:
        month = 1
        year += 1
    return '%d-%02d-01' % (year, month)


def get_prev_month(pstr, p_month=1):
    """计算str的前p_month个月，返回时间字符串"""
    date_time = converStrToDate(pstr)
    #next_month = date_time + timedelta(months = p_month)
    month = date_time.month
    year = date_time.year
    month -= p_month
    if month <= 0:
        month += 12
        year -= 1
    return '%d-%02d-01' % (year, month)


def get_last_hour():
    ''' 返回刚才1个小时的 日期和时间  '''
    today = datetime.today()
    weehours = datetime(
        year=today.year, month=today.month, day=today.day, hour=today.hour)
    onesecond = timedelta(seconds=1)
    lastnight = weehours - onesecond
    return str(lastnight)[:10], str(lastnight)[11:13]


def get_yesterday(dstr=None, days=1):
    ''' 返回前days天日期  '''
    if dstr:
        date_time = converStrToDate(dstr)
    else:
        date_time = datetime.now()
    yesterday = date_time - timedelta(days)
    return yesterday.strftime('%Y-%m-%d')


def get_now2str(has_ms=True):
    """ 获取当前时间的字符串 """
    if has_ms:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')
    else:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def timestamp_datetime(value):
    """ UNIX时间戳转换成日期 """
    frm = '%Y-%m-%d %H:%M:%S'
    # value为传入的值为时间戳(整形)，如：1332888820
    value = time.localtime(value)
    # 经过localtime转换后变成
    ## time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=0)
    # 最后再经过strftime函数转换为正常日期格式。
    dt = time.strftime(frm, value)
    return dt


def datetime_timestamp(dt):
    """ 日期转换成UNIX时间戳 """
    # dt为字符串
#    #中间过程，一般都需要将字符串转化为时间数组
#    time.strptime(dt, '%Y-%m-%d %H:%M:%S,%f')
    # time.struct_time(tm_year=2012, tm_mon=3, tm_mday=28, tm_hour=6, tm_min=53, tm_sec=40, tm_wday=2, tm_yday=88, tm_isdst=-1)
    # 将"2012-03-28 06:53:40"转化为时间戳
    s = time.mktime(time.strptime(dt, '%Y-%m-%d %H:%M:%S.%f'))
    return int(s)

#---------------------------------------------------------------------------
#    其他
#---------------------------------------------------------------------------


def get_server_info(sid, server_info=None):
    """  """
    if not GS_INFO.has_key(sid):
        return {'status': 1, 'tips': 'sid[%s] is not in GS_INFO.' % sid}
    else:
        if objIsEmpty(server_info):
            server_info = GS_INFO[sid]
        spname = '/sea_%s' % sid
        # 日志存放目录
        gamelog_dir = GAMELOG_PATH + spname
        if not _mkdir(gamelog_dir):
            return {'status': 2, 'tips': 'cannot create gamelog_dir[%r].' % gamelog_dir}
        server_info['gl_path'] = gamelog_dir
        # 日志转换后的用户数据
        userlog_dir = USERLOG_PATH + spname
        if not _mkdir(userlog_dir):
            return {'status': 2, 'tips': 'cannot create userlog_dir[%r].' % userlog_dir}
        server_info['ul_path'] = userlog_dir
        # 账号目录
        sea_account = DB_PATH + spname + '/sea_account'
        if not _mkdir(sea_account, ischmod=True):
            return {'status': 2, 'tips': 'cannot create sea_account[%r].' % sea_account}
        server_info['sea_account'] = sea_account
        # 角色目录
        sea_role = DB_PATH + spname + '/sea_role'
        if not _mkdir(sea_role, ischmod=True):
            return {'status': 2, 'tips': 'cannot create sea_role[%r].' % sea_role}
        server_info['sea_role'] = sea_role
        # 玩家充值目录
        sea_pay = DB_PATH + spname + '/sea_pay'
        if not _mkdir(sea_pay, ischmod=True):
            return {'status': 2, 'tips': 'cannot create sea_pay[%r].' % sea_pay}
        server_info['sea_pay'] = sea_pay
        # 角色消耗&获利目录
        cost_earn = DB_PATH + spname + '/cost_earn'
        if not _mkdir(cost_earn, ischmod=True):
            return {'status': 2, 'tips': 'cannot create cost_earn[%r].' % cost_earn}
        server_info['cost_earn'] = cost_earn
        # 角色消耗&获利目录
        payer_area = DB_PATH + '/payer_area'
        if not _mkdir(payer_area, ischmod=True):
            return {'status': 2, 'tips': 'cannot create payer_area[%r].' % payer_area}
        server_info['payer_area'] = payer_area
        # 运营活动数据目录
        activity = ACTIVETY_PATH
        if not _mkdir(activity, ischmod=True):
            return {'status': 2, 'tips': 'cannot create activity[%r].' % activity}
        server_info['activity'] = activity
        # 卡包消耗数据目录
        cardbag = DB_PATH + '/cardbag'
        if not _mkdir(cardbag, ischmod=True):
            return {'status': 2, 'tips': 'cannot create cardbag[%r].' % cardbag}
        server_info['cardbag'] = cardbag
        # 玩家付费数据目录
        payer_count = DB_PATH + spname + '/payer_count'
        if not _mkdir(payer_count, ischmod=True):
            return {'status': 2, 'tips': 'cannot create payer_count[%r].' % payer_count}
        server_info['payer_count'] = payer_count
        # 大付费玩家数据目录
        richman = DB_PATH + '/richman'
        if not _mkdir(richman, ischmod=True):
            return {'status': 2, 'tips': 'cannot create richman[%r].' % richman}
        server_info['richman'] = richman
        # 玩家排行数据目录
        award = DB_PATH + spname + '/award'
        if not _mkdir(award, ischmod=True):
            return {'status': 2, 'tips': 'cannot create award[%r].' % award}
        server_info['award'] = award
        # 烟火消耗数据目录
        fireworks = DB_PATH + '/fireworks'
        if not _mkdir(fireworks, ischmod=True):
            return {'status': 2, 'tips': 'cannot create fireworks[%r].' % fireworks}
        server_info['fireworks'] = fireworks
        # 横向分析数据目录
        horizontal = DB_PATH + '/horizontal'
        if not _mkdir(horizontal, ischmod=True):
            return {'status': 2, 'tips': 'cannot create horizontal[%r].' % horizontal}
        server_info['horizontal'] = horizontal
        # 横向分析数据目录
        jlb_cards = DB_PATH + '/jlb_cards'
        if not _mkdir(jlb_cards, ischmod=True):
            return {'status': 2, 'tips': 'cannot create jlb_cards[%r].' % jlb_cards}
        server_info['jlb_cards'] = jlb_cards
#        #玩家数据数据库
#        sea_base= DB_PATH + spname + '/sea_base.db'
#        if not os.path.exists(sea_base):
#            #return {'status': 6, 'tips': 'database path [%s] is not exist'%(sea_base)}
#            print get_now2str(),'\tdatabase path [%s] is not exist'%(sea_base)
#        server_info['sea_base'] = sea_base
        # 由于sea_data数据是固定数据，所以所有区共用一个数据库
        sea_data = DB_PATH + '/sea_data.db'
        if not os.path.exists(sea_data):
            return {'status': 7, 'tips': 'database path [%s] is not exist' % (sea_data)}
        server_info['sea_data'] = sea_data
        return {'status': 0, 'data': server_info}


def read_json_file(path, is_json=True):
    """ 获取文件中的数据 """
    datas = []
    if os.path.exists(path):
        fhandle = file(path, 'r')
        while True:
            line = fhandle.readline()
            if len(line) == 0:
                break
            if '\n' in line:
                line = line.replace('\n', '')
            if '\r' in line:
                line = line.replace('\r', '')
            if is_json:
                data = json.loads(line)
            else:
                data = line
            datas.append(data)
        #msg = {'status': 0}
        fhandle.close()
    return datas


def write_json_file(path, datas, mod='w', end='', is_json=True):
    """ 向path中写入msg """
    if datas is None:
        print 'datas is None'
        return
    if not isinstance(datas, list):
        datas = [datas]
    #fhandle = file(path, mod)
    #codecs.open(filename, mode, encoding, errors, buffering)
    fhandle = codecs.open(path, mod, 'utf-8')
    for data in datas:
        if is_json:
            fhandle.write(json.dumps(data) + end)
        else:
            fhandle.write(data + end)
    fhandle.close()


def get_dbpath(sid):
    """ 获取某个服务器的db目录 """
    sname = '/sea_%s' % sid
    sea_account = DB_PATH + sname + '/sea_account'
    sea_role = DB_PATH + sname + '/sea_role'
    sea_base = DB_PATH + sname + '/sea_base.db'
    return sea_account, sea_role, sea_base


def is_path_exist(path):
    """ 确定path是否存在，返回bool值 """
    if os.path.exists(path):
        return True
    else:
        return False


def _mkdir(path, ischmod=False, mod=0777):
    ''' 创建目录  '''
    if os.path.isdir(path):
        return True
    else:
        if os.path.exists(path):
            print_str('[%s] is not directory' % path)
            return False
        else:
            try:
                os.makedirs(path)
                if ischmod:
                    os.chmod(path, mod)
                return True
            except:
                print_str('%r' % tb.format_exc())


def find_key(key, value):
    """ 找出datas中的key的所有值 , 如果value是字典返回一个值或None, 
                如果为列表返回一个列表, 否则返回None
    """
    if isinstance(value, dict):
        datas = value.get(key, None)
    elif isinstance(value, list):
        datas = []
        for v in value:
            data = find_key(key, v)
            if data and data not in datas:
                datas.append(data)
    else:
        datas = None
    return datas


def repeats(v1, v2):
    """ v1在v2中重复值,repeat表示返回重复值（非重复值）  """
    repeats = []
    non_repeats = []
    for v in v1:
        if v in v2:
            repeats.append(v)
        else:
            non_repeats.append(v)
    return repeats, non_repeats


def get_date_file(path, sid='2'):
    """ 获取日期索引文件 """
    fnames = []
    start_date = GS_INFO.get(sid, {}).get('start_date', '2012-08-17')
    #start_date  = GAME_OPENTIME
    if len(start_date) > 10:
        start_date = start_date[:10]
    start_date = getLastDay(start_date, p_days=7)
    today = datetime.now().strftime('%Y-%m-%d')
    while True:
        if start_date > today:
            break
        # print 'start_date: ',start_date
        date_path = path + '/' + start_date
        if not os.path.exists(date_path):
            start_date = getNextDay(start_date)
            continue
        fnames.append(date_path)
        start_date = getNextDay(start_date)
    return fnames


def get_from_name(path, k='name', ps=None, fields=None, read_other=False, other_k=None, other_path='', other_fields=None, sid='2'):
    """ 从path中遍历文件获取角色名为name的玩家信息 """
    # ps为要查询的值，将其转换成列表
    if not isinstance(ps, list):
        params = [ps]
    else:
        params = []
        for p in ps:
            if p not in params:
                params.append(p)
    datas = {}
    # 获取path中的日期索引文件
    fnames = get_date_file(path, sid='2')
    for fname in fnames:
        try:
            infos = read_json_file(fname)
            for info in infos:
                v = info.get(k)
                if v not in params:
                    continue
                # 是否要连表查询
                if read_other:
                    other_v = info.get(other_k)
                    datas[v] = {}
                    if other_v is not None:
                        d1 = get_from_fname(
                            path=other_path, fname=other_v, fields=other_fields)
                        datas[v].update(d1.get(other_v))
                else:
                    if fields is None:
                        datas[v] = info
                    else:
                        datas[v] = {}
                        for field in fields:
                            datas[v][field] = info.get(field)
                params.remove(v)
                if not bool(params):
                    break
            if not bool(params):
                break
        except:
            print info, '\t%r' % tb.format_exc()
            continue
    return datas


def get_from_fname(path, fname, fields=None, read_other=False, other_k=None, other_path='', other_fields=None):
    """ 从path中获取keys中玩家信息 """
    if not isinstance(fname, list):
        keys = [fname]
    else:
        keys = fname
    datas = {}
    for k in keys:
        fpath = path + '/' + k
        if not os.path.exists(fpath):
            datas[k] = None
            continue
        data = read_json_file(fpath)[0]
        # 是否要连表查询
        if read_other:
            print 'connect table search'
            other_v = data.get(other_k)
            datas[k] = {}
            if other_v is not None:
                d1 = get_from_fname(
                    path=other_path, fname=other_v, fields=other_fields)
                datas[k].update(d1.get(other_v))
        else:
            print 'not connect table search'
            if fields is None:
                datas[k] = data
            else:
                datas[k] = {}
                for field in fields:
                    datas[k][field] = data.get(field)
    return datas


def get_from_roleid(path, roleid):
    """ 从path中遍历文件获取角色名为name的玩家信息 """
    fname = path + '/' + roleid
    if os.path.exists(fname):
        try:
            return read_json_file(fname)[0]
        except:
            return None


def get_from_roleids(path, roleids):
    """ 从path中遍历文件获取角色名为name的玩家信息 """
    datas = {}
    for roleid in roleids:
        fname = path + '/' + roleid
        if os.path.exists(fname):
            try:
                datas[roleid] = read_json_file(fname)[0]
            except:
                datas[roleid] = {}
        else:
            datas[roleid] = {}
    return datas


def visit_url(url, path=None, download=True, is_json=True, is_compress=False, method='GET', values=None, timeout=20):
    """ 从指定URL获取数据并写入文件path中 """
    # 为了防止访问过快、网站限制访问频度
    sleep(0.1)
    print_str('visit_url: %s' % url)
    if download:
        try:
            # 下载文件到path
            urllib.urlretrieve(url, path)
            msg = {'status': 0}
        except:
            msg = {'status': 1, 'tips': '%r' % tb.format_exc()}
    else:
        try:
            if method == 'GET':
                req = urllib2.Request(url)
                response = urllib2.urlopen(req, timeout=timeout)
            elif method == 'POST':
                data = urllib.urlencode(values)
                #req = urllib2.Request(url,data)
                # print 'data: ',data
                response = urllib2.urlopen(url, data=data, timeout=timeout)
            #req     = urllib2.Request(url)
            #response= urllib2.urlopen(req)
            msg = response.read()
            print_str('msg length:%s' % len(msg))
            print 'msg: ', msg
            if is_compress:
                try:
                    resp_str = zlib.decompress(msg)
                except:
                    resp_str = msg
            else:
                resp_str = msg
            # print 'response msg: ', resp_str
            if is_json:
                msg = json.loads(resp_str)
            else:
                msg = {'status': 0, 'data': resp_str}
        except:
            msg = {'status': 2, 'tips': '%r' % tb.format_exc()}
    return msg


def get_data_from_url(url, ret_field='data', is_compress=False, is_json=True, method='GET', values=None):
    """ 通过访问url获取数据 """
    for i in range(1, 4):
        htmlmsg = visit_url(
            url, download=False, is_compress=is_compress, is_json=is_json, method=method, values=values)
        hstatus = htmlmsg['status']
        if hstatus != 0:
            print 'get data fail, status: %r, tips: %s' % (hstatus, htmlmsg.get('tips'))
            if i > 3:
                return None
            sleep(1)
        else:
            return htmlmsg.get(ret_field)


def ip2area(ip, times=0, data_sql=None):
    """ 通过IP查询所在地信息 """
    ip_info = data_sql.find_one('ip_area', kwargs={'ip': ip})
    if not objIsEmpty(ip_info):
        return ip_info
    url = IP_TBAOBAO_URL + ip
    ret_msg = get_data_from_url(url, ret_field='data', is_json=False)
    if ret_msg is None:
        print 'url [%s] result is none' % url
        return
    else:
        ip_info = json.loads(ret_msg)
        if ip_info['code'] == 0:
            data_sql.insert('ip_area', [ip_info['data']])
            data_sql.commit('ip_area')
            return ip_info['data']
        else:
            print 'visit url [%s] fail. ret_msg %s'(url, ret_msg)
            times += 1
            if times < 3:
                ip2area(ip, times)
            else:
                return


def tb2rmbI(tb, pay_time=None):
    """ 通宝转换成RMB """
    tongbao = int(tb)
    if bool(pay_time) and pay_time > '2012-08-10 18:00:00':
        rmb = tongbao * 1.0 / TB2RMB
    else:
        if pay_time == '' or tongbao < 220:
            rmb = tongbao * 1.0 / TB2RMB
        elif tongbao == 220:
            rmb = 20.0
        elif tongbao > 220:
            rmb = tongbao * 1.0 / 1.2 / TB2RMB
    return rmb


def tb2rmb(tb, pay_time=None):
    """ 通宝转换成RMB """
    tongbao = int(tb)
    if tongbao < 0.00001:
        return 0.0
    else:
        rmb = tongbao * 1.0 / TB2RMB
        return rmb


def read_payment(ppath, ps_date, pe_date, roleids=None):
    """ 读取充值记录 """
    start_date = ps_date
    end_date = pe_date
    fnames = []
    while True:
        if start_date > end_date:
            break
        path = ppath + '/pay_' + start_date + '.log'
        print 'path: ', path
        if os.path.exists(path):
            fnames.append(path)
        start_date = getNextDay(start_date)
    datas = []
    tids = []
    for fname in fnames:
        print 'fname: ', fname
        log_strs = read_file_list(fname)
        for log_str in log_strs:
            if len(log_str) < 4:
                print log_str
                continue
            if bool(roleids) and log_str[1] not in roleids:
                continue
            param = json.loads(log_str[3])
            tid = param.get('tid')
            if tid in tids:
                continue
            tids.append(tid)
            param['create_time'] = log_str[0]
            param['roleid'] = log_str[1]
            if objIsEmpty(log_str[2]):
                param['cmd'] = 'top_up'
            else:
                param['cmd'] = log_str[2]
            datas.append(param)
    return datas


def get_pay_recordI(sid, ps_date=None, pe_date=None):
    """ 获取付费玩家记录 """
    #SEA_BASE    = ROUTER_SEABASE[0][0]
    sea_account, sea_role, sea_base = get_dbpath(sid)
    if not os.path.exists(sea_base):
        return
    sql = SqlLite(sea_base)
    sql.conn = sql.force_conn()
    if sql.conn is None:
        print 'connect db fail.'
        return

    if ps_date is None:
        # 查找所有记录
        condition = None
    elif pe_date is None:
        # 查找ps_date当天的记录
        condition = "create_time >= '%s 00:00:00' and create_time <= '%s 23:59:59'" % (
            ps_date, ps_date)
    else:
        # 查找ps_date到pe_date期间的记录
        condition = "create_time >= '%s 00:00:00' and create_time <= '%s 23:59:59'" % (
            ps_date, pe_date)
    # 付费表中字段[role_id][aid][username][tongbao][tid][time][create_time]
    payments = sql.find('role_payment', condition, DEFAULT_PAY_FIELDSS)
    sql.disconnect()
    return payments


def get_pay_record(sid, ps_date=None, pe_date=None, ppath=None, roleids=None):
    """ 获取付费玩家记录 """
    print 'get_pay_record'
#    if sid in ['1']:
#        return get_pay_recordI(sid,ps_date, pe_date)
#    else:
    if ps_date is None:
        # 查找所有记录
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        start_date = yesterday
        end_date = yesterday
    elif pe_date is None:
        # 查找ps_date当天的记录
        start_date = ps_date
        end_date = ps_date
    else:
        # 查找ps_date到pe_date期间的记录
        start_date = ps_date
        end_date = pe_date
    # 付费表中字段[role_id][aid][username][tongbao][tid][time][create_time]
    print 'start_date, end_date', start_date, end_date
    if ppath is None:
        ppath = DB_PATH + '/sea_' + sid + '/sea_pay'
    payments = read_payment(ppath, start_date, end_date, roleids=roleids)
    return payments


def get_person_count(records, k='roleid', roleids=None, pstart_time='2012-08-27 00:00:00', pend_time='2113-03-08 24:00:00'):
    """ 获取玩家的充值金额 """
    datas = {}
    for record in records:
        v = record.get(k)
        tongbao = record.get('tongbao', 0)
        create_time = record.get('create_time')
        if v is None or create_time is None:  # or tongbao == 0
            print 'error record ', record
            continue
        if create_time < pstart_time or create_time > pend_time:
            continue
        rmb = tb2rmb(tongbao, create_time)
        if datas.has_key(v):
            datas[v] += rmb
        else:
            datas[v] = rmb
    return datas


def get_person_countI(records, k='roleid', roleids=None, pcmd=None):
    """ 获取玩家的充值金额,充值命令限制 """
    datas = {}
    for roleid, infos in records.items():
        for cmd, info in infos.items():
            if pcmd is not None and pcmd != cmd:
                continue
            if not datas.has_key(cmd):
                datas[cmd] = {}
            v = info.get(k)
            if v is None:
                print 'error record ', info
                continue
            tongbao = info.get('pre_sum', 0) + info.get('day', 0)
            rmb = tb2rmb(tongbao)
            if datas[cmd].has_key(v):
                datas[cmd][v] += rmb
            else:
                datas[cmd][v] = rmb
    return datas


def get_person_countII(records, k='roleid', roleids=None, pcmd=None, min_count=0, max_count=100000000):
    """ 获取玩家的充值金币,范围限制 """
    datas = {}
    for roleid, infos in records.items():
        for cmd, info in infos.items():
            if pcmd is not None and pcmd != cmd:
                continue
            if not datas.has_key(cmd):
                datas[cmd] = {}
            info['roleid'] = roleid
            v = info.get(k)
            if v is None:
                print 'error record ', info
                continue
            count = info.get('pre_sum', 0) + info.get('day', 0)
            if count < min_count or count > max_count:
                continue
            datas[cmd][v] = info
    return datas


def get_person_countIII(records, k='roleid', roleids=None, pcmd=None, min_count=0, max_count=100000000, pts=['day']):
    """ 获取玩家的充值金币,范围限制&充值时间限制 """
    datas = {}
    for roleid, infos in records.items():
        for cmd, info in infos.items():
            if pcmd is not None and pcmd != cmd:
                continue
            if not datas.has_key(cmd):
                datas[cmd] = {}
            info['roleid'] = roleid
            v = info.get(k)
            if v is None:
                print 'error record ', info
                continue
            tongbao = 0
            for pt in pts:
                tongbao += info.get(pt, 0)
            if tongbao < min_count or tongbao > max_count:
                continue
            info['tongbao'] = tongbao
            info['rmb'] = tb2rmb(tongbao)
            datas[cmd][v] = info
    return datas


def get_person_countIIII(records, pcmd=None, pts=['day']):
    """ 获取玩家的充值金币 """
    datas = 0
    for infos in records.values():
        for cmd, info in infos.items():
            if pcmd is not None and pcmd != cmd:
                continue
            tongbao = 0
            for pt in pts:
                tongbao += info.get(pt, 0)
            if tongbao < 1:
                continue
            datas += tongbao
    return datas


def get_person_countIIIII(records, target='tongbao'):
    """ 获取玩家的充值金币 """
    if target == 'tongbao':
        tongbao = 0
        for record in records:
            tongbao += record.get('tongbao')
        return tongbao
    elif target == 'role':
        roles = []
        for record in records:
            roleid = record.get('roleid')
            if roleid not in roles:
                roles.append(roleid)
        return len(roles)


def get_person_countVI(records, k='roleid', roleids=None, pstart_time='2012-08-27 00:00:00', pend_time='2113-03-08 24:00:00'):
    """ 获取玩家的充值金币 """
    datas = {}
    for record in records:
        v = record.get(k)
        tongbao = record.get('tongbao', 0)
        create_time = record.get('create_time')
        if v is None or create_time is None:  # or tongbao == 0
            print 'error record ', record
            continue
        if create_time < pstart_time or create_time > pend_time:
            continue
        if datas.has_key(v):
            datas[v] += tongbao
        else:
            datas[v] = tongbao
    return datas


def get_person_single_pay(records, k='roleid', roleids=None, min_count=1000, pstart_time='2012-08-25 00:00:00', pend_time='2023-03-03 24:00:00'):
    """ 获取玩家的单笔充值游戏币 """
    datas = {}
    for record in records:
        v = record.get(k)
        tongbao = record.get('tongbao', 0)
        create_time = record.get('create_time')
        if v is None or create_time is None:
            print 'error record ', record
            continue
        if tongbao < min_count or create_time < pstart_time or create_time > pend_time:
            continue
        count = tongbao / min_count
        if datas.has_key(v):
            datas[v] += count
        else:
            datas[v] = count
    return datas


def merge_dict(d1, d2, add_str=True):
    """ 合并字典,d1是目标字典,d2是源字典 """
    for k, v in d2.items():
        if d1.has_key(k):
            if isinstance(v, dict):
                d1[k] = merge_dict(d1[k], v)
            elif isinstance(v, list):
                for i in v:
                    if i not in d1[k]:
                        d1[k].append(i)
            elif isinstance(v, int) or isinstance(v, float) or add_str:
                d1[k] += v
        else:
            d1[k] = v
    return d1


def get_field_index(fname, fields=[]):
    """根据传入的字符串，获得其在文件行中对应的索引值，返回为字段与索引值对应的字典"""
    field_index = {}
    # 打开fname文件
    f = file(fname, 'r')
    line = f.readline()
    splits = line.split('\t')
    if '\n' in splits[-1]:
        splits[-1] = splits[-1][:-1]

    for field in fields:
        field_index[field] = splits.index(field)

    f.close()
    return field_index


def read_file_list(fname, findexs=None, lines=None, keep_first=True):
    """读取文件，返回需要字段的列表，fname为文件名，后跟上需要的字段
    findexs为索引列表"""
    if lines is None:
        lines = []
    f = file(fname, 'r')
    # 略去第一行
    if not keep_first:
        f.readline()
    while True:
        line = f.readline()
        if len(line) == 0:
            break
        if line == '\n':
            continue
        # 将读出来的字符串分解
        splits = line.split('\t')
        # 去除最后一个字段中的\n
        if '\n' in splits[-1]:
            splits[-1] = splits[-1][0:-1]

        if findexs is None:
            lines.append(splits)
        else:
            ftmps = []
            for findex in findexs:
                ftmps.append(splits[findex - 1])
            lines.append(ftmps)
    f.close()
    return lines


def list2dict(objs, findexs):
    """根据传入的field返回包含该findexs的字典
    obj_list的格式为[[],[]...]，返回字典格式为
    {obj_list_item(field_index):obj_list_item,...}"""
    # 返回字典
    result_dict = {}
#    #获取需要字段的所以列表
#    findexs = getFieldIndex(fname, *fields)
#    #获取需要的字段列表
#    obj_list = readFile(fname, field_list)
    for obj in objs:
        for index in findexs:
            if result_dict.has_key(obj[index]):
                result_dict[obj[index]].append(obj)
            else:
                result_dict[obj[index]] = [obj]

    return result_dict


def get_special_values(fname, index_value, itargets, keep_first=True):
    """ 获取指定字段和值的itarget字段值列表， fname为文件名 """
    target_list = []
    lines = read_file_list(fname, keep_first=keep_first)
    for line in lines:
        splits = line.split('\t')
        # 默认是满足条件的
        btmp = True
        for index, value in index_value.items():
            # 假如有一个条件不满足，则立即退出
            if splits[index - 1] != value:
                btmp = False
                break
        if btmp:
            ftmps = []
            for itarget in itargets:
                ftmps.append(splits[itarget - 1])
            target_list.append(ftmps)
    return target_list


def read_file_dict(fname, fields=[], datas=[], keep_first=True):
    """ 读取文件，返回字典 """
    # 由于没有拿到定义，所以先自己预设一个
    time_index = 0
    roleid_index = 1
    param_index = 2

    f = file(fname, 'r')
    # 略去第一行
    if not keep_first:
        line = f.readline()
        # 将读出来的字符串分解
        splits = line.split('\t')
        # 去除最后一个字段中的\n
        if '\n' in splits[-1]:
            splits[-1] = splits[-1][0:-1]
        fields = splits
    elif not fields:
        print 'while the parameter keeep_first is True, the parameter fields can not be null.'
        return datas

    while True:
        line = f.readline()
        if len(line) == 0:
            break
        # 将读出来的字符串分解
        splits = line.split('\t')
        # 去除最后一个字段中的\n
        if '\n' in splits[-1]:
            splits[-1] = splits[-1][0:-1]

        indexs = len(fields) - 1
        data = {}
        for index in range(indexs):
            data[fields[index]] = splits[index]
        datas.append(data)

    f.close()
    return datas


def getSpecialModeFieldDict(fname, mode, mode_index, obj_index, key):
    """获取指定状态的字段，fname为文件名，返回一个字典
    mode为要返回数据的类型（'0'为新用户,'1'为老用户,'2'为所有用户）"""
    result_dict = {}
    if not is_path_exist(fname):
        return result_dict

    fcurrent = file(fname, 'r')
    while True:
        line = fcurrent.readline()
        if len(line) == 0:
            break
        if line == '\n':
            continue
        list_mid = line.rstrip('\n').split('\t')
#        #去除最后一个字段中的\n
#        if '\n' in list_mid[-1]:
#            list_mid[-1] = list_mid[-1][0:-1]

        if list_mid[mode_index - 1] == mode or mode == '2':
            result_dict[list_mid[key - 1]] = list_mid[obj_index - 1]

    fcurrent.close()
    return result_dict


def readIndexDict(fname, result_dict, indexs, keys):
    """读取fname文件，取出indexs中的索引，放入到result_dict中进行返回
    result_dict格式为{key:[[field1, field2, ...], []...], ...}"""
    f = file(fname, 'r')
    while True:
        line = f.readline()
        if len(line) == 0:
            break
        if line == '\n':
            continue
        # 去除最后一个字段中的\n,将读出来的字符串分解
        splits = line.rstrip('\n').split('\t')
#        if '\n' in splits[-1]:
#            splits[-1] = splits[-1][0:-1]

        tmp_list = []
        for index in indexs:
            if index == -1:
                tmp_list = splits
                break
            # 为了确保后面在引用该数据时不会出现越界异常
            if index > len(splits):
                tmp_list.append('')
                continue
            tmp_list.append(splits[index - 1])

        for key in keys:
            if result_dict.has_key(splits[key - 1]):
                result_dict[splits[key - 1]].append(tmp_list)
            else:
                result_dict[splits[key - 1]] = [tmp_list]
    f.close()
    return result_dict


def get_log_files(src_path, date_time, hour='', run_hour=True, run_hours=None):
    """ 获取src_path中的所有文件列表 """
    fnames = []
    # 指定某一个小时的日志文件
    if run_hour:
        fname = '%s/%s/%s/game_%s_%s.log' % (src_path,
                                             date_time, hour, date_time, hour)
        if os.path.exists(fname):
            fnames.append(fname)
        else:
            #public.writeLog('file[%s] is not exists.'%fname)
            print 'file[%s] is not exists.' % fname
    # 获取改天所有的日志文件
    else:
        for i in range(0, 24):
            if i < 10:
                hour = '0%s' % i
            else:
                hour = i
            fname = '%s/%s/%s/game_%s_%s.log' % (
                src_path, date_time, hour, date_time, hour)
            if os.path.exists(fname):
                fnames.append(fname)
            else:
                print 'file[%s] is not exists.' % fname
                continue

    return fnames


def get_log_filesI(src_path, date_time, hour=None, run_hours=None, run_hour=True):
    """ 获取src_path中的所有文件列表 """
    fnames = []
    # 指定某一个小时的日志文件
    hours = []
    for i in range(0, 24):
        if run_hour:
            if i < run_hours[0] or i > run_hours[1]:
                continue
        if i < 10:
            hour = '0%s' % i
        else:
            hour = i
        hours.append(hour)
    for hour in hours:
        fname = '%s/%s/%s/game_%s_%s.log' % (src_path,
                                             date_time, hour, date_time, hour)
        if os.path.exists(fname):
            fnames.append(fname)
        else:
            #public.writeLog('file[%s] is not exists.'%fname)
            print 'file[%s] is not exists.' % fname

    return fnames


def writeLog(pstr, fname=None):
    """ 打开日志文件 """
    if fname == None:
        fname = ('./log.txt')

    try:
        myFile = open(fname, 'a')
    except:
        print ("不可以打开日志文件: %s ") % fname

    log = ('%s\t%s \n') % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), pstr)
    myFile.write(log)

    myFile.flush()  # 清空文件I/O buffer，将日志直接写入磁盘
    myFile.close()


def serverlist2dict():
    """"""
    # print GS_INFO
    datas = ['#!/usr/bin/python2.7\n#coding=utf-8\nGS_INFO = {\n']
    for sid, info in GS_INFO.items():
        tmp_str = "%r: {" % sid
        for k, v in info.items():
            if k == 'name':
                tmp_str += "%r:u'%s'," % (k, v)
            else:
                if k == 'plat_info':
                    tmp_str += "%r:%s," % (k, v)
                else:
                    tmp_str += "%r:%r," % (k, v)
        tmp_str += "},\n"
        datas.append(tmp_str)
    datas.append('}\n')
    result_path = './serverlist2dict.py'
    write_json_file(result_path, datas, mod='w', end='', is_json=False)
    print result_path


def judge_internalip(ip):
    """ 判断是否为公司内网IP """
    if '127.0.0.1' == ip or '10.23.1.' in ip:
        return True
    msg = visit_url(
        LAN_IP_URL, download=False, is_json=False, is_compress=False)
    print 'msg: ', msg
    if msg['status'] == 0:
        company_ip = msg['data']
        print 'ip:', ip
        if company_ip == ip:
            return True
        else:
            return False
    else:
        return False


def print_str(*msgs):
    print get_now2str(has_ms=True), '\t'.join(msgs)


def reduce_spec_sign(msg):
    """ 去掉特殊符号 """
    # 去掉前后的空格
#    if msg.startswith(' '):
#        msg = msg[1:]
#    if msg.endswith(' '):
#        msg = msg[:-1]
#    #(' ', ''),
    return reduce(lambda r, x: r.replace(x[0], x[1]), [('\n', ''), ('\r', '')], msg.strip())


def paging(page=1, count=0, sep_count=10, is_reverse=False):
    """ 分页 """
    if (count % sep_count):
        end_page = count / sep_count + 1
    else:
        end_page = count / sep_count
    # 传入页数超出范围
    if page >= end_page:
        page = end_page
        next_page = page
    else:
        next_page = page + 1
    if page <= 1:
        pre_page = 1
        down_range = 0
    else:
        pre_page = page - 1
        down_range = pre_page * sep_count
    up_range = page * sep_count
    if up_range > count:
        up_range = count
    ret_msg = {'page': page, 'pre_page': pre_page, 'next_page': next_page, 'end_page': end_page,
               'count': count, 'sep_count': sep_count}
    if is_reverse:
        ret_msg['down_range'] = count - up_range
        ret_msg['up_range'] = count - down_range
    else:
        ret_msg['down_range'] = down_range
        ret_msg['up_range'] = up_range
    return ret_msg


def create_mailid():
    """ 生成一个mailid """
    # 用UNIX时间戳做邮件ID
    mailid = ('%s' % time.time()).replace('.', '')
    print 'mailid:\t', mailid
    time.sleep(0.1)
    return mailid


def req_param_rstrip(pstr):
    """ 页面请求参数去\r\n后缀 """
    if objIsEmpty(pstr):
        return ''
    return pstr.strip().rstrip('\r').rstrip('\n')


def underline2hump(s1, s_char='_'):
    """ 将字符串(两个单词之间用'_'分隔)中的第index个字母转成大写 """
    s2 = ''
    for s3 in s1.split(s_char):
        s2 += s3[0].upper() + s3[1:]
    return s2

if __name__ == '__main__':

    SERVER_NAME = {'3': 'qidian2', '4': 'qidian3', '5': '2144'}

    if False:
        l1 = [1, 34]
        l2 = [1, 341]
        print l1 == l2
        s1 = ' dsda  '
        print req_param_rstrip(s1)
        print s1
        # print globals().has_key('getSeconds')

    if False:
        cfd = os.path.abspath(os.path.dirname(__file__))
        print 'cfd: ', cfd
        db_path = cfd + '/../../facebook.db'
        print 'db_path: ', db_path

    if False:
        for server in SERVERS:
            if server['is_cross']:
                print server['name']

    if False:
        print_str('---------- start')
#        #写数据
#        datas   = {}
#        for i in range(0,100000):
#            datas['3657346925D34254F1E0417DF40BD902%s'%i]   = '255.255.255.255'
#        accounts= write_json_file('d:/account_ip.txt',datas)
#        2013-03-19 12:00:03,080000 ---------- start
#        2013-03-19 12:00:03,284000 ---------- end
#        #读数据
#        read_json_file('d:/account_ip.txt')
#        2013-03-19 12:01:59,545000 ---------- start
#        2013-03-19 12:01:59,850000 ---------- end

#        #写数据
#        datas   = {}
#        info= {"country":"\u4e2d\u56fd","country_id":"CN","area":"\u534e\u5357","area_id":"800000","region":"\u5e7f\u4e1c\u7701",
#               "region_id":"440000","city":"\u6df1\u5733\u5e02","city_id":"440300","county":"","county_id":"-1","isp":"\u7535\u4fe1",
#               "isp_id":"100017","ip":"116.25.211.89"}
#        for i in range(0,100000):
#            datas['255.255.255.%s'%i]   = info
#        accounts= write_json_file('d:/ip_area_data.txt',datas)
#        2013-03-19 12:07:49,273000 ---------- start
#        2013-03-19 12:07:50,729000 ---------- end
#        #读数据
#        read_json_file('d:/ip_area_data.txt')
#        2013-03-19 12:08:24,544000 ---------- start
#        2013-03-19 12:08:27,460000 ---------- end

#        db_path = 'd:/ip_area_data.db'
#        sql     = SqlLite(db_path)
#        sql.conn= sql.force_conn()
#        if  sql.conn is None:
#            print 'connect db fail.'
#        else:
#            #写数据
#            datas   = []
#            info= {"country":"\u4e2d\u56fd","country_id":"CN","area":"\u534e\u5357","area_id":"800000","region":"\u5e7f\u4e1c\u7701",
#                   "region_id":"440000","city":"\u6df1\u5733\u5e02","city_id":"440300","county":"","county_id":"-1","isp":"\u7535\u4fe1",
#                   "isp_id":"100017","ip":"116.25.211.89"}
#            for i in range(0,100000):
#                data= {'ip':'255.255.255.%s'%i}
#                data.update(info)
#                datas.append(data)
#            sql.insert('ip_area',datas)
#            sql.commit('ip_area')
#            2013-03-19 12:27:40,891000 ---------- start
#            begin to connect to 'd:/ip_area_data.db'
#            d:/ip_area_data.db is connected done
#            ip_area(100000) is inserted done
#            ip_area id committed done
#            2013-03-19 12:27:45,257000 ---------- end
#
#            #读数据
#            infos   = sql.find('ip_area')
#            datas   = {}
#            for info in infos:
#                datas[info['ip']]   = info
#
#        sql.disconnect()
        print_str('---------- end')

    if False:
        #        print get_now2str()
        print datetime_timestamp('2014-10-10 10:00:00.068')
        # print datetime_timestamp('2013-01-23 23:59:59')
        #s = timestamp_datetime(1364751033)
        # print s
        # print urllib.quote(json.dumps(['2be9a3eb-5fd8-46cc-9c3e-b2ff657b6ed8']))
        #url = 'http://221.dhh.darkhutgame.net:8008/index.php?controller=online_data&action=send_mailI&roles=%5B%222be9a3eb-5fd8-46cc-9c3e-b2ff657b6ed8%22%5D&tag=name&mail_id=1362732257&mail_info=%7B%22content%22%3A%20%22test%22%2C%20%22text%22%3A%20%22test%22%2C%20%22money%22%3A%205000%7D'
        #url = 'http://s12001.dhh.darkhutgame.com:8008/index.php?controller=online_data&action=hello'
        # print visit_url(url, download=False, is_json=False, is_compress=False)
        #print_str('visit_url over : %s'%url)
#        url = 'http://s8013.dhh.darkhutgame.com:8008/index.php?controller=online_data&action=%(func)s&qualitys=%(qualitys)s&num=%(num)s'% \
#               {'func':'captain_info','qualitys': json.dumps([4,5]),'num': 4}
#        infos   = get_data_from_url(url, ret_field='data', is_compress=True, method='GET')
#        for d in infos:
#            #"username": "aikennn", "roleid": "9d6ea87c-b824-495c-92be-4b2bfb301056", "num": 5, "name": "\u82cd\u4e91\u6708\u821e"}
#            print '%(username)s\t%(roleid)s\t%(num)s\t%(name)s'%d

#        import socket
#        socket.setdefaulttimeout(1)
#        print socket.getdefaulttimeout()
#        timeout = object()
#        print timeout.getdefaulttimeout()
#        print help(timeout)

    if 0:
        #'%(sname)s\t%(rankname)s\t%(order)s\t%(rolename)s\t%(roleid)\t%(money)s\t%(items)s\t%(success)s\t%(mailid)s\n'
        #{'sname': u'\u6d4b\u8bd5\u670d', 'success': '', u'money': 11014571, 'rankname': u'\u94f6\u5e01\u6392\u540d',
        # u'roleid': u'4ed5f396-703b-4af9-8ed2-5b1470a083aa', 'mailid': '135960420507', u'rolename': u'jean',
        #'items': '[{"count": 10, "itemsn": 41019, "name": "3\\u9636\\u6750\\u6599\\u5b9d\\u7bb1"}]', u'order': 1}
        content = '%(sname)s\t%(rankname)s\t%(order)s\t%(rolename)s\t%(roleid)\t'
        record = {'sname': u'\u6d4b\u8bd5\u670d', 'rankname': u'\u94f6\u5e01\u6392\u540d', u'order': 1, u'rolename': u'jean',
                  u'roleid': u'4ed5f396-703b-4af9-8ed2-5b1470a083aa', }
        print content % record

    if 0:
        _mkdir('/tmp/testchmod', ischmod=True)
        # print paging(page=1000,count=12,sep_count=5,is_reverse=True)

    if 0:
        from test import ips
        datas = []
        for ip in ips:
            data = ip2area(ip)
            datas.append('%s\t%s\t%s\t%s' % (
                data['country'], data['area'], data['region'], data['city']))
        for data in datas:
            print data
#        for k,v in ip2area(ips[0]).items():
#            print k,v
        # print
        # get_from_name('D:/check_data/db/sea/sea_11/sea_role',k='name',ps=u'大兵爱流汗',fields=['name','roleid'])

    if 0:
        serverlist2dict()

    if 0:
        #        from do_sqllite import SqlLite
        #        sql = SqlLite(R'D:\Jean\program\support\sea\analyze\sea_backstage\sea_backstage.db')
        #        sql.conn    = sql.force_conn()
        #        infos   = []
        for sid in GS_INFO:
            # infos.append(info)
            print sid
#            sql.insert('handle_gameserverinfo',info)
#        sql.commit('handle_gameserverinfo')
#        sql.disconnect()

    if 0:
        d1 = {'c1': {'count': 2, 'roles': ['1', '3']}}
        d2 = {'c1': {'count': 3, 'roles': ['1', '4']}, 'c2': {
            'count': 3, 'roles': ['1', '3']}}
        merge_dict(d1, d2)
        print d1

    if 0:
        print getDays('2011-06-17', '2011-11-15')

    if 0:
        # print getDays('2011-11-08', '2011-12-08')
        # print _mkdir('d:/test/test/')
        # print find_key('test', 'ds')
        # v1  = []    #1, 3, 5, 9
        # v2  = []    #4, 3, 2, 5
        # print repeats(v1, v2)
        # write_json_file('d:/test.py', {'test': 1, 'test1': 2})
        # print tb2rmb(100)
        datas = read_json_file(R'D:\5ca9a3df-770f-427e-9e29-38e805b8c732')
        print datas[0].get('name', 'un')
        for k, v in datas[0].items():
            print '%s\t%s' % (k, v)

    if True:
        #        now = datetime.now()
        #        dtime = converStrToTime('2012-11-26 10:45:09')
        #        print '%s-%s-%s'%(dtime.year,dtime.month,dtime.day)
        #        print dtime.weekday()
        #        print now.weekday()
        #        print dtime
        #
        # 返回前days天日期
        print converStrToDate('2015-03-09')
        print get_yesterday(days=1)

    print 'complete'
