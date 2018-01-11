# -*- coding:utf-8 -*-

import logging
from . import api
from flask import request, g, jsonify, session, current_app
from ihome.utils.common import login_required
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db
from ihome import constants

# 存储用户相关的设置


# 设置头像接口
@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():

    # 一. 获取参数
    # 1.1 因为数据库查询要用
    user_id = g.user_id

    # 1.2 图像文件
    avatar_file = request.files.get('avatar')

    # 二. 效验参数
    if avatar_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图像')

    # 三. 逻辑处理
    # 3.1 上传七牛云

    # # 获取二进制文件
    # avatar_data = avatar_file.read()
    #
    # # 调用工具类的函数
    # avatar_name = storage(avatar_data)

    # 3.2 更新数据库
    # user = User.query.filter_by(id=user_id).first()
    # user.avatar_url = avatar_name
    # db.session.add(user)
    # db.session.commit()

    # 3.1 try: 上传七牛云
    # 获取二进制文件
    avatar_data = avatar_file.read()
    try:
        # file_name 就存储的是图片名. 将来就可以再程序中调用显示
        file_name = storage(avatar_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图像异常')

    # 3.2 try:保存图像到数据库中
    try:
        # update: 查询之后拼接update, 可以直接进行更新操作
        # update中需要传入字典
        # 为了节省空间, 存数据库只存文件名. 域名可以自行拼接
        User.query.filter_by(id=user_id).update({"avatar_url": file_name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库保存图像失败')

    # 四. 返回数据
    # 返回给前端时, 需要拼接域名 , 返回一个完整的URL

    # 此时的文件名, 没有域名. 因此如果直接返回给客户端, 客户端无法直接加载
    # ozcxm6oo6.bkt.clouddn.com
    # 为了避免在数据库存储过多重复的域名前缀, 因此保存的时候, 不加域名. 返回给前端数据时, 我们拼接域名即可

    # 拼接完整的图像URL地址
    avatar_url = constants.QINIU_URL_DOMAIN + file_name

    # 返回的时候, 记得添加图像url信息
    # 如果还需要额外的返回数据, 可以再后方自行拼接数据, 一般会封装成一个字典返回额外数据
    return jsonify(errno=RET.OK, errmsg='保存图像成功', data={"avatar_url": avatar_url})


# 修改用户名
@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
    """修改用户名"""
    # 使用了login_required装饰器后，可以从g对象中获取用户user_id
    user_id = g.user_id

    # 获取用户想要设置的用户名
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    name = req_data.get("name")  # 用户想要设置的名字
    if not name:
        return jsonify(errno=RET.PARAMERR, errmsg="名字不能为空")

    # 保存用户昵称name，并同时判断name是否重复（利用数据库的唯一索引)
    try:
        User.query.filter_by(id=user_id).update({"name": name})
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="设置用户错误")

    # 修改session数据中的name字段
    session["user_name"] = name
    return jsonify(errno=RET.OK, errmsg="OK", data={"name": name})


# 获取用户的个人信息
@api.route("/users", methods=["GET"])
@login_required
def get_user_profile():
    """获取个人信息"""
    user_id = g.user_id

    # 查询数据库获取个人信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


# 设置实名认证
@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
    """保存实名认证信息"""
    user_id = g.user_id

    # 获取参数
    req_data = request.get_json()
    if not req_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    real_name = req_data.get("real_name")  # 真实姓名
    id_card = req_data.get("id_card")  # 身份证号

    # 参数校验
    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    # 保存用户的姓名与身份证号
    try:
        User.query.filter_by(id=user_id, real_name=None, id_card=None)\
            .update({"real_name": real_name, "id_card": id_card})
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存用户实名信息失败")

    return jsonify(errno=RET.OK, errmsg="OK")


# 获取实名认证信息
@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_auth():
    """获取用户 的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())