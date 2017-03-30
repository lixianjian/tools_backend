#!/usr/bin/python2.7
# coding=utf-8
'''
数据分析需要的配置
后台运营程序使用的参数文件
用于定义需要监控服务器的名称，地址，可以访问的端口等信息

Created on 2012-4-20

@author: lixianjian
'''


# 后台调试即时修改文件
PARAM_DEBUG_PATH = '/opt/program/tools_backend/debug/param_debug.txt'
# 启动的应用
APPLICATION = 'parameters'
# 数据库名称
BS_DB_NAME = 'tools_backend_%s.db' % APPLICATION
# 项目目录
PROGRAM_PATH = '/opt/program/tools_backend_cgame'
# 特殊字段的修改权限{table: {field: permission}}
EDIT_PERM_FIELDS = {
    'ask': {
        'sured': 'edit_amazon_ask_sured',  # 编辑申请状态
        'asker': 'edit_amazon_ask_asker',  # 编辑申请人
    }
}
# 调试状态
DEBUG = True
# 分页时每页数据的记录数量
PER_PAGE = 50
# 静态资源目录
STATIC_PATH = '/usr/local/lib/python2.7/dist-packages/django/contrib/admin/static/'
# 下载文件临时（中转）目录
DOWNLOAD_PATH = '/opt/program/tools_backend/download'
# 数据根目录
BASE_DATA_PATH = '/opt/program/tools_backend/db'
