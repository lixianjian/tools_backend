#coding=utf-8
'''
Created on 2012-6-19

@author: lixianjian
'''
from django.contrib import admin
#from django.contrib.auth.models import User
from django.contrib.auth.models import Permission
import datetime

from models import *

class PermissionAdmin(admin.ModelAdmin):
    pass

class ProgramAdmin(admin.ModelAdmin):
    """ 项目  """
    list_display = ['id','markid','name','createtime','username']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()
    
class LocaleAdmin(admin.ModelAdmin):
    """ 语言  """
    list_display = ['id','markid','name','createtime','username']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()
    
class ProgramLocaleUserAdmin(admin.ModelAdmin):
    """ 项目-语言-人员  """
    list_display = ['id','user','program','locale','createtime','username']
    raw_id_fields   = ['user','program','locale']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()

class SystemModelsAdmin(admin.ModelAdmin):
    """ 系统模块  """
    list_display= ['id','markid','name','createtime','username']
    search_fields   = ['name','username']
    raw_id_fields   = ['program','locale']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()
    
class SystemModels2Admin(admin.ModelAdmin):
    """ 系统模块2  """
    list_display= ['id','markid','name','createtime','username']
    search_fields   = ['name','username']
    raw_id_fields   = ['program','locale']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()
    
#class SheetsAdmin(admin.ModelAdmin):
#    """ 参数表  """
#    list_display= ['id','program','locale','markid','name','sys_model','sys_model2','createtime','username']
#    search_fields   = ['name','username']
#    raw_id_fields   = ['sys_model','sys_model2']
#    
#    def save_model(self, request, obj, form, change):
#        obj.username= request.user.username
#        obj.createtime  = datetime.datetime.now()
#        obj.save()

#class AppAdmin(admin.ModelAdmin):
#    list_display= ['id','name','module','createtime','username']
#    search_fields   = ['name','username']
#    
#    def save_model(self, request, obj, form, change):
#        obj.username= request.user.username
#        obj.createtime  = datetime.datetime.now()
#        obj.save()

class FormulaAdmin(admin.ModelAdmin):
    list_display= ['id','name','tables','code','ft','createtime','username']
    search_fields   = ['name','username']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()

class SheetAdmin(admin.ModelAdmin):
    list_display= ['id','name','intro','is_proto','num','display','program','locale','sys_model','sys_model2','formula','is_template','filters','conds',
                   'createtime','username']
    search_fields   = ['name','username']
    raw_id_fields   = ['program','locale','sys_model','sys_model2','formula']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()

class FieldType2Admin(admin.ModelAdmin):
    list_display= ['id','name','intro','createtime','username']
    search_fields   = ['name','username']
        
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()

class Field2Admin(admin.ModelAdmin):
    list_display= ['id','model','name','intro','type','to','to_field','max_length','createtime','username']
    search_fields   = ['name','username']
    raw_id_fields   = ['model','type']
    
    def save_model(self, request, obj, form, change):
        obj.username= request.user.username
        obj.createtime  = datetime.datetime.now()
        obj.save()

#class SettingAdmin(admin.ModelAdmin):
#    list_display= ['id','field','name','value','createtime','username']
#    search_fields   = ['name','username']
#    raw_id_fields   = ['field']
#    
#    def save_model(self, request, obj, form, change):
#        obj.username= request.user.username
#        obj.createtime  = datetime.datetime.now()
#        obj.save()


admin.site.register(Permission, PermissionAdmin)

admin.site.register(Program, ProgramAdmin)
admin.site.register(Locale, LocaleAdmin)
admin.site.register(ProgramLocaleUser, ProgramLocaleUserAdmin)
admin.site.register(SystemModels, SystemModelsAdmin)
admin.site.register(SystemModels2, SystemModels2Admin)
#admin.site.register(App, AppAdmin)
admin.site.register(Formula, FormulaAdmin)
admin.site.register(Sheet, SheetAdmin)
admin.site.register(FieldType2, FieldType2Admin)
admin.site.register(Field2, Field2Admin)
#admin.site.register(Setting, SettingAdmin)