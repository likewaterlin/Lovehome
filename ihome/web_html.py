# -*- coding:utf-8 -*-

# 处理html静态资源访问的
from flask import Blueprint, current_app, make_response, request
from flask_wtf.csrf import generate_csrf

html = Blueprint('html', __name__)

'''
127.0.0.1:5000  --> static/html/index.html
127.0.0.1:5000/index.html  --> static/html/index.html
127.0.0.1:5000/login.html  --> static/html/login.html
'''


# @html.route('/')
# def index():
#
#     # 将html当做静态文件返回
#     return current_app.send_static_file('html/index.html')
#
#
# @html.route('/<file_name>')
# def get_file_name(file_name):
#
#     # 将html当做静态文件返回
#     return current_app.send_static_file('html/' + file_name)


# . 匹配任何单个字符
# * 匹配0或多个
@html.route('/<re(r".*"):file_name>')
def get_html_file(file_name):

    # print file_name

    # 1. 处理没有文件名, 自行拼接首页
    if not file_name:
        file_name = 'index.html'

    # 2. 如果发现文件名不叫"favicon.ico", 再拼接html/路径
    # favicon.ico: 浏览器为了显示图标, 会自动向地址发出一个请求
    if file_name != 'favicon.ico':
        file_name = 'html/' + file_name

    #将html当做静态文件返回
    # 3. 如果文件名是'favicon.ico', 就直接返回

    # 如果访问的页面, 紧跟着post/put/delete 都需要csrf_token.
    # 所以, 应该在访问任意网页时, 增加cookie

    # generate_csrf会检测当前session, 如果有, 则返回session中的. 如果没有, 则重新创建
    # Flask中从Session里的csrftoken取出来做对比
    print file_name

    csrf_token = generate_csrf()
    response = make_response(current_app.send_static_file(file_name))
    response.set_cookie('csrf_token', csrf_token)

    print csrf_token
    return response