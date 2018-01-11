# -*- coding:utf-8 -*-

# 只负责程序的启动

from ihome import create_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

# manger.run
# add db

# 实际上, 程序的运行时需要区分开发模式和发布模式的. 这个模式的控制, 也应该交由manage来管理

app, db = create_app('develop')

# 创建manager
manager = Manager(app)
# 创建迁移对象
migrate = Migrate(app, db)
# 给manager添加db命令
manager.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manager.run()
