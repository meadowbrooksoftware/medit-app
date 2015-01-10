__author__ = 'luke'

from flask import Flask, request
import json
import uuid
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.dynamodb2.table import Table, Item
import os
from datetime import datetime
import calendar
import time
import logging
from logging import handlers

INI_FILE_ENV_VAR = 'MEDIT_INI_PATH'
DFLT_INI_FILE = 'meditsvc.ini'

app = Flask(__name__)

# load config

ini_file = os.environ.get(INI_FILE_ENV_VAR)
if not ini_file:
    os.environ[INI_FILE_ENV_VAR] = DFLT_INI_FILE
app.config.from_envvar(INI_FILE_ENV_VAR)

# create log

logfile = app.config['LOG_FILENAME']
if app.config['CREATE_LOG']:
    if not os.path.exists(os.path.dirname(logfile)):
        os.makedirs(os.path.dirname(logfile))
app.logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    logfile, maxBytes=20, backupCount=5)
app.logger.addHandler(handler)

# define endpoints

@app.route('/up')
def up():
    return '{"status": "up"}'


@app.route('/medit', methods=['POST'], defaults={'post_uuid': None})
@app.route('/medit/<post_uuid>', methods=['GET'])
def medit(post_uuid):
    if request.method == 'GET':
        return get(post_uuid)
    elif request.method == 'POST':
        probs = validate(request.json)
        if probs:
            return "{\"probs\": [%s]}" % ', '.join('"{0}"'.format(p) for p in probs)
        else:
            return post(uuid.uuid4(), request.json)


@app.route('/medits', methods=['GET'])
def medits():
    begin = int(request.args.get('beginat', '0'))
    end = int(request.args.get('endat', '0'))
    detail = request.args.get('detail', 'false').lower() == 'true'
    return "%s%s%s" % ("[", ",".join(query_at_range(begin, end, detail)), "]")


def get(post_uuid):
    if post_uuid is None or len(post_uuid) == 0:
        return '{}'
    else:
        app.logger.info('getting:%s|%s|%s' % (app.config['BUCKET_NAME'], app.config['S3_BASE_PATH'], post_uuid))
        return get_from_s3(post_uuid)


def get_from_s3(post_uuid):
    conn = S3Connection()
    bucket = conn.get_bucket(app.config['BUCKET_NAME'])
    k = Key(bucket)
    k.key = "%s/%s" % (app.config['S3_BASE_PATH'], post_uuid)
    return k.get_contents_as_string()


def post(post_uuid, medit_post):
    app.logger.info('posting:%s|%s|%s' % (app.config['BUCKET_NAME'], app.config['S3_BASE_PATH'], post_uuid))
    enhance(post_uuid, medit_post)
    rslt = write_metadata(medit_post)
    if rslt:
        app.logger.info("stored metadata %s to %s" % (post_uuid, app.config['DYNAMO_MEDIT_TABLE']))
        s3key = write_data(medit_post)
        app.logger.info("posted:%s" % s3key)
        return terse(medit_post)
    else:
        return "{'id':%s, 'probs':'dynamo'}" % post_uuid


def validate(medit_post):
    probs = [] # of strings
    if not medit_post['body']:
        probs.append('bodyless!')
    elif len(medit_post['body']) > app.config['MAX_BODY']:
        probs.append('big body')
    if 'head' in medit_post and len(medit_post['head']) > app.config['MAX_HEAD']:
        probs.append('big head')
    if 'by' in medit_post and len(medit_post['by']) > app.config['MAX_BY']:
        probs.append('big by')
    if 'type' in medit_post and len(medit_post['type']) > app.config['MAX_TYPE']:
        probs.append('big type')
    if len(json.dumps(medit_post)) > app.config['MAX_POST']:
        probs.append('big post')
    return probs


def enhance(post_uuid, medit_post):
    now = datetime.utcnow()
    at = calendar.timegm(time.gmtime())
    medit_post['at'] = at
    medit_post['date'] = now.strftime(app.config['DATE_FORMAT'])
    medit_post['id'] = str(post_uuid)
    medit_post['ctxt'] = str(app.config['CTXT'])


def write_metadata(medit_post):
    return Item(Table(app.config['DYNAMO_MEDIT_TABLE']), data=medit_post).save()


def write_data(medit_post):
    if not medit_post['id']:
        app.logger.error('must set id attribute before writing data')
    k = Key(S3Connection().get_bucket(app.config['BUCKET_NAME']))
    k.key = "%s/%s" % (app.config['S3_BASE_PATH'], medit_post['id'])
    k.set_contents_from_string(json.dumps(medit_post))
    return k.key


def terse(medit_post):
    return "{\"id\": \"%s\",\"at\": %d}" % (medit_post['id'], medit_post['at'])


def query_at_range(bgn_epoch, end_epoch, detail):
    data = [] # of json strings
    if bgn_epoch is not None and end_epoch is not None:
        app.logger.info("query by epoch: %d %d" % (bgn_epoch, end_epoch))
        dynamo_post = Table(app.config['DYNAMO_MEDIT_TABLE'])
        rslts = dynamo_post.query_2(
            index='ctxt-at-index', ctxt__eq=str(app.config['CTXT']), at__between=[int(bgn_epoch), int(end_epoch)])
        for rslt in rslts:
            app.logger.info("found: %s %s" % (rslt['id'], rslt['at']))
            if detail:
                app.logger.info("getting detail for %s" % rslt['id'])
                data.append(get_from_s3(rslt['id']))
            else:
                app.logger.info("getting metadata for %s" % rslt['id'])
                data.append("{\"id\": \"%s\", \"at\": %d}" % (rslt['id'], rslt['at']))
    return data


if __name__ == '__main__':
    app.run()

