#coding=utf-8
#全局变量设置

from django.http import HttpResponse,HttpResponseForbidden,HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from django.template import loader, RequestContext
from django.conf import settings
#import sys
#import os
import traceback as tb
#import datetime
#import shutil
import json

from libs.register import logout
import param_main
#from param_main import entrance,param_main_response,choose_param
from libs import public
#from libs.do_sqllite import SqlLite
#from settings import DATABASES
from models import Sheet,Field2
#ctf = os.path.abspath(os.path.dirname(__file__))
#sys.path.append(ctf)

#分发
def home(request,action=''):
    try:
        #检查是否登录not request.user.is_authenticated():
        if action == 'login' or not request.user.is_authenticated():
            return param_main.entrance(request)
        #如果没有权限访问该网站，则直接踢出去
        if not request.user.has_perm('auth.view_web'):
            logout(request)
            return HttpResponseForbidden()
        if public.objIsEmpty(action):
            action  = request.GET.get('action','entrance')
        if not hasattr(param_main,action):
            return HttpResponseServerError()
        model   = getattr(param_main, action)
        result  = model(request)
        return result
    except:
        print '%r'%tb.format_exc()
        return HttpResponseServerError()

@csrf_exempt
def parameters(request,pid='',localeid='',sheetid=''):
    #分发
    try:
        if request.GET.get('reqmode') != 'js':
            #检查是否登录not request.user.is_authenticated():
            if not request.user.is_authenticated():
                return param_main.entrance(request)
            #如果没有权限访问该网站，则直接踢出去
            if not request.user.has_perm('auth.view_web'):
                logout(request)
                return HttpResponseForbidden()
            public.print_str('parameters')
            public.print_str('------- request.user: %s'%request.user)
            public.print_str('------- request.user.username: %s'%request.user.username)
        if public.objIsEmpty(pid) or public.objIsEmpty(localeid):
            return param_main.choose_param(request)
        return param_main.param_main_response(request,pid,localeid,sheetid)
    except:
        print '%r'%tb.format_exc()
        return HttpResponseServerError()

def llogout(request):
    """ 登出 """
    return param_main.quity(request)

def lalter_password(request):
    """ 修改密码 """
    return param_main.alter_password(request)

def hello(request):
    """ 测试项目是否启动 """
    print request.get_host()
    print '--------  userid:',request.user.id
    return HttpResponse("Hello World!")

def do_crossdomain(request):
    cross = '''<?xml version="1.0" encoding="UTF-8"?>
<cross-domain-policy>
<allow-access-from  domain="*"  to-ports="*"  />
</cross-domain-policy>
'''
    return HttpResponse(cross)

def favicon_ico(request):
    """ 网站logo """
    image_data = open(settings.MEDIA_ROOT+'/images/favicon.ico', "rb").read()
    return HttpResponse(image_data, mimetype="image/png")

def test_templete(request):
    """ 入口 """
    t = loader.get_template('test_templete.html')
    c = RequestContext(request, {})
    return HttpResponse(t.render(c))

def get_fields(request):
    """ 获取表的字段信息 """
    from libs.config import AUTO_ADD_FIELD
    fields  = []
    to  = request.GET.get('to',"")
    if to:
        print 'to: ',to
        fields  = [f.name for f in Sheet.objects.get(name=to).fields.all().exclude(name__in=AUTO_ADD_FIELD)]
    return HttpResponse(json.dumps(fields))

def modify_sn(self):
    """ 处理数据表中SN """
    for sheet in Sheet.objects.filter(program=1, deleted=False):
        print 'sheet.name: ',sheet.name
        sheet_id = sheet.id
        try:
            Field2.objects.get(model=sheet_id,name='sn')
        except Field2.DoesNotExist:
            pass
        else:
            dyn_obj = sheet.get_django_model()
            for record in dyn_obj.objects.filter():
                record.sn   = int('%d%04d'%(sheet_id,record.id))
                record.save()
    return HttpResponse('OK')

@csrf_exempt
def get_card_sets(request, sheetid, set_id="null"):
    """ 获取卡片分组数据 """
    #归类
    if request.method == 'POST':
        req_msg = request.POST
    else:
        req_msg = request.GET
    condition = json.loads(req_msg.get('condition','{}'))
    if public.objIsEmpty(condition):
        return HttpResponse(json.dumps({}))
    datas = []
    sheet_obj   = Sheet.objects.get(name=sheetid)
    display = sheet_obj.display
    print 'display: ', display
    if not display:
        display = "name"
    conds   = {}
    for k1, v1 in condition.items():
        f   = sheet_obj.fields.get(name=k1)
        try:
            to_sheet= Sheet.objects.get(name=f.to)
        except Sheet.DoesNotExist:
            print 'do %s, sheet can not find to sheet %s'%(k1, f.to)
        else:
            to_obj  = to_sheet.get_django_model()
            try:
                to_record   = to_obj.objects.get(id=v1)
            except to_obj.DoesNotExist:
                print 'do %s, record can not find to sn %s'%(f.to, v1)
            else:
                conds[k1]   = to_record.id
    c1  = {}
    print 'condition: ', condition, conds
    for r in sheet_obj.get_django_model().objects.filter(**conds):
        print '-----',r
        try:
            set_value   = ""
            if set_id != 'null':
                set_value   = getattr(r, set_id, "")
                if isinstance(set_value,object):
                    set_value   = set_value.id
            print 'id, set_value: ', r.id, set_value
            if c1.has_key(set_value):
                c1[set_value].append({'sn': r.sn, 'name': getattr(r, display, "")})
            else:
                c1[set_value]   = [{'sn': r.sn, 'name': getattr(r, display, "")}]
        except:
            print '%s'%tb.format_exc()
    for set_value, v2 in c1.items():
        datas.append({'rare': set_value, 'card_len': len(v2), 'cards': v2})
    return HttpResponse(json.dumps(datas))
