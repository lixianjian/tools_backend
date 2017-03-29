#coding=utf-8

'''
@Created: 2012-02-28
@author: YangHong
'''
import sys
import os
from django.http import HttpResponse
import subprocess
import shlex
AbsolutePath = os.path.abspath(os.path.dirname(__file__))
sys.path.append(AbsolutePath+'/controller')


def home(request):
    return HttpResponse("ok")

def fight(request):
    print '1111111111'
    print fight_test2(request)
    print '222222222'
    return HttpResponse("OK")

def fight_test2(request):
    
    #shl = "/opt/cgamefighttest/darkhutgame_studio/media/fight/func " + str
    shl = 'python2.7 /opt/darkhutgame/support/tools_backend/cgame/tools_backend/parameters/test_popen.py'
    print shl
    run = open("/var/log.log", "w+")
    popen = subprocess.Popen(shl, shell=True, stdout=run, stderr=subprocess.STDOUT)


    #subprocess.Popen([shl,str, " >/opt/cgamefighttest/darkhutgame_studio/media/fight/run 2>> /opt/cgamefighttest/darkhutgame_studio/media/fight/run &" ], shell=True)
    
    print "================"
    return "fight_test2 is over"
    #return HttpResponse("ok")
