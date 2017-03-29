#!/usr/bin/python2.7
#coding=utf-8

import os,sys
ctf = os.path.dirname(os.path.abspath(__file__))
ltf = ctf.replace('multi_locale','')
lib_local_path  = os.path.join(ltf,'libs_local.py')
if os.path.exists(lib_local_path):
    try:
        sys.path.append(ltf)
        from libs_local import LANGUAGE
    except:
        #语言版本，默认为中文简体
        LANGUAGE    = 'zh_CN'

language_path   = ctf +'/'+LANGUAGE+'.py'
if os.path.exists(language_path):
    if ctf not in sys.path:
        sys.path.append(ctf)
    glocale = __import__(LANGUAGE)
else:
    import zh_CN as glocale
