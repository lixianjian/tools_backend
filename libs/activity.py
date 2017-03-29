#!/usr/bin/python2.7
#coding=utf-8
"""
运营活动任务配置信息
"""

#充值金额对应获取道具
OPEN_RMB_ITEMS= [
    (200,500,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}]),
    (500,1000,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}, 
               {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,}]),
    (1000,3000,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}, 
                {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,}, 
                {'itemsn': 43135, 'name': u'紫色升星礼包', 'count': 1,}]),
    (3000,10000000,[{'itemsn': 1079, 'name': u'榆木舱', 'count': 1,}, 
                    {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,},
                    {'itemsn': 43135, 'name': u'紫色升星礼包', 'count': 1,}, 
                    {'itemsn': 43136, 'name': u'橙色升星礼包', 'count': 1,}]),
    ]

#充值游戏币对应获取道具
OPEN_TB_ITEMS= [
    (2000,5000,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}]),
    (5000,10000,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}, 
               {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,}]),
    (10000,30000,[{'itemsn': 1078, 'name': u'杉木舱', 'count': 1,}, 
                {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,}, 
                {'itemsn': 43135, 'name': u'紫色升星礼包', 'count': 1,}]),
    (30000,100000000,[{'itemsn': 1079, 'name': u'榆木舱', 'count': 1,}, 
                    {'itemsn': 43134, 'name': u'蓝色升星礼包', 'count': 1,},
                    {'itemsn': 43135, 'name': u'紫色升星礼包', 'count': 1,}, 
                    {'itemsn': 43136, 'name': u'橙色升星礼包', 'count': 1,}]),
    ]

#充值金额对应获取道具
SPEC_RMB_ITEMS= [
    (200,500,u'200-500,圣诞装备包:1'),
    (500,1000,u'500-1000,圣诞技能包:1'),
    (1000,3000,u'1000-3000,圣诞装备包:2'),
    (3000,5000,u'3000-5000,圣诞技能包:2'),
    (5000,8000,u'5000以上,圣诞装备包:3'),
    (8000,10000,u'8000以上,圣诞技能包:5'),
    (10000,10000000,u'10000以上,圣诞装备包:3,圣诞技能包:3'),
    ]

#排名对应获取道具
RANK_ITEMS  = {'fight_power_rank': [{"itemsn":41052,"name":"紫色装备箱","count":1}],
               'role_level_rank': [{"itemsn":41049,"name":"紫色技能箱","count":1}],
               'money_rank': [{"itemsn":41019,"name":"3阶材料宝箱","count":10}],
               'ship_rank': [{"itemsn":43077,"name":"橙色船只卡","count":1}],
               'captain_rank': [{"itemsn":43082,"name":"橙色船长卡","count":1}],
               'fight_rank': [{"itemsn":43069,"name":"紫色宝藏","count":1}],
               }

#排名项目
RANK_PROGS  = {'fight_power_rank':u'战斗力排名','role_level_rank':u'等级排名','money_rank':u'银币排名',
               'ship_rank':u'船只排名','captain_rank':u'船长排名','fight_rank':u'战斗排名',}

#VIP对应获取道具
VIP_ITEMS   = {1:[{"itemsn":43075,"name":"蓝色船只卡","count":1}],
               2:[{"itemsn":43076,"name":"紫色船只卡","count":1}],
               3:[{"itemsn":43077,"name":"橙色船只卡","count":1}],
               4:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41051,"name":"蓝色裝备箱","count":1}],
               5:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41052,"name":"紫色裝备箱","count":1}],
               6:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41053,"name":"橙色裝备箱","count":1}],
               7:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41053,"name":"橙色裝备箱","count":1},
                  {"itemsn":41062,"name":"蓝色技能箱","count":1}],
               8:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41053,"name":"橙色裝备箱","count":1},
                  {"itemsn":41049,"name":"紫色技能箱","count":1}],
               9:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                  {"itemsn":41053,"name":"橙色裝备箱","count":1},
                  {"itemsn":41050,"name":"橙色技能箱","count":1}],
               10:[{"itemsn":43077,"name":"橙色船只卡","count":1},
                   {"itemsn":41053,"name":"橙色裝备箱","count":1},
                   {"itemsn":41050,"name":"橙色技能箱","count":1},
                   {"itemsn":43068,"name":"橙色宝藏","count":1}],
               }

#所有消耗打折(discount)活动邮件主题&内容
DISCOUNT_MAIL_TITLE = u'【消費輕鬆省，限時優惠】獎勵發放'
DISCOUNT_MAIL_TEXT  = u'''親愛的玩家：
您好！

感謝參與【消費輕鬆省，限時優惠】，這是您的獎勵，請注意查看附件；

支持原創遊戲！
支持小黑屋遊戲！
——大航海家運營團隊
'''