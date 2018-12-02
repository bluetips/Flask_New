from flask import Blueprint

passport_blu = Blueprint('passport-blu', __name__, url_prefix='/passport')

from . import views
