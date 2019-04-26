# coding: utf-8
import gevent.monkey

gevent.monkey.patch_all()
import sys
import logging
import logging.config

from flask import (
    Flask,
    got_request_exception,
    request_started,
    request_finished,
)
from hendrix.conf import setting
import mongoengine.errors
from werkzeug.wsgi import peek_path_info

from . import log
from .request import LitatomRequest
from .response import LitatomResponse, failure
from .signal import (
    before_first_request_handler,
    before_request_handler,
    got_request_exception_handler,
    request_started_handler,
    request_finished_handler,
    teardown_request_handler,
)
file_name = '/rdata/litatom' if not setting.IS_DEV else '/rdata/devlitatom'
logger = logging.getLogger(__name__)
#logger.setLevel(logging.INFO)
#loghanlder = logging.FileHandler(file_name, encoding='utf-8')
#loghanlder = logging.handlers.RotatingFileHandler(file_name, maxBytes=10240, backupCount=10)
#logger.addHandler(loghanlder)

class LitatomApp(Flask):
    request_class = LitatomRequest
    response_class = LitatomResponse

    def log_exception(self, exc_info):
        log.log_api_call(self.logger, exc_info[1], 500)


class LitatomAppFactory(object):
    app_name = __package__
    app_cls = LitatomApp

    _logging_setup = False

    @classmethod
    def setup_blueprints(cls, app, route_gen):
        route_gen(app)

    @classmethod
    def setup_error_handlers(cls, app):
        def register(err_or_code, resp_func):
            def handler(err):
                app.logger.info('error processing request: %s', err)
                return resp_func(err)

            app.register_error_handler(err_or_code, handler)

        register(404, lambda _: ('', 404))
        from .circuit_breaker import CircuitBreakerError
        register(CircuitBreakerError, lambda _: ('', 503))
        register(mongoengine.errors.ValidationError, lambda _: failure())

    @classmethod
    def setup_signals(cls, app):
        app.before_first_request(before_first_request_handler)
        request_started.connect(request_started_handler, app)
        app.before_request(before_request_handler)
        got_request_exception.connect(got_request_exception_handler, app)
        request_finished.connect(request_finished_handler, app)
        app.teardown_request(teardown_request_handler)

    @classmethod
    def setup_logging(cls, app):
        name = app.name
        if not cls._logging_setup:
            conf = log.gen_app_log_config(name, app.debug)
            logging.config.dictConfig(conf)
            logging.captureWarnings(True)
            cls._logging_setup = True
        app.logger_name = name
        app._logger = logging.getLogger(name)
        #print app._logger, dir(app._logger), app._logger.handlers
        #app._logger = logging.FileHandler("/rdata/litlog")
        # app._logger.addHandler(handler)

    @classmethod
    def create_app(cls,
                   app_cls=None,
                   logging=True,
                   signals=True,
                   route_gen=None,
                   errhandlers=True):
        app_cls = app_cls or cls.app_cls
        app = app_cls(cls.app_name)
        app.config.from_object(setting)
        if logging:
            cls.setup_logging(app)
        if signals:
            cls.setup_signals(app)
        if route_gen:
            cls.setup_blueprints(app, route_gen)
        if errhandlers:
            cls.setup_error_handlers(app)
        return app


def default_api_blueprints(app):
    from . import api

    app.register_blueprint(api.v1.blueprint, url_prefix='/api/sns/v1')
    app.register_blueprint(api.v2.blueprint, url_prefix='/api/sns/v2')


def web_api_blueprints(app):
    from . import web_api

    app.register_blueprint(web_api.v1.blueprint, url_prefix='/web_api/sns/v1')


def _all_api_blueprints(app):
    default_api_blueprints(app)
    web_api_blueprints(app)


def create_app_by_prefix(prefix):
    if prefix == 'web_api':
        return LitatomAppFactory.create_app(route_gen=web_api_blueprints)
    elif prefix == 'api':
        return LitatomAppFactory.create_app(route_gen=default_api_blueprints)


class PathDispatchMiddleware(object):
    def __init__(self, default_app, create_app):
        self.default_app = default_app
        self.create_app = create_app
        self.package_name = __package__
        self._health_app = None
        self._app_instances = {}

    def _make_health_app(self):
        health_app = LitatomAppFactory.create_app(signals=False, errhandlers=False)

        def health():
            return 'ok', 200

        health_app.add_url_rule('/health', 'health', health)
        return health_app

    def get_app(self, environ):
        prefix = peek_path_info(environ)
        if prefix == 'health':
            if not self._health_app:
                self._health_app = self._make_health_app()
            return self._health_app
        elif prefix not in self._app_instances:
            app = self.create_app(prefix)
            if not app:
                return self.default_app
            self._app_instances[prefix] = app
        return self._app_instances[prefix]

    def __call__(self, environ, start_response):
        try:
            logger.error('hello')
            app = self.get_app(environ)
            return app(environ, start_response)
        except Exception as e:
            #logger.error(traceback.print_exc())
            import traceback
            res = traceback.format_exc()
            print type(res)
            print dir(logger), logger.handlers
            logger.debug(res)
            logger.error(str(e), exc_info=True)



application = PathDispatchMiddleware(None, create_app_by_prefix)
