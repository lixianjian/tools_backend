#coding=utf-8
from django.db import models
from django.contrib import admin
from django.core.validators import ValidationError
from django.contrib.auth.models import User
import datetime

#from libs.config import AUTO_ADD_FIELD
# Create your models here.

class Program(models.Model):
    """ 项目 """
    class Meta:
        verbose_name= '项目'
        db_table= 'program'
    
    #标识
    markid  = models.CharField(verbose_name='标识',max_length=30)
    #名称
    name= models.CharField(verbose_name='名称',max_length=30)
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
    def __unicode__(self):
        return self.name

class Locale(models.Model):
    """ 语言 """
    class Meta:
        verbose_name = '语言'
        db_table= 'locale'
    
    #标识
    markid  = models.CharField(verbose_name='标识',max_length=30)
    #名称
    name= models.CharField(verbose_name='名称',max_length=30)
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
    def __unicode__(self):
        return self.name

class ProgramLocaleUser(models.Model):
    """ 项目-语言-人员 """
    class Meta:
        verbose_name = '项目-语言-人员'
        db_table    = 'program_locale_user'
    
    #用户
    user= models.ForeignKey(User,verbose_name='用户')
    #项目
    program = models.ForeignKey(Program,verbose_name='项目')
    #语言
    locale  = models.ForeignKey(Locale,verbose_name='语言')
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)

class SystemModels(models.Model):
    """ 系统模块 """
    class Meta:
        verbose_name= '系统模块'
        db_table= 'system_models'
    
    #项目
    program = models.ForeignKey(Program,verbose_name='项目')
    #语言
    locale  = models.ForeignKey(Locale,verbose_name='语言')
    #标识
    markid  = models.CharField(verbose_name='标识',max_length=30)
    #名称
    name= models.CharField(verbose_name='名称',max_length=30)
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
    def __unicode__(self):
        return self.name

class SystemModels2(models.Model):
    """ 系统模块2 """
    class Meta:
        verbose_name= '系统模块2'
        db_table= 'system_models2'
    
    #项目
    program = models.ForeignKey(Program,verbose_name='项目')
    #语言
    locale  = models.ForeignKey(Locale,verbose_name='语言')
    #标识
    markid  = models.CharField(verbose_name='标识',max_length=30)
    #名称
    name= models.CharField(verbose_name='名称',max_length=30)
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
    def __unicode__(self):
        return self.name

#class Sheets(models.Model):
#    """ 参数表 """
#    class Meta:
#        verbose_name= '参数表'
#        db_table= 'sheets'
#    
#    #项目
#    program = models.ForeignKey(Program,verbose_name='项目')
#    #语言
#    locale  = models.ForeignKey(Locale,verbose_name='语言')
#    #系统模块
#    sys_model   = models.ForeignKey(SystemModels,verbose_name='系统模块')
#    #系统模块2
#    sys_model2  = models.ForeignKey(SystemModels2,verbose_name='系统模块2')
#    #标识
#    markid  = models.CharField(verbose_name='标识',max_length=30)
#    #名称
#    name= models.CharField(verbose_name='名称',max_length=30)
#    #最后一个记录ID
#    num = models.IntegerField(verbose_name='最后一个记录ID',null=True,blank=True)
#    #创建时间
#    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
#    #操作用户
#    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
#    
#    def __unicode__(self):
#        return self.name

def create_model(name, fields=None, app_label='', module='', options=None, admin_opts=None, display=''):
    """
    Create specified model
    """
    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, 'app_label', app_label)

    # Update Meta with any options that were provided
    if options is not None:
        for key, value in options.iteritems():
            setattr(Meta, key, value)
 
    # Set up a dictionary to simulate declarations within a class
    attrs = {'__module__': module, 'Meta': Meta}

    # Add in any fields that were provided
    if fields:
        attrs.update(fields)

    # Create the class, which automatically triggers ModelBase processing
    if isinstance(name, unicode):
        name= name.encode('utf-8')
    model = type(name, (models.Model,), attrs)

    # Create an Admin class if admin options were provided
    if admin_opts is not None:
        class DyanAdmin(admin.ModelAdmin):
            pass
        for key, value in admin_opts.iteritems():
            setattr(DyanAdmin, key, value)
        admin.site.register(model, DyanAdmin)

    return model

def underline2hump(s1, s_char='_'):
    """ 将字符串(两个单词之间用'_'分隔)中的第index个字母转成大写 """
    s2  = ''
    for s3 in s1.split(s_char):
        s2  += s3[0].upper()+s3[1:]
    return s2

#class App(models.Model):
#    """ 应用 """
#    class Meta:
#        verbose_name= '应用'
#        db_table= 'app'
#    
#    #描述
#    name = models.CharField(verbose_name='描述',max_length=255)
#    #应用
#    module = models.CharField(verbose_name='应用',max_length=255)
#    #创建时间
#    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
#    #操作用户
#    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
#    
#    def __str__(self):
#        return self.name

class Formula(models.Model):
    """ 公式 """
    class Meta:
        verbose_name= '公式'
        db_table= 'formula'
    
    #名称
    name = models.CharField(verbose_name='名称', max_length='100',default='')
    #数据源表
    tables  = models.TextField(verbose_name='数据源表', default='[]')
    #公式代码
    code = models.TextField(verbose_name='公式代码', default='')
    #公式应用类型，1：数据表，2：图表
    ft  = models.IntegerField(verbose_name='公式应用类型', default=1,help_text='1：数据表，2：图表')
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    #删除
    deleted = models.BooleanField(verbose_name='删除',default=False)
    
    def __unicode__(self):
        return self.name

class Sheet(models.Model):
    """ 参数表 """
    class Meta:
        verbose_name= '参数表'
        db_table= 'sheet'
        unique_together = (('program','name'),)
    
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    #删除
    deleted = models.BooleanField(verbose_name='删除',default=False)
    #项目
    program = models.ForeignKey(Program,verbose_name='项目',related_name='models')
    #语言
    locale  = models.ForeignKey(Locale,verbose_name='语言')
    #系统模块
    sys_model   = models.ForeignKey(SystemModels,verbose_name='系统模块')
    #系统模块2
    sys_model2  = models.ForeignKey(SystemModels2,verbose_name='系统模块2')
    #表名
    name = models.CharField(verbose_name='表名',max_length=255)
    #描述
    intro   = models.CharField(verbose_name='描述',max_length=255)
    #最后一个记录ID
    num = models.IntegerField(verbose_name='最后一个记录ID',null=True,blank=True,default=0)
    #描述字段，做外键表时用于显示的字段，如果没有就为空
    display = models.CharField(verbose_name='描述字段',max_length=255,blank=True,default='')
    #是否上下行表，默认是上下行表
    is_proto= models.BooleanField(verbose_name='是否上下行表', default=True)
    #公式
    formula = models.ForeignKey(Formula, verbose_name='公式', blank=True, null=True, default=0)
    #是否模板表，默认不是模板表
    is_template = models.BooleanField(verbose_name='是否模板表', default=False)
    #归类字段
    conds   = models.CharField(verbose_name='归类字段',max_length=200,blank=True,default='[]')
    #筛选数据
    filters = models.CharField(verbose_name='筛选数据',max_length=200,blank=True,default='{}')
    
    def __str__(self):
        return self.name

    def get_django_model(self):
        "Returns a functional Django model based on current data"
        # Get all associated fields into a list ready for dict()
#        for f in Field2.objects.filter(model=self.id):
#            print f.name,f.type.name
        fields = []
        for f in Field2.objects.filter(model=self.id):
#            print f.name,f.type.name
            fields.append((f.name, f.get_django_field()))
        #list_display= [f.name for f in self.fields.all()]
        # Use the create_model function defined above
        print 'Use the create_model function defined above',self.name
        return create_model(underline2hump(self.name), 
                            dict(fields), 
                            self.program.markid, 
                            self.program.markid, 
                            options={'verbose_name':self.intro, },#'db_table': self.name 
                            #,admin_opts={'list_display': list_display},
                            display= self.display
                            )

def is_valid_field(self, field_data, all_data):
    if hasattr(models, field_data) and issubclass(getattr(models, field_data), models.Field):
        # It exists and is a proper field type
        return
    raise ValidationError("This is not a valid field type.")

class FieldType2(models.Model):
    """ 字段类型 """
    class Meta:
        verbose_name= '字段类型'
        db_table= 'field_type2'
    
    #字段类型
    name = models.CharField(verbose_name='字段类型', max_length=255)
    #描述
    intro   = models.CharField(verbose_name='描述',max_length=255)
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
    def __unicode__(self):
        return self.name

class Field2(models.Model):
    """ 字段 """
    class Meta:
        verbose_name= '字段'
        db_table= 'field2'
        unique_together = (('model', 'name'),)
    
    #参数表
    model   = models.ForeignKey(Sheet, verbose_name='参数表',related_name='fields')
    #字段名
    name= models.CharField(verbose_name='字段名', max_length=255)
    #描述
    intro   = models.CharField(verbose_name='描述',max_length=255)
    #类型
    #type = models.CharField(verbose_name='类型', max_length=255, validators=[is_valid_field])
    type= models.ForeignKey(FieldType2, verbose_name='类型')
    #外键表名
    to  = models.CharField(verbose_name='外键',max_length=255,blank=True,null=True,default=None)
    #外键字段
    to_field = models.CharField(verbose_name='外键字段',max_length=255,blank=True,null=True,default=None)
    #最大长度
    max_length  = models.IntegerField(verbose_name='最大长度',blank=True,null=True,default=None)
#    #字段填写说明
#    help= models.TextField(verbose_name='字段填写说明',blank=True,null=True,default='')
    #创建时间
    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
    #操作用户
    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
    
#    def get_django_field(self):
#        "Returns the correct field type, instantiated with applicable settings"
#        # Get all associated settings into a list ready for dict()
#        settings = [(s.name, s.value) for s in self.settings.all()]
#        settings.append(('verbose_name', self.intro))
#        # Instantiate the field with the settings as **kwargs
#        return getattr(models, self.type.name)(**dict(settings))
    def get_django_field(self):
        type_name   = self.type.name
        settings= {'verbose_name': self.intro,'null': True,'blank': True}
        if type_name == 'AutoField':
            settings['primary_key'] = True
            settings['null']= False
            settings['blank']   = False
        elif type_name == 'BooleanField':
            settings['null']= False
            settings['blank']   = False
        elif type_name == 'CharField':
            if self.max_length:
                settings['max_length']  = self.max_length
        elif type_name == 'ImageField':
            type_name   = 'CharField'
            if self.max_length:
                settings['max_length']  = self.max_length
            else:
                settings['max_length']  = 255
        elif type_name in ['ForeignKey',]:#'ManyToManyField'
            if self.to:
                #settings['to']  = underline2hump(self.to)
#                print 'self.to', self.to
                try:
                    sheet_obj   = Sheet.objects.get(program=self.model.program.id,name=self.to)
                except Sheet.DoesNotExist:
                    print 'sheet [%s] does not exist'%self.to
                    settings['to']  = self.to
                else:
                    settings['to']  = sheet_obj.get_django_model()
                    settings['related_name']= '%ss'%self.model.name
#                    settings['blank']   = True
#                    settings['null']    = True
                    settings['default'] = None
        elif type_name in ['ManyToManyField','DictArray','RepM2MField']:
            if self.to:
                type_name   = 'CharField'
                settings['default'] = '[]'#self.to
            settings['max_length']  = 255
        elif type_name == 'JSONChar':
            type_name   = 'CharField'
            if self.max_length:
                settings['max_length']  = self.max_length
            else:
                settings['max_length']  = 255
        elif type_name == 'ManyForeignsField':
            if self.to:
                type_name   = 'IntegerField'
                settings['default'] = '0'
            settings['max_length']  = 0
        elif type_name == 'OddsField':
            type_name   = 'TextField'
            settings['default'] = '[]'
        return getattr(models, type_name)(**settings)
    
    def __unicode__(self):
        return self.intro

#class Setting(models.Model):
#    """ 字段参数 """
#    class Meta:
#        verbose_name= '字段参数'
#        db_table= 'setting'
#        unique_together = (('field', 'name'),)
#    
#    #字段
#    field = models.ForeignKey(Field, verbose_name='字段', related_name='settings')
#    #参数名
#    name = models.CharField(verbose_name='参数名', max_length=255)
#    #参数值
#    value = models.CharField(verbose_name='参数值', max_length=255)
#    #创建时间
#    createtime  = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)
#    #操作用户
#    username= models.CharField(verbose_name='操作用户',max_length=30,blank=True)
