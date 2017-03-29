#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Created on 2011-11-29

@author: lixianjiancq@gmail.com
'''

import sys
import os

import django.core.handlers.wsgi

cfd = os.path.abspath(os.path.dirname(__file__))
sys.path.append(cfd)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'


application = django.core.handlers.wsgi.WSGIHandler()


if __name__ == "__main__":
    for item in sys.path:
        print item
