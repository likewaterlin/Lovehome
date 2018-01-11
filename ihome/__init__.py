# -*- coding:utf-8 -*-

# 创建APP用的

import redis
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config_dict, Config
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from logging.handlers import RotatingFileHandler
from utils.common import RegexConverter


# 将参数延后传入的技巧
# 问题抛出: 有些对象, 外界需要应用. 但是这个对象又必须在app创建之后
# 解决方案: 可以先创建该对象, 在app创建之后, 再设置app
db = SQLAlchemy()

csrf = CSRFProtect()

redis_store = None

# csrf保护, redis, Session


'''
日志的级别
ERROR: 错误级别
WARN: 警告级别
INFO: 信息界别
DEBUG: 调试级别

平时开发, 可以使用debug和info替代print, 来查看对象的值
上线时, 不需要删除这个日志, 只需要更改日志的级别为error/warn
'''

# 设置日志的记录等级
logging.basicConfig(level=logging.DEBUG)  # 调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

# 提供一个函数来参加app, 同时提供参数, 让外界传入
def create_app(config_name):

    # 参加Flask应用程序实例
    app = Flask(__name__)

    # 导入配置参数
    config_mode = config_dict[config_name]
    app.config.from_object(config_mode)

    # 给app的路由转换器字典增加我们自定义的转换器
    app.url_map.converters['re'] = RegexConverter

    # 在app创建只会, 给db对象传入app参数
    db.init_app(app)

    # 给csrf导入app
    csrf.init_app(app)

    # 创建redis
    global redis_store
    redis_store = redis.StrictRedis(port=Config.REDIS_PORT, host=Config.REDIS_HOST)

    # 创建能够将默认存放在cookie的sesion数据, 转移到redis的对象
    # http://pythonhosted.org/Flask-Session/
    Session(app)

    # 为了解决循环导入的问题, 需要将蓝图的导入延后导入.
    # 建议将URL前缀放在注册蓝图的地方.
    # 为了确保程序在查找目录时不出错, 需要设置工作目录
    from api_1_0 import api
    # 注册蓝图
    app.register_blueprint(api, url_prefix='/api/v1_0')

    import web_html
    app.register_blueprint(web_html.html)

    return app, db



