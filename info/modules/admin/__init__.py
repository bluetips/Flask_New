from flask import Blueprint

admin_blu = Blueprint('admin_blu', __name__)

from . import views
