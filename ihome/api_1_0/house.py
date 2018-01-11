# -*- coding:utf-8 -*-

import logging
from . import api
from ihome import redis_store
from ihome.models import Area, House, Facility, HouseImage, User, Order
from flask import jsonify, json, request, g, session
from ihome.utils.response_code import RET
from ihome import constants, db
from ihome.utils.common import login_required
from ihome.utils.image_storage import storage
from datetime import datetime


# 这里存放和房屋相关的路由


# /areas
# get
@api.route('/areas/')
def get_area_info():
    # 一. 逻辑处理

    '''
    1. 读取redis中的缓存数据
    2. 没有缓存, 去查询数据库
    3. 为了将来读取方便, 在存入redis的时候, 将数据转为JSON字典
    4. 将查询的数据, 存储到redis中
    '''
    # 1. 读取redis中的缓存数据
    try:
        areas_json = redis_store.get('area_info')
    except Exception as e:
        logging.error(e)
        # 这里不需要返回错误信息, 因为没有会直接查询数据库
        # 为了避免异常的事情发生, 如果执行失败, 就把数据设置为None
        areas_json = None

    # 2. 没有缓存, 去查询数据库
    if areas_json is None:
        # 查询区域信息
        areas_list = Area.query.all()

        # 3. 数据转JSON
        areas = []
        # for area in areas_list:
        #     # 调用模型的转字典方法, 不断拼接成一个areas
        #     areas.append(area.to_dict())
        #
        # # 将areas转换成JSON, 方便将来保存redis, 方便返回数据
        #
        # # json.dumps 将list类型转换成了str
        # areas_dict = {'areas': areas}
        # areas_json = json.dumps(areas_dict)

        # 调用模型的转字典方法, 不断拼接成一个areas
        areas_dict = {'areas': [area.to_dict() for area in areas_list]}

        # 将字典类型转换成了str
        areas_json = json.dumps(areas_dict)

        # 4. 保存redis中
        try:
            redis_store.setex('area_info', constants.AREA_INFO_REDIS_EXPIRES, areas_json)
        except Exception as e:
            logging.error(e)
            # 这里如果出错, 可以不用返回错误信息. 因此如果redis没有保存, 那么下一次会直接访问Mysql读取数据, 再次保存

    # 二. 返回数据
    # 1. 希望返回的数据, data里是一个字典
    # return jsonify(errno=RET.DBERR, errmsg='查询城区信息成功', data=areas)

    # 2. json.dumps --> jsonify --> 连续转换, 第二次会将第一次的结果当做一个字符串的value进行二次转换
    # return jsonify(errno=RET.DBERR, errmsg='查询城区信息成功', data={'areas': areas_json})

    # 3. a. 因为前面已经转换过了. 这里不需要二次转换.  b.JSON格式消耗性能, 返回原生字典会比较快
    # return '{"errno": 0, "errmsg": "查询城区信息成功", "data":%s}' % areas_json, 200, \
    #        {"Content-Type": "application/json"}
    return '{"errno": 0, "errmsg": "查询城区信息成功", "data":%s}' % areas_json
    '''
        为了方便客户端解析数据, data中最好返回的是字典. 客户端就可以通过字典的方式取值
       data = {
            "areas": [
                {
                    "aid": 1,
                    "aname": "东城区"
                },
                {
                    "aid": 2,
                    "aname": "西城区"
                }
            ]
        }

        area.to_dict():
        {
            "aid": 1,
            "aname": "东城区"
        }


        areas = []
        for area in areas_list:
            # 调用模型的转字典方法, 不断拼接成一个areas
            areas.append(area.to_dict()):
        [
            {
                "aid": 1,
                "aname": "东城区"
            },
            {
                "aid": 2,
                "aname": "西城区"
            }
        ]
    '''



# 发布房屋信息接口
@api.route('/houses/info', methods=['POST'])
@login_required
def save_house_info():
    """保存房屋的基本信息
        前端发送过来的json数据
        {
            "title":"",
            "price":"",
            "area_id":"1",
            "address":"",
            "room_count":"",
            "acreage":"",
            "unit":"",
            "capacity":"",
            "beds":"",
            "deposit":"",
            "min_days":"",
            "max_days":"",
            "facility":["7","8"]
        }
        """
    # 一. 获取参数
    house_data = request.get_json()
    if house_data is None:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数
    max_days = house_data.get("max_days")  # 最大入住天数

    # 二. 参数效验
    if not all(
            (title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days)):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 前端有可能传递的不是flost/int. 需要对价格和押金做转换
    # 服务器为了避免小数点精确度的影响, 最好保存成int类型. 以分为单位
    # 当前项目的需求, 价格没有小数点

    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='价格有误')

    # 三. 保存房屋信息
    # 1. 创建房屋对象

    # 谁订的房子
    user_id = g.user_id
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )

    # 2. 处理房屋的设施信息 --> 在这里获取房屋设施的信息, 如果有信息, 拼接到房屋对象里. 如果没有直接返回
    # 2.1 先去请求中获取facility数据
    facility_id_list = house_data.get('facility')

    # 2.2 再去查询数据库中是否存在-->避免前端传递了错误数据(相当于参数效验)
    if facility_id_list:
        try:
            # 去数据库查询, 所传入的设施ID是否存在
            facility_list = Facility.query.filter(Facility.id.in_(facility_id_list)).all()
            # select * from faclity where id in (facality_id_list)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')

        # 2.3查询到了, 添加到house数据中
        if facility_list:
            house.facilities = facility_list

    # 3. 保存数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库添加异常')

    # 四. 返回数据
    # 这里需要返回房屋的ID信息. 因为发布成功后, 会进入发布房屋图片的界面.
    # 设置图片, 必须知道房屋的ID才行
    return jsonify(errno=RET.OK, errmsg='设置房屋信息成功', data={'house_id': house.id})


@api.route('/houses/<int:house_id>/images', methods=['POST'])
@login_required
def save_house_image(house_id):

    # 一. 获取参数
    # house_id
    # image_file
    # 如果ID从接口传入的, 那么可以不用从form中获取
    # house_id = request.form.get('house_id')
    image_file = request.files.get('house_image')

    # 二. 效验参数
    if not all([house_id, image_file]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 三. 逻辑处理
    # 1. 查询房屋id是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 2. 上传图像到七牛云
    image_data = image_file.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='上传图像异常')

    # 3. 保存到数据库
    house_image = HouseImage(
        house_id = house_id,
        url = file_name
    )
    db.session.add(house_image)

    # 4. 将第一张图像加入到index_image_urlzhong
    if not house.index_image_url:
        house.index_image_url = file_name
        db.session.add(house)

    # 5. 统一提交
    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')

    # 四. 返回数据
    image_url = constants.QINIU_URL_DOMAIN + file_name
    return jsonify(errno=RET.OK, errmsg='上传图片成功', data={'image_url': image_url})


@api.route("/users/houses", methods=["GET"])
@login_required
def get_user_houses():
    """获取房东发布的房源信息条目"""
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses

        # houses = House.query.filter_by(user_id=user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取数据失败")

    # 将查询到的房屋信息转换为字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """获取主页幻灯片展示的房屋基本信息"""
    # 从缓存中尝试获取数据
    try:
        ret = redis_store.get("home_page_data")
    except Exception as e:
        logging.error(e)
        ret = None
    if ret:
        logging.info("hit house index info redis")
        # 因为redis中保存的是json字符串，所以直接进行字符串拼接返回
        return '{"errno":0, "errmsg":"OK", "data":%s}' % ret
    else:
        try:
            # 查询数据库，返回房屋订单数目最多的5条数据
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询无数据")

        houses_list = []
        for house in houses:
            # 如果房屋未设置主图片，则跳过
            if not house.index_image_url:
                continue
            houses_list.append(house.to_basic_dict())

        # 将数据转换为json，并保存到redis缓存
        json_houses = json.dumps(houses_list)
        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)

        return '{"errno":0, "errmsg":"OK", "data":%s}' % json_houses


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg="参数缺失")

    # 先从redis缓存中获取信息
    try:
        ret = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        logging.error(e)
        ret = None
    if ret:
        logging.info("hit house info redis")
        return '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, ret), 200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询数据失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 将房屋对象数据转换为字典
    try:
        house_data = house.to_full_dict()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg="数据出错")

    # 存入到redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, json_house)
    except Exception as e:
        logging.error(e)

    resp = '{"errno":"0", "errmsg":"OK", "data":{"user_id":%s, "house":%s}}' % (user_id, json_house)
    return resp


# GET /api/v1_0/houses/?sd=XX&ed=XX&sk=XX&aid=XX&p=XX
@api.route('/houses', methods=['GET'])
def get_house_list():
    # 一. 获取参数
    # 注意: 参数可以不传, 不传就把参数设为空值或者默认值
    start_date_str = request.args.get('sd', '')  # 查询的起始时间
    end_date_str = request.args.get('ed', '')  # 查询的起始时间
    sort_key = request.args.get('sk', 'new')  # 排序关键字
    area_id = request.args.get('aid', '')  # 查询的城区信息
    page = request.args.get('p', 1)  # 查询的页数

    # 二. 校验参数
    # 2.1判断日期
    # 需要确保能够转换成日期类, 且开始时间不能小于结束时间
    try:
        # 需要确保能够转换成日期类
        start_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        if start_date and end_date:
            # 开发期间, 可以通过增加断言来帮助挑错
            assert start_date <= end_date

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        # 且开始时间不能小于结束时间
    # 2.2判断页数
    # 需要确保页数能够转为int类型
    try:
        page = int(page)
    except Exception as e:
        page = 1


    # 三. 业务逻辑处理

    # 3.1 先从redis缓存中获取数据
    # 如果获取了数据, 可以直接返回, 不需要执行下面逻辑
    redis_key = 'houses_%s_%s_%s_%s' % (start_date_str, end_date_str, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
        resp_json = None

    if resp_json:
        # 说明获取了redis的值
        # return resp_json, 300
        return resp_json

    # 3.2 定义查询数据的参数空列表
    # 为了方便设置过滤条件, 先定义空列表, 然后逐步判断添加进来
    filter_params = []

    # 3.3 处理区域信息
    if area_id:
        # ==: 默认的==(__)  / < / > 内部是调用了某个函数
        # 数据库框架内部重写了==的__eq__函数, 所以结果是SQL对象
        filter_params.append(House.area_id == area_id)

    # 3.4 处理时间, 获取不冲突的房屋信息
    # 需要根据传入的时间参数不同, 获取冲突的房屋, 再从房屋中获取对应的房屋ID
    try:
        conflict_orders_li = []
        if start_date and end_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            # 从订单表中查询冲突的订单，进而获取冲突的房屋id
            conflict_orders_li = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库异常")

    if conflict_orders_li:
        conflict_house_id_li = [order.house_id for order in conflict_orders_li]
        # 添加条件，查询不冲突的房屋
        filter_params.append(House.id.notin_(conflict_house_id_li))

    # 定义查询语句, 将filter_params传入
    # House.query.filter_by(*filter_params).order_by()

    # 3.5 排序
    # 不同的排序, 过滤条件不同
    # sort - key = "booking" > 入住最多
    # sort - key = "price-inc" > 价格低 - 高
    # sort - key = "price-des" > 价格高 - 低 < / li >
    # new 默认 > 最新发布的在前

    if sort_key == 'booking':
        # 如果没有跟上all(), first(), paginate(), 下面的代码只是过滤条件
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == 'price-des':
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 3.6 分页  sqlalchemy的分页
    # 在之前房屋的过滤条件后面, 使用paginate设置分页
    # paginate三个参数: 当前要查询的页码, 每页数量, 是否要返回错误信息
    try:
        house_page = house_query.paginate(page, constants.HOUSE_LIST_PAGE_CAPACITY, False)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询错误')

    # 获取总页数
    total_page = house_page.pages
    # 获取当前页数
    # house_page.page

    # 获取分页的数据, 需要调用items
    house_li = house_page.items

    # 3.7 将数据转为JSON# 定义一个空列表, 遍历拼接转换后的模型数据
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    resp = dict(errno=RET.OK, errmsg='查询成功', data={'houses':houses, 'total_page': total_page, 'current_page': page})
    resp_json = json.dumps(resp)


    # 3.8 将结果缓存到redis中
    # 用redis的哈希类型保存分页数据, 并使用事务提交保存

    # 传入的页码超过了最大页数 6 > 5
    if page <= total_page:
        redis_key = 'houses_%s_%s_%s_%s' % (start_date_str, end_date_str, area_id, sort_key)

        try:
            # 这里使用事务提交. 两个操作必须同时执行才行.
            # 如果使用事务提交, 那么失败了, 会自动回滚
            pipeline = redis_store.pipeline()

            # 开启事务
            pipeline.multi()
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_EXPIRES)

            # 执行事务
            pipeline.execute()

        except Exception as e:
            logging.error(e)

    # 四. 数据返回
    # return resp_json, 200
    return resp_json