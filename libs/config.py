#!/usr/bin/python2.7
#coding=utf-8
'''
Created on 2012-08-12

@author: lixianjian@darkhutgame.com
'''

from multi_locale import glocale

####################### 项目启动配置 #############################
#uwsgi日志目录
UWSGI_LOG_PATH  = '/opt/darkhutgame/uwsgi_log/support/toos_backend'
#uwsgi端口
UWSGI_PORT  = 39181
#静态资源目录
STATIC_PATH = '/usr/local/lib/python2.7/site-packages/django/contrib/admin/static/'

#调试状态
DEBUG   = False
#分页时每页数据的记录数量
PER_PAGE= 50
#ASSETS资源下载URL
ASSETS_URL  = 'http://220.dhh.darkhutgame.net:8080/tb_assets'
#概率数组为
COMBOS  = ['0.1','0.5','1.0','2.0','4.0','8.0','16.0','30.0']
#后台调试即时修改文件
PARAM_DEBUG_PATH= '/data/kashen1/param_debug.txt'
#参数表程序自动添加字段
BASE_AUTO_ADD_FIELD = ['id','deleted','createtime','username']
AUTO_ADD_FIELD  = ['create','operator']
AUTO_ADD_FIELD.extend(BASE_AUTO_ADD_FIELD)
#表自动添加字段
AUTO_ADD_FIELD2 = ['create','operator','deleted','createtime','username']
#数字正则式
NUMBER_STR  ='\d{1,9}'
#时间正则表达式，如：2012-07-26 17:22:22
TIME_RE_STR ='\d{4}-\d{2}-\d{2}\s{1}\d{2}:\d{2}:\d{2}'
#日期正则表达式，如：2012-07-26
DATE_RE_STR ='\d{4}-\d{2}-\d{2}'
#浮点正则表达式
FLOAT_STR   = '(\d+)(\.\d+)'
#登陆后默认跳转页面
DEFAULT_LOGIN_PATH  = '/index/'
#启动的应用
APPLICATION = 'parameters'
#protobuf文件存放目录
PROTOBUF_PATH   = '/opt/darkhutgame/cgame/cgame_shared/protobuf/'
#系统标题
SYSTEM_TITLE    = '租用服务器'
#特殊权限处理字段{table: {field: permission}}
SPEC_PERM_FIELDS= {}

#===============================================================================
# 亚马逊租用服务器配置
#===============================================================================
#逻辑服服务器端配置
SVR_CONFIG_FILE = """[server]
;平台
plat_form = %(platform)s
;开服时间
opentime = %(opentime)s
;服务器名，对于多服填成{"1":"测试服","2":"开发服"}，注意要有双引号
server_name = %(name)s
;服务器ID
server_id = %(svrid)s
;一机多服ID
port_id = %(portid)s

;游戏名&版本（隐藏参数，可以在配置文件里添加）
game = kashen{{.Server_id}}
;gate地址&端口；port_id以2位数字填充
addr = :80{{.Port_id}}
;http地址&端口；port_id以2位数字填充
http = 127.0.0.1:88{{.Port_id}}
;内部支付地址&端口；port_id以2位数字填充
pay = 127.0.0.1:89{{.Port_id}}
;是否开启防沉迷，1-开启；0-不开启（隐藏参数，可以在配置文件里添加；若为1，则开启防沉迷）
fcm = 1
;内置GM帐号（隐藏参数，可以在配置文件里添加）
debug_gm = %(debug_gm)s

[log]
;log日志等级：1-debug, 2-info, 3-warning, 4-error, 5-critical
level = %(level)s
;log是否以屏幕方式输出
stdout = %(stdout)s
"""
#nginx配置
NGINX_CONFIG = """server {
    listen       80;
    server_name  %(domain)s;

    #charset koi8-r;

    #access_log  logs/host.access.log  main;

    location / {
        root   html;
        index  index.html index.htm;
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:4915%(portid)s;
    }
}

server {
    listen       8008;
    server_name  %(domain)s;

    #charset koi8-r;

    #access_log  logs/host.access.log  main;

    location / {
        limit_conn one 1;
        limit_rate 100k;
        root   html;
        index  index.html index.htm;
        include uwsgi_params;
        uwsgi_pass 127.0.0.1:4916%(portid)s;
    }

}
"""

#接口页面配置
WEB_CONFIG  = """#coding=utf-8
'''
存放需要在部署服务器的时候修改的参数,每个服务器不一样,会被var_local.py覆盖掉
被页面程序和服务器程序同时需要,web服务和游戏服务器都使用这一个配置文件
'''
import os,datetime


PORT_ID   = '%(portid)s'
SERVER_ID = '%(svrid)s'

#游戏代码
GAME_CODE = 'kashen'

#本服域名
DOMAIN      = '%(domain)s'
#充值域名，默认与本服域名相同
PAY_DOMAIN  = DOMAIN

#游戏页面标题
GAME_TITLE  = '%(name)s'
#区服名字
GAME_LOCATION_NAME = '%(name)s'
#开服时间
GAME_OPENTIME = '%(opentime)s'

#平台名
PINGTAI= '%(platform)s'
#--------------------------------------------------------------

#SECRET_CODE = '%(scret_code)s'
#玩家默认来源
DEFAULT_SOURCE= PINGTAI
#充值平台
PAY_PLAT_FORM   = PINGTAI
#该区所在平台，如腾讯(tencent)、自由服(self)等，默认为自有服
PLAT_FORM   = PINGTAI
#是否要推荐码
INTRO_CODE  = False
#是否封账号（不允许建新账号）
CLOSE_ACCOUNT= %(close_account)s
#报BUG地址
REPORT_URL  = 'http://%(report_domain)s/report/?serverid='+SERVER_ID
#是否在大航海充值的同时给大唐充值
IS_DT_PAY   = False
#游戏入口地址,该值是正常流程进入游戏的入口地址，比如自由服'www.darkhutgame.com',是给广告着陆跳转游戏用的，根据游戏区发生变化
GAME_URL    = '%(game_url)s'
#JS跨域域名
SCRIPT_DOMAIN   = '*'
#该服是否要生成二维码
CREATE_MOBILEID = False

"""

#数据库名称
BS_DB_NAME  = 'tools_backend.db'
#项目目录
PROGRAM_PATH= '/opt/darkhutgame/support/tools_backend/cgame/tools_backend'
#下载文件临时（中转）目录
DOWNLOAD_PATH   = '/data/download'
#数据根目录
BASE_DATA_PATH  = '/data'

import os
ctf = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(ctf + '/libs_local.py'):
    from libs_local import *
