#!/usr/bin/python2.7
#coding=utf-8
'''
Created on 2013-8-9

@author: lixianjian
'''

from django.template import RequestContext
from django.http import HttpResponse,HttpResponseForbidden,HttpResponseServerError
#from django.http import HttpResponseNotFound
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import csrf_exempt
#from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.forms.models import model_to_dict
from south.db import db
from django.db import connection
from django.db import models

import urllib
import os
import sys
import json
from datetime import timedelta
#import re
import traceback as tb
#import uuid
import subprocess
import shlex
import psutil
import time
import csv
import copy

#from settings import MEDIA_ROOT
from libs import public
from libs.config import glocale,DEBUG,PER_PAGE,ASSETS_URL,PARAM_DEBUG_PATH,BASE_AUTO_ADD_FIELD,AUTO_ADD_FIELD2,PROGRAM_PATH,BS_DB_NAME
from libs.register import login,alter,logout
from libs.read_file import ExReader
from libs.do_sqllite import SqlLite
from models import *

reload(sys)
sys.setdefaultencoding('utf-8')

#静态数据
const_data  = {'glocale': glocale,
               'assets_url': ASSETS_URL,
               }

#主模板目录
INDEX_PAGE  = 'main.html'
#登陆页面路径
LOGIN_PAGE  = 'login/login_page.html'
#参数表模板
PARAM_HTML_PATH = 'parameters'
#数字正则式
NUMBER_STR  ='\d{1,9}'
#时间正则表达式，如：2012-07-26 17:22:22
TIME_RE_STR ='\d{4}-\d{2}-\d{2}\s{1}\d{2}:\d{2}:\d{2}'
#日期正则表达式，如：2012-07-26
DATE_RE_STR ='\d{4}-\d{2}-\d{2}'
#浮点正则表达式
FLOAT_STR   = '(\d+)(\.\d+)'

def create_db_table(record,model_class,suffix=''):
    """ Takes a Django model class and create a database table, if necessary.
    """
    # XXX Create related tables for ManyToMany etc
    db.start_transaction()
    table_name = model_class._meta.db_table
    if suffix:
        table_name  += suffix
    # Introspect the database to see if it doesn't already exist
    if (connection.introspection.table_name_converter(table_name) not in connection.introspection.table_names()):
        fields  = [(f.name, f.get_django_field()) for f in record.fields.all()]
        if DEBUG:
            print fields
        db.create_table(table_name, fields)
        # Some fields are added differently, after table creation
        # eg GeoDjango fields
        db.execute_deferred_sql()
        print "Created table '%s'" % table_name
    db.commit_transaction()

def delete_db_table(model_class):
    table_name = model_class._meta.db_table
    db.start_transaction()
    db.delete_table(table_name)
    print "Deleted table '%s'" % table_name
    db.commit_transaction()

def add_db_table_column(model_class, field_name, field):
    table_name = model_class._meta.db_table
    db.start_transaction()
    #db.delete_table(table_name)
    db.add_column(table_name, field_name, field)
    print "table '%s' add colum %s" %(table_name, field_name)
    db.commit_transaction()

def alter_db_table_column(model_class, field_name, field):
    print 'in alter_db_table_column'
    table_name = model_class._meta.db_table
    db.start_transaction()
    db.alter_column(table_name, field_name, field)
    print "table '%s' alter colum %s" %(table_name, field_name)
    db.commit_transaction()

def delete_db_table_column(model_class, field_name, field_type):
    table_name = model_class._meta.db_table
    db.start_transaction()
    if field_type == 'ForeignKey':
        db.delete_foreign_key(table_name, field_name)
    elif field_type == 'AutoField':
        db.delete_primary_key(table_name)
    else:
        db.delete_column(table_name, field_name)
    print "table '%s' delete colum %s" %(table_name, field_name)
    db.commit_transaction()

def rename_db_table_column(model_class, field_name, new_name, field_type=''):
    table_name = model_class._meta.db_table
    db.start_transaction()
    db.rename_column(table_name, field_name, new_name)
    if field_type == 'ForeignKey':
        #db.rename_column(table_name, field_name+'_id', new_name+'_id')
        db.add_column(table_name, new_name+'_id', models.IntegerField(verbose_name=new_name+'_id',blank=True,null=True))
    db.commit_transaction()
    print "table '%s' rename colum %s to %s" %(table_name, field_name, new_name)

def get_contact(obj,**kwargs):
    """ 获取obj的记录 """
    try:
        contact = obj.objects.get(**kwargs)
    except obj.DoesNotExist:
        contact = {}
    return contact

def get_sheets(program=None,locale=None):
    """ 获取参数表 """
    sheets  = {}
    for sheet in Sheet.objects.filter(program=program,locale=locale):
        sys_markid  = sheet.sys_model.markid
        sys_markid2 = sheet.sys_model2.markid
        if sheets.has_key(sys_markid):
            if sheets[sys_markid]['sub_sheets'].has_key(sys_markid2):
                sheets[sys_markid]['sub_sheets'][sys_markid2]['sub_sheets2'].append(sheet)
            else:
                sheets[sys_markid]['sub_sheets'][sys_markid2]   = {'sys_model2': sheet.sys_model2, 'sub_sheets2': [sheet]}
        else:
            sheets[sys_markid]  = {'sys_model': sheet.sys_model, 'sub_sheets':{sys_markid2:{'sys_model2': sheet.sys_model2, 'sub_sheets2': [sheet]}}}
    #print sheets
    return sheets.values()

def some_view(data, output_name='excel_data'):
    """"""
    response = HttpResponse(mimetype='text/csv')
    response.write('\xEF\xBB\xBF')
    response['Content-Disposition'] = 'attachment; filename=%s.csv'%output_name
    writer = csv.writer(response)
    print 'make csv'
    for row in data:
        out_row = []
        for value in row:
            if not isinstance(value, basestring):
                value   = unicode(value)
            if value is None:
                value   = ''
            out_row.append(value.replace('"', '""'))
        writer.writerow(out_row)
    return response

def entrance(request):
    """ 入口 """
    if DEBUG:
        print 'HTTP_HOST:',request.META['HTTP_HOST']
        public.print_str('entrance')
        public.print_str('------- request.user: %s'%request.user)
        public.print_str('------- request.user.username: %s'%request.user.username)
    if request.user.is_authenticated():
        return choose_param(request)
    if request.method == 'GET':
        pre_path= request.get_full_path()
        content = {'form_action':'/login/','glocale': glocale,'pre_path': pre_path}
        content.update(csrf(request))
        return render_to_response(LOGIN_PAGE,content)
    elif request.method == 'POST':
        pre_path= request.POST.get('pre_path')
        msg = login(request)
        if msg.get('status',1) == 0:
            if not request.user.has_perm('auth.view_web'):
                logout(request)
                return HttpResponseForbidden()
            if pre_path is not None:
                return HttpResponseRedirect(pre_path)
            return choose_param(request)
        else:
            content = {'tips': msg.get('tips',glocale.LN_UID_NAME_ERROR),'form_action':'/login/',
                       'glocale': glocale,'pre_path': pre_path}
            page_path   = LOGIN_PAGE
            content.update(csrf(request))
            return render_to_response(page_path,content,context_instance=RequestContext(request))
    else:
        return HttpResponseServerError()
        
def quity(request):
    """ 出口 """
    logout(request)
    return entrance(request)

def alter_password(request):
    """ 修改密码 """
    #req_msg = get_request_data(request)
    content = {'data_title': glocale.LN_ALTER_PASSWORD,
               'form_action':'/alter_password/',}
    if request.method == 'GET':
        content.update({'html_path':'login/alter.html'})
        #return render_to_response(INDEX_PAGE,content,context_instance=RequestContext(request))
    elif request.method == 'POST':
        msg = alter(request)
        if msg.get('status',1) == 0:
            content.update({'tips': msg.get('tips',glocale.LN_CHOOSE_FUNC_IN_LEFT_FRAME),'html_path':'login/alter.html'})
        else:
            content.update({'tips': msg.get('tips',glocale.LN_FAIL),'html_path':'login/alter.html'})
    else:
        return HttpResponseServerError()
    content.update(const_data)
    content.update(csrf(request))
    return render_to_response(INDEX_PAGE,content,context_instance=RequestContext(request))

def choose_param(request,tips=''):
    """ 选择游戏项目 """
    if request.method == 'POST':
        req_msg = request.POST
    else:
        req_msg = request.GET
    pid  = req_msg.get('programid')
    localeid= req_msg.get('localeid')
    if public.objIsFull(pid) and public.objIsFull(localeid):
        try:
            program = Program.objects.get(markid=pid)
        except Program.DoesNotExist:
            program = None
        try:
            locale  = Locale.objects.get(markid=localeid)
        except Locale.DoesNotExist:
            locale  = None
        try:
            prog_loc_user   = ProgramLocaleUser.objects.get(program=program.id,locale=locale.id,user=request.user.id)
        except ProgramLocaleUser.DoesNotExist:
            prog_loc_user   = None
        content = {'program': program, 'locale': locale,'sheets': get_sheets(program=program.id,locale=locale.id), 'prog_loc_user': prog_loc_user}
        content.update(csrf(request))
        return render_to_response(INDEX_PAGE, content,context_instance=RequestContext(request))
    else:
        objs= ProgramLocaleUser.objects.filter(user=request.user.id)
        if public.objIsEmpty(objs):
            content = {'tips':tips+u'抱歉，目前没有项目，请先添加','form_action':'choose_param'}
        else:
            content = {'programs': objs,'form_action':'choose_param'}
        content.update(csrf(request))
        return render_to_response('parameters/choose_program.html',content,context_instance=RequestContext(request))

@csrf_exempt
def param_main_response(request,pid=None,localeid=None,sheetid=None):
    """ 响应入口 """
    print 'HTTP_HOST:',request.META['HTTP_HOST']
    program = get_contact(Program,markid=pid)
    locale  = get_contact(Locale,markid=localeid)
    if sheetid == 'model':
        sheet   = {'name':'model','intro': '参数表'}
    elif sheetid == 'formula':
        sheet   = {'name':'formula','intro': '公式表'}
    elif sheetid == 'charting':
        sheet   = {'name':'charting','intro': '绘制图表'}
    elif sheetid == 'import_excel':
        table   = request.POST.get('table','')
        sheet   = get_contact(Sheet,name=table)
    else:
        print 'do parameter sheet:',sheetid
        sheet   = get_contact(Sheet,name=sheetid)
    prog_loc_user   = get_contact(ProgramLocaleUser,program=program.id,locale=locale.id,user=request.user.id)
    info= {'program': program, 'locale': locale,'sheets': get_sheets(program=program.id,locale=locale.id),'sheet': sheet, 'prog_loc_user': prog_loc_user}
#    print info['sheets']
    reqmode = request.GET.get('reqmode')
    view_all= request.GET.get('view_all','0') == '1'
    #调用相关功能模块进行处理
    obj = ParamMain(request,program,locale,sheetid,reqmode,view_all)
    if bool(sheetid) and (bool(sheet) or hasattr(obj,sheetid)):
        if reqmode not in ['js']:
            obj.content.update(info)
        if hasattr(obj,sheetid):
            getattr(obj, sheetid)()
        else:
            obj.do_sheet()
            if obj.export_csv:
                #return ExcelResponse(obj.csv_datas,obj.csv_name)
                return some_view(obj.csv_datas,obj.csv_name)
        content = obj.content
        #载入页面
        if sheetid in ['model','protobufdata','restart','formula','reset_data','charting']:
            content['html_path']= PARAM_HTML_PATH+'/'+sheetid+'.html'
        elif sheetid == 'client_edit':
            return render_to_response('parameters/client_edit.html',content)
        else:
            content['html_path']= PARAM_HTML_PATH+'/parameters.html'
        if DEBUG:
            public.print_str('html_path: %s'%content['html_path'])
        #content['sheets']   = Sheets.objects.all()
    else:
        content = {'html_path': PARAM_HTML_PATH+'/right_default.html',
                   'data_title': glocale.LN_CHOOSE_FUNC_IN_LEFT_FRAME,
                   }
        content.update(info)
    if reqmode == 'js':
#        if DEBUG:
#            print '--------- content: ',content
        do_what = content.get('do_what')
        for k in content.keys():
            if k not in ['do_what','datas','tips','ret','msg']:
                content.pop(k)
            if k == 'datas':
                if do_what not in ['get','add']:
#                    content['datas']= json.dumps(content['datas'])
#                else:
                    del content['datas']
#        if content.has_key('datas'):
#            if content.get('do_what') == 'get':
#                content['datas']= json.dumps(content['datas'])
#            else:
#                del content['datas']
        return HttpResponse(json.dumps(content))
    else:
        content.update(const_data)
        content.update(csrf(request))
        return render_to_response(INDEX_PAGE,content,context_instance=RequestContext(request))

class ParamMain():
    
    def __init__(self,request,program,locale,sheetid,reqmode,view_all):
        self.request= request
        self.req_method = 'GET'
        #self.pid    = pid
        self.program= program
        self.pname  = program.name
        #self.localeid   = localeid
        self.locale = locale
        self.localename = locale.name
        self.sheetid= sheetid
        self.sheetname  = sheetid
        self.reqmode= reqmode
        #显示所有记录
        self.view_all   = view_all
        #参数表字段
        self.pkeys  = []
        #参数表字段名
        self.pvalues= []
        self.content= {}
        self.yesterday  = (datetime.datetime.now() - timedelta(days = 1)).strftime('%Y-%m-%d')
        self.today  = datetime.datetime.today().strftime('%Y-%m-%d')
        #当前操作的数据表对象
        self.sheet_obj  = None
        #数据表参数
        self.achieves= {}
        #数据表传入参数中控参数
        self.empties= []
        #是否显示全屏flash
        self.full_screen_swf= False
        self.full_screen_swf_name   = ''
        #卡片类型
        self.card_type  = 0
        #页面错误提示
        self.tips   = ''
        #查询条件
        self.filter_kwargs  = {}
        #记录ID
        self.recordid   = 0
        #文字类型
        self.text_type  = 0
        #导出EXCEL
        self.export_csv = False
        #EXCEL文件名
        self.csv_name   = 'anonymous'
        #EXCEL数据
        self.csv_datas  = []
        #表包含的字段数据
        self.fields = []
        #字段参数
        self.fields_settings= []
        #动态表在参数表中的实例
        self.dyn_model  = None
        #模板内容
        self.temp_html  = ''
        #模板内容2，表单或者表格之外的内容
        self.temp_html2 = ''
        #操作类型
        self.do_what    = 'get'
        #外键字典
        self.foreign_keys   = {}
#        #多对多字典
#        self.manytomanys= {}
        #排序字段
        self.order  = ''
        #是否有SN字段
        self.has_sn = False
        
    def alter_password(self):
        """ 修改密码 """
        self.sheetname  = glocale.LN_ALTER_PASSWORD
        if self.request.method == 'GET':
            pass
        elif self.request.method == 'POST':
            msg = alter(self.request)
            if msg.get('status',1) == 0:
                self.content.update({'tips': msg.get('tips',glocale.LN_CHOOSE_FUNC_IN_LEFT_FRAME)})
            else:
                self.content.update({'tips': msg.get('tips',glocale.LN_FAIL)})
        else:
            return HttpResponseServerError()
    
    def do_data(self):
        """ 处理数据库表 """
        datas   = {}
        errors  = []
        for sheet in Sheet.objects.filter(program=self.program.id, is_proto=True, deleted=False):
#            if sheet.name != 'bigtpye2smalltype':
#                continue
            print 'sheet.name: ',sheet.name
            err1 = '表[%s(%s)中'%(sheet.intro,sheet.name)
            datas[sheet.name]   = []
            dyn_obj = sheet.get_django_model()
            #多对多中对象
            to_objs = {}
            fields  = Field2.objects.filter(model=sheet.id)
            for f in fields:
#                if f.name == 'small_type':
#                    print f.name
                if f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
#                    if sheet.name == 'trade_road':
#                        print 'field',model_to_dict(f) 
                    try:
                        to_sheet= Sheet.objects.get(program=self.program.id, name=f.to, deleted=False)
                    except Sheet.DoesNotExist:
                        public.print_str('ManyToManyField sheet [%s] does not exist'%f.to)
                    else:
                        #于2014-07-02 11:52修改，一对多改成JS填写方式
#                        to_objs[f.name] = {'display': to_sheet.display, 'to_obj': to_sheet.get_django_model()}
#                        for f2 in to_sheet.fields.all():
#                            if f2.to == sheet.name:
#                                to_objs[f.name]['key']  = f2.name
                        to_objs[f.name] = to_sheet.get_django_model()
                elif f.type.name == 'ManyForeignsField':
                    to_objs[f.name] = []
                    to_objs2 = []
                    for to in json.loads(f.to):
                        try:
                            to_sheet= Sheet.objects.get(program=self.program.id, name=to, deleted=False)
                        except Sheet.DoesNotExist:
                            public.print_str('ManyForeignsField sheet [%s] does not exist'%to)
                            errors.append(err1+'多外键字段[%s(%s)]不存在对应外键表[%s]'%(f.intro,f.name,to))
                        else:
                            to_objs2.append(to_sheet.get_django_model())
                    to_objs[f.name] = to_objs2
            for record in dyn_obj.objects.filter(deleted=False):
                v1  = {}
                for f in fields:
                    t1  = f.type.name
                    name= f.name
                    if name in AUTO_ADD_FIELD2:
                        continue
                    if sheet.name == 'ship' and record.id == 8 and name == 'trans':
                        #print model_to_dict(record)
                        print 'break' 
                    v2  = getattr(record,name)
                    if name == 'id':
                        name = 'primary_id'
                    if v2 is None:
                        if t1 in ['IntegerField', 'BigIntegerField']:
                            v2  = 0
                        elif t1 == 'FloatField':
                            v2  = 0.0
                        elif t1 == 'BooleanField':
                            v2  = False
                        elif t1 in ['CharField','ImageField','TextField']:
                            v2  = ''
                        elif t1 == 'ForeignKey':
                            v2  = 0
                            #record2 = model_to_dict(record) 
                            #errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record2.get(f.name,'')))
#                            errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record.__getattribute__(f.name)))
                        elif t1 in ['ManyToManyField','DictArray','RepM2MField']:
                            v2  = []
                        elif t1 == 'ManyForeignsField':
                            v2  = 0
                    elif t1 == 'ForeignKey':
#                        if v2 is None:
#                            v1[name]= 0
#                            record2 = model_to_dict(record) 
#                            errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record2.get(f.name,'')))
#                        else:
                        if v2.deleted:
                            record2 = model_to_dict(record) 
                            errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record2.get(f.name,'')))
#                            errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record.__getattribute__(f.name)))
                        elif f.to_field:
                            v2  = getattr(v2,f.to_field,0)
                            if isinstance(v2,unicode) and v2.startswith('[') and v2.endswith(']'):
                                to_sheet= Sheet.objects.get(program=self.program.id, name=f.to, deleted=False)
                                to_field2   = Field2.objects.get(model=to_sheet.id,name=f.to_field)
                                if to_field2.type.name == 'DictArray':
                                    try:
                                        to_sheet3   = Sheet.objects.get(program=self.program.id, name=to_field2.to, deleted=False)
                                    except Sheet.DoesNotExist:
                                        errors.append('外键中的字典数组找不到数据:'+f.intro+f.name+'  '+f.to+'  '+f.to_field+' %s'%to_field2.to)
                                        v2  = []
                                    else:
                                        if to_objs.has_key(to_field2.to):
                                            to_obj  = to_objs[to_field2.to]
                                        else:
                                            to_obj  = to_sheet3.get_django_model()
                                            to_objs[to_field2.to]   = to_obj
                                        v3  = []
                                        for _id in json.loads(v2):
                                            try:
                                                v4  = to_obj.objects.get(id=_id,deleted=False)
                                            except to_obj.DoesNotExist:
                                                errors.append(err1+'记录[%s]字典数组字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,_id))
                                            else:
                                                v3.append(model_to_dict(v4,exclude=BASE_AUTO_ADD_FIELD))
                                        v2  = v3
                        else:
                            v2  = getattr(v2,'sn',0)
                            #v1[name]= model_to_dict(v2,exclude=BASE_AUTO_ADD_FIELD)
                    elif t1 in ['ManyToManyField','RepM2MField']:
#                        if v2 is None:
#                            v2  = []
#                        else:
#                            #于2014-07-02 11:52修改，一对多改成JS填写方式
#                            #多对多中间表对象
#                            if to_objs.has_key(name):
#                                v2  = [getattr(v3,to_objs[name]['display']).sn for v3 in to_objs[name]['to_obj'].objects.filter(**{to_objs[name]['key']: record.id,'deleted': False})]
#                            else:
#                                v2  = []
                        #多对多中间表对象
                        if to_objs.has_key(name):
                            if DEBUG:
                                print '------------',sheet.name, record.id, name, v2
                            #v1[name]= [getattr(v3,f.to_field) for v3 in to_objs[name].objects.filter(id__in=json.loads(v2),deleted=False)]
                            to_obj  = to_objs[name]
                            v3  = []
                            for _id in json.loads(v2):
                                try:
                                    v4  = to_obj.objects.get(id=_id,deleted=False)
                                except to_obj.DoesNotExist:
                                    #v3.append(_id)
                                    errors.append(err1+'记录[%s]多对多字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,_id))
                                else:
                                    if f.to_field:
                                        v3.append(getattr(v4,f.to_field,_id))
                                    else:
                                        v3.append(getattr(v4,'sn',_id))
                            v2  = v3
                            #print 'sheet.name: ',sheet.name,'v2',v2,'v3',v3
                        else:
                            v2  = []
                    elif t1 == 'DictArray':
                        #字典数组
                        if not to_objs.has_key(name):
                            v2  = []
                        else:
                            if DEBUG:
                                print '------------',sheet.name, record.id, name, v2
                            to_obj  = to_objs[name]
                            v3  = []
                            for _id in json.loads(v2):
                                try:
                                    v4  = to_obj.objects.get(id=_id,deleted=False)
                                except to_obj.DoesNotExist:
                                    errors.append(err1+'记录[%s]字典数组字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,_id))
                                else:
                                    to_sheet= Sheet.objects.get(program=self.program.id, name=f.to, deleted=False)
                                    up  = {}
                                    for f2 in Field2.objects.filter(model=to_sheet.id):
                                        if f2.type.name == 'ForeignKey':
                                            to_field = f2.to_field
                                            if not to_field:
                                                to_field = 'sn'
                                            up[f2.name] = v4.__getattribute__(f2.name).__getattribute__(to_field)
                                    v5  = model_to_dict(v4,exclude=BASE_AUTO_ADD_FIELD)
                                    v5.update(up)
                                    v3.append(v5)
                            v2  = v3
                    elif t1 in ['JSONChar', 'OddsField']:
                        #JSON格式
                        if v2:
                            try:
                                v2  = json.loads(v2)
                            except:
                                if DEBUG:
                                    print sheet.name, record.id, name, v2
                                v2  = []
                        else:
                            v2  = []
                    elif t1 == 'ManyForeignsField':
                        #多对多中间表对象
                        if to_objs.has_key(name):
                            if DEBUG:
                                print '------------',sheet.name, record.id, name, v2
                            v3  = None
                            for to_obj in to_objs[name]:
                                try:
                                    v3  = to_obj.objects.get(sn=v2,deleted=False)
                                except to_obj.DoesNotExist:
                                    pass
                                else:
                                    break
                            if v3 is None:
                                errors.append(err1+'记录[%s]多外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,v2))
                    v1[name]= v2
                datas[sheet.name].append(v1)
        #本文件所在上层目录
#        pfd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#        path= os.path.join(pfd,self.program.markid+'/db.txt')
#        print 'path: ',path
#        public.write_json_file(path, datas)
        print 'errors:',errors
        if not errors:
            pfd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path= os.path.join(pfd,self.program.markid+'/db.txt')
            print 'path: ',path
            public.write_json_file(path, datas)
        return errors
            #return datas
#                print 'type(record):',type(record)
#                print "type(record._meta.fields): ",type(record._meta.fields)
#                for f in record._meta.fields:
#                    print "%s=%s"%(f.name, getattr(record,f.name))
#                    print 'type(f): ',type(f)
#                    print 'help(f): ',help(f)
#                for k,v in record.iterator():
#                    print k,v
    
    def protobufdata(self):
        """ 生成服务器、客户端数据，protobuf上下行文件 """
        self.sheetname  = u'生成服务器、客户端数据，protobuf上下行文件'
        if self.request.method == 'POST':
            req_msg = self.request.POST
        else:
            req_msg = self.request.GET
        recreate= (req_msg.get('recreate') == '1')
        msg = None
        ret = 0
        procid  = self.request.GET.get('procid','0')
        if recreate == True:
            try:
                if public.objIsEmpty(procid):
                    procid  = 0
                else:
                    procid  = int(float(procid))
                #没有执行程序
                if procid < 1:
                    errors  = self.do_data()
                    if errors:
                        ret = 2
                        procid  = 65535
                        msg = '<br/>'.join(errors)
                    else:
                        shl = 'ssh root@localhost chown -R nobody.nobody /opt/darkhutgame/cgame/cgame_shared/protobuf/'
                        subprocess.call(shlex.split(shl))
                        cmd = '/opt/darkhutgame/cgame/cgame_shared/protobuf/run_protobuf_test.sh'
                        public.print_str('--------- command: %s'%cmd)
                        #用Popen启动子进程，子进程无法正常退出，使用call替代
#                        popen   = subprocess.Popen(shlex.split(cmd), shell=False, stdout=None, stderr=None)
##                        if psutil.pid_exists(procid):
##                            print '----------- procid1 is exist: ', procid
##                            #time.sleep(5)
#                        public.print_str('popen stdout: %s'%popen.stdout)
#                        public.print_str('popen stderr: %s'%popen.stderr)
#                        procid  = popen.pid
                        subprocess.call(shlex.split(cmd))
                        procid  = 65535
                #ret: 返回值，0:已完成，1:正在执行，2:报错
                if ret == 0:
                    if psutil.pid_exists(procid):
                        print '----------- procid is exist: ', procid
                        ret = 1
                        msg = u'正在执行'
                    else:
                        ret = 0
                        procid  = 0
                        msg = u'已完成'
            except:
                procid  = 0
                ret = 2
                msg = '%r'%tb.format_exc()
                public.print_str(msg)
        self.content.update({'ret': ret, 'msg': msg, 'procid': procid, 
                             'sheet': {'markid': 'protobufdata','name':u'生成数据库&data.swf&上下行','addness': True}})
    
    def get_sheet_data(self,sheet,datas={}):
        """ 获取sheet的数据 """
        errors  = []
        err1 = '表[%s(%s)中'%(sheet.intro,sheet.name)
        datas[sheet.name]   = []
        dyn_obj = sheet.get_django_model()
        #多对多中对象
        to_objs = {}
        fields  = Field2.objects.filter(model=sheet.id)
        for f in fields:
#                if f.name == 'small_type':
#                    print f.name
            if f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
                if sheet.name == 'trade_road':
                    print 'field',model_to_dict(f) 
                try:
                    to_sheet= Sheet.objects.get(program=self.program.id, name=f.to, deleted=False)
                except Sheet.DoesNotExist:
                    public.print_str('ManyToManyField sheet [%s] does not exist'%f.to)
                else:
                    #于2014-07-02 11:52修改，一对多改成JS填写方式
#                        to_objs[f.name] = {'display': to_sheet.display, 'to_obj': to_sheet.get_django_model()}
#                        for f2 in to_sheet.fields.all():
#                            if f2.to == sheet.name:
#                                to_objs[f.name]['key']  = f2.name
                    to_objs[f.name] = to_sheet.get_django_model()
            elif f.type.name == 'ManyForeignsField':
                to_objs[f.name] = []
                to_objs2 = []
                for to in json.loads(f.to):
                    try:
                        to_sheet= Sheet.objects.get(program=self.program.id, name=to, deleted=False)
                    except Sheet.DoesNotExist:
                        public.print_str('ManyForeignsField sheet [%s] does not exist'%to)
                        errors.append(err1+'多外键字段[%s(%s)]不存在对应外键表[%s]'%(f.intro,f.name,to))
                    else:
                        to_objs2.append(to_sheet.get_django_model())
                to_objs[f.name] = to_objs2
        for record in dyn_obj.objects.filter(deleted=False):
            v1  = {}
            for f in fields:
                t1  = f.type.name
                name= f.name
                if name in AUTO_ADD_FIELD2:
                    continue
                if sheet.name == 'ship' and record.id == 8 and name == 'trans':
                    print model_to_dict(record)
                    print 'break' 
                v2  = getattr(record,name)
                if name == 'id':
                    name = 'primary_id'
                if v2 is None:
                    if t1 in ['IntegerField', 'BigIntegerField']:
                        v2  = 0
                    elif t1 == 'FloatField':
                        v2  = 0.0
                    elif t1 == 'BooleanField':
                        v2  = False
                    elif t1 in ['CharField','ImageField','TextField']:
                        v2  = ''
                    elif t1 == 'ForeignKey':
                        v2  = 0
                        #record2 = model_to_dict(record) 
                        #errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record2.get(f.name,'')))
                        #errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record.__getattribute__(f.name)))
                    elif t1 in ['ManyToManyField','DictArray','RepM2MField']:
                        v2  = []
                    elif t1 == 'ManyForeignsField':
                        v2  = 0
                elif t1 == 'ForeignKey':
#                        if v2 is None:
#                            v1[name]= 0
#                            record2 = model_to_dict(record) 
#                            errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record2.get(f.name,'')))
#                        else:
                    if v2.deleted:
                        errors.append(err1+'记录[%s]外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,record.__getattribute__(f.name)))
                    elif f.to_field:
                        v2  = getattr(v2,f.to_field,0)
                    else:
                        v2  = getattr(v2,'sn',0)
                        #v1[name]= model_to_dict(v2,exclude=BASE_AUTO_ADD_FIELD)
                elif t1 in ['ManyToManyField','RepM2MField']:
#                        if v2 is None:
#                            v2  = []
#                        else:
#                            #于2014-07-02 11:52修改，一对多改成JS填写方式
#                            #多对多中间表对象
#                            if to_objs.has_key(name):
#                                v2  = [getattr(v3,to_objs[name]['display']).sn for v3 in to_objs[name]['to_obj'].objects.filter(**{to_objs[name]['key']: record.id,'deleted': False})]
#                            else:
#                                v2  = []
                    #多对多中间表对象
                    if to_objs.has_key(name):
                        if DEBUG:
                            print '------------',sheet.name, record.id, name, v2
                        #v1[name]= [getattr(v3,f.to_field) for v3 in to_objs[name].objects.filter(id__in=json.loads(v2),deleted=False)]
                        to_obj  = to_objs[name]
                        v3  = []
                        for _id in json.loads(v2):
                            try:
                                v4  = to_obj.objects.get(id=_id,deleted=False)
                            except to_obj.DoesNotExist:
                                #v3.append(_id)
                                errors.append(err1+'记录[%s]多对多字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,_id))
                            else:
                                if f.to_field:
                                    v3.append(getattr(v4,f.to_field,_id))
                                else:
                                    v3.append(getattr(v4,'sn',_id))
                        v2  = v3
                        #print 'sheet.name: ',sheet.name,'v2',v2,'v3',v3
                    else:
                        v2  = []
                elif t1 == 'DictArray':
                    #多对多中间表对象
                    if not to_objs.has_key(name):
                        v2  = []
                    else:
                        if DEBUG:
                            print '------------',sheet.name, record.id, name, v2
                        to_obj  = to_objs[name]
                        v3  = []
                        for _id in json.loads(v2):
                            try:
                                v4  = to_obj.objects.get(id=_id,deleted=False)
                            except to_obj.DoesNotExist:
                                errors.append(err1+'记录[%s]字典数组字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,_id))
                            else:
                                v3.append(model_to_dict(v4,exclude=BASE_AUTO_ADD_FIELD))
                        v2  = v3
                elif t1 == 'JSONChar':
                    #JSON格式
                    if v2:
                        try:
                            v2  = json.loads(v2)
                        except:
                            if DEBUG:
                                print sheet.name, record.id, name, v2
                            v2  = []
                    else:
                        v2  = []
                elif t1 == 'ManyForeignsField':
                    #多对多中间表对象
                    if to_objs.has_key(name):
                        if DEBUG:
                            print '------------',sheet.name, record.id, name, v2
                        v3  = None
                        for to_obj in to_objs[name]:
                            try:
                                v3  = to_obj.objects.get(sn=v2,deleted=False)
                            except to_obj.DoesNotExist:
                                pass
                            else:
                                break
                        if v3 is None:
                            errors.append(err1+'记录[%s]多外键字段[%s(%s)]中不存在[%s]'%(record.id,f.intro,name,v2))
                v1[name]= v2
            datas[sheet.name].append(v1)
        return datas
    
    def reset_data(self):
        """ 重新生成表数据 """
        self.sheetname  = u'重新生成表数据'
        ret = 1
        msg = ""
        table   = self.request.GET.get('table','')
        if not table:
            msg = "请选择需要重新生成数据的表"
        else:
            try:
                sheet_obj   = Sheet.objects.get(name=table)
                table_obj   = sheet_obj.get_django_model()
            except Sheet.DoesNotExist:
                msg = "表【%s】不存在"%table
            try:
                #组织传入参数
                src = {}
                for src_table_name in json.loads(sheet_obj.formula.tables):
#                    src[src_table_name] = []
                    src_table_obj   = Sheet.objects.get(name=src_table_name)#.get_django_model()
                    self.get_sheet_data(src_table_obj,src)
#                    for record in src_table_obj.objects.filter(deleted=False):
#                        src[src_table_name].append(model_to_dict(record,exclude=BASE_AUTO_ADD_FIELD))
#                        break
                #通过公式生成数据
                dst = None
                exec(sheet_obj.formula.code.replace('\\n','\n').replace('\\t','\t'))
                print 'dst:',dst
                #将结果写入数据库
                table_obj.objects.all().delete()
                username = self.request.user.username
                createtime  = datetime.datetime.now()
                sheet_id = sheet_obj.id
                querysetlist=[]
                auto_id = 1
                #如果结果集为空则报错
                if not dst:
                    msg = '生成的结果集为空'
                else:
                    print '生成后数据：'
                    print dst
                    for v2 in dst:
                        v2['username']  = username
                        v2['createtime']= createtime
                        if sheet_obj.num > 0:
                            v2['sn']    = int('%d%04d'%(sheet_id,auto_id))
                        print 'v2:',v2
                        querysetlist.append(table_obj(**v2))
                        auto_id += 1
                    table_obj.objects.bulk_create(querysetlist)
                    ret = 0
            except:
                ret = 2
                print tb.format_exc()
                msg = '%r'%tb.format_exc()
                
        self.content.update({'ret': ret, 'msg': msg})
    
    def charting(self):
        """ 绘制图表 """
        self.sheetname  = u'绘制图表'
        if self.reqmode != 'js':
            self.content['formulas']    = Formula.objects.filter(deleted=False,ft=2)
        else:
            ret = 1
            msg = ""
            fid = self.request.GET.get('formula')
            if not fid:
                msg = "请至少选择一个公式"
            else:
                try:
                    formula = Formula.objects.get(id=int(fid))
                except Formula.DoesNotExist:
                    msg = "公式表不存在ID【%s】的公式"%fid
                else:
                    try:
                        #组织传入参数
                        src = {}
                        dst = None
                        for src_table_name in json.loads(formula.tables):
                            src_table_obj   = Sheet.objects.get(name=src_table_name)
                            self.get_sheet_data(src_table_obj,src)
                        #通过公式生成数据
                        exec(formula.code.replace('\\n','\n').replace('\\t','\t'))
#                        print 'dst:',dst
                        #整理数据
#                        dst = {'table1': {0:0, 1:10, 2:23, 3:17, 4:18, 5:9},
#                               'table2': {0:1, 2:15, 3:9},
#                               'x': 'Time',
#                               'y': 'Popularity'}
                        #获取表中的X点
                        xpoints = []
                        datas   = {'td':{'cols': [{'id': 'id_x', 'label': 'x', 'type': 'number'}], 'rows': []}}
                        for name, v in dst.items():
                            if name in ['x','y']:
                                datas[name] = dst.pop(name)
                            else:
                                xpoints.extend(v.keys())
                                datas['td']['cols'].append({'id': 'id_'+name, 'label': name, 'type': 'number'})
                        for xpoint in sorted({}.fromkeys(xpoints).keys()):
                            v3  = [{'v': xpoint}]
                            for name, v2 in dst.items():
                                v4  = {}
                                if v2.has_key(xpoint):
                                    v4['v'] = v2[xpoint]
                                v3.append(v4)
                            datas['td']['rows'].append({'c': v3})
#                        datas   ={'x': 'Time', 'y': 'Popularity', 'td': {
#                             'cols': [{'id': 'id_time', 'label': 'time', 'type': 'number'},
#                                     {'id': 'id_popu', 'label': 'popu', 'type': 'number'},
#                                     {'id': 'id_popu2', 'label': 'popu2', 'type': 'number'}
#                                    ],
#                             'rows': [{'c':[{'v': 0}, {'v': 0}, {'v': 1}]},
#                                     {'c':[{'v': 1},{'v': 10},{}]},
#                                     {'c':[{'v': 2}, {'v': 23},{'v': 15}]},
#                                     {'c':[{'v': 3}, {'v': 17},{'v': 9}]},
#                                     {'c':[{'v': 4}, {'v': 18},{}]},
#                                     {'c':[{'v': 5}, {'v': 9},{}]}
#                                     ]
#                            }
#                         }
                        self.content['datas']   = datas
                        self.content['do_what'] = 'get'
                        ret = 0
                    except:
                        ret = 2
                        print tb.format_exc()
                        msg = '%r'%tb.format_exc()
            self.content.update({'ret': ret, 'msg': msg})
    
    def import_excel(self):
        """ 导入Excel表 """
        self.sheetname  = u'导入Excel表'
        if self.request.method == 'POST':
            self.sheetid    = self.request.POST.get('table','')
            fhandler= self.request.FILES['ex_file']
            print 'fhandler: ', fhandler
            if not fhandler:
                self.tips   = '请选择要导入的excel（*.xlsx）文件'
            else:
                fname   = '%s'%fhandler
                fpath   = PROGRAM_PATH+'/media/excel/'+fname
                destination = open(fpath, 'wb+')
                for chunk in fhandler.chunks():
                    destination.write(chunk)
                destination.close()
                #读取excel数据
                er  = ExReader(fpath, 'db')
                tables  = er.read_tables()
                #链接数据库
                sql = SqlLite(os.path.join(PROGRAM_PATH,BS_DB_NAME))
                sql.conn= sql.force_conn()
                if sql.conn is None:
                    print 'connect db fail.'
                    return False
                username= self.request.user.username
                for table, datas in tables.items():
                    if table != self.sheetid:
                        print 'table %s is not equal sheetid %s'%(table, self.sheetid)
                        continue
                    print table
                    #查找表
                    table_obj   = sql.find_one('sheet', fields=['id'], kwargs={'name': table})
                    if not table_obj:
                        self.tips   = 'table %s does not exist in sheet'%table
                        break
                    table_id= table_obj['id']
                    sn_rule_len = len('%d%04d'%(table_id,0))
                    table   = 'cgame_'+table.replace('_','')
                    print 'do table:',table
                    col_index   = 1
                    exist_sns   = []
                    error_sns   = []
                    self.tips   = ''
                    for data in datas[0]:
                        col_index   += 1
                        data.update({'username': username,'deleted':False,
                                     'createtime':datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
                        #print data
                        if data .has_key('sn'):
                            sn  = '%s'%data['sn']
                            if len(sn) != sn_rule_len or not sn.startswith('%s'%table_id):
                                error_sns.append(sn)
                            elif sql.find_one(table, kwargs={'sn': data['sn']}):
                                exist_sns.append(sn)
                    if error_sns:
                        self.tips   += '错误SN规则错误，请参考策划后台经行修改:'+ ','.join(error_sns)+'<br/>'
                    if exist_sns:
                        self.tips   += '已存在以下SN记录，请仔细检查excel文件:'+ ','.join(exist_sns)+'<br/>'
                    else:
                        sql.insert(table,datas[0])
                        sql.commit(table)
                        self.tips   = '导入成功'
                    break
                self.do_sheet()
#            self.content.update({'ret': ret, 'msg': msg})
    
    def client_edit(self):
        """ 客户端编辑 """
        self.sheetname  = u'客户端编辑'
        self.content.update({'sheet': {'markid': 'client_edit','name':u'客户端编辑','addness': True},
                             'full_screen_swf_name':'http://220.dhh.darkhutgame.net:8080/artres/cgame_edit/bin/eliminate_game.swf'})
    
    def restart(self):
        """ 重启进程 """
        self.sheetname  = u'重启进程'
        force   = self.request.GET.get('force','0')=='1'
        if force:
#            shl1 = 'ssh root@localhost python2.7 /opt/darkhutgame/support/tools_backend/cgame/tools_backend/project_ctl.py stop'
#            subprocess.call(shlex.split(shl1))
#            print shl1
#            time.sleep(2)
#            shl2 = 'ssh root@localhost python2.7 /opt/darkhutgame/support/tools_backend/cgame/tools_backend/project_ctl.py start'
#            print shl2
#            subprocess.call(shlex.split(shl2))
            shl = 'ssh root@localhost /opt/darkhutgame/support/tools_backend/cgame/tools_backend/run_protobuf_test.sh'
            print shl
            subprocess.call(shlex.split(shl))
            
        time.sleep(2)
        
    def modifylog(self):
        """ 参数表修改记录 """
        self.sheetname  = u'参数表修改记录'
        if self.request.method == 'POST':
            req_msg = self.request.POST
        else:
            req_msg = self.request.GET
        today   = datetime.today().strftime('%Y-%m-%d')
        start_day   = req_msg.get('start_day',today)
        end_day = req_msg.get('end_day',today)
        
        cmd = 'sh /opt/darkhutgame/kashen_shared/protobuf/run_protobuf_test.sh'
        public.print_str('--------- command: %s'%cmd)
        try:
            if public.objIsEmpty():
                procid  = 0
            else:
                procid  = int(float(procid))
            #没有执行程序
            if procid < 1:
                popen   = subprocess.Popen(shlex.split(cmd), shell=True, stdout=None, stderr=None)
                if psutil.pid_exists(procid):
                    print '----------- procid1 is exist: ', procid
                    #time.sleep(5)
                #public.print_str('%s'%popen.stdout)
                procid  = popen.pid
            #ret: 返回值，0:已完成，1:正在执行，2:报错
            if psutil.pid_exists(procid):
                print '----------- procid is exist: ', procid
                ret = 1
                msg = u'正在执行'
            else:
                ret = 0
                procid  = 0
                msg = u'已完成'
        except:
            procid  = 0
            ret = 2
            msg = '%r'%tb.format_exc()
            public.print_str(msg)
        self.content.update({'ret': ret, 'msg': msg, 'procid': procid, 
                             'sheet': {'sheetid': 'protobufdata','name':u'生成数据库&data.swf&上下行','addness': True}})
        
    def paging(self,obj,per_page,page,**kwargs):
        """ 分页 """
        #print 'obj:',obj
        if public.objIsFull(kwargs):
            objects = obj.objects.filter(**kwargs)
        else:
            objects = obj.objects.all()
        if self.order:
            objects = objects.order_by(self.order)
        #每页两条数据的一个分页器
        paginator   = Paginator(objects, per_page)
        try:
            contacts = paginator.page(int(page))
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            contacts = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            contacts = paginator.page(paginator.num_pages)
        return paginator,contacts
    
    def list_upper(self, l1, s_char='_', index=0):
        """ 将字符串(两个单词之间用'_'分隔)中的第index个字母转成大写 """
        l2  = []
        for s1 in l1:
            tmp_str = ''
            if s_char in s1:
                s2  = s1.split(s_char)
                tmp_str = s2[0]
                for s3 in s2[1:]:
                    #tmp_str += str.replace(str[index], str[index].upper())
                    tmp_str += s3[0].upper()+s3[1:]
            else:
                tmp_str = s1
            l2.append(tmp_str)
        return l2
        
    def string2other(self,ps,mode,name):
        """ 将字符串ps转换成其他类型 mode"""
        modes   = {'int':u'整数','float':u'小数','json':u'列表或字典'}
        data= ps
        try:
            if mode == 'int':
                data= int(ps)
            elif mode == 'float':
                data= float(ps)
            elif mode == 'json':
                data= json.loads(ps)
        except:
            self.tips   += u'[%s]不是[%s]字符串，'%(name,modes.get(mode,mode))
        return data
    
    def sheet_init(self):
        """ 数据表参数初始化 """
        print 'in module sheet_init'
        try:
            if self.sheetid == 'model':
                self.sheet_obj  = Sheet
            elif self.sheetid == 'formula':
                self.sheet_obj  = Formula
            else:
                self.dyn_model  = Sheet.objects.get(program=self.program.id,name=self.sheetid)
#            self.dyn_model  = Sheet.objects.get(program=self.program.id,name=self.sheetid)
        except Sheet.DoesNotExist:
            self.sheet_obj  = None
            #return '表【%s】不存在'%self.sheetname
        else:
            if self.sheetid == 'model':
                self.content['field_types'] = FieldType2.objects.all()
                self.content['tables']  = Sheet.objects.filter(program=self.program.id)
                self.content['sys_models']  = SystemModels.objects.filter(program=self.program.id)
                self.content['sys_models2'] = SystemModels2.objects.filter(program=self.program.id)
                self.content['formulas']    = Formula.objects.filter(deleted=False,ft=1)
                self.achieves['program']= self.program
                self.achieves['locale'] = self.locale
                self.pkeys  = ['sys_model','sys_model2','name','intro','num','is_proto','display','field','formula','is_template']
                self.pvalues= [u'一级目录',u'二级目录',u'英文名',u'中文名',u'最后一个记录ID',u'是否上下行表',u'外键表显示字段(英文名)',u'字段',u'公式',u'是否模板']
            elif self.sheetid == 'formula':
                self.content['tables']  = Sheet.objects.filter(program=self.program.id)
                self.pkeys  = ['name','tables','code','ft']
                self.pvalues= [u'名称',u'数据源表','公式','公式应用类型']
            else:
                self.sheet_obj  = self.dyn_model.get_django_model()
#                print '--------------- self.dyn_model.fields'
#                for field in self.sheet_obj._meta.fields:
#                    print field.name
#                print 'self.dyn_model.id:',self.dyn_model.id
#                print 'self.dyn_model.name:',self.dyn_model.name
                self.fields = Field2.objects.filter(model=self.dyn_model.id).exclude(name__in=BASE_AUTO_ADD_FIELD)
                foreigns = {}
                for f in self.fields:
                    if DEBUG:
                        print 'field name', f.name
                    if f.name == 'sn':
                        self.has_sn = True
                    if f.name not in BASE_AUTO_ADD_FIELD:
                        self.pkeys.append(f.name)
                        self.pvalues.append(f.intro)
                    if f.type.name == 'ForeignKey':
                        self.foreign_keys[f.name] = Sheet.objects.get(program=self.program.id,name=f.to).display
                    elif f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
                        #self.foreign_keys[f.name] = Sheet.objects.get(program=self.program.id,name=f.to).intro
                        #于2014-05-09 16:33修改，不显示表名，显示对应的SN列表
                        to_obj  = Sheet.objects.get(program=self.program.id,name=f.to)
                        display = to_obj.display
                        primary_key = ''
                        for f2 in to_obj.fields.exclude(name__in=BASE_AUTO_ADD_FIELD):
                            if f2.name != display:
                                primary_key = f2.name
                                break
                        self.foreign_keys[f.name] = {'to_obj': to_obj.get_django_model(),'display': display, 'primary_key': primary_key}
                        model_obj   = to_obj.get_django_model()
                        foreigns[f.to]  = []
                        for record in model_obj.objects.filter(deleted=False):
                            display2= getattr(record,display)
                            if isinstance(display2,models.Model) and not isinstance(display2,unicode) and not isinstance(display2,str):
                                display2 = display2.sn
                            foreigns[f.to].append([record.id,display2])
                    elif f.type.name == 'ManyForeignsField':
                        self.foreign_keys[f.name] = {'to_obj': [],'display': 'name', 'primary_key': 'id'}
                        to_objs = []
                        for to in json.loads(f.to):
                            to_obj  = Sheet.objects.get(program=self.program.id,name=to)
                            to_objs.append((to_obj,to_obj.get_django_model()))
                        self.foreign_keys[f.name]['to_obj'] = to_objs
#                if DEBUG:
#                    print 'foreigns',foreigns
                self.content['foreigns']    = json.dumps(foreigns)
                print 'self.dyn_model.is_template: ', self.dyn_model.is_template
                if self.dyn_model.is_template:
                    self.content['conds']   = self.dyn_model.conds
                    self.content['filters'] = json.loads(self.dyn_model.filters)
#                for f in Field2.objects.exclude(model=self.dyn_model.id,name__in=['createtime','username']):
#                    self.pkeys.append(f.name)
#                    self.pvalues.append(f.intro)
    
    def sheet_do_add_req_data(self):
        """ 处理数据表增加、修改参数 """
        #修改人
        self.achieves['username']   = self.request.user.username
        self.achieves['createtime'] = datetime.datetime.now()
        if self.sheetid == 'model':
            #参数表,model
            conds   = []
            for index in range(0,len(self.pkeys)):
                k   = self.pkeys[index]
                name= self.pvalues[index]
                if k in ['field']:
                    record_count= self.request.POST.get(k+'_index')
#                    v1  = []
                    if public.objIsFull(record_count):
                        #检查字段名重复
                        names   = []
                        for i in range(1,int(record_count)):
                            field_id= self.string2other(self.request.POST.get(k+'_id%s'%i,0), 'int', name+'记录ID')
                            status_id   = self.string2other(self.request.POST.get(k+'_status%s'%i,1), 'int', name+'记录状态')
#                            if field_id is None:
#                                continue
                            name1   = self.request.POST.get(k+'_name%s'%i)
                            intro   = self.request.POST.get(k+'_intro%s'%i)
                            type1   = self.request.POST.get(k+'_type%s'%i)
                            to  = self.request.POST.get(k+'_to%s'%i)
                            to_field= self.request.POST.get(k+'_to_field%s'%i)
                            max_length  = self.request.POST.get(k+'_max_length%s'%i)
#                            help= self.request.POST.get(k+'_help%s'%i)
                            is_condition= self.request.POST.get(k+'_is_cond%s'%i)
                            if is_condition == "1":
                                conds.append(name1)
#                            default = self.request.POST.get(k+'_default%s'%i)
                            if public.objsIsEmpty([name1,intro,type1]):
                                if status_id == '2':
                                    continue
                                self.tips   = name+'第%s行，英文名、中文名、类型中有空参数'%i
                                public.print_str('name,intro,type1: %s, %s, %s'%(name1,intro,type1))
                                #break
                            else:
#                                sets= []
                                try:
                                    type_obj= FieldType2.objects.get(id=int(type1))
                                except FieldType2.DoesNotExist:
                                    type_obj= None
                                    self.tips   = '字段类型不存在ID【%s】'%type1
                                    print 'self.tips:',self.tips
#                                if type1 == 'ForeignKey':
#                                    if to == '0':
#                                        self.tips   = name+'外键参数为空'
#                                    else:
#                                        try:
#                                            to_obj  = Sheet.objects.get(id=int(to))
#                                        except Sheet.DoesNotExist:
#                                            self.tips   = name+'外键参数对应的表不存在'
#                                            #to  = self.string2other(to,'int',name+'外键参数对应的表')
#                                        else:
#                                            to  = to_obj#.__class__.__name__
#                                else:
#                                    to  = 
                                if type_obj is not None and type_obj.name in ['CharField','ImageField','JSONChar']:
                                    if public.objIsEmpty(max_length):
                                        max_length  = 255
                                    max_length  = self.string2other(max_length,'int',name+'最大长度')
                                else:
                                    max_length  = 0
                                if type_obj.name == 'ManyForeignsField':
                                    to_field    = 'sn'
                                    to  = self.request.REQUEST.getlist(k+'_to%s'%i)
                                    if not to:
                                        self.tips   = name+'第%s行，多外键字段至少要选择一张表'
                                    to  = json.dumps(to)
                                self.fields.append({'id': field_id,
                                                    'status': status_id,
                                                    'name': name1,
                                                    'intro': intro,
                                                    'type': type_obj,
                                                    'to': to,
                                                    'to_field': to_field,
                                                    'max_length': max_length,
                                                    #'help': help,
#                                                    'settings': sets,
                                                    })
                            if name1 not in names:
                                names.append(name1)
                                if name1 == 'sn':
                                    self.achieves['num']    = 1
                            else:
                                self.tips   = name+'第%s行字段名已经存在，请仔细检查'%i
                else:
                    v1  = public.req_param_rstrip(self.request.POST.get(k))
                    if k in ['num','sys_model','sys_model2','formula']:
                        v1  = self.string2other(v1,'int',name)
                        if k == 'sys_model':
                            try:
                                v1  = SystemModels.objects.get(id=v1)
                            except SystemModels.DoesNotExist:
                                self.tips   += name+'不存在ID【%s】'%v1
                            print 'self.tips: ',self.tips
                        elif k == 'sys_model2':
                            try:
                                v1  = SystemModels2.objects.get(id=v1)
                            except SystemModels2.DoesNotExist:
                                self.tips   += name+'不存在ID【%s】'%v1
                            print 'self.tips: ',self.tips
                        elif k == 'formula':
                            try:
                                v1  = Formula.objects.get(id=v1)
                            except Formula.DoesNotExist:
                                continue
                                #self.tips   += name+'不存在ID【%s】'%v1
                            print 'self.tips: ',self.tips
                    elif k in ['is_proto', 'is_template']:
                        v1  = bool(v1=='1')
                        if k == 'is_template':
                            filters = {}
                            if v1:
                                filters['inst_name']= public.req_param_rstrip(self.request.POST.get('inst_name',''))
                                filters['inst_field']   = public.req_param_rstrip(self.request.POST.get('inst_field',''))
                                if not filters['inst_name']:
                                    self.tips   += name+'不存在ID【%s】'%v1
                            self.achieves['filters']= json.dumps(filters)
                    self.achieves[k]  = v1
            self.achieves['conds']  = json.dumps(conds)
            if public.objIsEmpty(self.tips) and self.do_what == 'add':
                if Sheet.objects.filter(program=self.program.id,name=self.achieves.get('name')):
                    self.tips   = '表名【%s】已经存在'%self.achieves['name']
                else:
                    self.fields.extend([{'name': 'id', 'intro': 'ID', 'type': FieldType2.objects.get(name='AutoField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        {'name': 'createtime', 'intro': '创建时间', 'type': FieldType2.objects.get(name='DateTimeField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        {'name': 'username', 'intro': '操作用户', 'type': FieldType2.objects.get(name='CharField'),'to': '', 'max_length': 50, 'id': 0,'status': 1},
                                        {'name': 'deleted', 'intro': '删除', 'type': FieldType2.objects.get(name='BooleanField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        ])
                    if self.achieves['is_template']:
                        self.fields.append({'name': 'odds', 'intro': '掉落', 'type': FieldType2.objects.get(name='OddsField'),'to': '', 'max_length': 0, 'id': 0,'status': 1})
#                    print "sheet_do_add_req_data:", self.fields
        elif self.sheetid == 'formula':
            #公式表,formula
            for index in range(0,len(self.pkeys)):
                k   = self.pkeys[index]
                name= self.pvalues[index]
                if k == 'tables':
                    v1  = json.dumps(public.req_param_rstrip(self.request.POST.get(k+'_selected')).strip(',').split(','))
                else:
                    v1  = public.req_param_rstrip(self.request.POST.get(k))
                    if k == 'code':
                        v1  = v1.strip('\r\n')
                self.achieves[k]  = v1
        else:
            #动态表
            self.achieves['deleted']    = False
            for f in self.fields:
                type_name   = f.type.name
                if f.type.name in ['ManyToManyField','DictArray',]:
                    if self.reqmode == 'js':
                        v1  = self.request.POST.get(f.name,'[]')
                        if DEBUG:
                            print '--------- many2many js',f.name,v1
                    else:
                        v1  = self.request.POST.get('%s_selected'%f.name).strip(',')
                        if v1:
                            v1  = [int(_id) for _id in v1.split(',')]
                        else:
                            v1  = []
                        v1  = json.dumps(v1)
                elif f.type.name == 'RepM2MField':
                    if self.reqmode == 'js':
                        v1  = self.request.POST.get(f.name,'[]')
                        if DEBUG:
                            print '--------- many2many js',f.name,v1
                    else:
                        path_len  = self.request.POST.get('%s_index'%f.name)
                        if DEBUG:
                            print '------- path_len: ',path_len
                        if public.objIsEmpty(path_len):
                            v1  = []
                        else:
                            v1  = []
                            for i in range(1,int(path_len)):
                                prefix  = '第%s行'%i
                                v2  = public.req_param_rstrip(self.request.POST.get(f.name+'%s'%i))
                                if public.objIsFull(v2):
                                    v1.append(self.string2other(v2,'int',prefix+f.intro))
                            v1  = json.dumps(v1)
                elif f.type.name == 'ManyForeignsField':
                    v1  = 0
                    for k1 in json.loads(f.to):
                        v1  = int(self.request.POST.get('%s_%s'%(f.name,k1),'0'))
                        if DEBUG:
                            print '------- k, v: ',k1, v1
                        if v1 > 0.1:
                            break
                    if v1 < 1:
                        self.tips   = f.name+'是空值'
                elif f.type.name == 'OddsField':
                    if self.reqmode == 'js':
                        v1  = self.request.POST.get(f.name,'[]')
                        if DEBUG:
                            print '--------- many2many js',f.name,v1
                    else:
                        path_len  = self.request.POST.get('%s_index'%f.name)
                        if DEBUG:
                            print '------- path_len: ',path_len
                        if public.objIsEmpty(path_len):
                            v1  = []
                        else:
                            v1  = []
                            for i in range(1,int(path_len)):
                                prefix  = '第%s行'%i
                                rare  = public.req_param_rstrip(self.request.POST.get(f.name+'_rare%s'%i,''))
                                odds  = public.req_param_rstrip(self.request.POST.get(f.name+'_odds%s'%i,'0'))
                                cards   = [int(r) for r in self.request.POST.getlist(f.name+'_card%s'%i)]
                                v1.append({'rare': rare,
                                           'odds': self.string2other(odds,'int',prefix+'掉率'),
                                           'cards': cards
                                           })
                            v1  = json.dumps(v1)
                else:
                    v1  = self.request.POST.get(f.name)
#                    print f.name,v1, self.do_what
                    if v1 is None:# and self.do_what == 'modify':
                        continue
                    v1  = public.req_param_rstrip(v1)
                    if type_name == 'IntegerField':
                        if not v1: 
                            v1  = 0
                        else:
                            v1  = self.string2other(v1, 'int', f.intro)
                    elif type_name == 'FloatField':
                        if not v1:
                            v1  = 0
                        else:
                            v1  = self.string2other(v1, 'float', f.intro)
                    elif type_name == 'ForeignKey':
                        v1  = self.string2other(v1,'int',f.intro)
                        try:
                            to_obj  = Sheet.objects.get(program=self.program.id, name=f.to)
                        except Sheet.DoesNotExist:
                            self.tips   = f.intro+'外键参数对应的表[%s]不存在'%f.to
                            #pass
                        else:
                            to_model = to_obj.get_django_model()
                            try:
                                v1  = to_model.objects.get(id=v1)
                            except to_model.DoesNotExist:
                                #self.tips   = f.intro+'，表[%s]中不存在记录[%s]'%(self.sheetname,v1)
                                v1  = None
                    elif type_name == 'BooleanField':
                        v1  = bool(v1=='1')
                if f.name == 'name':
                    v1  = public.reduce_spec_sign(v1)
                self.achieves[f.name]   = v1
    
    def sheet_do_add_req_data_201412111110(self):
        """ 处理数据表增加、修改参数，于2014-12-11 11:10为修改多对多格式所做备份 """
        #修改人
        self.achieves['username']   = self.request.user.username
        self.achieves['createtime'] = datetime.datetime.now()
        if self.sheetid == 'model':
            #参数表,model
            for index in range(0,len(self.pkeys)):
                k   = self.pkeys[index]
                name= self.pvalues[index]
                if k in ['field']:
                    record_count= self.request.POST.get(k+'_index')
#                    v1  = []
                    if public.objIsFull(record_count):
                        #检查字段名重复
                        names   = []
                        for i in range(1,int(record_count)):
                            field_id= self.string2other(self.request.POST.get(k+'_id%s'%i,0), 'int', name+'记录ID')
                            status_id   = self.string2other(self.request.POST.get(k+'_status%s'%i,1), 'int', name+'记录状态')
#                            if field_id is None:
#                                continue
                            name1   = self.request.POST.get(k+'_name%s'%i)
                            intro   = self.request.POST.get(k+'_intro%s'%i)
                            type1   = self.request.POST.get(k+'_type%s'%i)
                            to  = self.request.POST.get(k+'_to%s'%i)
                            to_field= self.request.POST.get(k+'_to_field%s'%i)
                            max_length  = self.request.POST.get(k+'_max_length%s'%i)
                            help= self.request.POST.get(k+'_help%s'%i)
#                            default = self.request.POST.get(k+'_default%s'%i)
                            if public.objsIsEmpty([name1,intro,type1]):
                                if status_id == '2':
                                    continue
                                self.tips   = name+'第%s行，英文名、中文名、类型中有空参数'%i
                                public.print_str('name,intro,type1: %s, %s, %s'%(name1,intro,type1))
                                #break
                            else:
#                                sets= []
                                try:
                                    type_obj= FieldType2.objects.get(id=int(type1))
                                except FieldType2.DoesNotExist:
                                    type_obj= None
                                    self.tips   = '字段类型不存在ID【%s】'%type1
                                    print 'self.tips:',self.tips
#                                if type1 == 'ForeignKey':
#                                    if to == '0':
#                                        self.tips   = name+'外键参数为空'
#                                    else:
#                                        try:
#                                            to_obj  = Sheet.objects.get(id=int(to))
#                                        except Sheet.DoesNotExist:
#                                            self.tips   = name+'外键参数对应的表不存在'
#                                            #to  = self.string2other(to,'int',name+'外键参数对应的表')
#                                        else:
#                                            to  = to_obj#.__class__.__name__
#                                else:
#                                    to  = 
                                if type_obj is not None and type_obj.name in ['CharField','ImageField','JSONChar']:
                                    if public.objIsEmpty(max_length):
                                        max_length  = 255
                                    max_length  = self.string2other(max_length,'int',name+'最大长度')
                                else:
                                    max_length  = 0
                                if type_obj.name == 'ManyForeignsField':
                                    to_field    = 'sn'
                                    to  = self.request.REQUEST.getlist(k+'_to%s'%i)
                                    if not to:
                                        self.tips   = name+'第%s行，多外键字段至少要选择一张表'
                                    to  = json.dumps(to)
                                self.fields.append({'id': field_id,
                                                    'status': status_id,
                                                    'name': name1,
                                                    'intro': intro,
                                                    'type': type_obj,
                                                    'to': to,
                                                    'to_field': to_field,
                                                    'max_length': max_length,
                                                    #'help': help,
#                                                    'settings': sets,
                                                    })
                            if name1 not in names:
                                names.append(name1)
                            else:
                                self.tips   = name+'第%s行字段名已经存在，请仔细检查'%i
                else:
                    v1  = public.req_param_rstrip(self.request.POST.get(k))
                    if k in ['num','sys_model','sys_model2']:
                        v1  = self.string2other(v1,'int',name)
                        if k == 'sys_model':
                            try:
                                v1  = SystemModels.objects.get(id=v1)
                            except SystemModels.DoesNotExist:
                                self.tips   += name+'不存在ID【%s】'%v1
                            print 'self.tips: ',self.tips
                        if k == 'sys_model2':
                            try:
                                v1  = SystemModels2.objects.get(id=v1)
                            except SystemModels2.DoesNotExist:
                                self.tips   += name+'不存在ID【%s】'%v1
                            print 'self.tips: ',self.tips
                    elif k == 'is_proto':
                        v1  = bool(v1=='1')
                    self.achieves[k]  = v1
            if public.objIsEmpty(self.tips) and self.do_what == 'add':
                if Sheet.objects.filter(program=self.program.id,name=self.achieves.get('name')):
                    self.tips   = '表名【%s】已经存在'%v1
                else:
                    self.fields.extend([{'name': 'id', 'intro': 'ID', 'type': FieldType2.objects.get(name='AutoField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        {'name': 'createtime', 'intro': '创建时间', 'type': FieldType2.objects.get(name='DateTimeField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        {'name': 'username', 'intro': '操作用户', 'type': FieldType2.objects.get(name='CharField'),'to': '', 'max_length': 50, 'id': 0,'status': 1},
                                        {'name': 'deleted', 'intro': '删除', 'type': FieldType2.objects.get(name='BooleanField'),'to': '', 'max_length': 0, 'id': 0,'status': 1},
                                        ])
#                    print "sheet_do_add_req_data:", self.fields
        else:
            #动态表
            self.achieves['deleted']    = False
            for f in self.fields:
                type_name   = f.type.name
                if f.type.name == 'ManyToManyField':
#                    v1  = []
#                    for v2 in self.request.REQUEST.getlist(f.name):
#                        v1.append(self.string2other(v2,'int',f.intro))
#                    try:
#                        to_obj  = Sheet.objects.get(program=self.program.id, name=f.to)
#                    except Sheet.DoesNotExist:
#                        self.tips   = f.intro+'外键参数对应的表[%s]不存在'%f.to
#                    else:
#                        try:
#                            v1  = to_obj.get_django_model().objects.filter(id__in=v1)
#                        except to_obj.DoesNotExist:
#                            self.tips   = f.intro+'，表[%s]中不存在记录[%s]'%v1
#                    #print 'v1: ',v1
#                    self.manytomanys[f.name]= v1
                    if self.reqmode == 'js':
                        v1  = self.request.POST.get(f.name,'[]')
                        if DEBUG:
                            print '--------- many2many js',f.name,v1
                    else:
                        path_len  = self.request.POST.get('%s_index'%f.name)
                        if DEBUG:
                            print '------- path_len: ',path_len
                        if public.objIsEmpty(path_len):
                            v1  = []
                        else:
                            v1  = []
                            for i in range(1,int(path_len)):
                                prefix  = '第%s行'%i
                                v2  = public.req_param_rstrip(self.request.POST.get(f.name+'%s'%i))
#                                if public.objsIsEmpty([v2]):
#                                    self.tips   = prefix+'有空参数'
#                                    public.print_str('v2: %s'%v2)
#                                    break
                                if public.objIsFull(v2):
                                    v1.append(self.string2other(v2,'int',prefix+f.intro))
                            v1  = json.dumps(v1)
                elif f.type.name == 'ManyForeignsField':
                    v1  = 0
                    for k1 in json.loads(f.to):
                        v1  = int(self.request.POST.get('%s_%s'%(f.name,k1),'0'))
                        if DEBUG:
                            print '------- k, v: ',k1, v1
                        if v1 > 0.1:
                            break
                    if v1 < 1:
                        self.tips   = f.name+'是空值'
                else:
                    v1  = self.request.POST.get(f.name)
#                    print f.name,v1, self.do_what
                    if v1 is None:# and self.do_what == 'modify':
                        continue
                    v1  = public.req_param_rstrip(v1)
                    if type_name == 'IntegerField':
                        if not v1: 
                            v1  = 0
                        else:
                            v1  = self.string2other(v1, 'int', f.intro)
                    elif type_name == 'FloatField':
                        if not v1:
                            v1  = 0
                        else:
                            v1  = self.string2other(v1, 'float', f.intro)
                    elif type_name == 'ForeignKey':
                        v1  = self.string2other(v1,'int',f.intro)
                        try:
                            to_obj  = Sheet.objects.get(program=self.program.id, name=f.to)
                        except Sheet.DoesNotExist:
                            self.tips   = f.intro+'外键参数对应的表[%s]不存在'%f.to
                        else:
                            to_model = to_obj.get_django_model()
                            try:
                                v1  = to_model.objects.get(id=v1)
                            except to_model.DoesNotExist:
                                self.tips   = f.intro+'，表[%s]中不存在记录[%s]'%(self.sheetname,v1)
                                v1  = None
                    elif type_name == 'BooleanField':
                        v1  = bool(v1=='1')
                if f.name == 'name':
                    v1  = public.reduce_spec_sign(v1)
                self.achieves[f.name]   = v1
    
    def do_modify_post_exception(self):
        """ 处理修改提交异常 """
        if self.sheetid == 'model':
            i   = 0
            for f in self.fields:
                if f['name'] in BASE_AUTO_ADD_FIELD:
                    del f
                i   += 1
            self.achieves['field']  = self.fields#json.loads(self.achieves['field'])
            self.content['field_len']   = len(self.achieves['field'])+1
            for f in self.achieves['field']:
                print '------- ',f
                if f['type'].name == 'ForeignKey':
                    if DEBUG:
                        print 'name: ',f['name']
                    f['fields'] = [f2.name for f2 in Sheet.objects.get(name=f['to']).fields.all().exclude(name__in=BASE_AUTO_ADD_FIELD)]
                elif f['type'].name == 'ManyForeignsField':
                    if DEBUG:
                        print 'name: ',f['name']
                    f['to'] = json.loads(f['to'])
            self.achieves['conds']  = json.loads(self.achieves['conds'])
            self.achieves['filters']= json.loads(self.achieves['filters'])
        elif self.sheetid == 'formula':
            self.achieves['tables'] = ','.join(self.achieves['tables'])
            
    def do_modify_get_special_field(self,db_obj):
        """ 处理修改获取的特殊字段 """
        if self.sheetid == 'model':
            model_id= db_obj.id
            fields  = copy.copy(self.pkeys)
            fields.append('conds')
            fields.append('filters')
            db_obj  = model_to_dict(db_obj, fields=fields,exclude=['field'])
            db_obj['field']= Field2.objects.filter(model=model_id).exclude(name__in=BASE_AUTO_ADD_FIELD)
            self.content['field_len']   = len(db_obj['field'])+1
            fields  = []
            for f in db_obj['field']:
                f   = model_to_dict(f)
                if f['type'] in [9,11]:                    
                    if DEBUG:
                        print 'name: ',f['to']
                    f['fields'] = [f2.name for f2 in Sheet.objects.get(name=f['to']).fields.all().exclude(name__in=BASE_AUTO_ADD_FIELD)]
                fields.append(f)
#            db_obj['field'] = sorted(fields, key=operator.itemgetter('sort'), reverse=False)
            db_obj['field'] = fields
            db_obj['conds'] = json.loads(db_obj['conds'])
            db_obj['filters']   = json.loads(db_obj['filters'])
            if DEBUG:
                print 'do_modify_get_special_field, db_obj: ',db_obj
        elif self.sheetid == 'formula':
            db_obj.tables   = ','.join(json.loads(db_obj.tables))
#        else:
#            model_id= db_obj.id
#            db_obj  = model_to_dict(db_obj, fields=self.pkeys,exclude=BASE_AUTO_ADD_FIELD)
#            fields  = []
#            for f in self.fields:
#                if db_obj.has_key(f.name):
#                    fields.append({'name': f.name, 'intro': f.intro, 'value': db_obj['name'], 'type': f.type.name})
#                    #db_obj[f.name]  = {'intro': f.intro, 'value': db_obj['name'], 'type': f.type.name}
#            db_obj  = fields
        return db_obj
    
    def do_modify_get_exception(self):
        """ 处理修改获取异常 """
        if self.sheetid == 'model':
            self.content['field_len']   = 1
            
    def do_add_special(self,db_obj):
        """ 处理增加记录的特殊操作 """
        if self.sheetid == 'model':
#            i   = 0
#            print "do_add_special:", self.fields
            for f in self.fields:
#                if f['name'] in BASE_AUTO_ADD_FIELD:
#                    self.fields.pop(i)
                #排除不需要的字段
                _id = f.pop('id')
                status  = f.pop('status')
                if _id != 0 or status != 1:
                    continue
#                print f
                f['model']  = db_obj
                #添加字段表记录
                print '------------ field table add record [', f, ']'
                f_obj   = Field2(**f)
                f_obj.save()
#                i   += 1
            create_db_table(db_obj,db_obj.get_django_model())
        elif self.sheetid == 'formula':
            pass
        else:
#            if self.dyn_model.num > 0:
#                db_obj.sn   = self.dyn_model.num + db_obj.id-1
##                db_obj.sn   = self.dyn_model.num
#                db_obj.save()
##                self.dyn_model.num  += 1
##                self.dyn_model.save()
##            for k,v in self.manytomanys.items():
##                setattr(db_obj,k,v)
##            db_obj.save()
            #于2014-07-22修改SN规则，sn=表ID+记录自增ID(4位)
            if self.dyn_model.num > 0:
                db_obj.sn   = int('%d%04d'%(self.dyn_model.id,db_obj.id))
                db_obj.save()
        self.content['sheets']  = get_sheets(program=self.program,locale=self.locale)
    
    def do_modify_special(self,db_obj):
        """ 处理修改记录的特殊操作 """
        if self.sheetid == 'model':
            django_model = db_obj.get_django_model()
            modified = False
            #老表的字段在新表中的字段名
            new_fields  = copy.copy(BASE_AUTO_ADD_FIELD)
#            new_foreign_keys    = []
            #新表增加的字段
            new_fields2 = []
            old_fields  = copy.copy(BASE_AUTO_ADD_FIELD)
            for f1 in self.fields:
                f   = copy.copy(f1)
                if f['name'] in BASE_AUTO_ADD_FIELD:
                    continue
                field_id= f.pop('id')
                status  = f.pop('status')
                #新增字段
                if field_id == 0:
                    if status > 1:
                        continue
                    new_fields2.append(f['name'])
                    f['model']  = db_obj
                    f_obj   = Field2(**f)
                    f_obj.save()
                    add_db_table_column(django_model,f['name'],f_obj.get_django_field())
                else:
                    if status == 1:
                        new_fields2.append(f['name'])
                        continue
                    else:
                        modified = True
                        try:
                            f_objs  = Field2.objects.filter(id=field_id)
                        except:
                            public.print_str('wariming: field id [%s] is not exists'%field_id)
                        else:
                            if public.objIsEmpty(f_objs):
                                public.print_str(u'记录ID【%s】不存在，请检查数据的正确性'%self.recordid)
                            else:
                                if status == 2:
                                    #删除
                                    #原字段名
#                                    field_name  = f_objs[0].name
#                                    field_type  = f_objs[0].type.name
                                    f_objs[0].delete()
#                                    delete_db_table_column(django_model, field_name, field_type)
                                    pass
                                else:
                                    #修改
                                    #原字段名
                                    field_name  = f_objs[0].name
                                    field_type  = f_objs[0].type.name
#                                    if f['name'] != field_name:
#                                        rename_db_table_column(django_model, field_name, f1['name'], field_type=f_objs[0].type.name)
                                    #修改Field2表记录
                                    f_objs.update(**f)
#                                    print 'field_name:',field_name
#                                    #修改对应表的字段
#                                    alter_db_table_column(django_model,field_name,f_objs[0].get_django_field())
                                    if f['type'].name == 'ForeignKey': 
                                        if field_type == 'ForeignKey':
                                            new_fields.append(f['name']+'_id')
                                            old_fields.append(field_name+'_id')
                                            try:
                                                db.delete_index(django_model._meta.db_table, [field_name])
                                            except:
                                                pass
#                                        else:
#                                            new_foreign_keys.append(f['name']+'_id')
#                                        print 'new_fields: ', new_fields
#                                        print 'old_fields: ', old_fields
                                    else:
                                        new_fields.append(f['name'])
                                        old_fields.append(field_name)
            if modified:
                t1  = '%d'%time.time()
                create_db_table(db_obj,django_model,suffix='_'+t1)
                table_name = django_model._meta.db_table
#                print 'INSERT INTO %s(%s) select %s from %s'%(table_name+'_'+t1,','.join(new_fields),','.join(old_fields), table_name)
                db.execute('INSERT INTO %s(%s) select %s from %s'%(table_name+'_'+t1,'"'+'","'.join(new_fields)+'"','"'+'","'.join(old_fields)+'"', table_name))                
#                for f2 in new_foreign_keys:
#                    print 'update %s set %s=0'%(table_name+'_'+t1,f2)
#                    db.execute('update %s set %s=0'%(table_name+'_'+t1,f2))
                db.execute('drop table %s'%table_name)
                db.execute('alter table %s rename to %s'%(table_name+'_'+t1,table_name))
#                if new_fields2:
#                    print 'update %s set %s'%(table_name+'_'+t1,'="" '.join(new_fields2))
#                    db.execute('update %s set %s'%(table_name+'_'+t1,'="" '.join(new_fields2)))
#                #添加字段表记录
#                f_obj   = Field2(**f)
#                f_obj.save()
            #create_db_table(db_obj,db_obj.get_django_model())
        else:
#            if self.dyn_model.num > 0:
#                db_obj.sn   = self.dyn_model.num
#                db_obj.save()
#                self.dyn_model.num  += 1
#                self.dyn_model.save()
            if self.dyn_model.num > 0 and not db_obj.sn:
                db_obj.sn   = int('%d%04d'%(self.dyn_model.id,db_obj.id))
                db_obj.save()

    def do_achieve_recordid(self):
        """ 处理特殊记录ID """
        if self.do_what in ['modify','delete'] and self.sheetid in ['topo_graph'] and self.reqmode == 'js':
            if self.do_what == 'modify':
                #print 'self.request.raw_post_data: ',self.request.raw_post_data
                self.recordid   = json.loads(self.request.raw_post_data).get('id','0')
            else:
                self.recordid   = self.request.GET.get('recordid','0')
#            if self.sheetid == 'topo_graph2' and int(self.recordid) < 1000:
#                self.recordid   = int(self.recordid) + 1000
            try:
                db_obj  = self.sheet_obj.objects.get(id=self.recordid)
            except self.sheet_obj.DoesNotExist:
                self.recordid= 0
            else:
                self.recordid   = db_obj.id
#                if self.sheetid == 'topo_graph2':
#                    self.recordid   += 1000
        else:
            self.recordid   = self.request.GET.get('recordid','0')
#        if self.sheetid == 'topo_graph2' and int(self.recordid) < 1000:
#            self.recordid   = int(self.recordid) + 1000
    
    def do_achieve_records(self,page,id=0):
        """ 处理获取记录数据 """
        #if self.sheetid in ['topo_graph','topo_map']:
        if self.view_all:
            pre_pages   = 10000
        else:
            pre_pages   = PER_PAGE
        if self.reqmode == 'js':
            if self.recordid:
                paginator,records   = self.paging(self.sheet_obj,10000,1,deleted=False,id=self.recordid)
            else:
                paginator,records   = self.paging(self.sheet_obj,10000,1,deleted=False)
            datas   = []
            for record in records:
                #datas.append(model_to_dict(record, fields=self.pkeys))
                d1  = model_to_dict(record, exclude=AUTO_ADD_FIELD2)
                d1['primary_id']    = d1.pop('id')
                datas.append(d1)
        elif self.export_csv:
            #paginator,contacts  = self.paging(self.sheet_obj,10000000,1,**self.achieves)
            paginator   = None
            datas   = self.sheet_obj.objects.filter(deleted=False)
        else:
            paginator,datas = self.paging(self.sheet_obj,pre_pages,page,deleted=False)
#            print datas
#        if public.objIsFull(datas):
#            print help(datas[0])
#            print datas[0].name.verbose_name
#            print datas[0].name.__class__.__name__
#            for k in datas[0]:
#                help(k)
#                break
#                self.pkeys.append()
#                self.pvalues.append()
        if self.sheetid != 'model' and  self.reqmode != 'js' and not self.export_csv:
            public.print_str('view html start')
            t1  = time.time()
            self.view_template(datas,page)
            public.print_str('view html end, %s'%(time.time()-t1))
        return paginator,datas
    
    def set_filter_kwargs(self):
        """ 初始化查询条件 """
        self.filter_kwargs  = {'id': int(self.recordid)}
    
    def do_spec_table(self):
        """ 处理特殊表 """
        if self.sheetid == 'trade_npc':
            paginator,records   = self.paging(self.sheet_obj,10000,1,deleted=False)
            datas   = []
            for record in records:
                datas.append(model_to_dict(record, fields=self.pkeys))
            public.write_json_file(PARAM_DEBUG_PATH, {'trad_npc': datas}, end='\n')
            
    def do_record_del(self,db_obj):
        """ 处理删除表记录 """
        if self.sheetid == 'model':
            delete_db_table(db_obj.get_django_model())
            db_obj.delete()            
        else:
            db_obj.deleted  = True
            db_obj.save()
    
    def view_template(self,datas,page):
        """ 查看记录模板 """
        self.pkeys  = []
        self.pvalues= []
        for f in self.fields:
            self.pkeys.append(f.name)
            if f.type.name == 'ForeignKey':
                view_all= 0
                if self.view_all:
                    view_all= 1
                self.pvalues.append('<a href="/parameters/%(pid)s/%(loc_id)s/%(sheet_name)s/?do_what=get&page=%(number)s&view_all=%(view_all)s&o=%(name)s__id" class="order">%(intro)s</a>'% \
                                  {'pid': self.program.markid, 'loc_id': self.locale.markid, 'sheet_name': self.sheetid, 'intro': f.intro, 'number': page, 'name': f.name,'view_all': view_all})
            else:
                self.pvalues.append(f.intro)
        if public.objIsFull(datas):
            number  = datas.number
            for d1 in datas: 
                self.temp_html  += '<tr>'
                self.temp_html  += '<td>'
                self.temp_html  += '<a href="/parameters/%(pid)s/%(loc_id)s/%(sheet_name)s/?do_what=modify&recordid=%(recordid)s&page=%(number)s">编辑</a>'% \
                {'pid': self.program.markid, 'loc_id': self.locale.markid, 'sheet_name': self.sheetid, 'recordid': d1.id, 'number': number}
                self.temp_html  += '</td>'
                self.temp_html  += '<td>%s</td>'%d1.id
                self.temp_html  += ''
                for f in self.fields:
                    self.temp_html   += '<!-- %s -->'%f.intro
                    self.temp_html  += '<td>'
                    if DEBUG:
                        print f.name
                    v1  = getattr(d1,f.name)
                    if DEBUG:
                        print '-----',f.name, v1
                    if not v1:
                        if f.type.name in ['IntegerField','FloatField']:
                            self.temp_html  += '0'
                        else:
                            self.temp_html  += ''
                    else:
                        if f.type.name == 'ImageField':
                            self.temp_html  += '<p><EMBED src="%(assets_url)s/cgame/assets/%(field)s.swf" width="75" height="75" wmode="transparent" menu="false" quality="high" type="application/x-shockwave-flash"></EMBED></p>'% \
                            {'assets_url': ASSETS_URL, 'field': v1}
                            self.temp_html  += '<p><a href="%(assets_url)s/cgame/assets/%(field)s.swf" target="_blank">%(field)s</a></p>'% \
                            {'assets_url': ASSETS_URL, 'field': v1}
                        elif f.type.name in ['TextField','JSONChar']:
                            if len(v1) > 8:
                                self.temp_html  += '<a href="#" title="%(value)s">%(value_short)s</a>'%{'value': v1, 'value_short': v1[:8]}
                            else:
                                self.temp_html  += v1
                        elif f.type.name == 'ForeignKey':
                            if v1:
                                self.temp_html   += '%s'%getattr(v1,self.foreign_keys[f.name])
                            else:
                                self.temp_html   += ''
                        #于2014-07-01 15:36修改，显示对应的字段列表
                        elif f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
                            v2  = []
                            to_obj  = self.foreign_keys[f.name]['to_obj']
                            display = self.foreign_keys[f.name]['display']
                            try:
                                v1  = json.loads(v1)
                            except:
                                if DEBUG:
                                    print 'v1: ',v1,'\nexcept:%r'%tb.format_exc()
                                v1  = []
                            for _id in v1:
                                try:
                                    r1  = to_obj.objects.get(id=_id)
                                except to_obj.DoesNotExist:
                                    v2.append('%s'%_id)
                                else:
                                    v2.append(getattr(r1,display))
                            tmp_str = '['+', '.join(v2)+']'
                            if len(tmp_str) > 8:
                                self.temp_html   += '<a href="#" title="%s">%s...</a>'%(tmp_str, tmp_str[:8])
                            else:
                                self.temp_html   += tmp_str
                        elif f.type.name == 'ManyForeignsField':
                            if v1:
                                for to_obj,to_model in self.foreign_keys[f.name]['to_obj']:
#                                    to_model= to_obj.get_django_model()
                                    try:
                                        r1  = to_model.objects.get(sn=v1)
                                    except to_model.DoesNotExist:
                                        pass
                                    else:
                                        v1  = getattr(r1,'name',v1)
                                        break
                                self.temp_html   += '%s'%v1
                            else:
                                self.temp_html   += ''
                        else:
                            self.temp_html   += '%s'%v1
                    self.temp_html  += '</td>'
                #self.temp_html  += '<!-- 删除 -->'
                self.temp_html  += '<td>'
                #self.temp_html  += '<a href="/parameters/{{ program.markid }}/{{ locale.markid }}/{{ sheet.name }}/?do_what=delete&recordid={{ data.id }}&page={{ datas.number }}">删除</a>'
                self.temp_html  += '<a href="/parameters/%(pid)s/%(loc_id)s/%(sheet_name)s/?do_what=delete&recordid=%(recordid)s&page=%(number)s">删除</a>'% \
                {'pid': self.program.markid, 'loc_id': self.locale.markid, 'sheet_name': self.sheetid, 'recordid': d1.id, 'number': number}
                self.temp_html  += '</td>'
                #self.temp_html  += '<!-- 多选删除 -->'
                self.temp_html  += '<td>'
                #self.temp_html  += '<a href="/parameters/{{ program.markid }}/{{ locale.markid }}/{{ sheet.name }}/?do_what=delete&recordid={{ data.id }}&page={{ datas.number }}">删除</a>'
                self.temp_html  += '<input type="checkbox" name="recordids" id="id_recordids_%(recordid)s" value="%(recordid)s"/>'%{'recordid': d1.id}
                self.temp_html  += '</td>'
                self.temp_html  += '</tr>'
    
    def translate_to_html(self, db_obj, fields, dyn_model):
        """ 将表字段转换成模板 """
        html = ''
        table   = dyn_model.name
        for f in fields:
            if f.name == 'sn' and dyn_model.num > 0:
                html += '<div class="form-group" style="display:none;">'
            else:
                html  += '<div class="form-group">'
            html  += '<div class="col-sm-3"><label for="name" class="control-label">%s</label></div>'%f.intro
            html  += '<div class="col-sm-9">'
            v1  = ''
            if public.objIsFull(db_obj):
                v1  = getattr(db_obj,f.name,'')
            if not v1:
                if f.type.name == 'IntegerField':
                    v1  = '0'
                elif f.type.name == 'FloatField':
                    v1  = '0.0'
                elif f.type.name == 'JSONChar':
                    v1  = '[]'
                elif f.type.name == 'TextField':
                    v1  = ''
                elif f.type.name in ['ManyToManyField','DictArray','RepM2MField','OddsField']:
                    v1  = '[]'
            if f.type.name == 'BooleanField':
                html  += '<label style="width:150px;float:left;background-color:#CCC;margin-right:2px;margin-bottom:2px;padding-left:5px;">'
                if v1:
                    html  += '<input id="id_%(table)_%(field)s" name="%(field)s" value="1" type="checkbox" checked="checked" />'%{'field': f.type.name,'table':table}
                else:
                    html  += '<input id="id_%(table)s_%(field)s" name="%(field)s" value="1" type="checkbox" />'%{'field': f.name, 'table': table}
                html  += '<span style="color:#000;">%s</span>'%f.intro
                html  += '</label>'
            elif f.type.name in ['ForeignKey','ManyToManyField','DictArray','RepM2MField']:
                try:
                    to_obj  = Sheet.objects.get(program=self.program.id,name=f.to)
                except Sheet.DoesNotExist:
                    self.tips   = '外键参数对应的表[%s]不存在'%f.to
                    public.print_str(self.tips)
                else:
                    model_obj   = to_obj.get_django_model()
                    if f.type.name == 'ForeignKey':
                        html  += '<select class="form-control" id="id_%(table)s_%(name)s" name="%(name)s">'%{'name': f.name, 'table': table}
                        #html  += '<select multiple class="form-control" id="id_%(name)s" name="%(name)s" style="width:150px;height:20px;">'%{'name': f.name}
                        html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                        for record in model_obj.objects.filter(deleted=False):
                            param1  = {'id': record.id, 'display': getattr(record,to_obj.display), 'table': table}
                            if v1 and record.id == getattr(v1,'id'):
                                html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param1
                            else:
                                html  += '<option value="%(id)s">%(display)s</option>'%param1
                        html  += '</select>'
                    else:
#                        html  += '%(sheetname)s<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="hidden" />'% \
#                        {'field': f.name, 'value': f.to, 'sheetname': to_obj.intro}
                        #于2014-07-01 15:36修改，显示成可添加状态
                        param1  = {'name': f.name,'to':f.to, 'table':f.to}
                        html  += '<p>'
                        html  += '<table width="500" border="0" cellpadding="2" cellspacing="1" id="id_%(table)s_%(name)s_frame">'%param1
                        html  += '<tr id="%(table)s_%(name)s_tr">'%param1
                        html  += '<td width="45" align="center" bgcolor="#96E0E2">序号</td>'
                        html  += '<td width="400" align="center" bgcolor="#96E0E2">%s</td>'%f.intro
                        html  += '<td width="45" align="center" bgcolor="#96E0E2">操作</td>'
                        html  += '</tr>'
                        param1['index'] = 0
                        try:
                            v1  = json.loads(v1)
                        except:
                            if DEBUG:
                                print 'v1: ',v1
                            v1  = []
                        for d1 in v1:
                            param1['index'] += 1
                            html  += '<tr id="id_%(name)s_tr%(index)s">'%param1
                            html  += '<td>'
                            html  += '%(index)s'%param1
                            html  += '</td>'
                            html  += '<td>'
                            html  += '<select id="id_%(table)s_%(name)s%(index)s" name="%(name)s%(index)s" style="width:150px;height:20px;">'%param1
                            html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                            for record in model_obj.objects.filter(deleted=False):
                                param2  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                                if d1 and d1 == record.id:
                                    html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param2
                                else:
                                    html  += '<option value="%(id)s">%(display)s</option>'%param2
                            html  += '</select>'
                            html  += '</td>'
                            html  += '<td>'
                            html  += '<div align="center" style="width:40px"><a href="javascript:void();" onclick="DeleteSignRow(\'id_%(table)s_%(name)s_frame\',\'id_%(table)s_%(name)s_tr%(index)s\')">删除</a></div>'%param1
                            html  += '</td>'
                            html  += '</tr>'
                        html  += '</table>'
                        html  += '</p>'
                        html  += '<p>'
                        html  += '<input type="button" name="%(name)s_add" value="添加记录" onclick="AddSignRow(\'id_%(table)s_%(name)s_frame\',\'id_%(table)s_%(name)s_index\',\'id_%(table)s_%(name)s_tr\',\'%(to)s\',\'%(name)s\')" />&nbsp;&nbsp;'%param1
                        html  += '<input type="button" name="%(name)s_clean" value="清空所有记录" onclick="ClearAllSign(\'id_%(table)s_%(name)s_frame\',\'id_%(table)s_%(name)s_index\',\'id_%(table)s_%(name)s_tr\')" />'%param1
                        param1['index'] += 1
                        html  += '<input name="%(name)s_index" type="hidden" id="id_%(table)s_%(name)s_index" value="%(index)s" />'%param1
                        html  += '</p>'
            elif f.type.name == 'ManyForeignsField':
                for to_obj,model_obj in self.foreign_keys[f.name]['to_obj']:
#                    model_obj   = to_obj.get_django_model()
                    html  += '<p><span style="width:100px;">%(to_intro)s：</span><select id="id_%(table)s_%(name)s_%(to_name)s" name="%(name)s_%(to_name)s" style="width:250px;height:20px;">'% \
                    {'name': f.name,'intro': f.intro, 'to_name': to_obj.name,'to_intro': to_obj.intro, 'table': table}
                    html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                    for record in model_obj.objects.filter(deleted=False):
                        _id = record.id
                        sn  = getattr(record,'sn',0)
                        param1  = {'sn': sn, 'display': getattr(record,'name', _id)}
                        if v1 and sn == v1:
                            html  += '<option value="%(sn)s" selected="selected">%(display)s</option>'%param1
                        else:
                            html  += '<option value="%(sn)s">%(display)s</option>'%param1
                    html  += '</select></p>'
            elif f.type.name == 'ImageField':
                html  += '<input id="id_%(table)s_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1,'table':table}
                html  += '<a href="http://220.dhh.darkhutgame.net:8080/view_res/?gameid=%s&localeid=chs" target="_blank">选择图片</a>'%self.program.markid
            elif f.type.name == 'TextField':
                html  += '<textarea id="id_%(table)s%(field)s" name="%(field)s" style="width:350px;height:120px;">%(value)s</textarea>'%{'field': f.name, 'value': v1, 'table': table}
            elif f.type.name == 'JSONChar':
#                print f.name, v1
                html  += '<input id="id_%(table)s_%(field)s" name="%(field)s" style="width:350px;" value=\'%(value)s\' type="text" />'%{'field': f.name, 'value': v1, 'table': table}
                html  += '&nbsp;&nbsp;<a href="javascript:void();" onclick="javascript:check_json(\'id_%(field)s\',\'%(intro)s\');">检查JSON格式</a>'%{'field': f.name, 'intro': f.intro}
                self.content['js_str']  = "javascript:return check_json(\'id_%(field)s\',\'%(intro)s\',\', 确认提交\');"%{'field': f.name, 'intro': f.intro}
            else:
                html  += '<input id="id_%(table)s_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1, 'table': table}
#            if f.help:
#                html  += '</p><p>&nbsp;&nbsp;%s'%f.help
            html  += '</div>'
            html  += '</div>'
        return html
    
    def edit_template(self,db_obj):
        """ 编辑记录模板 """
        if DEBUG:
            print '--------------------- ',db_obj,BASE_AUTO_ADD_FIELD
        for f in self.fields:
            if f.name == 'sn' and self.dyn_model.num > 0:
                self.temp_html  += '<tr style="display:none;">'
            else:
                self.temp_html  += '<tr>'
            self.temp_html  += '<td class="right_td">%s：</td>'%f.intro
            self.temp_html  += '<td class="left_td"><p>'
            v1  = ''
            if public.objIsFull(db_obj):
                v1  = getattr(db_obj,f.name,'')
            if not v1:
                if f.type.name == 'IntegerField':
                    v1  = '0'
                elif f.type.name == 'FloatField':
                    v1  = '0.0'
                elif f.type.name == 'JSONChar':
                    v1  = '[]'
                elif f.type.name == 'TextField':
                    v1  = ''
                elif f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
                    v1  = '[]'
            if f.type.name == 'BooleanField':
                self.temp_html  += '<label style="width:150px;float:left;background-color:#CCC;margin-right:2px;margin-bottom:2px;padding-left:5px;">'
                if v1:
                    self.temp_html  += '<input id="id_%(field)s" name="%(field)s" value="1" type="checkbox" checked="checked" />'%{'field': f.type.name}
                else:
                    self.temp_html  += '<input id="id_%(field)s" name="%(field)s" value="1" type="checkbox" />'%{'field': f.name}
                self.temp_html  += '<span style="color:#000;">%s</span>'%f.intro
                self.temp_html  += '</label>'
            elif f.type.name in ['ForeignKey','ManyToManyField','DictArray','RepM2MField']:
                try:
                    to_obj  = Sheet.objects.get(program=self.program.id,name=f.to)
                except Sheet.DoesNotExist:
                    self.tips   = '外键参数对应的表[%s]不存在'%f.to
                    public.print_str(self.tips)
                else:
                    model_obj   = to_obj.get_django_model()
                    if f.type.name == 'ForeignKey':
                        self.temp_html  += '<select id="id_%(name)s" name="%(name)s" style="width:150px;height:20px;">'%{'name': f.name}
                        self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                        for record in model_obj.objects.filter(deleted=False):
                            param1  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                            if v1 and record.id == getattr(v1,'id'):
                                self.temp_html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param1
                            else:
                                self.temp_html  += '<option value="%(id)s">%(display)s</option>'%param1
                        self.temp_html  += '</select>'
                    elif f.type.name == 'RepM2MField':
                        param1  = {'name': f.name,'to':f.to}
                        self.temp_html  += '<p>'
                        self.temp_html  += '<table width="500" border="0" cellpadding="2" cellspacing="1" id="id_%(name)s_frame">'%param1
                        self.temp_html  += '<tr id="%(name)s_tr">'%param1
                        self.temp_html  += '<td width="45" align="center" bgcolor="#96E0E2">序号</td>'
                        self.temp_html  += '<td width="400" align="center" bgcolor="#96E0E2">%s</td>'%f.intro
                        self.temp_html  += '<td width="45" align="center" bgcolor="#96E0E2">操作</td>'
                        self.temp_html  += '</tr>'
                        param1['index'] = 0
                        try:
                            v1  = json.loads(v1)
                        except:
                            if DEBUG:
                                print 'v1: ',v1
                            v1  = []
                        for d1 in v1:
                            param1['index'] += 1
                            self.temp_html  += '<tr id="id_%(name)s_tr%(index)s">'%param1
                            self.temp_html  += '<td>'
                            self.temp_html  += '%(index)s'%param1
                            self.temp_html  += '</td>'
                            self.temp_html  += '<td>'
                            self.temp_html  += '<select id="id_%(name)s%(index)s" name="%(name)s%(index)s" style="width:150px;height:20px;">'%param1
                            self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                            for record in model_obj.objects.filter(deleted=False):
                                param2  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                                if d1 and d1 == record.id:
                                    self.temp_html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param2
                                else:
                                    self.temp_html  += '<option value="%(id)s">%(display)s</option>'%param2
                            self.temp_html  += '</select>'
                            self.temp_html  += '</td>'
                            self.temp_html  += '<td>'
                            self.temp_html  += '<div align="center" style="width:40px"><a href="javascript:void();" onclick="DeleteSignRow(\'id_%(name)s_frame\',\'id_%(name)s_tr%(index)s\')">删除</a></div>'%param1
                            self.temp_html  += '</td>'
                            self.temp_html  += '</tr>'
                        self.temp_html  += '</table>'
                        self.temp_html  += '</p>'
                        self.temp_html  += '<p>'
                        self.temp_html  += '<input type="button" name="%(name)s_add" value="添加记录" onclick="AddSignRow(\'id_%(name)s_frame\',\'id_%(name)s_index\',\'id_%(name)s_tr\',\'%(to)s\',\'%(name)s\')" />&nbsp;&nbsp;'%param1
                        self.temp_html  += '<input type="button" name="%(name)s_clean" value="清空所有记录" onclick="ClearAllSign(\'id_%(name)s_frame\',\'id_%(name)s_index\',\'id_%(name)s_tr\')" />'%param1
                        param1['index'] += 1
                        self.temp_html  += '<input name="%(name)s_index" type="hidden" id="id_%(name)s_index" value="%(index)s" />'%param1
                        self.temp_html  += '</p>'
                    else:
                        #于2014-07-01 15:36修改，显示成可添加状态
                        try:
                            v1  = json.loads(v1)
                        except:
                            if DEBUG:
                                print 'v1: ',v1
                            v1  = []
                        param1  = {'name': f.name,'to':f.to, 'table': self.sheetid, 'value': ','.join([str(v2) for v2 in v1])}
                        self.temp_html  += '<div class="col-sm-12">'
                        self.temp_html  += '<div class="col-sm-8">'
                        self.temp_html  += '<input id="id_%(table)s_%(name)s_selected" name="%(name)s_selected" value="%(value)s" type="hidden" />'%param1
                        self.temp_html  += '<select multiple class="multi" id="id_%(table)s_%(name)s" name="%(name)s" size="8">'%param1
                        for record in model_obj.objects.filter(deleted=False):                            
                            param2  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                            if record.id in v1:
                                self.temp_html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param2
                            else:
                                self.temp_html  += '<option value="%(id)s">%(display)s</option>'%param2
                        self.temp_html  += '</select>'
                        if f.type.name == 'DictArray':
                            #弹窗添加外键表记录
                            self.temp_html  += '</div>'
                            self.temp_html  += '<div class="col-sm-4">'
                            self.temp_html  += '<button type="button" class="btn btn-primary" data-toggle="modal" data-target=".%s-modal-lg">添加%s</button>'%(f.to,to_obj.intro)
                            self.temp_html  += '</div>'
                            self.temp_html  += '</div>'
                            self.temp_html2 += '<div class="modal fade %(to)s-modal-lg" tabindex="-1" role="dialog" aria-labelledby="%(to)s_largeModalLabel" aria-hidden="true" id="id_%(to)s_modal">'%{'to': f.to}
                            self.temp_html2 += '<div class="modal-dialog modal-lg">'
                            self.temp_html2 += '<div class="modal-content">'
                            self.temp_html2 += '<div class="modal-header">'
                            self.temp_html2 += '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'
                            self.temp_html2 += '<h4 class="modal-title" id="myModalLabel">%s</h4>'%to_obj.intro
                            self.temp_html2 += '</div>'
                            self.temp_html2 += '<div class="modal-body">'
                            self.temp_html2 += '<form id="id_%(name)s_form" class="form-horizontal" role="form">'%param1
                            #self.temp_html2 += '<table>'
                            mm_fields   = Field2.objects.filter(model=to_obj.id).exclude(name__in=BASE_AUTO_ADD_FIELD)
                            self.temp_html2 += self.translate_to_html(None, mm_fields, to_obj)
                            #self.temp_html2 += '</table>'
                            self.temp_html2 += '</form>'
                            self.temp_html2 += '</div>'
                            self.temp_html2 += '<div class="modal-footer">'
                            self.temp_html2 += '<button type="button" class="btn btn-default" data-dismiss="modal">关闭</button>'
                            self.temp_html2 += '''<button type="button" class="btn btn-primary" onclick="javascript:save_record('%s','%s', '%s', '%s')">保存</button>'''% \
                            (f.to,','.join([f2.name for f2 in mm_fields]), to_obj.display, 'id_'+self.sheetid+'_'+f.name)
                            self.temp_html2 += '</div>'
                            self.temp_html2 += '</div>'
                            self.temp_html2 += '</div>'
                            self.temp_html2 += '</div>'
            elif f.type.name == 'ManyForeignsField':
                for to_obj,model_obj in self.foreign_keys[f.name]['to_obj']:
#                    model_obj   = to_obj.get_django_model()
                    self.temp_html  += '<p><span style="width:100px;">%(to_intro)s：</span><select id="id_%(name)s_%(to_name)s" name="%(name)s_%(to_name)s" style="width:250px;height:20px;">'% \
                    {'name': f.name,'intro': f.intro, 'to_name': to_obj.name,'to_intro': to_obj.intro}
                    self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                    for record in model_obj.objects.filter(deleted=False):
                        _id = record.id
                        sn  = getattr(record,'sn',0)
                        param1  = {'sn': sn, 'display': getattr(record,'name', _id)}
                        if v1 and sn == v1:
                            self.temp_html  += '<option value="%(sn)s" selected="selected">%(display)s</option>'%param1
                        else:
                            self.temp_html  += '<option value="%(sn)s">%(display)s</option>'%param1
                    self.temp_html  += '</select></p>'
            elif f.type.name == 'ImageField':
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1}
                self.temp_html  += '<a href="http://220.dhh.darkhutgame.net:8080/view_res/?gameid=%s&localeid=chs" target="_blank">选择图片</a>'%self.program.markid
            elif f.type.name == 'OddsField':
                #获取被筛选的表和分类字段（如果有的话）
                inst_sheet  = None
                inst_sheet_obj  = None
                inst_field  = None
                if self.dyn_model.filters:
                    filters = json.loads(self.dyn_model.filters)
                    inst_name   = filters.get('inst_name')
                    inst_field  = filters.get('inst_field')
                    if inst_name:
                        inst_sheet  = Sheet.objects.get(program=self.program.id, name=inst_name,deleted=False)
                        inst_sheet_obj  = inst_sheet.get_django_model()
                        if inst_field:
                            inst_field  = Field2.objects.get(model=inst_sheet.id, name=inst_field)
                #写表头
                param1  = {'name': f.name,'index': 0, 'inst_field_name': inst_field.name}
                self.temp_html  += '<p>'
                self.temp_html  += '<table width="1000" border="0" cellpadding="2" cellspacing="1" id="id_%(name)s_frame">'%param1
                self.temp_html  += '<tr id="%(name)s_tr">'%param1
                self.temp_html  += '<td width="30" align="center" bgcolor="#96E0E2">序号</td>'
                if inst_field:
                    self.temp_html  += '<td width="120" align="center" bgcolor="#96E0E2">%s</td>'%inst_field.intro
                self.temp_html  += '<td width="60" align="center" bgcolor="#96E0E2">记录数量</td>'
                self.temp_html  += '<td width="120" align="center" bgcolor="#96E0E2">掉率(%)</td>'
                self.temp_html  += '<td width="600" align="center" bgcolor="#96E0E2">选择记录</td>'
                self.temp_html  += '</tr>'
                if self.do_what == 'modify':
                    #根据条件筛选出数据
                    frecords= {}
                    conds2  = {'deleted': False}
                    for cond in json.loads(getattr(self.dyn_model,'conds','[]')):
                        if isinstance(db_obj, dict):
                            conds2[cond] = db_obj[cond].id
                        else:
                            conds2[cond]    = getattr(db_obj, cond).id
                    inst_field_name = ""
                    if inst_field:
                        inst_field_name = inst_field.name
                    display = inst_sheet.display
                    #要排除已经被删除的数据
                    conds2['deleted'] = False
                    print 'conds2: ', conds2
                    for r in inst_sheet_obj.objects.filter(**conds2):
                        inst_value  = ''
                        if inst_field_name:
                            inst_value  = getattr(r, inst_field_name, '')
                            if isinstance(inst_value,object):
                                inst_value  = inst_value.id
                        if frecords.has_key(inst_value):
                            frecords[inst_value].append(r)
                        else:
                            frecords[inst_value]    = [r]
                    #填充表数据
                    try:
                        v1  = json.loads(v1)
                    except:
                        if DEBUG:
                            print 'v1: ',v1
                        v1  = []
                    print "v1: ",v1, frecords
                    if v1:    
                        for rare, cards in frecords.items():
                            rare= str(rare)
                            checked_cards   = []
                            odds    = 0.0
                            for d1 in v1:
                                if d1['rare'] == rare:
                                    checked_cards   = d1['cards']
                                    odds    = d1['odds']
                                    break
                            param1['index'] += 1
                            self.temp_html  += '<tr id="id_%(name)s_tr%(index)s">'%param1
                            self.temp_html  += '<td>'
                            self.temp_html  += '%(index)s'%param1
                            self.temp_html  += '</td>'
                            if inst_field:
                                self.temp_html  += '<td>'
                                self.temp_html  += '<input id="id_%(name)s_rare%(index)s" name="%(name)s_rare%(index)s" style="width:100px;" '%param1+'value="%s" readonly="readonly" >'%rare
                                self.temp_html  += '</td>'
                            
                            self.temp_html  += '<td>'
                            self.temp_html  += '%s'%len(cards)
                            self.temp_html  += '</td>'
                            self.temp_html  += '<td>'
                            self.temp_html  += '<input id="id_%(name)s_odds%(index)s" name="%(name)s_odds%(index)s" style="width:100px;" '%param1+'value="%s" type="text" />'%odds
                            self.temp_html  += '</td>'
                            #记录筛选
                            self.temp_html  += '<td>'
                            for r in cards:
                                self.temp_html  += '<label style="width:120px;float:left;background-color:#CCC;margin-right:2px;margin-bottom:2px;padding-left:5px;">'
                                if r.sn in checked_cards:
                                    self.temp_html  += '<input type="checkbox" checked="checked" value="%s"'%r.sn+' name="%(name)s_card%(index)s" id="id_%(name)s_card%(index)s_'%param1+'%s">'%r.sn
                                else:
                                    self.temp_html  += '<input type="checkbox" value="%s"'%r.sn+' name="%(name)s_card%(index)s" id="id_%(name)s_card%(index)s_'%param1+'%s">'%r.sn
                                self.temp_html  += '<span style="color:#000;">&nbsp;%s</span>'%getattr(r,display)
                                self.temp_html  += '</label>'
                            self.temp_html  += '</td>'
                            self.temp_html  += '</tr>'
                        param1['index'] += 1
                self.temp_html  += '</table>'
                self.temp_html  += '</p>'
                self.temp_html  += '<p>'
                self.temp_html  += '<input type="button" name="add" value="填写掉率" onclick="write_rare(\'id_%(name)s_frame\',\'set_id\')">'%param1
                self.temp_html  += '<input name="%(name)s_index" type="hidden" id="id_%(name)s_index" value="%(index)s">'%param1
                self.temp_html  += '</p>'
            elif f.type.name == 'TextField':
                self.temp_html  += '<textarea id="id_%(field)s" name="%(field)s" style="width:350px;height:120px;">%(value)s</textarea>'%{'field': f.name, 'value': v1}
            elif f.type.name == 'JSONChar':
#                print f.name, v1
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:350px;" value=\'%(value)s\' type="text" />'%{'field': f.name, 'value': v1}
                self.temp_html  += '&nbsp;&nbsp;<a href="javascript:void();" onclick="javascript:check_json(\'id_%(field)s\',\'%(intro)s\');">检查JSON格式</a>'%{'field': f.name, 'intro': f.intro}
                self.content['js_str']  = "javascript:return check_json(\'id_%(field)s\',\'%(intro)s\',\', 确认提交\');"%{'field': f.name, 'intro': f.intro}
            else:
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1}
#            if f.help:
#                self.temp_html  += '</p><p>&nbsp;&nbsp;%s'%f.help
            self.temp_html  += '</p></td>'
            self.temp_html  += '</tr>'
    
    def edit_template_201412091416(self,db_obj):
        """ 编辑记录模板,2014-12-09 14:16备份 """
        if DEBUG:
            print '--------------------- ',db_obj,BASE_AUTO_ADD_FIELD
        for f in self.fields:
            if f.name == 'sn' and self.dyn_model.num > 0:
                self.temp_html  += '<tr style="display:none;">'
            else:
                self.temp_html  += '<tr>'
            self.temp_html  += '<td class="right_td">%s：</td>'%f.intro
            self.temp_html  += '<td class="left_td"><p>'
            v1  = ''
            if public.objIsFull(db_obj):
                v1  = getattr(db_obj,f.name,'')
            if not v1:
                if f.type.name == 'IntegerField':
                    v1  = '0'
                elif f.type.name == 'FloatField':
                    v1  = '0.0'
                elif f.type.name == 'JSONChar':
                    v1  = '[]'
                elif f.type.name == 'TextField':
                    v1  = ''
                elif f.type.name == 'ManyToManyField':
                    v1  = '[]'
            if f.type.name == 'BooleanField':
                self.temp_html  += '<label style="width:150px;float:left;background-color:#CCC;margin-right:2px;margin-bottom:2px;padding-left:5px;">'
                if v1:
                    self.temp_html  += '<input id="id_%(field)s" name="%(field)s" value="1" type="checkbox" checked="checked" />'%{'field': f.type.name}
                else:
                    self.temp_html  += '<input id="id_%(field)s" name="%(field)s" value="1" type="checkbox" />'%{'field': f.name}
                self.temp_html  += '<span style="color:#000;">%s</span>'%f.intro
                self.temp_html  += '</label>'
            elif f.type.name in ['ForeignKey','ManyToManyField']:
                try:
                    to_obj  = Sheet.objects.get(program=self.program.id,name=f.to)
                except Sheet.DoesNotExist:
                    self.tips   = '外键参数对应的表[%s]不存在'%f.to
                    public.print_str(self.tips)
                else:
                    model_obj   = to_obj.get_django_model()
                    if f.type.name == 'ForeignKey':
                        self.temp_html  += '<select id="id_%(name)s" name="%(name)s" style="width:150px;height:20px;">'%{'name': f.name}
                        self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                        for record in model_obj.objects.filter(deleted=False):
                            param1  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                            if v1 and record.id == getattr(v1,'id'):
                                self.temp_html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param1
                            else:
                                self.temp_html  += '<option value="%(id)s">%(display)s</option>'%param1
                        self.temp_html  += '</select>'
                    else:
#                        self.temp_html  += '%(sheetname)s<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="hidden" />'% \
#                        {'field': f.name, 'value': f.to, 'sheetname': to_obj.intro}
                        #于2014-07-01 15:36修改，显示成可添加状态
                        param1  = {'name': f.name,'to':f.to}
                        self.temp_html  += '<p>'
                        self.temp_html  += '<table width="500" border="0" cellpadding="2" cellspacing="1" id="id_%(name)s_frame">'%param1
                        self.temp_html  += '<tr id="%(name)s_tr">'%param1
                        self.temp_html  += '<td width="45" align="center" bgcolor="#96E0E2">序号</td>'
                        self.temp_html  += '<td width="400" align="center" bgcolor="#96E0E2">%s</td>'%f.intro
                        self.temp_html  += '<td width="45" align="center" bgcolor="#96E0E2">操作</td>'
                        self.temp_html  += '</tr>'
                        param1['index'] = 0
                        try:
                            v1  = json.loads(v1)
                        except:
                            if DEBUG:
                                print 'v1: ',v1
                            v1  = []
                        for d1 in v1:
                            param1['index'] += 1
                            self.temp_html  += '<tr id="id_%(name)s_tr%(index)s">'%param1
                            self.temp_html  += '<td>'
                            self.temp_html  += '%(index)s'%param1
                            self.temp_html  += '</td>'
                            self.temp_html  += '<td>'
                            self.temp_html  += '<select id="id_%(name)s%(index)s" name="%(name)s%(index)s" style="width:150px;height:20px;">'%param1
                            self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                            for record in model_obj.objects.filter(deleted=False):
                                param2  = {'id': record.id, 'display': getattr(record,to_obj.display)}
                                if d1 and d1 == record.id:
                                    self.temp_html  += '<option value="%(id)s" selected="selected">%(display)s</option>'%param2
                                else:
                                    self.temp_html  += '<option value="%(id)s">%(display)s</option>'%param2
                            self.temp_html  += '</select>'
                            self.temp_html  += '</td>'
                            self.temp_html  += '<td>'
                            self.temp_html  += '<div align="center" style="width:40px"><a href="javascript:void();" onclick="DeleteSignRow(\'id_%(name)s_frame\',\'id_%(name)s_tr%(index)s\')">删除</a></div>'%param1
                            self.temp_html  += '</td>'
                            self.temp_html  += '</tr>'
                        self.temp_html  += '</table>'
                        self.temp_html  += '</p>'
                        
                        #弹窗添加外键表记录
                        self.temp_html  += '<button type="button" class="btn btn-primary" data-toggle="modal" data-target=".%s-modal-lg">添加%s</button>'%(f.to,to_obj.intro)
                        self.temp_html  += '<div class="modal fade %(to)s-modal-lg" tabindex="-1" role="dialog" aria-labelledby="%(to)s_largeModalLabel" aria-hidden="true" id="id_%(to)s_modal">'%{'to': f.to}
                        self.temp_html  += '<div class="modal-dialog modal-lg">'
                        self.temp_html  += '<div class="modal-content">'
                        self.temp_html  += '<div class="modal-header">'
                        self.temp_html  += '<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'
                        self.temp_html  += '<h4 class="modal-title" id="myModalLabel">%s</h4>'%to_obj.intro
                        self.temp_html  += '</div>'
                        self.temp_html  += '<div class="modal-body">'
                        self.temp_html  += '<form>'
                        self.temp_html  += '<table>'
                        mm_fields   = Field2.objects.filter(model=to_obj.id).exclude(name__in=BASE_AUTO_ADD_FIELD)
                        self.temp_html  += self.translate_to_html(None, mm_fields, to_obj)
                        self.temp_html  += '</table>'
                        self.temp_html  += '</form>'
                        self.temp_html  += '</div>'
                        self.temp_html  += '<div class="modal-footer">'
                        self.temp_html  += '<button type="button" class="btn btn-default" data-dismiss="modal">Close</button>'
                        self.temp_html  += '''<button type="button" class="btn btn-primary" onclick="javascript:save_record('%s','%s')">Save changes</button>'''% \
                        (f.to,','.join([f2.name for f2 in mm_fields]))
                        self.temp_html  += '</div>'
                        self.temp_html  += '</div>'
                        self.temp_html  += '</div>'
                        self.temp_html  += '</div>'
                        
                        self.temp_html  += '<p>'
                        self.temp_html  += '<input type="button" name="%(name)s_add" value="添加记录" onclick="AddSignRow(\'id_%(name)s_frame\',\'id_%(name)s_index\',\'id_%(name)s_tr\',\'%(to)s\',\'%(name)s\')" />&nbsp;&nbsp;'%param1
                        self.temp_html  += '<input type="button" name="%(name)s_clean" value="清空所有记录" onclick="ClearAllSign(\'id_%(name)s_frame\',\'id_%(name)s_index\',\'id_%(name)s_tr\')" />'%param1
                        param1['index'] += 1
                        self.temp_html  += '<input name="%(name)s_index" type="hidden" id="id_%(name)s_index" value="%(index)s" />'%param1
                        self.temp_html  += '</p>'
            elif f.type.name == 'ManyForeignsField':
                for to_obj,model_obj in self.foreign_keys[f.name]['to_obj']:
#                    model_obj   = to_obj.get_django_model()
                    self.temp_html  += '<p><span style="width:100px;">%(to_intro)s：</span><select id="id_%(name)s_%(to_name)s" name="%(name)s_%(to_name)s" style="width:250px;height:20px;">'% \
                    {'name': f.name,'intro': f.intro, 'to_name': to_obj.name,'to_intro': to_obj.intro}
                    self.temp_html  += '<option value="0">请选择一个%s</option>'%to_obj.intro
                    for record in model_obj.objects.filter(deleted=False):
                        _id = record.id
                        sn  = getattr(record,'sn',0)
                        param1  = {'sn': sn, 'display': getattr(record,'name', _id)}
                        if v1 and sn == v1:
                            self.temp_html  += '<option value="%(sn)s" selected="selected">%(display)s</option>'%param1
                        else:
                            self.temp_html  += '<option value="%(sn)s">%(display)s</option>'%param1
                    self.temp_html  += '</select></p>'
            elif f.type.name == 'ImageField':
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1}
                self.temp_html  += '<a href="http://220.dhh.darkhutgame.net:8080/view_res/?gameid=%s&localeid=chs" target="_blank">选择图片</a>'%self.program.markid
            elif f.type.name == 'TextField':
                self.temp_html  += '<textarea id="id_%(field)s" name="%(field)s" style="width:350px;height:120px;">%(value)s</textarea>'%{'field': f.name, 'value': v1}
            elif f.type.name == 'JSONChar':
#                print f.name, v1
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:350px;" value=\'%(value)s\' type="text" />'%{'field': f.name, 'value': v1}
                self.temp_html  += '&nbsp;&nbsp;<a href="javascript:void();" onclick="javascript:check_json(\'id_%(field)s\',\'%(intro)s\');">检查JSON格式</a>'%{'field': f.name, 'intro': f.intro}
                self.content['js_str']  = "javascript:return check_json(\'id_%(field)s\',\'%(intro)s\',\', 确认提交\');"%{'field': f.name, 'intro': f.intro}
            else:
                self.temp_html  += '<input id="id_%(field)s" name="%(field)s" style="width:150px;" value="%(value)s" type="text" />'%{'field': f.name, 'value': v1}
#            if f.help:
#                self.temp_html  += '</p><p>&nbsp;&nbsp;%s'%f.help
            self.temp_html  += '</p></td>'
            self.temp_html  += '</tr>'
    
    def do_csv_data(self,datas):
        """ 处理导入CSV文件的记录 """
        rd  = []
        for d1 in datas:
            rd2 = []
            for f in self.fields:
                v1  = getattr(d1,f.name)
                if not v1:
                    if f.type.name in ['IntegerField','FloatField']:
                        rd2.append('0')
                    else:
                        rd2.append('')
                else:
                    if f.type.name == 'ForeignKey':
                        if v1:
                            rd2.append('%s'%getattr(v1,self.foreign_keys[f.name]))
                        else:
                            rd2.append('')
                    elif f.type.name in ['ManyToManyField','DictArray','RepM2MField']:
                        v2  = []
                        to_obj  = self.foreign_keys[f.name]['to_obj']
                        display = self.foreign_keys[f.name]['display']
                        try:
                            v1  = json.loads(v1)
                        except:
                            v1  = []
                        for _id in v1:
                            try:
                                r1  = to_obj.objects.get(id=_id)
                            except to_obj.DoesNotExist:
                                v2.append('%s'%_id)
                            else:
                                v2.append(getattr(r1,display))
                        rd2.append('['+', '.join(v2)+']')
                    else:
                        rd2.append('%s'%v1)
            rd.append(rd2)
        return rd
    
    def do_sheet(self):
        """ 处理表 """
        self.sheet_init()
        self.req_method = self.request.method
        self.do_what= urllib.unquote(self.request.GET.get('do_what', 'get'))
        page    = self.request.GET.get('page', '1')
        #recordid= self.request.GET.get('recordid','0')
        self.export_csv = (self.request.GET.get('export_csv') == '1')
        self.order  = self.request.GET.get('o','')
        self.do_achieve_recordid()
        paginator   = None
        datas   = None
        if self.sheet_obj is None:
            self.tips   = '表【%s】不存在'%self.sheetname
        #查看玩家反馈信息
        elif self.do_what == 'get':
            #paginator,datas = self.paging(self.sheet_obj,PER_PAGE,page,deleted=False)
            paginator,datas = self.do_achieve_records(page)
            if self.export_csv:
                public.print_str('make csv data start')
                self.csv_name= self.sheetname
                if os.path.exists('/root'):
                    self.csv_name   = public._2utf8(self.csv_name)
                else:
                    self.csv_name   = str(self.csv_name)
                self.csv_datas.append(self.pvalues)
                self.csv_datas.append(self.pkeys)
#                for record in datas:
#                    l1  = []
#                    for key in self.pkeys:
#                        try:
#                            v1  = getattr(record, key, '')
#                        except AttributeError:
#                            public.print_str('key [%s] is not exist'%key)
#                        else:
#                            l1.append(v1)
#                    self.csv_datas.append(l1)
                self.csv_datas.extend(self.do_csv_data(datas))
                public.print_str('make csv data end')
        elif self.do_what in ['add','modify']:
            if self.req_method == 'POST':
                #self.achieves = {'createtime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'uuid':'%s'%uuid.uuid4(),
                #                'deleted':False}
                self.sheet_do_add_req_data()
                db_obj  = None
                #有空数据
                if public.objIsFull(self.empties):
                    self.tips= u'【%s】为空'%(u'，'.join(self.empties))
                    self.do_modify_post_exception()
                    datas   = self.achieves
                elif public.objIsFull(self.tips):
                    self.do_modify_post_exception()
                    datas   = self.achieves
                else:
                    #添加记录
                    if self.do_what == 'add':
                        #print self.achieves
                        db_obj  = self.sheet_obj(**self.achieves)
                        db_obj.save()
                        self.do_add_special(db_obj)
                        #最后一页查看刚刚添加的数据记录
                        page= 9999
                    #修改记录
                    else:
                        if public.objIsEmpty(self.recordid):
                            self.tips= u'记录ID为空，请检查数据的正确性'
                        else:
                            try:
                                self.set_filter_kwargs()
                                db_objs = self.sheet_obj.objects.filter(**self.filter_kwargs)
                            #except self.sheet_obj.DoesNotExist:
                            except:
                                self.tips= u'记录ID【%s】不存在，请检查数据的正确性'%self.recordid
                                self.do_modify_post_exception()
                                datas   = self.achieves
                            else:
                                if public.objIsEmpty(db_objs):
                                    public.print_str(u'记录ID【%s】不存在，请检查数据的正确性'%self.recordid)
                                    self.do_modify_post_exception()
                                    datas   = self.achieves
                                else:
                                    public.print_str(u'记录ID【%s】更新， %s'%(self.recordid,self.achieves))
                                    db_objs.update(**self.achieves)
                                    self.do_modify_special(db_objs[0])
                                    db_obj  = db_objs[0]
                    if public.objIsEmpty(self.tips):
                        #获取最后一页的数据
                        #paginator,datas = self.paging(self.sheet_obj,PER_PAGE,page,deleted=False)
                        if self.reqmode == 'js':
                            paginator   = None
                            d2  = model_to_dict(db_obj, exclude=AUTO_ADD_FIELD2)
                            d2['primary_id']    = d2.pop('id')
                            datas   = [d2]
                            if DEBUG:
                                print '----------js datas', datas
                        else:
                            self.do_spec_table()
                            paginator,datas = self.do_achieve_records(page)
                        self.do_what = 'get'
            #跳转到添加、修改页面
            elif self.req_method == 'GET':
                try:
                    db_obj  = self.sheet_obj.objects.get(id=int(self.recordid))
                except self.sheet_obj.DoesNotExist:
                    self.do_modify_get_exception()
                else:
                    #db_obj.pk_profit_add= json.loads(db_obj.pk_profit_add)                    
                    datas   = self.do_modify_get_special_field(db_obj)
            if self.sheetid != 'model' and self.do_what in ['add','modify']:
                if DEBUG:
                    print self.tips
                self.edit_template(datas)
        elif self.do_what == 'delete':
            #删除反馈记录
            if self.req_method == 'POST':
                recordids   = self.request.REQUEST.getlist('recordids')
            elif self.req_method == 'GET':
                recordids   = [self.recordid]
            for recordid in recordids:
                try:
                    db_obj  = self.sheet_obj.objects.get(id=int(recordid))
                except self.sheet_obj.DoesNotExist:
                    pass
                else:
                    self.do_record_del(db_obj)
            #paginator,datas = self.paging(self.sheet_obj,PER_PAGE,page,deleted=False)
            paginator,datas = self.do_achieve_records(page)
            self.do_what = 'get'
        print 'self.tips: ',self.tips
        self.content.update({'datas': datas, 
                             'title': self.pvalues,
                             'data_title': self.sheetname,
                             'tips': self.tips,
                             'recordid': self.recordid,
                             'page': page,
                             'do_what': self.do_what,
                             'paginator': paginator,
                             'pkeys': self.pkeys,
                             'full_screen_swf': self.full_screen_swf,
                             'full_screen_swf_name': self.full_screen_swf_name,
                             'card_type': self.card_type,
                             'view_all': self.view_all,
                             'temp_html': self.temp_html,
                             'temp_html2': self.temp_html2,
                             'order': self.order,
                             })
        
if __name__ == "__main__":
    
    print __file__
#    model   = __import__('operate_backend')
    obj = ParamMain()
    getattr(obj, 'test_getattr')()
    
    