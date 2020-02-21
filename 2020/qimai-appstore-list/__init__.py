# -*- coding: utf-8 -*-

import os
import xlwt
import re
import configparser

from utils import req, get_date_str, random_sleep, random_sleep_random
from utils import login
from logger import logger

cf = configparser.ConfigParser()
cf.read("config.ini")
date = cf.get("Config", "date")


def get_header(date):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.qimai.cn",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
        "Referer": "https://www.qimai.cn/rank/release/genre/36/country/cn/date/"+date,
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6",
    }
    return headers

def get_rank():
    sess = ""

    """
    安卓关键词量
    https://api.qimai.cn/rank/release?analysis=dQ51TyxzAEd9WQBIdyB6Cj0GAlxwEx9CUV5bFxZSVAFVRQRwEwYGCQUGCVQCDVcEdkIB&genre=36&country=cn&date=2020-02-18
    :return:
    """
    date_str = get_date_str()
    path = '/rank/release'
    method = 'GET'

    if not date or date == "":
        logger.error("配置错误，请配置日期")

    maxPage = 1
    page = 1
    results = []

    while page <= maxPage:
        if page == 2:
            sess = login()
        params = {
            "genre": 36,
            "country": "cn",
            "date": date,
            "page":page
        }
        logger.info("抓取%s排行数据第%s页", date, page)
        random_sleep()
        res, sess = req(path, params=params, method=method, sess = sess, req_type='', product_name='',
                        market_name='', headers=get_header(date))
        if not res :
            logger.error("获取失败，请重启程序")
            break

        app_list = res['rankInfo']
        maxPage = int(res['maxPage'])
        page  = page + 1
        count = 0
        for rankInfo in app_list:
            appInfo = rankInfo['appInfo']
            appName = appInfo['appName']

            zhmodel = re.compile(u'[\u4e00-\u9fa5]')
            match = zhmodel.search(appName)
            if match:
                continue
            app = {
                "名称" : appName,
                "分类": rankInfo['genre'],
                "开发商": appInfo['publisher'],
                "时间": rankInfo['releaseTime'],
                "pageUrl" : "https://apps.apple.com/cn/app/id" + appInfo['appId']
            }
            count = count + 1
            logger.info("解析出应用【%s】，现在获取支持网站信息，累计获取%s个", appInfo['appName'], count)
            url = get_website(appInfo['appId'])

            if "facebook" in url or "google" in url or "twitter" in url :
                continue
            app['网址'] = url

            results.append(app)
    return results


def get_website(id):
    path = '/app/baseinfo'
    method = 'GET'

    params = {
        "appid": id,
        "country": "cn"
    }
    random_sleep_random(1, 2)

    res, sess = req(path, params=params, method=method, req_type='', product_name='',
                    market_name='', headers=get_header(date))
    if not res or not res['appInfo']:
        logger.error("解析失败")
        return ""
    appInfo = res['appInfo']
    for key in appInfo:
        if key['name'] == "支持网站" or key['name'] == "开发者网站":
            return key['value']
    logger.warning("无法解析出支持网站信息")
    return ""


# 设置表格样式
def set_style(name, height, bold=False):
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


default = set_style('Times New Roman', 220, True)


def save(data, path):
    f = xlwt.Workbook()
    sheet1 = f.add_sheet('sheet1', cell_overwrite_ok=True)

    row_count = 0
    for line in data:
        if row_count == 0:
            keys = line.keys()
            for i in range(0, len(keys)):
                sheet1.write(row_count, i, str(list(keys)[i]), default)
        row_count += 1
        for i, key in enumerate(keys):
            sheet1.write(row_count, i, str(line.get(key, '')), default)

    f.save('%s\%s.xls' % (str(path), str(date)))


if __name__ == '__main__':
    cur_path = os.path.abspath(os.path.dirname(__file__))
    res_path = '%s\excel\%s' % (cur_path, get_date_str())
    logger.info("结果文件在：%s", res_path)
    if not os.path.isdir(res_path):
        os.mkdir(res_path)

    results = get_rank()
    save(results, res_path)

