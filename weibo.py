# -*- coding: UTF-8 -*-
from __future__ import print_function
import requests
from lxml import etree
import re
import utils
from selenium import webdriver
from bs4 import BeautifulSoup
import datetime
import os
import json
import sys


"""

Followers details:
This requires more information in cookie to access: _T_WM
I think using selenium with simulated web browser behavior it is achievable, but
1. I don't fully understand the package
2. not very familiar with xtree path (bs4 is better)
Leave it until I know what happened

url = "https://weibo.cn/1776448504/fans?page=19&display=0&retcode=6102"
r = requests.get(url, cookies={"Cookie": "_T_WM=ec1a4454c0d9d6d28bb947142ca09f4f; SUB=_2A253gE9VDeThGeVM6FQZ9yvOyD6IHXVUi1EdrDV6PUJbkdBeLUbdkW1NTKWBvjMxvfXWbMrYJ01hTA-fdYsQshDp; SUHB=0OM0IZCuuDil4y; SCF=Aj52M7AisY2zemY_Am0nKcL71Og-kwj4KrbW9HkL8O51TjMxprJ7l2Sryhd6P9gtzV7sn1wG4n0t3QM9ZNxcc0w.; SSOLoginState=1518616325"}, headers=headers)

"""

# in case old cookie method fails
def get_cookie_with_selenium(username, password):
    chromePath = "/usr/local/bin/chromedriver"
    wd = webdriver.Chrome(executable_path=chromePath)
    loginUrl = 'http://www.weibo.com/login.php'
    wd.get(loginUrl)
    wd.find_element_by_xpath('//*[@id="loginname"]').send_keys(username)
    wd.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys(password)
    wd.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()

    req = requests.Session()
    cookies = wd.get_cookies()
    print(cookies)
    for cookie in cookies:
        req.cookies.set(cookie["name"], cookie["value"])
    url = "http://chart.weibo.com/chart?rank_type=6&version=v1"
    r = req.get(url)
    print(r.content)


class Cookie(object):

    def __init__(self):
        self.cookie_parts = {}

    def set(self, key, value):
        self.cookie_parts[key] = value

    def get_cookie(self):
        cookies = []
        for key, value in self.cookie_parts.items():
            cookies.append("%s=%s" % (key, value))
        return " ".join(cookies)


# 获取微博登录的cookie，分三步。第一步登录，获取SUB, SUHB, SCF和SSOLogin
# 然后读取https://m.weibo.cn，获取M_WEIBOCN_PARAMS和_T_WM
# 最后登录独立超话，获取WEIBOCN_FROM并更新M_WEIBOCN_PARAMS
def get_cookie(username, password):

    cookie = Cookie()

    payload = {"username": username,
               "password": password,
               "savestate": "1",
               "ec": "0",
               "entry": "mweibo",
               "mainpageflag": "1"}
    headers = {"Accept-Encoding": "gzip, deflate, br",
               "Connection": "keep-alive",
               "Content-Length": "162",
               "Content-Type": "application/x-www-form-urlencoded",
               "Host": "passport.weibo.cn",
               "Origin": "https://passport.weibo.cn",
               "Referer": "https://passport.weibo.cn/signin/login",
               "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"}
    url = "https://passport.weibo.cn/sso/login"
    response = requests.post(url, data=payload, headers=headers)
    
    for info in response.headers["Set-Cookie"].split():
        if info.startswith("SUB=") or info.startswith("SUHB=") or info.startswith("SCF=") or info.startswith("SSOLoginState="):
            key, value = info.split("=")
            cookie.set(key, value)

    '''
    curl 'https://m.weibo.cn/' 
    -H 'authority: m.weibo.cn' 
    -H 'upgrade-insecure-requests: 1' 
    -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36' 
    -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8' 
    -H 'referer: https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F' 
    -H 'accept-encoding: gzip, deflate, br' 
    -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7' 
    -H 'cookie: SUB=_2A252GUo0DeThGeVM6FQZ9yvOyD6IHXVV4lZ8rDV6PUJbkdBeLRbikW1NTKWBvlMd6utP8-GniJG48Z69mYN_MLcM; SUHB=0QSp1-7WD51Jix; SCF=Aj52M7AisY2zemY_Am0nKcL71Og-kwj4KrbW9HkL8O511BUUv7LFPRgmmi6VLFtweCnnDEZFxb6DXYNUEBPSkx8.; SSOLoginState=1528642148' 
    --compressed
    '''
    headers = {
        "authority": "m.weibo.cn",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "referer": "https://passport.weibo.cn/signin/login?entry=mweibo&res=wel&wm=3349&r=https%3A%2F%2Fm.weibo.cn%2F",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "cookie": cookie.get_cookie()
    }
    url = "https://m.weibo.cn"
    response = requests.get(url, headers=headers)
    for info in response.headers["Set-Cookie"].split():
        if info.startswith("M_WEIBOCN_PARAMS") or info.startswith("_T_WM"):
            key, value = info.split("=")
            cookie.set(key, value)
    cookie.set("MLOGIN", "1;")
    
    # 随意选择了一个超话尝试了一下
    page_id = "100808066f8f58c6a0520a79d77ce704ab5ae6"
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://m.weibo.cn/p/%s" % page_id,
        "authority": "m.weibo.cn",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie.get_cookie()
    }

    url = "https://m.weibo.cn/p/%s" % page_id
    response = requests.get(url, headers=headers)
    for info in response.headers["Set-Cookie"].split():
        if info.startswith("M_WEIBOCN_PARAMS") or info.startswith("WEIBOCN_FROM"):
            key, value = info.split("=")
            cookie.set(key, value)

    return cookie


'''
curl -H 'Host: chart.weibo.com'
    -H 'Cache-Control: max-age=0'
    -H 'Upgrade-Insecure-Requests: 1'
    -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36'
    -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
    -H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7'
    -H 'Cookie: login_sid_t=b689be1da75c3e30c88ca9aa4371b135; cross_origin_proto=SSL; _s_tentry=passport.weibo.com; Apache=4200097554956.783.1518665647383; SINAGLOBAL=4200097554956.783.1518665647383; ULV=1518665647389:1:1:1:4200097554956.783.1518665647383:; STAR-G0=13a69f4f7468fb922d999343597548de; UOR=,,login.sina.com.cn; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFTdxv_d-bjYALZqEF93-os5JpX5K2hUgL.FoeEe0qRS0-Ee0z2dJLoI0YLxKnL1K5L1-BLxKnL12-L1h.LxKqL12-LBKMLxK-LBKBLBKMLxK-L12qL1KBLxKBLBonL1hMLxK-LBozL1h2t; ALF=1559528706; SSOLoginState=1527992707; SCF=Aj52M7AisY2zemY_Am0nKcL71Og-kwj4KrbW9HkL8O517oKZRofb_QPG4qYxYhsm5zKyLCJT01QWh3E-pVX5Rz8.; SUB=_2A252FyHUDeThGeVM6FQZ9yvOyD6IHXVVZRQcrDV8PUNbmtBeLWHSkW9NTKWBvn9UvVUe676zdYzFcUZrOaamNoGE; SUHB=02M_U7vB7LcaoU; wvr=6; rank_type=6; WBStorage=5548c0baa42e6f3d|undefined'
    --compressed 'http://chart.weibo.com/chart?rank_type=6'
'''

# This method is used to caluclate the post on chart.weibo.com and recording their four features.
def get_chart(cookie):

    headers = {
        "Host": "chart.weibo.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "Cookie": cookie.get_cookie()
    }

    for rank in [3, 5, 6]:
        for page in [1, 2]:
            url = "http://chart.weibo.com/chart?rank_type=%s&page=%s" % (rank, page)
            response = requests.get(url, headers=headers)

            soup = BeautifulSoup(response.content, "lxml")
            name_divs = soup.find_all("div", class_=re.compile("sr_name S_func1"))
            read_num_divs = soup.find_all("li", class_=re.compile("arr1 clearfix"))
            interaction_num_divs = soup.find_all("li", class_=re.compile("arr2 clearfix"))
            affection_num_divs = soup.find_all("li", class_=re.compile("arr3 clearfix"))
            loveness_num_divs = soup.find_all("li", class_=re.compile("arr4 clearfix"))
            for name_div, read_div, inter_div, affect_div, loveness_div in zip(name_divs, read_num_divs, interaction_num_divs, affection_num_divs, loveness_num_divs):
                name = name_div.text.encode("utf-8")
                read_num = read_div.find_all("span", class_="pro_num")[0].text
                interaction_num = inter_div.find_all("span", class_="pro_num")[0].text
                affection_num = affect_div.find_all("span", class_="pro_num")[0].text
                loveness_num = loveness_div.find_all("span", class_="pro_num")[0].text
                print(name, read_num, interaction_num, affection_num, loveness_num)

    # get_followers(cookie, "caixukun")

# 从微博页面获取单条微博的评论，赞，转发数量和上头条价格
def get_post_data(cookie, username):
    
    url = "https://weibo.cn/%s" % username
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "lxml")
    for div in soup.find_all("div", class_="c"):
        if div.get("id") is None:
            continue

        div_id = div.get("id")
        assert div_id.startswith("M_")
        mid = url_to_mid(div_id[2:])
        url = "https://pay.biz.weibo.com/aj/getprice/advance?mid=%s&touid=%s" % (mid, username)
        headers = {
            "Host": "pay.biz.weibo.com",
            "Accept-Encoding": "gzip, deflate, br",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
            "Cookie": cookie.get_cookie()
        }
        data = requests.get(url, headers=headers)
        data = json.loads(data.content)

        for a in div.find_all("a"):
            if a.text.encode("utf-8").startswith("评论"):
                print(username, div_id, mid, "".join(re.findall("[(\d+)]", a.text.encode("utf-8"))))
            if a.text.encode("utf-8").startswith("赞"):
                print(username, div_id, mid, "".join(re.findall("[(\d+)]", a.text.encode("utf-8"))))
            if a.text.encode("utf-8").startswith("转发"):
                print(username, div_id, mid, "".join(re.findall("[(\d+)]", a.text.encode("utf-8"))))
        print(username, div_id, mid, data["data"]["price"])

# 为了获取某条评论的评论，赞，转发数量，需要计算出一个这条微博的mid值
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
def base62_encode(num, alphabet=ALPHABET):

    """Encode a number in Base X
    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)

def base62_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num

def url_to_mid(url):

    url = str(url)[::-1]
    size = len(url) / 4 if len(url) % 4 == 0 else len(url) / 4 + 1
    result = []
    for i in range(size):
        s = url[i * 4: (i + 1) * 4][::-1]
        s = str(base62_decode(str(s)))
        s_len = len(s)
        if i < size - 1 and s_len < 7:
            s = (7 - s_len) * '0' + s
        result.append(s)
    result.reverse()
    return int(''.join(result))


def get_followers(cookie, name):

    def retrive_followers_content(cookie, username):
        url = "https://weibo.cn/%s?display=0&retcode=6102" % username
        response = requests.get(url, "html", cookies=cookie)
        return response

    def extract_follower_from_content(content):
        selector = etree.HTML(content)
        str_gz = selector.xpath("//div[@class='tip2']/a/text()")[1]
        pattern = r"\d+\.?\d*"
        guid = re.findall(pattern, str_gz, re.M)
        followers = int(guid[0])
        return followers

    username = "caizicaixukun"
    response = retrive_followers_content(cookie, username)
    if response is None:
        return None
    start_time = response.start_time.strftime("%Y%m%d,%H:%M:%S.%f")
    finish_time = response.finish_time.strftime("%Y%m%d,%H:%M:%S.%f")
    followers = extract_follower_from_content(response.get_html())
    return start_time, finish_time, name, username, followers


def get_all_followers(cookie):
    def print_follower_count_header(f):
        raise

    date = datetime.date.today().strftime("%Y%m%d")
    filename = "%s_follower_counts.csv" % date

    usernames = []
    with open("weibo_ids.csv") as f:
        for line in f.readlines():
            segs = line.strip().split(",")
            name = segs[0].decode("GB2312").encode("utf-8")
            username = segs[2]
            if username == "id":
                continue
            usernames.append((name, username))

    is_file = os.path.isfile(filename)
    with open(filename, "a") as f:
        if not is_file:
            print_follower_count_header(f)
        # username = "caizicaixukun"
        for name, username in usernames:
            utils.log_print("[** LOG **] Get followers %s" % name)
            res = get_followers(cookie, name, username)
            if res is None:
                utils.log_print("[** ERROR LOG **] Failed getting followers %s" % name)
                date = datetime.date.today().strftime("%Y%m%d")
                time = datetime.datetime.now().strftime("%Y%m%d,%H:%M:%S.%f")
                with open(".%s_error.log" % date, "a") as f_err:
                    print("Failed", time, name, username, file=f_err)
            else:
                utils.log_print("[** LOG **] Succeed getting followers %s" % name)
                start_time, finish_time, name, username, followers = res
                print(start_time, finish_time, name, username, followers)
    return filename


'''
curl 'https://m.weibo.cn/api/container/getIndex?containerid=1008084df10e1237b5578013705ae934cc0b5a' 
-H 'cookie: _T_WM=2347d44799bd017a7c42d4b0778e9eff; WEIBOCN_FROM=1110006030; ALF=1530701067; SCF=Aj52M7AisY2zemY_Am0nKcL71Og-kwj4KrbW9HkL8O519CB_gPvclMRjWoBZ1JpYr7_h4F81dOxbdG6-pz2FcR0.; SUB=_2A252EWkXDeThGeVM6FQZ9yvOyD6IHXVV-ndfrDV6PUJbktBeLWjckW1NTKWBvpSLDufBiIX08-g5g_RhTpQRWURW; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFTdxv_d-bjYALZqEF93-os5JpX5K-hUgL.FoeEe0qRS0-Ee0z2dJLoI0YLxKnL1K5L1-BLxKnL12-L1h.LxKqL12-LBKMLxK-LBKBLBKMLxK-L12qL1KBLxKBLBonL1hMLxK-LBozL1h2t; SUHB=0sqROPqomMAY9G; SSOLoginState=1528109383; MLOGIN=1; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D1008084df10e1237b5578013705ae934cc0b5a_-_main%26fid%3D1008084df10e1237b5578013705ae934cc0b5a%26uicode%3D10000011' 
-H 'accept-encoding: gzip, deflate, br' 
-H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7' 
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36' 
-H 'accept: application/json, text/plain, */*' 
-H 'referer: https://m.weibo.cn/p/1008084df10e1237b5578013705ae934cc0b5a' 
-H 'authority: m.weibo.cn' 
-H 'x-requested-with: XMLHttpRequest' 
--compressed
'''
# 获取用于签到的地址
def get_super_sign_info(cookie, page_id):
    
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://m.weibo.cn/p/%s" % page_id,
        "authority": "m.weibo.cn",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie.get_cookie()
    }

    url = "https://m.weibo.cn/api/container/getIndex?containerid=%s" % page_id
    response = requests.get(url, headers=headers)
    data = json.loads(response.content)
    return data["data"]["pageInfo"]["toolbar_menus"][0]["scheme"]
    

'''
curl 'https://m.weibo.cn/api/config' 
-H cookie 
-H 'accept-encoding: gzip, deflate, br' 
-H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7' 
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36' 
-H 'accept: application/json, text/plain, */*' 
-H 'referer: https://m.weibo.cn/p/1008084df10e1237b5578013705ae934cc0b5a' 
-H 'authority: m.weibo.cn' 
-H 'x-requested-with: XMLHttpRequest' --compressed
'''
# 获取用于签到的st数据，需要作为data post到服务器
def get_config(cookie, page_id):
    
    headers = {
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "accept": "application/json, text/plain, */*",
        "referer": "https://m.weibo.cn/p/%s" % page_id,
        "authority": "m.weibo.cn",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie.get_cookie()
    }

    url = "https://m.weibo.cn/api/config"
    response = requests.get(url, headers=headers)
    data = json.loads(response.content)
    return data["data"]["st"]


'''
curl 'https://m.weibo.cn/api/container/button?sign=44b7be&request_url=http%3A%2F%2Fi.huati.weibo.com%2Fmobile%2Fsuper%2Factive_checkin%3Fpageid%3D10080877197fd1ded939d5a32cac51e9200c47' 
-H 'cookie: _T_WM=2347d44799bd017a7c42d4b0778e9eff; 
    WEIBOCN_FROM=1110006030; 
    ALF=1530701067; 
    SCF=Aj52M7AisY2zemY_Am0nKcL71Og-kwj4KrbW9HkL8O519CB_gPvclMRjWoBZ1JpYr7_h4F81dOxbdG6-pz2FcR0.; 
    SUB=_2A252EWkXDeThGeVM6FQZ9yvOyD6IHXVV-ndfrDV6PUJbktBeLWjckW1NTKWBvpSLDufBiIX08-g5g_RhTpQRWURW; 
    SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WFTdxv_d-bjYALZqEF93-os5JpX5K-hUgL.FoeEe0qRS0-Ee0z2dJLoI0YLxKnL1K5L1-BLxKnL12-L1h.LxKqL12-LBKMLxK-LBKBLBKMLxK-L12qL1KBLxKBLBonL1hMLxK-LBozL1h2t; 
    SUHB=0sqROPqomMAY9G; 
    SSOLoginState=1528109383; 
    MLOGIN=1; 
    M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D10080877197fd1ded939d5a32cac51e9200c47_-_main%26fid%3D10080877197fd1ded939d5a32cac51e9200c47_-_main%26uicode%3D10000011' 
-H 'origin: https://m.weibo.cn' 
-H 'accept-encoding: gzip, deflate, br' 
-H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7' 
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36' 
-H 'content-type: application/x-www-form-urlencoded' 
-H 'accept: application/json, text/plain, */*' 
-H 'referer: https://m.weibo.cn/p/10080877197fd1ded939d5a32cac51e9200c47' 
-H 'authority: m.weibo.cn' 
-H 'x-requested-with: XMLHttpRequest' 
--data 'st=fcc0da' --compressed
'''

# 获取签到信息
def get_sign_rank(cookie, page_id):
    
    url = "https://m.weibo.cn%s" % get_super_sign_info(cookie, page_id)
    
    st = get_config(cookie, page_id)
    post_data = {"st": st.encode("ascii")}

    headers = {
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.181 Safari/537.36",
        "content-type": "application/x-www-form-urlencoded",
        "accept": "application/json, text/plain, */*",
        "referer": "https://m.weibo.cn/p/%s" % page_id,
        "authority": "m.weibo.cn",
        "x-requested-with": "XMLHttpRequest",
        "Cookie": cookie.get_cookie()
    }
    response = requests.post(url, headers=headers, data=post_data)
    data = json.loads(response.content)
    print(data)
    print(data["data"]["msg"])

    

if __name__ == "__main__":
    username, password = sys.argv[1], sys.argv[2]
    cookie = get_cookie(username, password)
    #get_chart(cookie)

    username = "1776448504"  # 微博页面的id
    get_post_data(cookie, username)

    page_id = "10080877197fd1ded939d5a32cac51e9200c47"  # 超话的页面id
    #get_sign_rank(cookie)
