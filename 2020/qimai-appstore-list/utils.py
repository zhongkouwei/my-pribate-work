# -*- coding: utf-8 -*-

import time
import os
import json
import base64
import requests
from requests.exceptions import *
import random
import datetime
import configparser

from logger import logger
from settings import *

root_dir = os.path.abspath('.')
cf = configparser.ConfigParser()
cf.read(root_dir+"/config.ini")
username = cf.get("User", "username")
password = cf.get("User", "password")

data = {
    'username': username,
    'password': password,
    # 'code': captcha,  # 验证码
}


def XOR_secret(v):
    new_v_list = []
    for i, item in enumerate(v):
        j = ord(item) ^ ord(secret[(i + 10) % len(secret)])
        new_v_list.append(chr(j))
    return ''.join(new_v_list)


def encrypt(params, path):
    # 提取查询参数值并排序
    # s = ''.join(str(i[1]) for i in sorted(params.items(), lambda x, y: cmp(x[0], y[0])))
    s = "".join(sorted([str(v) for v in params.values()]))

    # Base64 Encode
    s = str(base64.b64encode(s.encode("utf-8")), "utf-8")

    # 时间差
    t = str(int((time.time() * 1000 - start_timestamp)))

    v = '@#'.join([s, path, t, "1"])
    v = XOR_secret(v)

    # 自定义加密 & Base64 Encode
    v = str(base64.b64encode(v.encode("utf-8")), "utf-8")

    return v


def _req(path, params=None, data=None, method='GET', sess=None, req_type="", product_name="", market_name="", headers=""):
    method = method.upper()
    if method not in ['GET', 'POST']:
        logger.info('%s，请求的方法不被支持，%s_%s，path：%s，method：%s' % (req_type, product_name, market_name, path, method))
        return None, sess

    if not params:
        params = {}
    v = encrypt(params, path)
    # 拼接 URL
    params["analysis"] = v

    if not sess:
        sess = requests.session()
    # 发起请求

    try:
        if method == 'GET':
            resp = sess.get(base_url + path, params=params, headers=headers)
        else:
            if not data:
                logger.info(
                    '%s，请求的没有post body，%s_%s，path：%s，method：%s' % (req_type, product_name, market_name, path, method))
                return None, sess
            resp = sess.post(base_url + path, params=params, headers=headers, data=data)
    except RequestException:
        logger.info(
            '%s，请求失败，%s_%s，path：%s，method：%s，error' % (req_type, product_name, market_name, path, method))
        return None, sess

    if resp.status_code != 200:
        logger.info('%s，请求失败，%s_%s，status_code：%s，path：%s，method：%s' % (
            req_type, product_name, market_name, resp.status_code, path, method))
        return None, sess

    res = json.loads(resp.text)
    code = res.get('code', 0)
    if code != 10000:
        logger.info(
            '%s，请求出错，%s_%s，status_code：%s，res：%s, path：%s，method：%s' % (
                req_type, product_name, market_name, resp.text, resp.status_code, path, method))
        return None, sess

    logger.info('%s，请求成功，%s_%s，status_code：%s，path：%s，method：%s' % (
        req_type, product_name, market_name, resp.status_code, path, method))
    return res, sess


def req(path, params=None, data=None, method='GET', sess=None, req_type="", product_name="", market_name="", headers=""):
    retry = 3
    res = {}
    while retry:
        res, sess = _req(path, params, data, method, sess, req_type, product_name, market_name, headers)
        if res:
            return res, sess
        else:
            retry -= 1
            random_sleep()
    return res, sess


def login():
    sess = requests.session()
    path = '/account/signinForm'
    random_sleep()
    res, sess = req(path, data=data, method="POST", sess=sess, product_name='login', market_name='iOS', req_type='iOS_login')
    logger.info('登录的结果：%s', res)
    return sess


def random_sleep():
    delay = random.uniform(4, 6)
    delay = round(delay, 2)
    logger.info('随机延时%s秒...' % delay)
    time.sleep(delay)


def random_sleep_random(min, max):
    delay = random.uniform(min, max)
    delay = round(delay, 2)
    logger.info('随机延时%s秒...' % delay)
    time.sleep(delay)


def get_date_str():
    return datetime.datetime.strftime(datetime.datetime.today(), '%Y-%m-%d')
