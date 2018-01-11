# -*- coding:utf-8 -*-

import logging
from . import api
from ihome import models


@api.route('/')
def hello_world():
    logging.debug('debug')
    logging.info('info')
    logging.warn('warn')
    logging.error('error')
    return 'Hello World!'
