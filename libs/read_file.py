#!/usr/bin/env python2.7
#coding=utf-8

'''
读取文件，包括xls, xlsx, txt等

Created on 2012-3-22

@author: lixianjian
'''


from openpyxl.reader.excel import load_workbook
import xlrd
import types
import re

#from lazyjson import lazy_to_json
from parse import DataRuler

COMMENT_CHAR = ';'
TABLE_CHAR = '#'
H_TABLE_FLAG = 'h'
V_TABLE_FLAG = 'v'


def _2utf8(obj):
    '''将对象转换为UTF-8字符串'''
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    return obj


def _2unicode(obj):
    '''将对象转换为UNICODE字符串'''
    if isinstance(obj, unicode):
        return obj
    else:
        return unicode(obj, 'utf-8')


class ExReader():
    def __init__(self,excel_file_name, operation='db'):
        self.book       = load_workbook(filename = excel_file_name)
        self.operation  = operation
    
    def process_h_table(self,table_data, sheet_name):
        '''
        读取横向表的内容,table_data 是包括第一行在内的列表*列表((第一行),(第二行))
        返回结果为[{key1:value1,key2:value2...},{...}]每一个字典代表一行数据
        '''
        result = []
        keys = []
        current_logic_table = {}
        dr = DataRuler()
        #get keys and width
        line = table_data[0]
        for cell in line:
            if cell.value != None:
                keys.append(str(_2utf8(cell.value)))#key must be string
        width = len(keys)
        for i in xrange(1,len(table_data)):
            current_logic_table = {}
            line = table_data[i]
            for j in xrange(width):
                v_str   = line[j].value
#                if v_str == None:
#                    value = ''
#                else:
#                    if type(v_str) not in [types.IntType, types.FloatType] and v_str[0] in ['[','{']:
#                        value = lazy_to_json(v_str)
#                        if value == None:
#                            value = v_str
#                    else:
#                        value = v_str
##                    value = lazy_to_json(v_str)
##                    if value == None:
##                        value = v_str
                if v_str == None:
                    cell_value = ''
                elif isinstance(v_str, basestring):
                    cell_value = v_str
                else:
                    cell_value = str(v_str)
                #current_logic_table[keys[j]] = dr.parse(cell_value)
                
                if self.operation == 'db': 
#                    #为近海配置路径
#                    if (sheet_name == 'scene') and (keys[j] == 'config'):
#                        current_logic_table['path'] = scene_config_path_db(cell_value)
#                    #为近海配置城市间航线
#                    elif (sheet_name == 'scene') and (keys[j] == 'campid'):
#                        current_logic_table['lane'], current_logic_table['laneNoCost'] = scene_config_lane(cell_value)
#                        current_logic_table[keys[j]] = dr.parse(cell_value)
#                    elif cell_value == '':
                    if cell_value == '':
                        current_logic_table[keys[j]] = None
                    else:
                        current_logic_table[keys[j]] = dr.parse(cell_value)
                else:
#                    if sheet_name in ['city'] and keys[j] in ['is_main']:
#                        print cell_value
                    current_logic_table[keys[j]] = dr.parse(cell_value)
                
            result.append(current_logic_table)                        
        return result
 
    def process_v_table(self,table_data):
        '''@todo: implement vertical table parse
        '''
        result = []
                  
        return result       
        
    def save_table_list(self,table_list,table_flag,result_list, sheet_name=''):
        if len(table_list) > 1:
            if table_flag == H_TABLE_FLAG:
                tmp = self.process_h_table(table_list, sheet_name)
            else:
                tmp = self.process_v_table(table_list, sheet_name)
            result_list.append(tmp)

        
    def read_tables(self):
        '''读取核心内容,跳过注释,读取多表,返回sheet列表,以sheet名字为key,每个sheet内容为逻辑表的列表,从上到下
        {sheetname:[logicsheet1,logicsheet2...],sheetname2:[..]}
        logicsheet 结构:
        [{key1:value1,key2:value2},{}]
        key取值与第一行数据的值,value取值于每一行对应的值,每一行数据就是一个字典
        '''
        result = {}
        for sheet_name in self.book.get_sheet_names():
            sheet = self.book.get_sheet_by_name(sheet_name)
            result[sheet.title] = []
            table = sheet.range(sheet.calculate_dimension())#读取table
            table_list = []
            table_flag = H_TABLE_FLAG
            for line in table:#去掉注释,分割table,读取数据表内容
                str_cell_val = None
                if isinstance(line[0].value,unicode) :
                    str_cell_val = line[0].value.encode('utf-8')
                #guild_main表中第1项为镖盟初始化的人数上限，line[0].value=0；
                #如果只用not bool(line[0].value)判断条件，则会把第1项滤掉
                #if not bool(line[0].value) and (line[0].value != 0):
                if line[0].value is None:
                    continue #skip empty 
                if isinstance(str_cell_val, basestring) and (len(str_cell_val)>0) and (str_cell_val[0]==COMMENT_CHAR):
                    continue #skip the comment line
                if isinstance(str_cell_val, basestring) and (len(str_cell_val)>0) and (str_cell_val[0]==TABLE_CHAR):
                    self.save_table_list(table_list, table_flag,result[sheet.title])  #save old data and begin a new logic table       
                    if len(str_cell_val) > 1:
                        table_flag = str_cell_val[1].lower()
                    else:
                        table_flag = H_TABLE_FLAG
                    table_list = []
                    continue #skip the table tag line
                table_list.append(line)
            #the last line of table
            self.save_table_list(table_list, table_flag,result[sheet.title], sheet_name)
        return result
        


def cacheBadwords(filepath=''):
    '''缓冲政治敏感字
    filepath: 政治敏感字路径名
    '''
    lBadwords = []
    dExist = {}

    try:
        fread = open(filepath, 'r')
        lines = fread.readlines()
        for line in lines:
            #分割字符串
            fields = re.split(r'\s', line)
            word = fields[0]
            if bool(word) and not word.isspace() and (word not in dExist):
                lBadwords.append(word)
                dExist[word] = True

        fread.close()
    except Exception, e:
        print 'cacheBadwords has error:\t', e

    return lBadwords #return plain string list


#---------------------------------------------------------------------------
#   盛大游戏屏蔽词列表
#---------------------------------------------------------------------------

#工作表可见行
(
    SYS_SHEET_VISIBLE,     #visible
    SYS_SHEET_HIDDEN,      #hidden (can be unhidden by user -- Format/Sheet/Unhide)
    SYS_SHEET_VERY_HIDDEN, #"very hidden" (can be unhidden only by VBA macro)
) = range(3)

IDX_SHEET_FROM = 0 #有效开始工作表
IDX_COL_FROM   = 2 #有效开始列
IDX_ROW_FROM   = 2 #有效开始行

class XlsReaderSNDA:
    '''Reader .xls'''
    def __init__(self, filename):
        '''初始化'''
        try:
            self.filename = filename
            self.book = xlrd.open_workbook(self.filename)
        except Exception, e:
            print 'XlsReaderSNDA has error:\t', e

    def load(self):
        '''导入'''
        lRet = []
        dExist = {}
        try:
            #遍历工作表
            for sheetx in range(IDX_SHEET_FROM, self.book.nsheets):
                sheet = self.book.sheet_by_index(sheetx)

                #只取可见的工作表
                if sheet.visibility != SYS_SHEET_VISIBLE:
                    continue

                #遍历列，从第三列开始（列号从2开始）
                for col in range(IDX_COL_FROM, sheet.ncols):
                    #遍历行，从第三行开始（行号从2开始）
                    for row in range(IDX_ROW_FROM, sheet.nrows):
                        cells = sheet.row(row)
                        cell_value = cells[col]
                        strings = cell_value.value
                        #分割字符串
                        for uMark in [u'、', u'，', ',']:
                            utf8Mark = _2utf8(uMark)
                            strings = strings.replace(uMark, '\n') #2012最新屏蔽词库
                        fields = strings.split('\n')
                        for field in fields:
                            if bool(field) and not field.isspace() and (field not in dExist):
                                lRet.append(field)
                                dExist[field] = True

        except Exception, e:
            print 'XlsReaderSNDA has error:\t', e
        return lRet


def cacheBadwords_snda(filepath=''):
    '''盛大游戏屏蔽词列表, filepath: 盛大游戏屏蔽词路径名 '''
    lBadwords = []
    try:
        #读.xls文件
        lBadwords = XlsReaderSNDA(filepath).load()
    except Exception, e:
        print 'cacheBadwords_snda has error:\t', e

    return lBadwords #return unicode string list


#---------------------------------------------------------------------------
#   创建角色的屏蔽字附表
#---------------------------------------------------------------------------

class XlsReaderRole:
    '''Reader .xls'''
    def __init__(self, filename):
        '''初始化'''
        try:
            try:
                self.filename = _2unicode(filename)
            except Exception, e:
                print 'XlsReaderRole has error:\t', e
                self.filename = filename

            self.book = xlrd.open_workbook(self.filename)

        except Exception, e:
            print 'XlsReaderRole has error:\t', e

    def load(self):
        '''导入'''
        lRet = []
        dExist = {}
        try:
            #遍历工作表
            for sheetx in range(IDX_SHEET_FROM, self.book.nsheets):
                sheet = self.book.sheet_by_index(sheetx)

                #只取可见的工作表
                if sheet.visibility != SYS_SHEET_VISIBLE:
                    continue

                #遍历行
                for row in range(sheet.nrows):
                    cells = sheet.row(row)
                    for cell_value in cells:
                        if cell_value.ctype != xlrd.XL_CELL_TEXT:
                            continue
                        field = cell_value.value
                        if bool(field) and not field.isspace() and (field not in dExist):
                            lRet.append(field)
                            dExist[field] = True

        except Exception, e:
            print 'XlsReaderRole has error:\t', e

        return lRet

def cacheBadwords_role(filepath=''):
    '''创建角色的屏蔽字附表
    filepath: 创建角色的屏蔽字路径名
    '''
    lBadwords = []
    try:
        #读.xls文件
        lBadwords = XlsReaderRole(filepath).load()
    except Exception, e:
        print 'cacheBadwords_role has error:\t', e
    return lBadwords #return unicode string list


def scene_config_path(config):
    '''为近海配置路径'''
    import os, json
    try:
        from config import DATA_PATH
        data_path = os.path.join(DATA_PATH, config)
        rfile = open(data_path, 'r+b')
        scene_path = rfile.read()
        rfile.close()
        #scene_path = json.loads(buff)
    except Exception,e:
        scene_path = None
        print 'scene_config_path has error: ', e
    return scene_path

def scene_config_path_db(config):
    '''为近海配置路径'''
    import json

    buff = scene_config_path(config)
    if bool(buff):
        scene_path = json.loads(buff)
    else:
        scene_path = []
    return scene_path

def scene_config_lane(campid):
    '''为近海配置城市间航线'''
    import json

    lane = {}
    laneNoCost = {}

    try:
        from config import LANEDATA_FILE
        rfile = open(LANEDATA_FILE, 'r+b')
        buff = rfile.read()
        rfile.close()

        camp2lane = json.loads(buff)

        if isinstance(camp2lane, dict):
            data = camp2lane.get(str(campid))
            if isinstance(data, dict):
                lane       = data.get('lane', {})
                laneNoCost = data.get('laneNoCost', {})
    except:
        pass
    return lane, laneNoCost


if __name__ == "__main__":
    
#    ex = ExReader('D:/check_data/sea_data/params.xlsx', 'swf')
#    ex.read_tables()
#    badwords      = cacheBadwords(BADWORDS_FILE)
#    print badwords
    result = scene_config_path('pathdata.txt')
    print result
    
    print 'complete'
