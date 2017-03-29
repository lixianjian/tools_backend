#!/usr/bin/python2.7
#coding=utf-8
'''
Created on 2013-8-9

@author: lixianjian
'''

from django.template import RequestContext
from django.http import HttpResponseRedirect,HttpResponseForbidden,HttpResponseServerError,HttpResponse
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
import csv

from libs.config import glocale,DEBUG,DEFAULT_LOGIN_PATH
from libs import public, register
#静态数据
const_data  = {'glocale': glocale,
               }

#登陆页面路径
LOGIN_PAGE  = 'login/login_page.html'
#修改密码页面路径
ALTER_PAGE  = 'login/alter.html'
#首页路径
INDEX_PAGE  = 'main.html'


def login(request):
    """ 入口 """
    if DEBUG:
        print 'HTTP_HOST:',request.META['HTTP_HOST']
        public.print_str('login')
        public.print_str('------- request.user: %s'%request.user)
        public.print_str('------- request.user.username: %s'%request.user.username)
    if DEBUG:
        print 'request.method: ',request.method
    if request.method == 'GET':
        pre_path= request.get_full_path()
        if DEBUG:
            print 'GET pre_path: ',pre_path
        if pre_path in ['/login/','/quity/']:
            pre_path = DEFAULT_LOGIN_PATH
        if request.user.is_authenticated():
            return HttpResponseRedirect(pre_path)
        content = {'form_action':'/login/','glocale': glocale,'pre_path': pre_path}
        content.update(csrf(request))
        return render_to_response(LOGIN_PAGE,content)
    elif request.method == 'POST':
        pre_path= request.POST.get('pre_path')
        msg = register.login(request)
        if msg.get('status',1) == 0:
            if not request.user.has_perm('auth.view_web'):
                register.logout(request)
                return HttpResponseForbidden()
            if pre_path is None:
                pre_path = DEFAULT_LOGIN_PATH
            if DEBUG:
                print 'POST pre_path: ',pre_path
            return HttpResponseRedirect(pre_path)
        else:
            content = {'tips': msg.get('tips',glocale.LN_UID_NAME_ERROR),'form_action':'/login/',
                       'glocale': glocale, 'pre_path': pre_path}
            content.update(csrf(request))
            return render_to_response(LOGIN_PAGE,content,context_instance=RequestContext(request))
    else:
        return HttpResponseServerError()

def alter_password(request):
    """ 修改密码 """
    if DEBUG:
        print 'HTTP_HOST:',request.META['HTTP_HOST']
        public.print_str('login')
        public.print_str('------- request.user: %s'%request.user)
        public.print_str('------- request.user.username: %s'%request.user.username)
    content = {'data_title': glocale.LN_ALTER_PASSWORD,
               'form_action':'/alter_password/',}
    if request.method == 'GET':
        pre_path= request.get_full_path()
        if pre_path == '/alter_password/':
            pre_path = DEFAULT_LOGIN_PATH
        if request.user.is_authenticated():
            return HttpResponseRedirect(pre_path)
        content['pre_path'] = pre_path
        content.update(csrf(request))
        return render_to_response(ALTER_PAGE,content)
    elif request.method == 'POST':
        pre_path= request.POST.get('pre_path')
        msg = register.alter(request)
        if msg.get('status',1) == 0:
            if not request.user.has_perm('auth.view_web'):
                register.logout(request)
                return HttpResponseForbidden()
            if pre_path is None:
                pre_path = DEFAULT_LOGIN_PATH
            return HttpResponseRedirect(pre_path)
        else:
            content.update({'tips': msg.get('tips',glocale.LN_FAIL),'pre_path': pre_path})
            content.update(csrf(request))
            return render_to_response(ALTER_PAGE,content,context_instance=RequestContext(request))
    else:
        return HttpResponseServerError()
        
def quity(request):
    """ 出口 """
    register.logout(request)
    return login(request)

def some_view(data, output_name='excel_data'):
    """ 写CSV文件 """
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


if __name__ == "__main__":
    
    pass