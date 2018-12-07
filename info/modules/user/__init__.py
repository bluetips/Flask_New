from flask import Blueprint

user_blu = Blueprint('user_blu', __name__,url_prefix='/user')

from . import views
