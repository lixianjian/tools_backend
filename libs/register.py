#coding=utf-8
'''
Created on 2012-9-20

@author: lixianjian
'''

from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import auth

import traceback as tb

def get_request_data(req):
    """ 根据request请求的方式不同，返回请求数据 """
    if req.method == 'POST':
        req_msg = req.POST
    else:
        req_msg = req.GET
    return req_msg

def hello(request):
    """  """
    return  HttpResponse('hello world!')

def regist(request):
    """ 用户注册 """
    req_msg = get_request_data(request)
    username= req_msg.get('username')
    password= req_msg.get('password')
    email   = req_msg.get('email','')
    first_name= req_msg.get('first_name','')
    last_name= req_msg.get('last_name','')
    user= None
    if not username or not password:
        tips= '用户名与密码不能为空'
        status  = 1
    else:
        users= User.objects.filter(username=username)
        if bool(users):
            tips= '用户名已存在'
            status  = 1
        else:
            user= User.objects.create_user(username, email, password)
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            tips= '注册成功'
            status  = 0
    return {'status': status, 'tips': tips, 'user': user}

def login(request):
    """ 用户登录 """
    req_msg = get_request_data(request)
    username= req_msg.get('username')
    password= req_msg.get('password')
    user = auth.authenticate(username=username, password=password)
    if user is not None and user.is_active:
        # Correct password, and the user is marked "active"
        auth.login(request, user)
        # Redirect to a success page.
        #return HttpResponseRedirect("/account/loggedin/")
        data= '登陆成功'
        status  = 0
        #return render_to_response('login.html',{})
    else:
        # Show an error page
        #return HttpResponseRedirect("/account/invalid/")
        data    = '用户名和密码不对'
        status  = 1
    return {'status': status, 'tips': data}
    
def alter(request):
    """ 修改密码 """
    try:
        req_msg = get_request_data(request)
        password= req_msg.get('password')
        surepassword= req_msg.get('surepassword')
        if not bool(password) or not bool(surepassword):
            data= '密码不能为空'
            status  = 1
        elif password != surepassword:
            data= '两次输入密码不同'
            status  = 1
        else:
            username= request.user.username
            user = User.objects.get(username=username)
            user.set_password(password)
            user.save()
            data    = '修改成功'
            status  = 0
    except:
        print '%r'%tb.format_exc()
        data    = '修改失败'
        status  = 1
    return {'status': status, 'tips': data}

def logout(request):
    """ 登出 """
    auth.logout(request)
