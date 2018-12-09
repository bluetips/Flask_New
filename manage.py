from flask import current_app
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import db, create_app
from info import models
from info.models import User

app = create_app('development')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@manager.option('-n', '-name', dest='name')
@manager.option('-p', '-pwd', dest='pwd')
def createsuperuser(name, pwd):
    if not all([name, pwd]):
        print('参数不足')
        return

    user = User()
    user.name = name
    user.mobile = name
    user.nick_name = name
    user.password = pwd
    user.is_admin = True

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        print('数据库错误')
        return

    print('创建成功')
    return


if __name__ == '__main__':
    manager.run()
