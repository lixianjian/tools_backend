tools_backend
============================

策划数据填写和发布。
在游戏的开发过程中，策划数据是非常重要的一环，但是策划同学们还在用excel表填写数据，程序在拿到这数据的时候还学要转换成程序可读的格式，或是导入数据库，这个过程会出现几个常见的问题。如：主键混乱、数据难以检查、数值难以控制、更新麻烦和需要大量额外脚本辅助等。<br/>
此项目就是旨在解决以上所说到的问题，所有表结构由服务器端程序员定义，策划只需要填写数据；一键发布数据，程序自动将数据组织成服务器端和客户端程序需要的结构，并根据表结构编写上下行protobuf文件，并给数据加入版本信息，避免客户端下载缓存不能更新的问题。
从此以后策划文档的更新就不再需要了程序的介入，策划人员自己发布之后就能在游戏中看到效果，这还不ＷＯＷ！

## 主要功能
　　parameters应用，该应用实现了页面上定义策划数据表结构、数据增加、数据删除、数据修改、数据查找、数据上下行结构定义和数据发布。


使用方法
===============

  * 本项目支持python2.7，不支持python3以上版本

  * 安装相关依赖

    pip install requirements.txt

  * 启动

  　　python project_ctrl.py start -u (启动用户)　-p (uwsgi占用端口)

  * 停止

  　　pytohn project_ctrl.py stop

  * 重启

  　　pytohn project_ctrl.py restart -u (启动用户)　-p (uwsgi占用端口)


注意
===============

该项目使用的是django１.4.5版本，数据库动态更新使用的是south框架，所以在django1.7以上版本无法运行，需要修改成migrations的方式。
