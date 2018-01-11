# -*- coding: UTF-8 -*-

import logging
from CCPRestSDK import REST
import ConfigParser

# 主帐号
accountSid = '8aaf07085f9eb021015fb58c56d906e8'

# 主帐号Token
accountToken = 'e21ca96da61c49ee97e0fdf1ba47de5a'

# 应用Id
appId = '8aaf07085f9eb021015fb58c574106ef'

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com'

# 请求端口
serverPort = '8883'

# REST版本号
softVersion = '2013-12-26'

# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为列表 例如：['12','34']，如不需替换请填 ''
# @param $tempId 模板Id

'''
1. 工具类 , 属于拿过来就可以直接使用.
2. SDK, 软件开发工具包. 
    1>一般的SDK, 都会有官网, 需要注册, 创建一个应用
    2>这个应用都有一些对应的APPID, SECRET_KEY等之类的信息, 用于认证用户(因为这些服务通常要收费, 一般人不能随便调用)
    3>SDK, 官网有详细的文档, 示例(Demo), 提供技术支持
    4>有所的SDK在使用之前, 都会进行鉴权操作(鉴定你是否有调用接口的权利)
'''


class CCP(object):
    # 提供单例, 重写__new__
    # 核心思路: 创建一个类对象, 第一次用一个属性保存起来. 当下次调用时, 直接返回即可
    # 单例核心: 如果没有就创建, 如果有就返回

    def __new__(cls):
        # 1. 判断是否有某个属性
        if not hasattr(cls, 'instance'):
            # 2. 调用父类方法, 创建一个对象
            # cls.instance = super(CCP, cls).__new__(cls)
            obj = super(CCP, cls).__new__(cls)

            # 3. 修改初始化REST SDK的方法
            # cls.instance.rest = REST(serverIP, serverPort, softVersion)
            # cls.instance.rest.setAccount(accountSid, accountToken)
            # cls.instance.rest.setAppId(appId)
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)

            cls.instance = obj

        # 4. 如果有instance属性, 直接返回
        return cls.instance

    '''
    1. to: 短信接收手机号码集合, 用英文逗号分开, 如'13810001000,13810011001', 最多一次发送200个。
    2. datas：内容数据，需定义成列表方式，如模板中有两个参数，定义方式为array['验证码', '过期时间']。
    3. temp_id: 模板Id, 如使用测试模板，模板id为"1"，如使用自己创建的模板，则使用自己创建的短信模板id即可。 
    '''

    def send_template_sms(self, to, datas, temp_id):
        # self: 这里的self就是cls.instance

        # 发送网络请求, 所以加try
        try:
            result = self.rest.sendTemplateSMS(to, datas, temp_id)
        except Exception as e:
            logging.error(e)
            raise e

        # 主要的目的啊是从result获取statusCode的值. 如果是'000000'才是正确
        return result.get('statusCode')


if __name__ == '__main__':
    ccp = CCP()
    ccp.send_template_sms('17610812003', ['123456', '5'], 1)


# def send_template_sms(to,datas,tempId):
#
#
#     #初始化REST SDK
#     rest = REST(serverIP,serverPort,softVersion)
#     rest.setAccount(accountSid,accountToken)
#     rest.setAppId(appId)
#
#     result = rest.sendTemplateSMS(to,datas,tempId)
#     for k,v in result.iteritems():
#
#         if k=='templateSMS' :
#                 for k,s in v.iteritems():
#                     print '%s:%s' % (k, s)
#         else:
#             print '%s:%s' % (k, v)


#sendTemplateSMS(手机号码,内容数据,模板Id)

# if __name__ == '__main__':
    # sendTemplateSMS('17610812003', ['123456', '5'], 1)

    # ccp1 = CCP()
    # ccp2 = CCP()
    # print ccp1
    # print ccp2

    # 1. 提供单例
    # ccp = CCP()
    # 2. 修改方法, 提供返回值
    # status_code = ccp.sendTemplateSMS