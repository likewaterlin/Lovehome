# -*- coding:utf-8 -*-

# 管理api的路由, 应该使用蓝图的目录方式去实现

from flask import Blueprint

api = Blueprint('api', __name__)

import index, verify_code, passport, profile, house, order


# 为了封装response设置content-type为JSON.
# 可以使用请求钩子函数进行设置
@api.after_request
def  after_request(response):
    # 可以先判断, responce的content-type类型是否是json. 如果不是, 再设置
    if response.headers.get("Content-Type").startswith("text"):
        response.headers['Content-Type'] = 'application/json'
    return response

