# coding=utf-8
# 全局变量设置

from django.http import HttpResponse
from django.template import loader, RequestContext
from django.conf import settings

from libs.register import logout
import controller


def login(request):
    """ 登入 """
    return controller.login(request)


def quity(request):
    """ 登出 """
    return controller.quity(request)


def lalter_password(request):
    """ 修改密码 """
    return controller.alter_password(request)


def hello(request):
    """ 测试项目是否启动 """
    print request.get_host()
    print '--------  userid:', request.user.id
    return HttpResponse("Hello World!")


def report(request):
    """ '报'处理 """
    package = __import__('report')
    model = getattr(package, 'report')
    return model(request)


def do_crossdomain(request):
    cross = '''<?xml version="1.0" encoding="UTF-8"?>
<cross-domain-policy>
<allow-access-from  domain="*"  to-ports="*"  />
</cross-domain-policy>
'''
    return HttpResponse(cross)


def favicon_ico(request):
    """ 网站logo """
    image_data = open(settings.MEDIA_ROOT + '/images/favicon.ico', "rb").read()
    return HttpResponse(image_data, content_type="image/png")


def test_templete(request):
    """ 入口 """
    t = loader.get_template('test_templete.html')
    c = RequestContext(request, {})
    return HttpResponse(t.render(c))
