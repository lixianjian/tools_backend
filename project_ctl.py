# coding=utf-8
'''
Created on 2011-11-29

@author: YangHong
'''

import os
import sys
from datetime import datetime
import time
from subprocess import call
from argparse import ArgumentParser
import shlex

from libs.config import UWSGI_LOG_PATH, UWSGI_PORT

cfd = os.path.abspath(os.path.dirname(__file__))
sys.path.append(cfd)
USER = 'nobody'


def stop():
    """ 关闭项目 """
    # call('pkill -f "%s"' % cfd, shell=True)
    # call('pkill -f "%s"'%cfd,shell=True)
    call("kill -2 `ps uax |grep '%s' | grep -v 'grep' | awk -F' ' " +
         "'{print $2}'`" % cfd, shell=True)
    time.sleep(3)


def start(user, port):
    """ 启动项目 """
    if not os.path.exists(UWSGI_LOG_PATH):
        os.makedirs(UWSGI_LOG_PATH)
        os.chmod(UWSGI_LOG_PATH, 0777)
    right_now = datetime.now()
    log_stamp = '_%d-%02d-%02d_%02d_%02d_%02d_%04d' % \
        (right_now.year, right_now.month, right_now.day, right_now.hour,
         right_now.minute, right_now.second, right_now.microsecond)
    params = {'pythonpath': cfd, 'uwsgi_log_path': UWSGI_LOG_PATH,
              'log_stamp': log_stamp, 'uwsgi_port': port}
    shl = 'uwsgi --pythonpath=%(pythonpath)s/ \
--module=wsgi_app \
--socket=127.0.0.1:%(uwsgi_port)s \
--close-on-exec \
> %(uwsgi_log_path)s/project_%(log_stamp)s.log 2>&1 &' % params

    shl2 = 'su ' + user + ' -s /bin/bash -c "' + shl + '"'
    print shl2
    call(shlex.split(shl2))


def control(tag, user, port):
    if tag == 'stop':
        stop()
    elif tag == 'start':
        start(user, port)
    elif tag == 'restart':
        stop()
        start(user, port)

if __name__ == '__main__':
    parser = ArgumentParser(description='report starter')
    parser.add_argument('control', choices=['start', 'stop', 'restart'])
    parser.add_argument('-u', '--user', default=USER,
                        help='user for start process')
    parser.add_argument('-p', '--port', default=UWSGI_PORT,
                        help='port for start process')

    args = parser.parse_args()
    control(args.control, args.user, args.port)
