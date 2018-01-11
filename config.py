# -*- coding:utf-8 -*-

import redis


class Config(object):
    # 调试模式 SECRET_KEY MYSQL Redis Session
    # MYSQL
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@127.0.0.1/ihomesh04'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 创建redis实例用到的参数
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # 配置SECREK_KEY
    '''
    import os
    import base64
    base64.b64encode(os.urandom(32))
    '''
    SECRET_KEY = 'gC3mALnjFSMTl8hOh2JAwtjEY/o22/k061PK5mXlbg8='

    # 配置session存储到redis中
    PERMANENT_SESSION_LIFETIME = 86400  # 单位是秒, 设置session过期的时间
    SESSION_TYPE = 'redis'  # 指定存储session的位置为redis
    SESSION_USE_SIGNER = True  # 对数据进行签名加密, 提高安全性
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)  # 设置redis的ip和端口


class DevelopmentConfig(Config):
    # 调试模式
    DEBUG = True


class ProductionConfig(Config):
    # 暂时用不上, 如果需要, 请填入对应配置信息
    pass


# 提供一个字典, 绑定关系
config_dict = {
    'develop': DevelopmentConfig,
    'product': ProductionConfig
}
