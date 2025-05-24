from flask import Blueprint
from flask_cors import CORS

api_bp = Blueprint('api', __name__)

from . import auth
from . import scan
from . import search
from . import trash 