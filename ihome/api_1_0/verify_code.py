# -*- coding:utf-8 -*-

import logging
import random
from . import api
from ihome.utils.captcha.captcha import captcha
from ihome import redis_store, constants
from flask import jsonify, make_response,request
from ihome.utils.response_code import RET
from ihome.models import User
from ihome.libs.yuntongxun.sms import CCP

'''
开发流程:
产品经理设计好了原型图, 给了需求
一. 先后台再前端
1. 自行开发接口(定义路由, 实现视图函数) 
2. 测试接口(postman/浏览器/单元测试)
3. 编写API文档
4. 让前端根据文档进行开发

二. 前后端一起开发
1. 全后端一起交流, 定义出简易API文档, 及符合此文档的JSON数据.
2. 前后端分别开发
3. 后端先测试, 然后让前端测试
4. 完善API文档


'''



# 专门处理验证码



# 图片验证码
# url: 127.0.0.1:5000/api/v1_0/image_codes/<image_code_id>

# 参数: image_code_id

# 返回: image图像

# 格式: JSON


@api.route('/image_codes/<image_code_id>')
def get_image_code(image_code_id):

    # 1. 获取参数
    # 2. 对参数做完整性校验


    # 3. 处理业务逻辑
    # 3.1 生成验证码
    # 图片名  验证码内容  验证码图片
    name, text, image_data = captcha.generate_captcha()


    # 3.2 保存到Redis中
    try:
        # image_code_image_code_id --> text
        # setex --> set + expire
        # 第一个参数: key , 第二个参数: 过期时间 第三个参数: value
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRE, text)
    except Exception as e:
        # 保存日志
        logging.error(e)

        # 返回错误信息
        return jsonify({'errno': RET.DBERR, 'errmsg': '数据库发生了异常, 请重试'})

    # 4. 处理返回值 contet-type : text/html --> image/jpg
    response =  make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response


# 获取短信验证码
# URL 127.0.0.1:5000/api/v1_0/sms_codes/17612345678?image_code=1234&image_code_id=1234156

# 手机号: mobile
# 图片验证码:image_code
# UUID:image_code_id

# GET

@api.route('/sms_codes/<re(r"1[34578][0-9]{9}"):mobile>')
def get_sms_code(mobile):

    # 1. 获取参数
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    # 2. 效验参数
    if not all([image_code, image_code_id]):
        response_dict = {
            'errno': RET.PARAMERR,
            'errmsg': '参数不全, 请填写完整'
        }
        return jsonify(response_dict)

    # 3. 逻辑处理

    # 1. 和redis数据对比: 获取redis数据, 判断是否为None, 无论正确与否都要删除, 和用户传入的数据做对比
    # 2. 判断用户是否已经注册过, 判断是否为空
    # 3. 发送短信验证码: 自行生成验证码, 保存到redis, 调用云通信接口发送验证码

    # 3.1 获取redis数据 --> try
    try:
        real_image_code = redis_store.get('image_code_' + image_code_id)
    except Exception as e:
        logging.error(e)
        response_dict = {
            'errno': RET.DBERR,
            'errmsg': '访问数据库异常'
        }
        return jsonify(response_dict)

    # 3.2判断是否为None
    # 数据库, 获取空值就是None
    if real_image_code is None:
        response_dict = {
            'errno': RET.NODATA,
            'errmsg': '验证码已过期/或已删除'
        }
        return jsonify(response_dict)

    # 3.3 无论正确与否都要删除 try
    # 图片验证码通常只能用一次
    try:
        redis_store.delete('image_code_' + image_code_id)
    except Exception as e:
        logging.error(e)
        # 理论上应该返回错误信息. 但是从用户体验的角度来说. 用户没有做错事, 只是服务器删除失败.
        # 就算没有立即删掉, 2分钟后也会过期. 可以考虑不删除 --> 产品经理角度(将来和产品经理商量一下)

    # 3.4 和用户传入的数据做对比
    # 142B 142b 为了忽略大小写的问题, 建议全大写或小写
    if image_code.lower() != real_image_code.lower():
        response_dict = {
            'errno': RET.DATAERR,
            'errmsg': '验证码输入错误'
        }
        return jsonify(response_dict)

    # 3.5 判断用户是否已经注册过, 判断是否为空 try
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        # 理论上, 需要返回错. 从体验角度讲, 后面的立即注册也会去检测用户是否注册. 因此可以考虑本次错误不返回
    else:
        # 判断用户不为空, 说明已经注册过
        if user is not None:
            response_dict = {
                'errno': RET.DATAEXIST,
                'errmsg': '该手机号已存在'
            }
            return jsonify(response_dict)

    # 3.6 自行生成验证码
    # 06d: 要求6位数, 不足以0补齐
    sms_code = '%06d' % random.randint(0, 999999)

    # 3.7 保存到redis try
    try:
        # 第一个参数: key , 第二个参数: 过期时间 第三个参数: value
        redis_store.setex('sms_code_' + mobile, constants.SMS_CODE_REDIS_EXPIRE, sms_code)
    except Exception as e:
        logging.error(e)
        response_dict = {
            'errno': RET.DBERR,
            'errmsg': '访问redis出错'
        }
        return jsonify(response_dict)

    # 3.8 调用云通信接口发送验证码 try
    ccp = CCP()
    try:
        status_code = ccp.send_template_sms(mobile, [sms_code, str(constants.SMS_CODE_REDIS_EXPIRE / 60)], 1)
    except Exception as e:
        logging.error(e)
        response_dict = {
            'errno': RET.THIRDERR,
            'errmsg': '发送异常'
        }
        return jsonify(response_dict)

    # 4. 返回数据
    if status_code == '000000':
        # 发送成功
        response_dict = {
            'errno': RET.OK,
            'errmsg': '发送成功'
        }
        return jsonify(response_dict)
    else:
        # 发送失败
        response_dict = {
            'errno': RET.THIRDERR,
            'errmsg': '发送失败'
        }
        return jsonify(response_dict)
