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
import math

db_ = redis.Redis(host="localhost",password=123, port=6379,decode_responses=True)

thread_proxy_list = []

ua = UserAgent()

OPEN_PROXY_IP_THREAD = False

GET_PROXY_IP_BY_FREE = True

GET_RESPONSE_BY_PROXY = False

current_cookies = None


def main():
    # updateComponyInfoByCompanyName([1,"腾讯"])
    # getSbByComponyName("深圳中基集团有限公司",1)
    # getZlByCompanyName("")
    # getZpzzqByCompanyName("北京学",1)
    # save_proxy_ip_by_agent(200)
    if OPEN_PROXY_IP_THREAD:
        run_get_proxy_fun_by_thread()
    companyList = get_all_companys("zb_tbCompanyInfo",[2,3])
    for companyDatas in companyList:
       try:
           company = companyDatas["data"]
           # 更新
           get_compony_info_by_companyname(company)
       except Exception as e:
           formartPrint("请求错误", "请求被拦截")
           print(e)
    for thread_proxy in thread_proxy_list:
        thread_proxy.stop()


# 根据公司名称查找公司
def get_compony_info_by_companyname(company):
    company_name = company[1]
    company_local_id = company[0]
    selectors = [
        'div.search-item:nth-child(1)>.search-result-single',
    ]
    url_temp = {'url': 'http://www.tianyancha.com/search/p1', 'selectors': selectors}
    response = getHttpResponse(url_temp["url"]+'?key=%s' % urllib.request.quote(company_name))
    if response is None:
        formartPrint("获取公司出错", "响应为空")
    elif response.status_code is not 200:
        formartPrint("获取公司出错", "被拦截")
    elif response.status_code == 200:
        soup = BeautifulSoup(response.text, 'lxml')
        result = soup.select(url_temp["selectors"][0])
        if len(result) > 0:
            # 获得远端companyId
            company_remote_id = result[0]["data-id"]
            if not company_remote_id:
                formartPrint("未找到公司id", company_local_id)
            else:
                get_compony_detaile_by_id(company_name, company_remote_id, company_local_id)
        else:
            formartPrint("没有该企业", company_name)
    else:
        formartPrint("获取公司出错","未知异常")


# 查找公司的详细信息
def get_compony_detaile_by_id(company_name,company_remote_id,company_local_id):
    url_temp = {'url': 'http://www.tianyancha.com/company/'+company_remote_id}
    response = getHttpResponse(url_temp["url"])
    # 更新企业信息
    update_company_info(response,company_name,company_remote_id,company_local_id)
    # 更新商标信息
    get_sb_by_componyname(response,company_name, company_remote_id,company_local_id)
    # 更新软件著作权
    get_rz_by_componyname(response,company_name, company_remote_id,company_local_id)
    # 更新专利
    get_zl_by_componyname(response,company_name, company_remote_id,company_local_id)
    # 更新作品著作权
    get_zp_by_componyname(response,company_name, company_remote_id,company_local_id)


# 更新企业是否高新
def update_company_info(company_detail_response,company_name,company_remote_id,company_local_id):
    soup = BeautifulSoup(company_detail_response.text, 'lxml')
    result = soup.select('div.content>.tag-list-content>.tag-list>.tag-common.-hint')
    if len(result) == 0:
        formartPrint("更新高新类型" + company_name, "非高新")
        # 不是高新企业
        mysqlDaoeExecutor_update(
            "zb_tbCompanyInfo",
            [
                {"name": "gxlx", "data": "非高新"}
            ],
            [
                {"name": "compy_id", "data": company_local_id}
            ]
        )
    else:
        formartPrint("更新高新类型" + company_name, "高新企业")
        zs_count_res = beauifulHtmlEleAndGetValue(company_detail_response, ["#nav-main-certificateCount>span.data-count"])
        if len(zs_count_res) > 0 and len(zs_count_res[0]) > 0:
            zs_count = zs_count_res[0][0]
            # 查询证书的详情
            selectors = [
                'table>tbody>tr>td:nth-child(2)>span',
                'table>tbody>tr>td:nth-child(4)>span'
            ]
            page_count = math.ceil(int(zs_count) / 5)
            formartPrint(company_name + "的证书列表页数", page_count)
            url_temp = {'url': 'https://www.tianyancha.com/pagination/certificate.xhtml?ps=5&pn=$num&id=' + str(company_remote_id) + '&_=1555935634142', 'selectors': selectors}
            formartPrint("发送请求", "正在获取【" + company_name + "】的证书列表")
            for num in range(1,page_count+1):
                url = url_temp["url"].replace("$num",str(num))
                response = getHttpResponse(url)
                if response is None:
                    formartPrint("获取"+company_name+"证书列表错误","请求超时")
                elif response.status_code == 200:
                    zs_lists = beauifulHtmlEleAndGetValue(response,url_temp["selectors"])
                    exists = False
                    for zs in zs_lists:
                        if zs[0] == "高新技术企业":
                            exists = True
                            mysqlDaoeExecutor_update(
                                "zb_tbCompanyInfo",
                                [
                                    {"name": "gxlx", "data": "国家高新"},
                                    {"name": "gggx_time", "data": zs[1]}
                                ],
                                [
                                    {"name": "compy_id", "data": company_local_id}
                                ]
                            )
                            break
                    if exists is True:
                        break
                elif response.status_code is not 200:
                    formartPrint("获取" + company_name + "证书列表错误", "请求被拦截")
                else:
                    formartPrint("获取" + company_name + "证书列表错误", "未知异常")
        else:
            formartPrint(company_name + "的证书列表为空", [])


# 根据公司id查找商标
def get_sb_by_componyname(company_detail_response, company_name, company_remote_id, company_local_id):
    # 更新商标的个数
    sb_count_res = beauifulHtmlEleAndGetValue(company_detail_response,["#nav-main-tmCount>span.data-count"])
    sb_count = 0
    if len(sb_count_res) > 0 and len(sb_count_res[0]) > 0:
        sb_count = sb_count_res[0][0]
        # 查询商标的详情
        selectors = [
            'div.data-content>table>tbody>tr>td:nth-child(4)>span',
            'div.data-content>table>tbody>tr>td:nth-child(2)>span',
            'div.data-content>table>tbody>tr>td:nth-child(6)>span',
            'div.data-content>table>tbody>tr>td:nth-child(5)>span',
            'div.data-content>table>tbody>tr>td:nth-child(7)>span'
        ]
        page_count =math.ceil(int(sb_count)/10)
        formartPrint(company_name + "的商标列表页数", page_count)
        url_temp = {'url':'https://www.tianyancha.com/pagination/tmInfo.xhtml?ps=10&pn=$num&id='+str(company_remote_id)+'&_=1555775408946','selectors': selectors}
        formartPrint("发送请求", "正在获取【" + company_name + "】的商标列表")
        results = do_search_with_url_no_prarms(url_temp,1,page_count)
        formartPrint(company_name + "的商标列表", results)
        if len(results)> 0 :
            # 先删除掉之前的数据
            mysqlDaoeExecutor_delete("zb_tbSbinfo", [
                {"name": "compy_id", "data": str(company_local_id)}
            ])
            for result in results:
                mysqlDaoeExecutor_insert(
                    "zb_tbSbinfo",
                    [
                        {"name": "park_id", "data": 'SZ00000001'},
                        {"name": "compy_id", "data": str(company_local_id)},
                        {"name": "sbname", "data": result[0]},
                        {"name": "sqrq", "data": result[1]},
                        {"name": "sblx", "data": result[2]},
                        {"name": "sbsn", "data": result[3]},
                        {"name": "sbstate", "data": result[4]}
                    ]
                )
    else:
        formartPrint(company_name + "的商标列表为空", [])
    # 更新商标个数
    mysqlDaoeExecutor_update(
        "zb_tbCompanyInfo",
        [
            {"name": "sbnums", "data": sb_count},
        ],
        [
            {"name": "compy_id", "data": company_local_id}
        ]
    )


# 根据公司id查找软件著作权
def get_rz_by_componyname(company_detail_response, company_name, company_remote_id, company_local_id):
    # 更新商标的个数
    rz_count_res = beauifulHtmlEleAndGetValue(company_detail_response,["#nav-main-cpoyRCount>span.data-count"])
    rz_count = 0
    if len(rz_count_res) > 0 and len(rz_count_res[0]) > 0:
        rz_count = rz_count_res[0][0]
        # 查询商标的详情
        selectors = [
            'table>tbody>tr>td:nth-child(3)>span',
            'table>tbody>tr>td:nth-child(4)>span',
            'table>tbody>tr>td:nth-child(5)>span',
            'table>tbody>tr>td:nth-child(7)>span',
            'table>tbody>tr>td:nth-child(2)>span'
        ]
        page_count =math.ceil(int(rz_count)/5)
        formartPrint(company_name + "的软件著作权列表页数", page_count)
        url_temp = {'url':'https://www.tianyancha.com/pagination/copyright.xhtml?ps=5&pn=$num&id='+str(company_remote_id)+'&_=1555834707614','selectors': selectors}
        formartPrint("发送请求", "正在获取【" + company_name + "】的软件著作权列表")
        results = do_search_with_url_no_prarms(url_temp,1,page_count)
        formartPrint(company_name + "的软件著作权列表", results)
        if len(results)> 0 :
            # 先删除掉之前的数据
            mysqlDaoeExecutor_delete("zb_tbRzinfo", [
                {"name": "compy_id", "data": str(company_local_id)}
            ])
            for result in results:
                mysqlDaoeExecutor_insert(
                    "zb_tbRzinfo",
                    [
                        {"name": "park_id", "data": 'SZ00000001'},
                        {"name": "compy_id", "data": str(company_local_id)},
                        {"name": "fullname", "data": result[0]},
                        {"name": "shortname", "data": result[1]},
                        {"name": "rzsn", "data": result[2]},
                        {"name": "rzver", "data": result[3]},
                        {"name": "sqrq", "data": result[4]}
                    ]
                )
    else:
        formartPrint(company_name + "的软件著作权列表为空", [])
    # 更新软件著作权数量
    mysqlDaoeExecutor_update(
        "zb_tbCompanyInfo",
        [
            {"name": "rznums", "data": rz_count},
        ],
        [
            {"name": "compy_id", "data": company_local_id}
        ]
    )


# 根据公司id查找专利
def get_zl_by_componyname(company_detail_response, company_name, company_remote_id, company_local_id):
    # 获得专利链接
    zl_count_res = beauifulHtmlEleAndGetValue(company_detail_response,["#nav-main-patentCount>span.data-count"])
    # 先删除掉之前的数据
    mysqlDaoeExecutor_delete(
        "zb_tbZlinfo",
        [
            {"name": "compy_id", "data": str(company_local_id)}
        ]
    )
    if len(zl_count_res) > 0 and len(zl_count_res[0]) > 0:
        zl_count = zl_count_res[0][0]
        # 查询专利的详情
        selectors = [
            'table>tbody>tr>td:nth-child(4)>span',
            'table>tbody>tr>td:nth-child(6)>span'
        ]
        page_count =math.ceil(int(zl_count)/5)
        formartPrint(company_name + "的专利列表页数", page_count)
        url_temp = {'url':'https://www.tianyancha.com/pagination/patent.xhtml?ps=5&pn=$num&id='+str(company_remote_id)+'&_=1555834707617','selectors': selectors}
        formartPrint("发送请求", "正在获取【" + company_name + "】的专利链接列表")
        zl_links = []
        sn_lx_lists = []
        zlnums = 0
        xyzlnums = 0
        wgzlnums = 0
        for num in range(1,page_count+1):
            formartPrint(company_name + "当前正在处理的专利列表页数", str(num) + "/" + str(page_count))
            #  page_count+1
            try:
                response = getHttpResponse(url_temp["url"].replace("$num", str(num)))
                if response is None:
                    formartPrint(company_name + "的专利列表获取超时", "休息一下")
                    continue
                elif response.status_code == 200:
                    sn_lx_datas = beauifulHtmlEleAndGetValue(response, url_temp["selectors"])
                    # 收集专利类型
                    for data in sn_lx_datas:
                        sn_lx_lists.append(data)
                        if data[1] == "发明专利":
                            zlnums = zlnums + 1
                        elif data[1] == "外观专利":
                            wgzlnums = wgzlnums + 1
                        elif data[1] == "实用新型":
                            xyzlnums = xyzlnums + 1
                        else:
                            formartPrint(company_name+"的专利类型非采集类型",data[1])
                    soup = BeautifulSoup(response.text, 'lxml')
                    # 收集专利链接
                    a_lists = soup.select('table>tbody>tr>td:nth-child(7)>a')
                    for link in a_lists:
                        zl_links.append(link["href"])
                else:
                    formartPrint(company_name + "获取专利链接时被拦截", response.status_code)
                    break
            except Exception as e:
                continue
                formartPrint("获取"+company_name+"时出现异常",e)
        # 更新公司专利内容
        mysqlDaoeExecutor_update(
            "zb_tbCompanyInfo",
            [
                {"name": "zlnums", "data": zlnums},
                {"name": "xyzlnums", "data": xyzlnums},
                {"name": "wgzlnums", "data": wgzlnums},
            ],
            [
                {"name": "compy_id", "data": company_local_id}
            ]
        )
        # 更新专利详情
        update_zl_by_zl_links(company_name,company_local_id,zl_links,sn_lx_lists)
    else:
        formartPrint(company_name + "的专利列表为空", [])


# 根据链接查找专利详情并且更新内容
def update_zl_by_zl_links(company_name,company_local_id,zl_links,sn_lx_lists):
    formartPrint(company_name + "的专利的链接数", len(zl_links))
    zl_results_db_datas = []
    for num in range(len(zl_links)):
        formartPrint(company_name + "当前正在处理的专利链接索引", str(num+1)+"/"+str(len(zl_links)))
        link = zl_links[num]
        response = getHttpResponse(link)
        if response is None:
            formartPrint(company_name + "的专利获取超时", "休息一下")
            continue
        elif response.status_code == 200:
            zl_selectors = [
                "#patentTitle>table>tr:nth-child(1)>td:nth-child(4)",
                "#patentTitle>table>tr:nth-child(6)>td:nth-child(4)",
                "#patentTitle>table>tr:nth-child(4)>td:nth-child(2)",
                "#patentTitle>table>tr:nth-child(6)>td:nth-child(2)"
            ]
            zl_results = beauifulHtmlEleAndGetValue(response, zl_selectors)
            if len(zl_results_db_datas) == 0:
                zl_results_db_datas = zl_results
            else:
                zl_results_db_datas = np.concatenate((zl_results_db_datas, zl_results))
        else:
            formartPrint(company_name + "的专利获取被拦截", response.status_code)
            break
    formartPrint(company_name + "的专利列表", zl_results_db_datas)
    # 更新专利详情
    for zl in zl_results_db_datas:
        mysqlDaoeExecutor_insert(
            "zb_tbZlinfo",
            [
                {"name": "park_id", "data": 'SZ00000001'},
                {"name": "compy_id", "data": str(company_local_id)},
                {"name": "zlsn", "data": zl[0]},
                {"name": "lzsj", "data": zl[1]},
                {"name": "zlname", "data": zl[2]},
                {"name": "sqrq", "data": zl[3]},
                {"name": "zllx", "data": '-'},
            ]
        )
    # 更新专利类型
    for sn_lx in sn_lx_lists:
        # 更新公司专利内容
        mysqlDaoeExecutor_update(
            "zb_tbZlinfo",
            [
                {"name": "zllx", "data": sn_lx[1]},
            ],
            [
                {"name": "zlsn", "data": sn_lx[0]}
            ]
        )

# 根据公司id查找作品著作权
def get_zp_by_componyname(company_detail_response, company_name, company_remote_id, company_local_id):
    # 更新商标的个数
    zp_count_res = beauifulHtmlEleAndGetValue(company_detail_response,["#nav-main-copyrightWorks>span.data-count"])
    zp_count = 0
    if len(zp_count_res) > 0 and len(zp_count_res[0]) > 0:
        zp_count = zp_count_res[0][0]
        # 查询作品著作权的详情
        selectors = [
            'table>tbody>tr>td:nth-child(2)>span',
            'table>tbody>tr>td:nth-child(4)>span',
            'table>tbody>tr>td:nth-child(3)>span',
            'table>tbody>tr>td:nth-child(6)>span',
            'table>tbody>tr>td:nth-child(5)>span',
            'table>tbody>tr>td:nth-child(7)>span'
        ]
        page_count =math.ceil(int(zp_count)/5)
        formartPrint(company_name + "的作品著作权列表页数", page_count)
        url_temp = {'url':'https://www.tianyancha.com/pagination/copyrightWorks.xhtml?ps=5&pn=$num&id='+str(company_remote_id)+'&_=1555844934449','selectors': selectors}
        formartPrint("发送请求", "正在获取【" + company_name + "】的作品著作权列表")
        results = do_search_with_url_no_prarms(url_temp,1,page_count)
        formartPrint(company_name + "的作品著作权列表", results)
        if len(results)> 0 :
            # 先删除掉之前的数据
            mysqlDaoeExecutor_delete("zb_tbZpinfo", [
                {"name": "compy_id", "data": str(company_local_id)}
            ])
            for result in results:
                mysqlDaoeExecutor_insert(
                    "zb_tbZpinfo",
                    [
                        {"name": "park_id", "data": 'SZ00000001'},
                        {"name": "compy_id", "data": company_local_id},
                        {"name": "zpname", "data": result[0]},
                        {"name": "zplx", "data": result[1]},
                        {"name": "zpsn", "data": result[2]},
                        {"name": "sqrq", "data": result[3]},
                        {"name": "firstpub_rq", "data": result[4]},
                        {"name": "end_rq", "data": result[5]},
                    ]
                )
    else:
        formartPrint(company_name + "的作品著作权列表为空", [])
    # 更新作品著作权数量
    mysqlDaoeExecutor_update(
        "zb_tbCompanyInfo",
        [
            {"name": "zpnums", "data": zp_count},
        ],
        [
            {"name": "compy_id", "data": company_local_id}
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

# 发送请求
def do_search_with_url_no_prarms(url_temp,pageStart,pageEnd):
    if not pageStart:
        pageStart = 1
    if not pageEnd:
        pageEnd = 2
    resultList = []
    for num in range(pageStart,pageEnd+1):
        # 爬取知识产权前十页数据，其他的url可以在首页模板中查询
        url = url_temp["url"].replace("$num",str(num))
        try:
            response = getHttpResponse(url)
            if response is None:
              continue
            elif response.status_code is not 200:
                formartPrint("请求被阻止，状态码",response.status_code)
                break
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
            continue
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
        return response
    except Exception as e:
        print(e)
        formartPrint("发送请求失败", "网页请求被拦截")
        return None

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
    return requests.get(url, headers=getHttpHeaders(), cookies=getHttpCookies(), proxies=proxy,timeout=10)

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
   return get_users_cookies_pool_response(url)


def get_users_cookies_pool_response(url):
    try:
        if current_cookies is None:
            return do_get_users_cookies_pool_response(url)
        else:
            response = requests.get(url, headers=getHttpHeaders(), cookies=current_cookies["cookies"], timeout=10)
            if response is None:
                update_cookies_expire_error_code(current_cookies["user_cookies"][0])
                return do_get_users_cookies_pool_response(url)
            elif response.status_code is 200:
                update_cookies_request_count_url(current_cookies["user_cookies"],url)
                return response
            elif response.status_code is not 200:
                update_cookies_expire_error_code(current_cookies["user_cookies"][0],response.status_code)
                return do_get_users_cookies_pool_response(url)
            else:
                update_cookies_expire_error_code(current_cookies["user_cookies"][0])
                return do_get_users_cookies_pool_response(url)
    except Exception as e:
        formartPrint("使用临时cookies异常",e)
        return do_get_users_cookies_pool_response(url)


def do_get_users_cookies_pool_response(url):
    while True:
        formartPrint("获取用户cookies", "正在切换cookies")
        user_cookies = get_user_cookies()
        if user_cookies is None:
            formartPrint("获取用户cookies", "cookies为空")
            return None
            break
        else:
            cookies = format_user_cookies(user_cookies[3])
            if cookies is None:
                update_cookies_expire_error_code(user_cookies[0])
                continue
            else:
                # 在请求中设定头，cookie
                formartPrint("正在使用cookies获取response", "当前用户【"+user_cookies[1]+"】")
                response = requests.get(url, headers=getHttpHeaders(), cookies=cookies, timeout=10)
                if response is None:
                    formartPrint("获取用户cookies异常", "response为None")
                    update_cookies_expire_error_code(user_cookies[0])
                    continue
                elif response.status_code is 200:
                    global current_cookies
                    current_cookies = {'user_cookies': user_cookies, 'cookies': cookies}
                    update_cookies_request_count_url(user_cookies, url)
                    formartPrint("当前用户", user_cookies[1])
                    response.encoding = "utf-8"
                    return response
                    break
                elif response.status_code is not 200:
                    formartPrint("使用cookies请求异常", "当前用户被拦截【" + user_cookies[1] + "】")
                    update_cookies_expire_error_code(user_cookies[0],response.status_code)
                    continue
                else:
                    formartPrint("使用cookies请求异常", "未知异常，当前用户【" + user_cookies[1] + "】")
                    update_cookies_expire_error_code(user_cookies[0])
                    continue


def update_cookies_expire_error_code(cookie_id,error_code = 414):
    mysqlDaoeExecutor_update(
        'tb_users_cookies_pool',
        [
            {'name': 'active', 'data': '0'},
            {'name': 'last_expire_time', 'data': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())},
            {'name': 'error_code', 'data': error_code}
        ],
        [
            {'name': 'id', 'data': cookie_id}
        ]
    )

def update_cookies_request_count_url(user_cookies,url):
    count = 0 if user_cookies[7] is None or user_cookies[7] == '' else int(user_cookies[7])
    print("================",count)
    mysqlDaoeExecutor_update(
        'tb_users_cookies_pool',
        [
            {'name': 'request_count', 'data': count+1},
            {'name': 'last_request_url', 'data': url}
        ],
        [
            {'name': 'id', 'data': user_cookies[0]}
        ]
    )

def get_user_cookies():
    while True:
        try:
            formartPrint("获取用户cookies", "正在获取")
            user_cookies = mysqlDaoeExecutor_select('tb_users_cookies_pool', [
                {'name': "active", 'data': '1'}
            ], 0, 1)
            if len(user_cookies) == 0:
                formartPrint("用户cookie的数量为空", "没有可用的用户cookie，请及时激活或补充")
                return None
            else:
                formartPrint("获取用户cookies", "获取成功")
                return user_cookies[0]
            break
        except Exception as e:
            formartPrint("获取用户cookies的时候发生了异常", e)
            continue

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

def get_all_companys(tableName,rowIndexs):
    try:
        results = []
        results_temp = mysqlDaoeExecutor_select(tableName)
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

def mysqlDaoeExecutor_select(tableName,searchDatas=[],limit_start=None,limit_end=None):
    try:
        sql = "select * from " + tableName
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
        if limit_start is not None and limit_end is not None:
            sql = sql.replace(";","")
            sql = sql + ' limit '+ str(limit_start) + ',' + str(limit_end) + ';'
        return excuteAndGetcursorByMysql("select", sql).fetchall()
    except Exception as e:
        print(e)
        formartPrint("数据库异常","数据库【select】异常")


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

def mysqlDaoeExecutor_delete(tableName,searchDatas=[]):
    try:
        sql = "delete from " + tableName
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


def format_user_cookies(cookie_str):
   try:
       cookie_list = cookie_str.split("; ")
       user_cookie = {}
       for cookie in cookie_list:
           cookie_name = cookie.split("=")[0]
           cookie_value = cookie.split("=")[1]
           user_cookie[cookie_name] = cookie_value
       formartPrint("当前使用的cookies",user_cookie)
       return user_cookie
   except Exception as e:
       formartPrint("获取cookies异常", e)
       return None


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
    # res = mysqlDaoeExecutor_select('tb_users_cookies_pool')
    # print(res[0][7])