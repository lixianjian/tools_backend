#coding=utf-8
'''
读取lazy格式的json,将不打引号的json字符视为字符串处理
'''
import re,json
import logging

BRACKETS_LEFT = '\x01'
INPUT_BRACKETS_LEFT = '\['
BRACKETS_RIGHT = '\x02'
INPUT_BRACKETS_RIGHT = '\]'

#prog = re.compile("[^\[\,]\{|\:|\}|\,|\[|\]",re.U)
#prog = re.compile(":|,|{.|.}",re.U)
#prog = re.compile(":|(?P<comma>[^}],[^{])|(?P<start_dict>{.)|(?P<end_dict>.})|(?P<start_list>\[[^{])|(?P<end_list>[^}]\])")
str_long = '''
\s*:\s*|
\s*\[\s*{\s*|
\s*}\s*\]\s*|
\s*{\s*|
\s*}\s*|
\s*\[\s*|
\s*\]\s*|
(?!\s*\}\s*)\s*,\s*(?!\s*\{\s*)
'''
str_long = str_long.replace('\n', '')
prog = re.compile(str_long,re.U)

def repl(match):
    token =  match.group(0)
    print match.lastindex
    if token in ('{','['):
        return token+'"'
    if token in ('}',']'):
        return '"'+token
    if token in (':',','):
        return '"'+token+'"'

def repl2(match):
    dict_str = match.group('start_dict') or match.group('end_dict')  
    list_str_start = match.group('start_list') 
    list_str_end = match.group('end_list')
    comma_str = match.group('comma')
    if dict_str:
        return dict_str[0] + '"' + dict_str[1]
    if list_str_start:
        return list_str_start[0] + '"' + list_str_start[1] +'"'
    if list_str_end:
        return '"' + list_str_end[0] + '"' + list_str_end[1]
    if comma_str:
        return comma_str[0]+'"'+comma_str[1]+'"' + comma_str[2]
    else:
        return '"' + match.group() + '"'
    
def repl3(match):
    token = match.group(0)
    token = token.strip()
    token = token.expandtabs()
    token = token.replace(' ','')
    if token in ('[{','{','['):
        return token + '"'
    if token in ('}]','}',']'):
        return '"' + token
    if token in (':',','):
        return '"' + token + '"'

def try_parse_number(v):
    result = v
    if v.find('.') != -1:
        try:
            result = float(v)
        except:
            pass
    else:
        try:
            result = int(v)
        except:
            pass
    return result
        

def parse_dict(d):
    for k,v in d.iteritems():
        d[k] = try_parse_number(v)
    return d

def lazy_to_json(raw_str):
    if raw_str is None:
        return {}
    if isinstance(raw_str, basestring):
        if not bool(raw_str) or (raw_str.upper() in ['NULL', 'NONE']):
            return {}
    try:
        #预处理,把\[替换为不可见字符BRACKETS
        raw_str = raw_str.replace(INPUT_BRACKETS_LEFT,BRACKETS_LEFT)
        raw_str = raw_str.replace(INPUT_BRACKETS_RIGHT,BRACKETS_RIGHT)
        jstr = prog.sub(repl3,raw_str)
        jstr = jstr.replace(BRACKETS_LEFT,'[')
        jstr = jstr.replace(BRACKETS_RIGHT,']')
    #    print jstr
        obj =  json.loads(jstr)
    except:
        print 'fail transform to lazyjson %r -> %r',raw_str,jstr
        return
        
    if isinstance(obj, list):
        for i in xrange(len(obj)):
            ld = obj[i]
            if isinstance(ld,dict):
                obj[i] = parse_dict(ld)
            else:
                obj[i] = try_parse_number(ld)
    else:
        obj = parse_dict(obj)
    return obj

                    

if __name__ == "__main__":
#    from genericfunc import _2utf8
#    mjson = _2utf8(u'[ { itemname : 铁令牌 , count : 1 , odds : 40 } , { test : ddd } ]')
#    print mjson
#    result = lazy_to_json(mjson)
#    print result
#    mjson = _2utf8(u'[ 1 ,2 ,4, 5 ]')
#    print lazy_to_json(mjson)
#    mjson = _2utf8(u'{itemname:铁令牌,count:1,odds:40}')
#    print lazy_to_json(mjson)
#    mjson = _2utf8(u'{itemname:草泥马\[未鉴定\]}')
#    print lazy_to_json(mjson)
#    
#    print lazy_to_json("{拜访[<交付npc职位>]:1}")

    print lazy_to_json({"from": "city2", "role_level": 1})
    
    
    
    
    
    
    