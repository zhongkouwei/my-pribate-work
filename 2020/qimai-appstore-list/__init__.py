# -*- coding: utf-8 -*-

import os
import xlwt
import re
import configparser
import requests

from string import digits
from utils import req, get_date_str, random_sleep, random_sleep_random
from utils import login
from logger import logger
from bs4 import BeautifulSoup

root_dir = os.path.abspath('.')
cf = configparser.ConfigParser()
cf.read(root_dir+"/config.ini")
dates = cf.get("Config", "date")
min = int(cf.get("Config", "min"))
max = int(cf.get("Config", "max"))
useqimai = int(cf.get("Config", "max"))


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


def get_rank(date):
    sess = login()

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
    count = 0

    while page <= maxPage:
        # if page == 2:
        #     sess = login()
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

        for rankInfo in app_list:
            appInfo = rankInfo['appInfo']
            appName = appInfo['appName']
            publisher = appInfo['publisher']

            name = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", "",appName)
            name = name.translate(digits)
            name = name.replace("-","")
            name = name.replace(" ","")
            if not judge_pure_english(name):
                continue
            pub = re.sub("[\s+\.\!\/_,$%^*(+\"\')]+|[+——()?【】“”！，。？、~@#￥%……&*（）]+", "",publisher)
            pub = pub.translate(digits)
            pub = pub.replace("-", "")
            pub = pub.replace(" ", "")
            if not judge_pure_english(pub):
                continue

            app = {
                "名称" : appName,
                "分类": rankInfo['genre'],
                "开发商": publisher,
                "时间": rankInfo['releaseTime'],
                "pageUrl" : "https://apps.apple.com/cn/app/id" + appInfo['appId']
            }
            logger.info("解析出应用【%s】，现在获取禅大师支持网站信息，累计获取%s个", appInfo['appName'], count)
            url = get_chandashi(appInfo['appId'])

            if url == "" and useqimai == 1:
                logger.info("尝试从七麦获取")
                url = get_website(appInfo['appId'])

            if url == "":
                continue

            if "facebook" in url or "google" in url or "twitter" in url :
                continue
            app['网址'] = url
            count = count + 1
            results.append(app)
    return results


def get_chandashi_header():
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "cds_session_id=j501o04nn3h45u5masi40hmdk1; Hm_lvt_0cb325d7c4fd9303b6185c4f6cf36e36=1582284601; Hm_lpvt_0cb325d7c4fd9303b6185c4f6cf36e36=1582286094",
        "Host": "www.chandashi.com",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36"
    }
    return headers


def get_chandashi(id):
    max = 3
    cur = 0
    res = ""
    while cur < max:
        random_sleep_random(min, max)
        res = _get_chandashi(id)
        if not res == None:
            break
        cur = cur + 1

    if res != None and res != "":
        try:
            soup = BeautifulSoup(res, 'html.parser')
            if len(soup.select(".package-info ul li")) > 0:
                for li in soup.select(".package-info ul li"):
                    if len(li.select(".title")) > 0:
                        title = li.select(".title")[0].get_text()
                        if title == "支持网站":
                            if len(li.select(".info")) > 0:
                                url = li.select(".info")[0].get_text()
                                return url.replace("\n", "")
        except Exception:
            logger.info("解析禅大师失败")
            return ""

    else:
        logger.info("解析禅大师失败")
        return ""

    return ""



def _get_chandashi(id):
    url = "https://www.chandashi.com/apps/description/appId/" + id + "/country/cn.html"
    sess = requests.session()
    try:
        resp = sess.get(url, headers=get_chandashi_header())
        if resp.status_code != 200:
            logger.error("获取禅大师失败")
            return None
        return resp.text.replace('\u200b','')
    except Exception:
        logger.error("获取禅大师失败")
        return None


def get_website(id):
    path = '/app/baseinfo'
    method = 'GET'

    params = {
        "appid": id,
        "country": "cn"
    }
    random_sleep_random(min, max)

    res, sess = req(path, params=params, method=method, req_type='', product_name='',
                    market_name='', headers=get_header(date))
    if not res or not res['appInfo']:
        logger.error("解析失败")
        return ""
    appInfo = res['appInfo']
    for key in appInfo:
        if key['name'] == "开发者网站":
            return key['value']
    for key in appInfo:
        if key['name'] == "支持网站":
            return key['value']
    logger.warning("无法解析出支持网站信息")
    return ""


def judge_pure_english(keyword):
    return all(ord(c) < 128 for c in keyword)


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


def save(data, path, date):
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

    f.save('%s/%s.xls' % (str(path), str(date)))


if __name__ == '__main__':
    cur_path = os.path.abspath(os.path.dirname(__file__))
    res_path = '%s/excel/%s' % (cur_path, get_date_str())
    logger.info("结果文件在：%s", res_path)
    if not os.path.isdir(res_path):
        os.mkdir(res_path)

    dateList = dates.split(",")
    if not dateList:
        print("日期配置错误，请重新配置，多个时间中间用英文逗号,分隔")
    else:
        for date in dateList:
            results = get_rank(date)
            save(results, res_path, date)

