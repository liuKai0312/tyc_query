import sys
import time
import importlib
import urllib
import urllib.request
import requests
from bs4 import BeautifulSoup
import pymysql
import numpy as np
import threading
import redis
from fake_useragent import UserAgent

db_ = redis.Redis(host="localhost",password=123, port=6379,decode_responses=True)

thread_proxy_list = []

ua = UserAgent()

OPEN_PROXY_IP_THREAD = False

GET_PROXY_IP_BY_FREE = True

GET_RESPONSE_BY_PROXY = False


def main():
    # updateComponyInfoByCompanyName([1,"腾讯"])
    # getSbByComponyName("深圳中基集团有限公司",1)
    # getZlByCompanyName("")
    # getZpzzqByCompanyName("北京学",1)
    # save_proxy_ip_by_agent(200)
    if OPEN_PROXY_IP_THREAD:
        run_get_proxy_fun_by_thread()
    companyList = mysqlDaoeExecutor_select("zb_tbCompanyInfo",[2,3])
    for companyDatas in companyList:
       try:
           company = companyDatas["data"]
           # 软件著作权
           getRjzzqCompanyName(company[1], company[0])
           # 商标
           getSbByComponyName(company[1], company[0])
           # 作品
           getZpzzqByCompanyName(company[1], company[0])
           # 专利
           getZlByComponyName(company[1], company[0])
           # 更新是否高新
           updateComponyInfoByCompanyName(company)
       except Exception as e:
           formartPrint("请求错误", "请求被拦截")
           print(e)
    for thread_proxy in thread_proxy_list:
        thread_proxy.stop()


# 根据公司名称查找公司的高新企业信息
def updateComponyInfoByCompanyName(company):
    companyName = company[1]
    companyIdForHttp = company[0]
    selectors = [
        'div.search-item:nth-child(1)>.search-result-single',
    ]
    url_temp = {'url': 'http://www.tianyancha.com/search/p1', 'selectors': selectors}
    response = getHttpResponse(url_temp["url"]+'?key=%s' % urllib.request.quote(companyName))
    soup = BeautifulSoup(response.text, 'lxml')
    result = soup.select(url_temp["selectors"][0])
    if len(result) >0:
        # 获得companyId
        companyId = result[0]["data-id"]
        if not companyId:
            formartPrint("未找到公司id",companyIdForHttp)
        else:
            getComponyDetaileById(companyName,companyId,companyIdForHttp)
    else:
        formartPrint("没有该企业",companyName)

def getComponyDetaileById(companyName,companyId,companyIdForHttp):
    selectors = [
        'div.content>.tag-list-content>.tag-list>.tag-common.-hint',
    ]
    url_temp = {'url': 'http://www.tianyancha.com/company/'+companyId, 'selectors': selectors}
    response = getHttpResponse(url_temp["url"])
    soup = BeautifulSoup(response.text, 'lxml')
    result = soup.select(url_temp["selectors"][0])
    if len(result) == 0:
        formartPrint("更新高新类型" + companyName, "非高新")
        # 不是高新企业
        mysqlDaoeExecutor_update("zb_tbCompanyInfo",[{"name":"gxlx","data": "非高新"}],[{"name":"compy_id","data":companyIdForHttp}])
        return
    else:
        formartPrint("更新高新类型" + companyName, "高新企业")
        # 高新企业
        result = beauifulHtmlEleAndGetValue(response,[
            'div#_container_certificate>table>tbody>tr:nth-child(1)>td:nth-child(3)',
            'div#_container_certificate>table>tbody>tr:nth-child(1)>td:nth-child(4)'
        ])
        for updateData in result:
            mysqlDaoeExecutor_update(
                "zb_tbCompanyInfo",
                [
                    {"name": "gxlx", "data": "国家高新"},
                    {"name": "gggx_time", "data": updateData[1]}
                ],
                [
                    {"name": "compy_id", "data": companyIdForHttp}
                ]
            )


# 根据公司名称查找专利（未完成：容易丢失连接）
# def getZlByCompanyName(companyName):
#     url = 'http://epub.sipo.gov.cn/patentoutline.action'
#     headers = {
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
#         "Accept-Encoding": "gzip, deflate",
#         "Accept-Language": "zh-CN,zh;q=0.9",
#         "Cache-Control": "no-cache",
#         "Connection": "keep-alive",
#         # "Cookie": "JSESSIONID=F3AD76F7541D4D487A31B32B4EFA827B; WEB=20111130; Hm_lvt_06635991e58cd892f536626ef17b3348=1547784443; _gscu_7281245=477844427wdni722; _gscbrs_7281245=1; TY_SESSION_ID=50e66a7d-2cd2-4f41-8c9a-7d8671c1dbd3; keycookie=8c84680b58; expirecookie=1547784913; Hm_lpvt_06635991e58cd892f536626ef17b3348=1547784611; _gscs_7281245=47784442erb04p22|pv:6",
#         "Cookie": "JSESSIONID=42EACAD2E87371FBCF4FF7F76AA14558",
#         "Host": "epub.sipo.gov.cn",
#         "Origin": "http://epub.sipo.gov.cn",
#         "Pragma": "Pragma",
#         "Referer": "http://epub.sipo.gov.cn/gjcx.jsp?tdsourcetag=s_pcqq_aiomsg",
#         "Upgrade-Insecure-Requests": "1",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6788.400 QQBrowser/10.3.2767.400",
#     }
#     # 构造form表单
#     data = {"showType": "1",
#             "strSources": "",
#             "strWhere": "PA='%腾讯%'",
#             "numSortMethod": "",
#             "strLicenseCode": "",
#             "IdTypologie": "",
#             "numIp": "",
#             "numIpc": "",
#             "numIg": "",
#             "numIgc": "",
#             "numIgd": "",
#             "numUg": "",
#             "numUgc": "",
#             "numUgd": "",
#             "numDg": "",
#             "numDgc": "",
#             "pageSize": "3",
#             "pageNow": "1",
#             }
#     response = requests.post(url=url, data=data, headers=headers, timeout=60000)
#     response.encoding = "utf-8"
#     print(response.text)
#     beauifulHtmlEleAndGetValue(response, ['div#all_link>ul>li>a'])


# 根据公司名查找商标
def getSbByComponyName(companyName,companyId):
    selectors = [
        'div.search_result_type>.filter_risk>.filter_brand_box>.risk-title>span',
        'div.search_result_type>.filter_risk>.filter_brand_box>div:nth-child(3)>div.item-left>span',
        'div.search_result_type>.filter_risk>.filter_brand_box>div:nth-child(4)>div.item-left>span',
        'div.search_result_type>.filter_risk>.filter_brand_box>div:nth-child(3)>div.item-right>span',
        'div.search_result_type>.filter_risk>.filter_brand_box>div:nth-child(4)>div.item-right>span'
    ]
    url_temp = {'url':'http://www.tianyancha.com/search/t401/p','selectors': selectors}
    formartPrint("发送请求", "正在获取【" + companyName + "】的商标列表")
    results = doSearch(url_temp,companyName,1,11)
    formartPrint(companyName + "的商标列表", results)
    if len(results)> 0 :
        # 先删除掉之前的数据
        mysqlDaoeExecutor_delete("zb_tbSbinfo", [
            {"name": "compy_id", "data": str(companyId)}
        ])
        for result in results:
            mysqlDaoeExecutor_insert(
                "zb_tbSbinfo",
                [
                    {"name": "park_id", "data": 'SZ00000001'},
                    {"name": "sbname", "data": result[0]},
                    {"name": "compy_id", "data": str(companyId)},
                    {"name": "sqrq", "data": result[1]},
                    {"name": "sblx", "data": result[2]},
                    {"name": "sbsn", "data": result[3]},
                    {"name": "sbstate", "data": result[4]}
                ]
            )

# 根据公司名查找专利
def getZlByComponyName(companyName,companyId):
    url_temp = {'url':'http://www.tianyancha.com/search/t402/p'}
    formartPrint("发送请求", "正在获取【" + companyName + "】的专利列表")
    results = []
    for num in range(1,11):
        url = url_temp["url"] + str(num) + '?key=%s' % urllib.request.quote(companyName)
        response = getHttpResponse(url)
        res_list = BeautifulSoup(response.text, "lxml").select('div.search_result_type>.filter_risk>a')
        if len(res_list) == 0:
            break
        for list in res_list:
            results.append(list)
    if len(results) == 0:
        formartPrint(companyName + "的专利", [])
    else:
        # 先删除掉之前的数据
        mysqlDaoeExecutor_delete("zb_tbZlinfo", [
            {"name": "compy_id", "data": str(companyId)}
        ])
        for result in results:
            zl_selectors = [
                "#patentTitle>table>tr:nth-child(1)>td:nth-child(1)",
                "#patentTitle>table>tr:nth-child(2)>td:nth-child(4)",
                "#patentTitle>table>tr:nth-child(3)>td:nth-child(4)",
                "#patentTitle>table>tr:nth-child(4)>td:nth-child(2)",
                "#patentTitle>table>tr:nth-child(6)>td:nth-child(4)"
            ]
            zl_response = getHttpResponse(str(result["href"]).replace("https", "http"))
            zl_result = beauifulHtmlEleAndGetValue(zl_response, zl_selectors)[0];
            formartPrint(companyName + "的专利", zl_result)
            mysqlDaoeExecutor_insert(
                "zb_tbZlinfo",
                [
                    {"name": "park_id", "data": 'SZ00000001'},
                    {"name": "compy_id", "data": str(companyId)},
                    {"name": "zlsn", "data": zl_result[0]},
                    {"name": "zllx", "data": zl_result[1]},
                    {"name": "lzsj", "data": zl_result[2]},
                    {"name": "zlname", "data": zl_result[3]},
                    {"name": "sqrq", "data": zl_result[4]},
                ]
            )


# 根据公司名查找软件著作权
def getRjzzqCompanyName(companyName,companyId):
    selectors = [
        'div.search_result_type>.filter_risk>.risk-title>span:nth-child(1)',
        'div.search_result_type>.filter_risk>div:nth-child(3)>div.item-left>span',
        'div.search_result_type>.filter_risk>div:nth-child(2)>div.item-right>span',
        'div.search_result_type>.filter_risk>.risk-title>span:nth-child(2)',
        'div.search_result_type>.filter_risk>div:nth-child(2)>div.item-left>span'
    ]
    url_temp = {'url':'http://www.tianyancha.com/search/t403/p','selectors': selectors}
    formartPrint("发送请求","正在获取【"+companyName+"】的软件著作权列表")
    results = doSearch(url_temp, companyName, 1, 11)
    formartPrint(companyName+"的软件著作权列表", results)
    if len(results)>0:
        # 先删除掉之前的数据
        mysqlDaoeExecutor_delete("zb_tbRzinfo", [
            {"name": "compy_id", "data": str(companyId)}
        ])
        for result in results:
            mysqlDaoeExecutor_insert(
                "zb_tbRzinfo",
                [
                    {"name": "park_id", "data": 'SZ00000001'},
                    {"name": "compy_id", "data": str(companyId)},
                    {"name": "fullname", "data": result[0]},
                    {"name": "shortname", "data": result[1]},
                    {"name": "rzsn", "data": result[2]},
                    {"name": "rzver", "data": result[3]},
                    {"name": "sqrq", "data": result[4]}
                ]
            )


# 发送请求
def doSearch(url_temp,companyName,pageStart,pageEnd):
    if not pageStart:
        pageStart = 1
    if not pageEnd:
        pageEnd = 2
    resultList = []
    for num in range(pageStart,pageEnd):
        # 爬取知识产权前十页数据，其他的url可以在首页模板中查询
        url = url_temp["url"] + str(num) + '?key=%s' % urllib.request.quote(companyName)
        try:
            response = getHttpResponse(url)
            if response.status_code is not 200:
                formartPrint("请求被阻止，状态码",response.status_code)
            # time.sleep(5)
            result = beauifulHtmlEleAndGetValue(response, url_temp["selectors"])
            if len(result) == 0:
                break
            else:
                if len(resultList) == 0:
                    resultList = result
                else:
                    resultList = np.concatenate((resultList, result))
        except Exception as e:
            formartPrint("爬取网页出错",url)
            print(e)
            break
    return resultList


def getHttpResponse(url):
    if GET_RESPONSE_BY_PROXY:
        return getHttpResponseWithProxy(url)
    else:
        return getHttpResponseWithoutProxy(url)


def getHttpResponseWithProxy(url):
    formartPrint("请求地址", url)
    try:
        response = get_http_response_by_proxy_ip(url)
        response.encoding = "utf-8"
        return response
    except Exception as e:
        print(e)
        formartPrint("发送请求失败", "网页请求被拦截")

def getHttpResponseWithoutProxy(url):
    formartPrint("请求地址", url)
    try:
        response = do_get_response(url)
        response.encoding = "utf-8"
        return response
    except Exception as e:
        print(e)
        formartPrint("发送请求失败", "网页请求被拦截")

def get_proxy():
    while True:
        try:
            if db_.llen("proxies") == 0:
                time.sleep(5)
            else:
                return {"http": "http://" + get_proxy_ip()}
                break
        except Exception:
            formartPrint("代理ip为空","None")

def get_http_response_by_proxy_ip(url):
    count = 0
    proxy = get_proxy()
    while True:
        count = count + 1
        formartPrint("循环监听代理次数",count)
        try:
            formartPrint("使用了代理",proxy)
            response = get_http_response_by_proxy_ip_wapper(url,proxy)
            formartPrint("响应状态码",response.status_code)
            if response.status_code == 200 and response.text:
                return response
                break
            elif response.status_code == 503:
                time.sleep(3)
                proxy = get_proxy()
            elif count >= 10:
                print('抓取网页失败')
                break
            else:
                proxy = get_proxy()
        except Exception as e:
            formartPrint("获取请求连接报错",e)
            proxy = get_proxy()

def get_http_response_by_proxy_ip_wapper(url,proxy):
    # s = requests.session()
    # s.keep_alive = False
    return requests.get(url, headers=getHttpHeaders(), cookies=getHttpCookies(), proxies=proxy,timeout=5)


def run_get_proxy_fun_by_thread():
    if GET_PROXY_IP_BY_FREE:
        thread_proxy_list.append(threading.Thread(target=get_ip_proxys_kuaidaili))
        thread_proxy_list.append(threading.Thread(target=get_ip_proxys_xici))
    else:
        thread_proxy_list.append(threading.Thread(target=get_proxy_ip_customer))
    for thread_proxy in thread_proxy_list:
        thread_proxy.start()



# 根据代理ip获得response
def do_proxy_get_response(url, proxy):
    # 在请求中设定头，cookie
    return requests.get(url, headers=getHttpHeaders(), cookies=getHttpCookies(), proxies={"http":proxy},timeout=5)

# 不根据代理ip获得response
def do_get_response(url):
    # 在请求中设定头，cookie
    return requests.get(url, headers=getHttpHeaders(), cookies=getHttpCookies(),timeout=5)

def get_ip_proxys_kuaidaili():
    if db_.llen("proxies") == 0:
        try:
            # formartPrint("代理ip运营商","快代理")
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"}
            for num in range(1, 2000):
                response = requests.get("https://www.kuaidaili.com/free/inha/" + str(num), headers=header, timeout=1)
                response.encoding = "utf-8"
                proxies = beauifulHtmlEleAndGetValue(response, [
                    "#list>table>tbody>tr>td:nth-child(1)",
                    "#list>table>tbody>tr>td:nth-child(2)",
                    "#list>table>tbody>tr>td:nth-child(4)",
                ])
                if len(proxies) == 0:
                    get_ip_proxys_kuaidaili()
                else:
                    for proxy in proxies:
                        valid_proxy_ip(proxy[0] + ":" + proxy[1], proxy[2], "快代理")
        except Exception as e:
            print(e)
            formartPrint("获取代理池失败", "快代理")

def get_ip_proxys_xici():
    if db_.llen("proxies") == 0:
        try:
            # formartPrint("代理ip运营商", "西刺")
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"}
            for num in range(1, 2000):
                response = requests.get("https://www.xicidaili.com/wt/" + str(num), headers=header, timeout=1)
                response.encoding = "utf-8"
                proxies = beauifulHtmlEleAndGetValue(response, [
                    "#ip_list>tr.odd>td:nth-child(2)",
                    "#ip_list>tr.odd>td:nth-child(3)",
                    "#ip_list>tr.odd>td:nth-child(6)",
                ])
                if len(proxies) == 0:
                    get_ip_proxys_xici()
                else:
                    for proxy in proxies:
                        valid_proxy_ip(proxy[0] + ":" + proxy[1], proxy[2],"西刺")
        except Exception as e:
            print(e)
            formartPrint("获取代理池失败","西刺")

def get_ip_proxys_daili66():
    try:
        # formartPrint("代理ip运营商", "代理66")
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"}
        for num in range(1, 2000):
            response = requests.get("http://www.66ip.cn/"+str(num)+".html", headers=header, timeout=1)
            response.encoding = "utf-8"
            print(response.text)
            proxies = beauifulHtmlEleAndGetValue(response, [
                "table>tr>td:nth-child(1)",
                "table>tr>td:nth-child(2)",
            ])
            print(proxies)
            if len(proxies) == 0:
                get_ip_proxys_daili66()
            else:
                for proxy in proxies:
                    valid_proxy_ip(proxy[0] + ":" + proxy[1], "代理66")
    except Exception as e:
        print(e)
        # formartPrint("获取代理池失败","代理66")


def valid_proxy_ip(proxy,agreement,agent):
    if agreement == "HTTP":
        try:
            url = "http://www.baidu.com/"
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"}
            response = requests.get(url, headers=header, proxies={"http": proxy}, timeout=1)
            if not response:
                return
                # formartPrint(agent+"该代理ip不可用", "")
            elif response.status_code == 200:
                push_proxy_ip(proxy)
                formartPrint(agent + "ip存入成功,"+ agreement, proxy)
        except Exception as e:
            pass
            # print(e)
            # formartPrint(agent+"存储代理ip异常",proxy)

def push_proxy_ip(proxy_ip):
    db_.lpush("proxies", proxy_ip)


def get_proxy_ip():
    if db_.llen("proxies") == 0:
        return None
    else:
        return db_.rpop("proxies")


def get_proxy_ip_customer():
   while True:
       if db_.llen("proxies") == 0:
           formartPrint("获取蘑菇代理ip", "10条")
           proxy_ip_datas = requests.get(
               "http://piping.mogumiao.com/proxy/api/get_ip_bs?appKey=ecfc21c9cbd84190893bb255298093d3&count=10&expiryDate=0&format=2&newLine=1").text.strip()
           for proxy_ip in proxy_ip_datas.split(" "):
               valid_proxy_ip(proxy_ip, "HTTP", "蘑菇代理")


# 根据公司名获得作品著作权
def getZpzzqByCompanyName(companyName,companyId):
    url = 'http://qgzpdj.ccopyright.com:8080/registerinfo/combineNew.do'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        # "Cookie": "JSESSIONID=1B720C08EC086DE584FB20B24DF840DC",
        "Host": "qgzpdj.ccopyright.com:8080",
        "Origin": "http://qgzpdj.ccopyright.com:8080",
        "Pragma": "no-cache",
        "Referer": "http://qgzpdj.ccopyright.com:8080/registerinfo/combineNew.do",
        "Upgrade-Insecure-Requests": "1",
        'User-Agent': ua.random
    }
    # 构造form表单
    data = {
            "ownername": companyName,
            "pageNumber": "1",
            "pageSize": "9999",
            }
    formartPrint("发送请求","正在获取【"+companyName+"】的作品列表")
    response = requests.post(url=url, data=data, headers=headers, timeout=60000)
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, 'lxml')
    results = soup.select('div#all_link>ul>li>a')
    if len(results) > 0:
        # 先删除掉之前的数据
        mysqlDaoeExecutor_delete("zb_tbZpinfo", [
            {"name": "compy_id", "data": str(companyId)}
        ])
        for num in range(len(results)):
            result = results[num]
            href = "http://qgzpdj.ccopyright.com:8080" + result["href"]
            formartPrint("发送请求", "正在获取【" + companyName + "】的第" + str(num + 1) + "个作品详情")
            item_response = getHttpResponseWithoutProxy(href)
            item_soup = BeautifulSoup(item_response.text, 'lxml')
            mysqlDaoeExecutor_insert(
                "zb_tbZpinfo",
                [
                    {"name": "park_id", "data": 'SZ00000001'},
                    {"name": "compy_id", "data": str(companyId)},
                    {"name": "zpname", "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(2)>td:nth-child(2)')},
                    {"name": "zplx", "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(3)>td:nth-child(2)')},
                    {"name": "zpsn", "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(8)>td:nth-child(2)')},
                    {"name": "sqrq", "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(8)>td:nth-child(4)')},
                    {"name": "end_rq", "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(7)>td:nth-child(2)')},
                    {"name": "firstpub_rq",
                     "data": getZpTextByXpathForSoup(item_soup, 'tr:nth-child(7)>td:nth-child(4)')}
                ]
            )

def getZpTextByXpathForSoup(soup,select):
    return soup.select(select)[0].get_text().strip()


# 解析html
def beauifulHtmlEleAndGetValue(response,selectors):
    try:
        soup = BeautifulSoup(response.text, 'lxml')
        htmlResult = [];
        resData = [];
        for selector in selectors:
            result_temp = []
            for res in soup.select(selector):
                result_temp.append(res.get_text().strip())
            if len(result_temp) > 0:
                htmlResult.append(result_temp)
        if len(htmlResult) == 0:
            return []
        else:
            for pos in range(len(htmlResult[0])):
                resData_temp = []
                for num in range(len(htmlResult)):
                    resData_temp.append(htmlResult[num][pos])
                resData.append(resData_temp)
            return resData
    except Exception as e:
        print(e)
        formartPrint("解析html","解析html异常")
        return []

def excuteAndGetcursorByMysql(type,sql):
    formartPrint("数据库执行"+type,sql)
    try:
        conn = pymysql.connect(host='localhost', user='root', passwd='123', db='tyc', port=3306, charset='utf8')
        # conn = pymysql.connect(host='hdm13147088.my3w.com', user='hdm13147088', passwd='ZY0119S1220DGQ2012',db='hdm13147088_db', port=3306, charset='utf8')
        cur = conn.cursor()  # 获取一个游标
        cur.execute(sql)
        conn.commit()
        return cur
    except Exception as e:
        formartPrint("数据库操作失败",sql)
        print(e)

def mysqlDaoeExecutor_select(tableName,rowIndexs):
    try:
        results = []
        results_temp = excuteAndGetcursorByMysql("select","select * from " + tableName).fetchall()
        if len(results_temp) == 0:
            formartPrint("无数据","查询")
        else:
            for result in results_temp:
                rowData = {"data":[]}
                if not rowIndexs:
                    rowData["data"].append(result)
                else:
                    for rowIndex in rowIndexs:
                        rowData["data"].append(result[rowIndex])
                if len(rowData["data"]) == 0:
                    formartPrint("无数据","查询")
                else:
                    results.append(rowData)
        return results
    except Exception as e:
        formartPrint("数据库异常","数据库【select】异常")
        print(e)

def mysqlDaoeExecutor_update(tableName,columns,searchDatas):
    try:
        sql = "update " + tableName + " set "
        for index in range(len(columns)):
            column = columns[index]
            if index == len(columns) - 1:
                sql = sql + column["name"] + "='" + str(column["data"]) + "'"
            else:
                sql = sql + column["name"] + "='" + str(column["data"]) + "',"
        if not searchDatas or len(searchDatas) == 0:
            sql = sql + ";"
        else:
            sql = sql + " where "
            for index in range(len(searchDatas)):
                column = searchDatas[index]
                if index == len(searchDatas) - 1:
                    sql = sql + column["name"] + "='" + str(column["data"]) + "';"
                else:
                    sql = sql + column["name"] + "='" + str(column["data"]) + "',"
        excuteAndGetcursorByMysql("update", sql)
    except:
        formartPrint("数据库异常","数据库【update】异常")

def mysqlDaoeExecutor_insert(tableName,columns):
    try:
        sql_column = "insert into " + tableName + " ("
        sql_values = " values ("
        for index in range(len(columns)):
            column = columns[index]
            if index == len(columns) - 1:
                sql_column = sql_column + column["name"] + ")"
                sql_values = sql_values + "'" + column["data"] + "');"
            else:
                sql_column = sql_column + column["name"] + ","
                sql_values = sql_values + "'" + column["data"] + "',"
        excuteAndGetcursorByMysql("insert", sql_column + sql_values)
    except Exception as e:
        print(e)
        formartPrint("数据库异常","数据库【插入】异常")

def mysqlDaoeExecutor_delete(tableName,searchDatas):
    try:
        sql = "delete from " + tableName + " where "
        for index in range(len(searchDatas)):
            column = searchDatas[index]
            if index == len(searchDatas) - 1:
                sql = sql + column["name"] + "='" + str(column["data"]) + "';"
            else:
                sql = sql + column["name"] + "='" + str(column["data"]) + "',"
        excuteAndGetcursorByMysql("delete", sql)
    except Exception as e:
        print(e)
        formartPrint("数据库异常","数据库【delete】异常")



def getHttpHeaders():

    return {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
               'Connection': 'close',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,zh-TW;q=0.2',
               'Connection': 'keep-alive',
               'DNT': '1',
               'Host': 'www.tianyancha.com',
               'Upgrade-Insecure-Requests': '1',
               'User-Agent': ua.random
               }

def getHttpCookies():
    return {'aliyungf_tc': 'AQAAAFiQ724iBwUAvYrbchiXbweaUmpi',
               'csrfToken': '4ObJTtL8wGkpkuSVmp5wvcmo',
               'TYCID': 'b800b0e0194d11e99789e7e0149a2303',
               'undefined': 'b800b0e0194d11e99789e7e0149a2303',
               'ssuid': '1270484662',
               '__insp_wid': '677961980',
               '__insp_nv': 'true',
               '__insp_targlpu': 'aHR0cHM6Ly93d3cudGlhbnlhbmNoYS5jb20v',
               '__insp_targlpt': '5aSp55y85p_lLeWVhuS4muWuieWFqOW3peWFt1%2FkvIHkuJrkv6Hmga%2Fmn6Xor6Jf5YWs5Y_45p_l6K_iX_W3peWVhuafpeivol%2FkvIHkuJrkv6HnlKjkv6Hmga%2Fns7vnu58%3D',
               'Hm_lvt_e92c8d65d92d534b0fc290df538b4758': '1547553402',
               '_ga': 'GA1.2.1490777280.1547553402',
               '_gid': 'GA1.2.229367458.1547553402',
               '__insp_norec_sess': 'true',
               'token': 'af3881f9e61542bbab43af2b0033409f',
               '_utm': '3e1d7328237649498dd90fef5e80d15a',
               'tyc-user-info': '%257B%2522claimEditPoint%2522%253A%25220%2522%252C%2522myQuestionCount%2522%253A%25220%2522%252C%2522explainPoint%2522%253A%25220%2522%252C%2522nickname%2522%253A%2522%25E7%25BB%25B4%25E6%258B%2589%25C2%25B7%25E6%25B3%2595%25E7%25B1%25B3%25E5%258A%25A0%2522%252C%2522integrity%2522%253A%25220%2525%2522%252C%2522state%2522%253A%25220%2522%252C%2522announcementPoint%2522%253A%25220%2522%252C%2522vipManager%2522%253A%25220%2522%252C%2522discussCommendCount%2522%253A%25221%2522%252C%2522monitorUnreadCount%2522%253A%25226%2522%252C%2522onum%2522%253A%25220%2522%252C%2522claimPoint%2522%253A%25220%2522%252C%2522token%2522%253A%2522eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzM1NDM0ODc5NiIsImlhdCI6MTU0NzYxMzIwNywiZXhwIjoxNTYzMTY1MjA3fQ.HLbft7wEp1Pf4QQur6EpNgjWFuTPwa3nNV_wVknQyCY8MWRai6pVxWsPmpVDxPGro7utyDDJutZ7kgflrSGO2Q%2522%252C%2522redPoint%2522%253A%25220%2522%252C%2522pleaseAnswerCount%2522%253A%25221%2522%252C%2522bizCardUnread%2522%253A%25220%2522%252C%2522vnum%2522%253A%25220%2522%252C%2522mobile%2522%253A%252217354348796%2522%257D',
               'auth_token': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzM1NDM0ODc5NiIsImlhdCI6MTU1NTczNDE3MSwiZXhwIjoxNTg3MjcwMTcxfQ.w0W_HzjiYs1W2BGHmYwc030uQ7d9jPUJEfn0gq42tn-2KDol8kvxiR1kZJQvUni6VIUoBmGEP-n3INmlE0plcQ',
               '__insp_slim': '1547553988518',
               'Hm_lpvt_e92c8d65d92d534b0fc290df538b4758': '1547553989'
               }

def getHttpCookies1():
    return {'auth_token': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzM1NDM0ODc5NiIsImlhdCI6MTU1NDk5MDUwMSwiZXhwIjoxNTcwNTQyNTAxfQ.HUWVoqspH3lecZgyMgJ4CNcSQoiRA3x78nweastHpGf6Zz_IR8eV-r4FOZjymq-XK55x7zRFFQcwUU1sim-JrQ'}

def formartPrint(type,data):
    print("【" + type + "】：",data)
    log = open("./log_"+time.strftime("%Y%m%d", time.localtime())+".txt", "a+")
    log.write("【" + type + "】："+str(data) + "\n")

def test_zl():
    count = 0
    for num in range(1, 600):
        url = 'https://www.tianyancha.com/pagination/patent.xhtml?ps=5&pn=' + str(num) + '&id=32377046&_=1555765944888'
        response = requests.get(url, headers=getHttpHeaders(), cookies=getHttpCookies(), timeout=5)
        response.encoding = "utf-8"
        if response.status_code is not 200:
            print(count)
            break
        else:
            count = count + 1
            soup = BeautifulSoup(response.text, 'lxml')
            results = soup.select("table>tbody>tr>td.left-col>span")
            for res in results:
                mysqlDaoeExecutor_insert("t_test",[
                    {"name":"name","data":res.get_text().strip()}
                ])


if __name__ == '__main__':
    importlib.reload(sys)
    main()
    # test_zl()