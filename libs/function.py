#!/usr/bin/python2.7
#coding=utf-8

"""
后台功能配置信息
"""
from multi_locale import glocale

#后台登陆数据的几个功能相关信息
FUNC_URL    = [ ('login_percent', '/handle/?controller=login_data&action=index&func=login_percent', u'登录率'),
                ('level_lose', '/handle/?controller=login_data&action=index&func=level_lose', u'等级流失'),
                ('action', '/handle/?controller=login_data&action=index&func=action', u'操作与行为'),  
                ('cost', '/handle/?controller=login_data&action=index&func=cost', u'成本'),  
                ('role_cost', '/handle/?controller=login_data&action=index&func=role_cost', u'玩家消费'),
            ]

DATA_FUNC_URL= {glocale.LN_OPERATE_DATA: [
                ('h_analyse', '/handle/?controller=data_backend&action=index&func=h_analyse', glocale.LN_COMPLEX_DATA),
                ('role_lose', '/handle/?controller=data_backend&action=index&func=role_lose', glocale.LN_ROLE_LOSS_PROPORTION_COUNT),
                ('level_lose', '/handle/?controller=data_backend&action=index&func=level_lose', glocale.LN_LEVEL_LOSS_PROPORTION),
                ('cre_login', '/handle/?controller=data_backend&action=index&func=cre_login', glocale.LN_ROLE_CREATE_LOGIN_COUNT),
                ('login_percent', '/handle/?controller=data_backend&action=index&func=login_percent', glocale.LN_ROLE_LOGIN_PROPORTION),
                #('cost', '/handle/?controller=data_backend&action=index&func=cost', glocale.LN_COST),  
                ('richman_info', '/handle/?controller=data_backend&action=richman_info', glocale.LN_RICHMAN),
                ('role_cost', '/handle/?controller=data_backend&action=search_role_info', glocale.LN_SEARCH_ROLE_INFO),
                #('role_cost', '/handle/?controller=data_backend&action=index&func=role_cost', u'玩家渠道统计'),
                ('faq_first', '/handle/?action=faq_first', u'FAQ'),
                #('faq_second', '/handle/?action=faq_second', u'FAQ内容'),
                ],
               glocale.LN_PAYER_MANAGE: [
                ('payment', '/handle/?controller=data_backend&action=index&func=payment', glocale.LN_SERVER_PAY_STATISTICS),
                ('payment_logs', '/handle/?controller=data_backend&action=index&func=payment_logs', glocale.LN_PAY_LOG),
                ('pay_sorts', '/handle/?controller=data_backend&action=index&func=pay_sorts', glocale.LN_PAYER_RANK),
                ('pay_sorts_day', '/handle/?controller=data_backend&action=pay_sorts_day', glocale.LN_DAY_PAY_RANK),
                ],
               glocale.LN_GOLD_GIFT_SILVER_MANAGE: [
                ('exist_counts', '/handle/?controller=data_backend&action=index&func=exist_counts', glocale.LN_INVENTORY_STATISTICS),
                #统一到玩家消费中去，暂时不做细分
                ('cost_tongbao', '/handle/?controller=data_backend&action=index&func=cost_tongbao', glocale.LN_OBTAIN_USE_GOLD),
                ('cost_money', '/handle/?controller=data_backend&action=index&func=cost_money', glocale.LN_OBTAIN_USE_SILVER),
                ('exist_logs', '/handle/?controller=data_backend&action=index&func=exist_logs', glocale.LN_ROLE_INVENTORY_RECORD),
                ('cost_feiqian', '/handle/?controller=data_backend&action=index&func=cost_feiqian', glocale.LN_OBTAIN_USE_GIFTS),
                ('cardbag_info', '/handle/?controller=data_backend&action=cardbag_info', glocale.LN_CARD_PACKAGE_DATA),
                ('fireworks_info', '/handle/?controller=data_backend&action=fireworks_info', glocale.LN_FIREWORK_DATA),
                ('jlb_sea_cost_info', '/handle/?controller=data_backend&action=jlb_sea_cost_info', glocale.LN_CARIB_GOLD_GIFT_COST),
                ('jlb_card_info', '/handle/?controller=data_backend&action=jlb_card_info', glocale.LN_CARIB_CARD),
                #('plat_pay_info', '/handle/?controller=data_backend&action=plat_pay_info', u'平台充值数据'),
               ],
               glocale.LN_OTHER:[
                ('alter_password', '/handle/?controller=data_backend&action=alter_password', glocale.LN_ALTER_PASSWORD),
                ('quity', '/handle/?controller=data_backend&action=quity', glocale.LN_LOGOUT),
                ],
               u'advertisement':[
                ('payer_area_info', '/handle/?controller=data_backend&action=payer_area_info&min_count=0', glocale.LN_PAYER_DISTRIBUTION),
                ('payer_area_info', '/handle/?controller=data_backend&action=payer_area_info&min_count=500', glocale.LN_UP500_PAYER_DISTRIBUTION),
                ('DAU_info', '/handle/?controller=data_backend&action=DAU_info', glocale.LN_DAY_LOGIN_ROLES),
                ('platonline_info', '/handle/?controller=data_backend&action=platonline_info', glocale.LN_PLAT_COMPLEX_DATA),
                ]
            }

OPERATE_FUNC_URL    = {glocale.LN_OPERATE_DATA:[
                        ('role_item_lists', '/operate/role_item_lists/', glocale.LN_ROLE_ITEM_LIST,True),
                        ('login_username', '/operate/login_username/', glocale.LN_LOGIN_ACCOUNT,True),
                        ('feedback_manage', '/operate/feedback_manage/', glocale.LN_FEEDBACK_MANAGE,True),
                        ('game_fsa', '/operate/game_fsa/', glocale.LN_GAME_FSA,True),
                        ('send_mails', '/operate/send_mails/', glocale.LN_BULK_MAIL,True),
                        ('check_mails', '/operate/check_mails/', glocale.LN_MAIL_CHECK,True),
                        ('find_same_ip', '/operate/find_same_ip/', glocale.LN_SAME_IP_ROLE_SEARCH,True),
                        ('close_ip', '/operate/close_ip/', glocale.LN_CLOSE_ROLE_IP,True),
                        ('game_muter', '/operate/game_muter/', glocale.LN_GAME_MUTER,True),
                        ('close_account', '/operate/close_account/', glocale.LN_CLOSE_ACCOUNT,True),
                        ('spy_rogue', '/operate/spy_rogue/', glocale.LN_SPY_ROGUE_ROLE,True),
                        ('role_comm_info', '/operate/role_comm_info/', glocale.LN_ROLE_ADDRESS_BOOK,True),
                        ('role_mail_log', '/operate/role_mail_log/', glocale.LN_MAIL_RECORD,True),
                        ('role_login_log', '/operate/role_login_log/', glocale.LN_ROLE_LOGIN_RECORD,True),
                        ('sort_flash', '/operate/sort_flash/', glocale.LN_RANK_SNAPSHOT_RECORD,True),
                        ('vip_log_info', '/operate/vip_log_info/', glocale.LN_VIP_ROLE_RECORD,True),
                        ('find_role_info', '/operate/find_role_info/', glocale.LN_SEARCH_ROLE_INFO,True),
                        ('client_login_info', '/operate/client_login_info/', glocale.LN_CLIENT_LOGIN_ROLE,True),
                        ('award_code', '/operate/award_code/', glocale.LN_AWARD_CODE,True),
                        ('timing_mails', '/operate/timing_mails/', glocale.LN_TIMING_MAIL,True),
                        ('activity_task', '/operate/activity_task/', glocale.LN_ACTIVITY_CREATE,True),
                        ('operate_activity', '/operate/operate_activity/', glocale.LN_OPERATE_ACTIVITY,True),
                        ('white_list', '/operate/white_list/', glocale.LN_WHITE_LIST,True),
                        ('sstart_time', '/operate/sstart_time/', glocale.LN_SSTART_TIME,True),
                        ('announcement', '/operate/announcement/', glocale.LN_ANNOUNCEMENT,True),
                       ],
                       glocale.LN_OTHER:[
                        ('alter_password', '/operate/alter_password/', glocale.LN_ALTER_PASSWORD,True),
                        ('quity', '/operate/quity/', glocale.LN_LOGOUT,True),
                        ]
                       #u'未开发功能': [
                       # ('', '/operate/', u'物品掉落日志'),
                       # ('', '/operate/', u'玩家仓库操作日志'),
                       # ('', '/operate/', u'角色已删除物品日志'),
                       # ('', '/operate/', u'拍卖日志'),
                       # ('', '/operate/', u'充值返奖活动'),
                       # ('', '/operate/', u'首充返奖活动'),
                       #],
                    }