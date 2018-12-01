from flask import session
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from info import db, create_app

app = create_app('development')
manager = Manager(app)
Migrate(app, db)
manager.add_command('db', MigrateCommand)


@app.route('/')
def hello_world():
    session['name'] = 'itcast'
    return 'Hello World!'


if __name__ == '__main__':
    manager.run()
