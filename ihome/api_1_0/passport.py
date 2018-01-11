# -*- coding:utf-8 -*-

import re
import logging
from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import User
from ihome.utils.common import login_required
from ihome import constants

# 注册/登录/退出

# URL: 127.0.0.1:5000/api/v1_0/users/

# POST

# mobile
# sms_code
# password(可以不需要第二个密码, 前端做好判断即可)


# 注册是对user资源做处理
# 以前定义的路由正则转换器, 只针对路由地址的参数做匹配的
@api.route('/users', methods=['POST'])
def register():

    # 405 --> 检查模块是否导入, 检查是否有POST

    # 前后端分离的项目, 要求都用JSON传递数据

    # 一. 获取参数
    # request.args
    # request.form
    # request.data --> 获取的是JSON字符串 --> 需要转换JSON格式
    # request.get_data()
    # request.get_json() --> 直接可以获取json格式的数据

    # 测试时, 先去掉csrf保护
    # resp_data = request.get_data()
    # print 'get_data(: mobile %s' % resp_data.get('mobile')
    # resp_json = request.get_json()
    # print 'get_json: mobile %s' % resp_json.get('mobile')

    # 获取JSON数据, 并将数据转为字典
    resp_json = request.get_json()
    mobile= resp_json.get('mobile')
    sms_code= resp_json.get('sms_code')
    password= resp_json.get('password')

    # 二. 效验参数
    # 2.1 完整性
    if not all([mobile, sms_code, password]):
        return jsonify({'errno': RET.PARAMERR, 'errmsg': '参数不完整'})

    # 2.2 手机号正则
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify({'errno': RET.PARAMERR, 'errmsg': '不正确的手机号'})

    # 三. 逻辑处理
    # 3.1 从redis中获取短信验证码 try
    try:
        real_sms_code = redis_store.get('sms_code_' + mobile)
    except Exception as e:
        # logging.error(e)
        # current_app里, 有loggin模块, 也可以实现日志记录. 但是不如logging好用
        current_app.logger.error(e)
        return jsonify({'errno': RET.DBERR, 'errmsg': '访问数据库异常'})

    # 3.2 判断是否为None(5分钟就过期了)
    if real_sms_code is None:
        return jsonify({'errno': RET.NODATA, 'errmsg': '短信验证码已过期'})

    # 如果先删除再判断. 用 1. 服务器要重发验户输入错误的体验不好.证码 2. 发送时间可能较长, 可能会流失用户
    # 正常开发中, 允许短信验证码输入错误, 不会立刻删除
    # 3.3 对比短信验证码
    if sms_code != real_sms_code:
        return jsonify({'errno': RET.DATAERR, 'errmsg': '短信验证码输入错误'})

    # 3.4 删除redis中的验证码 try
    try:
        redis_store.delete('sms_code_' + mobile)
    except Exception as e:
        logging.error(e)
        # 这里不删除, 一会也会过期. 而且用户没有做错事情, 只是服务器有点异常. 我们可以此此错误不返回信息

    # 3.5 增加用户信息-->密码加密
    # 这里不需要再次查询用户是否存在
    # 原因: 1. 获取短信验证码的时候已经判断过了. 2. 数据模型中已经增加了unique, 无法重复添加相同的数据
    user = User(name=mobile, mobile=mobile)

    # 调用user的password的setter方法
    user.password = password
    # 密码记录时, 会保存盐值和加密方式. 目的是为了登录时验证用的
    # pbkdf2:sha256:50000$HDEvpuI3$23f026797d7b9f507f4ccd7b88dd5e39a9bbd0b833451fcb1ae78d9d22298743

    # user1 123456 aserwq
    # user2 123456 zxdifa
    # password --> 做加密处理
    # user.password_hash
    # TODO(zhubo) 未设置密码
    # user.password = password

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify({'errno': RET.DBERR, 'errmsg': '数据库错误请重试'})

    # 3.6 可以返回首页(设置session, 达到状态保持), 也可以返回登录页((登录成功设置session, 达到状态保持))
    # 如果要返回的登录页面, 那么这里就不用设置session
    # session['user_id'] = user.id
    # session['mobile'] = mobile
    # session['user_name'] = mobile


    # 四. 返回数据
    return jsonify({'errno': RET.OK, 'errmsg':'注册成功'})


# 登录是对session进行设置
# URL: 127.0.0.1:5000/api/v1_0/sessions/

# POST

# mobile
# password
@api.route('/sessions', methods=['POST'])
def login():
    # 一. 获取参数
    resp_json = request.get_json()
    mobile = resp_json.get('mobile')
    password = resp_json.get('password')

    # 二. 效验参数
    # 2.1 完整性
    if not all([mobile, password]):
        return jsonify({'errno': RET.PARAMERR, 'errmsg': '参数不完整'})

    # 2.2 手机号正则
    if not re.match(r'1[34578]\d{9}', mobile):
        return jsonify({'errno': RET.PARAMERR, 'errmsg': '不正确的手机号'})

    # 三. 逻辑处理
    '''
    1. 登录需要判断和记录错误次数, 登录错误次数过多, 在redis中记录该手机号或者IP
    如果超过了最大次数, 就直返返回, 不需要执行登录逻辑

    2. 判断用户名(查询数据库)和密码(验证密码)是否正确, 设置错误次数INCR key, 同时设置有效期

    3. 登录成功, 删除redis的错误数据

    4. 设置session
    '''
    # 3.1 读取redis数据 try  'access_' + user_ip
    user_ip = request.remote_addr
    try:
        access_count = redis_store.get('access_count_' + user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify({'errno': RET.DBERR, 'errmsg': 'redis数据库错误'})

    # 获取到了数据, and 次数没有超过最大值. 假设最大次数为5
    if access_count is not None and int(access_count) >= constants.LOGIN_ERROR_MAX_NUM:
        return jsonify({'errno': RET.REQERR, 'errmsg': '登录机会已用完, 请稍后重试'})

    # 3.2 判断用户名(查询数据库)和密码(验证密码)是否正确, 设置错误次数INCR key, 同时设置有效期 try
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify({'errno': RET.DBERR, 'errmsg': 'mysql数据库错误'})

    # user不存在 or 密码检查没通过  --> 用户名或密码错误
    if user is None or not user.check_password(password):

        try:
            # incr: 增加次数, 默认增加1
            redis_store.incr('access_count_' + user_ip)
            redis_store.expire('access_count_' + user_ip, constants.LOGIN_ERROR_FORBID_TIME)
        except Exception as e:
            logging.error(e)
            return jsonify({'errno': RET.DBERR, 'errmsg': 'redis设置有效期出错'})

        return jsonify({'errno': RET.LOGINERR, 'errmsg': '用户名或密码错误'})

    # 3.3 登录成功, 删除redis的错误数据 try
    try:
        redis_store.delete('access_count_' + user_ip)
    except Exception as e:
        logging.error(e)
        return jsonify({'errno': RET.DBERR, 'errmsg': 'redis删除有效期出错'})

    # 3.4. 设置session
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['user_name'] = user.name

    # 四. 数据返回
    return jsonify({'errno': RET.OK, 'errmsg': '登录成功'})


# 检查登陆状态
@api.route("/sessions", methods=["GET"])
def check_login():
    """检查登陆状态"""
    # 尝试从session中获取用户的名字
    name = session.get("user_name")
    # 如果session中数据name名字存在，则表示用户已登录，否则未登录
    if name is not None:
        return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg="false")


# 退出登录
@api.route("/sessions", methods=["DELETE"])
@login_required
def logout():
    """登出"""
    # location.href = '/login.html'   location.href 只是页面内跳转, 网页不会刷新. 如果不刷新, 无法设置csrf_token.
    # 清除session数据, csrf_token需要保留.
    csrf_token = session['csrf_token']
    session.clear()
    session['csrf_token'] = csrf_token
    return jsonify(errno=RET.OK, errmsg="OK")