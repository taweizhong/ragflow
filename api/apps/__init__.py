#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import logging
import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from flask import Blueprint, Flask
from werkzeug.wrappers.request import Request
from flask_cors import CORS

from api.db import StatusEnum
from api.db.db_models import close_connection
from api.db.services import UserService
from api.utils import CustomJSONEncoder

from flask_session import Session
from flask_login import LoginManager
from api.settings import SECRET_KEY, stat_logger
from api.settings import API_VERSION, access_logger
from api.utils.api_utils import server_error_response
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
# 导出
__all__ = ['app']

# 将 Flask 应用的访问日志处理器添加到名为 'flask.app' 的日志记录器中
logger = logging.getLogger('flask.app')
for h in access_logger.handlers:
    logger.addHandler(h)
# 为 Request 对象定义 json 属性
Request.json = property(lambda self: self.get_json(force=True, silent=True))
# 创建应用
app = Flask(__name__)
app.debug = True  # 启用调试模式
# 跨域
CORS(app, supports_credentials=True,max_age=2592000)
# 忽略URL后的/
app.url_map.strict_slashes = False
# 设置自定义JSON编码器
app.json_encoder = CustomJSONEncoder
# 捕获错误
app.errorhandler(Exception)(server_error_response)


## convince for dev and debug
# app.config["LOGIN_DISABLED"] = True
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get("MAX_CONTENT_LENGTH", 128 * 1024 * 1024))
# 用于在服务器端管理会话数据
Session(app)
# 用于管理用户的登录状态和会话
login_manager = LoginManager()
# 集成登录管理功能
login_manager.init_app(app)



def search_pages_path(pages_dir):
    app_path_list = [path for path in pages_dir.glob('*_app.py') if not path.name.startswith('.')]
    api_path_list = [path for path in pages_dir.glob('*_api.py') if not path.name.startswith('.')]
    app_path_list.extend(api_path_list)
    return app_path_list

# 设置路由分组
def register_page(page_path):
    path = f'{page_path}'

    page_name = page_path.stem.rstrip('_api') if "_api" in path else page_path.stem.rstrip('_app')
    module_name = '.'.join(page_path.parts[page_path.parts.index('api'):-1] + (page_name,))

    spec = spec_from_file_location(module_name, page_path)
    page = module_from_spec(spec)
    page.app = app
    page.manager = Blueprint(page_name, module_name)
    sys.modules[module_name] = page
    spec.loader.exec_module(page)
    page_name = getattr(page, 'page_name', page_name)
    url_prefix = f'/api/{API_VERSION}/{page_name}' if "_api" in path else f'/{API_VERSION}/{page_name}'

    app.register_blueprint(page.manager, url_prefix=url_prefix)
    return url_prefix


pages_dir = [
    Path(__file__).parent,
    Path(__file__).parent.parent / 'api' / 'apps', # FIXME: ragflow/api/api/apps, can be remove?
]

client_urls_prefix = [
    register_page(path)
    for dir in pages_dir
    for path in search_pages_path(dir)
]


@login_manager.request_loader
def load_user(web_request):
    jwt = Serializer(secret_key=SECRET_KEY)
    authorization = web_request.headers.get("Authorization")
    if authorization:
        try:
            access_token = str(jwt.loads(authorization))
            user = UserService.query(access_token=access_token, status=StatusEnum.VALID.value)
            if user:
                return user[0]
            else:
                return None
        except Exception as e:
            stat_logger.exception(e)
            return None
    else:
        return None


@app.teardown_request
def _db_close(exc):
    close_connection()