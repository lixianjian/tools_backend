#!/usr/bin/env python2.7
#coding=utf-8
'''
Created on 2012-3-22

@author: lixianjian
'''

from lazyjson import lazy_to_json


class DataRuler():
    '''读取和转化excel表格式为程序可以使用的数据格式'''
    def try_to_float(self,value):
        try:
            return float(value)
        except:
            return None

    def try_to_int(self,value):
        try:
            return int(value)
        except:
            return None

    def parse(self,cell_value):
        '''
        检查开始的第一个字符,如果为[ or { 使用lazyjson读取
        试着寻找小数点.符号,如果找到试着转化为浮点数
        试着转化为整形数字,如果失败就识别为字符串
        '''
        if cell_value == '':
            return ''
        token = cell_value[0]
        if token in ['[','{']:
            pass
            #return lazy_to_json(cell_value)
        elif cell_value.lower() in ['true','false']:
            return cell_value.lower() == 'true'
        else:
            if '.' in cell_value:
                value = self.try_to_float(cell_value)
                if value is not None:
                    return value
            else:
                value = self.try_to_int(cell_value)
                if value is not None:
                    return value

        #return str(cell_value)
        return cell_value


def transform(table_data):
    dr = DataRuler()
    for t in table_data:
        #transform data
        for x in t: 
            #t[x] = dr.parse(str(t[x]))
            if t[x] == None:
                cell_value = ''
            elif isinstance(t[x], basestring):
                cell_value = t[x]
            else:
                cell_value = str(t[x])
            t[x] = dr.parse(cell_value)
    return table_data


if __name__ == '__main__':
    
    dr  = DataRuler()
    print dr.parse('[[12,3,4,54,56],[3,243,545,532,56]]')
    
    print 'complete'
