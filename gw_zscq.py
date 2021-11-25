import sys
import time
import importlib
import urllib
import urllib.request
import requests


def main():
    url = 'http://epub.sipo.gov.cn/patentoutline.action'

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        #"Cookie": "JSESSIONID=F3AD76F7541D4D487A31B32B4EFA827B; WEB=20111130; Hm_lvt_06635991e58cd892f536626ef17b3348=1547784443; _gscu_7281245=477844427wdni722; _gscbrs_7281245=1; TY_SESSION_ID=50e66a7d-2cd2-4f41-8c9a-7d8671c1dbd3; keycookie=8c84680b58; expirecookie=1547784913; Hm_lpvt_06635991e58cd892f536626ef17b3348=1547784611; _gscs_7281245=47784442erb04p22|pv:6",
        "Host": "epub.sipo.gov.cn",
        "Origin": "http://epub.sipo.gov.cn",
        "Pragma": "Pragma",
        "Referer":"http://epub.sipo.gov.cn/gjcx.jsp?tdsourcetag=s_pcqq_aiomsg",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6788.400 QQBrowser/10.3.2767.400",
    }
    # 构造form表单
    data = {"showType": "1",
            "strSources": "",
            "strWhere": "(TI='腾讯')",
            "numSortMethod": "",
            "strLicenseCode": "",
            "IdTypologie": "",
            "numIp": "",
            "numIpc": "",
            "numIg": "",
            "numIgc": "",
            "numIgd": "",
            "numUg": "",
            "numUgc": "",
            "numUgd": "",
            "numDg": "",
            "numDgc": "",
            "pageSize": "3",
            "pageNow": "1",
            }
    response = requests.post(url=url, data=data, headers=headers, timeout=10)
    response.encoding = "utf-8"
    txt = format(response.text)  # 获取响应的html内容
    print(txt)  # 返回值：<Response [200]>
if __name__ == '__main__':
    importlib.reload(sys)
    main()