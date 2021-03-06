from serialization import serialize
from flask import Flask, request, make_response, send_file
from flask import Response
from flask_restful import Resource
from APIError import APIError
from rate_limiting import shared_limiter
from security import md5hash
import sys
sys.path.append('../')
from app import app
from utils.Log import Log
from caching import make_key

# import the flask extension
from flask.ext.cache import Cache


class ResourceBase(Resource):

    # Rate limiting setup --------------------

    if app.config['RATE_LIMITING_ACTIVE']:
        Log.info('Rate limiting active : %s' %
                 (app.config['GLOBAL_RATE_LIMITS']))
        decorators = [shared_limiter]
    else:
        Log.info('Rate limiting is turned off')

    # Caching setup --------------------
    if app.config['CACHING_ACTIVE']:
        Log.info('Caching is active')
    else:
        app.config['CACHE_TYPE'] = 'null'
        Log.info('Caching is disabled')
        app.config['CACHE_NO_NULL_WARNING'] = True

    # register the cache instance and binds it on to your app
    app.cache = Cache(app)
    app.cache.clear()

    def __init__(self):

        self.to_hal = None

    def render(self, data, headers={}, status_code=200, raw=False):

        if not self.resolve_content():
            data = {'message': 'invalid format',
                    'code': 55}
            status_code = 405

        if self.content_type == 'xml':
            if raw:
                data = data
            else:
                data = serialize(data, 'xml')
            response = Response(
                data, content_type='application/xml; charset=utf-8')

        elif self.content_type == 'csv':
            if raw:
                data = data
            else:
                data = serialize(data, 'csv')

            resource_path = request.path.split("/")

            if resource_path[len(resource_path) - 1] != "":
                resource_type = resource_path[len(resource_path) - 1]

            else:
                resource_type = resource_path[len(resource_path) - 2]

            args_hash = md5hash(format_args(request.args))

            headers["Content-Disposition"] = "attachment; filename=salicapi-%s-%s.csv" % (
                resource_type, args_hash)

            response = Response(data, content_type='text/csv; charset=utf-8')

        # JSON or invalid Content-Type
        else:
            if raw:
                data = data
            else:
                if self.to_hal is not None and status_code == 200:
                    if 'X-Total-Count' in headers:
                        args = {'total': headers['X-Total-Count']}
                    else:
                        args = {}

                    data = self.to_hal(data, args=args)

                data = serialize(data, 'json')

            response = Response(
                data, content_type='application/hal+json; charset=utf-8')

        access_control_headers = "Content-Length, Content-Type, "
        access_control_headers += "Date, Server, "
        access_control_headers += "X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After, "
        access_control_headers += "X-Total-Count, "
        access_control_headers += "Content-Disposition"

        headers['Access-Control-Expose-Headers'] = access_control_headers

        response.headers.extend(headers)
        response.status_code = status_code
        real_ip = request.headers.get('X-Real-Ip')

        if real_ip == None:
            real_ip = ''

        Log.info(request.path + ' ' + real_ip + ' ' + str(status_code) +
                 ' ' + str(response.headers.get('Content-Length')))

        return response

        # Given a cgc/cpf/cnpj, makes sure it return only elements with exact match
    # Used to correct the use of SQL LIKE statement
    def get_unique(self, cgccpf, elements):

        exact_matches = []

        for e in elements:

            if e['cgccpf'] == cgccpf:
                exact_matches.append(e)

        return exact_matches

    def get_last_offset(self, n_records, limit):

        if n_records % limit == 0:
            return (n_records / limit - 1) * limit

        else:
            return n_records - (n_records % limit)

    def resolve_content(self):
        # Content Type resolution
        if request.args.get('format') is not None:

            format = request.args.get('format')

            if format == 'json':
                self.content_type = 'json'
                return True

            elif format == 'xml':
                self.content_type = 'xml'
                return True

            elif format == 'csv':
                self.content_type = 'csv'
                return True

            else:
                self.content_type = 'json'
                return False

        else:
            if request.headers['Accept'] == 'application/xml':
                self.content_type = 'xml'
                return True

            elif request.headers['Accept'] == 'text/csv':
                self.content_type = 'csv'
                return True

            else:
                self.content_type = 'json'
                return True


def format_args(hearder_args):
    formated = ''

    for key in hearder_args:
        formated = formated + str(key) + '=' + hearder_args[key] + '&'

    return formated


@app.before_request
def request_start():
    content_type = request.headers.get('Accept') or ''
    real_ip = request.headers.get('X-Real-Ip') or ''

    Log.info(request.path + ' ' + format_args(request.args)
             + ' ' + real_ip
             + ' ' + content_type)

    # Test content_type

    # if content_type and content_type not in  AVAILABLE_CONTENT_TYPES:
    #     results = {'message' : 'Content-Type not supported',
    #                 'message_code' : 8
    #             }
    #     return {'error' : 'content-type'}
    #     return self.render(results, status_code = 405)
