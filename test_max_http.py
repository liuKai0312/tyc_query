import requests
import time
from fake_useragent import UserAgent

ua = UserAgent()


def getHttpHeaders():
    return {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,zh-TW;q=0.2',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'www.tianyancha.com',
            'Referer': 'http://www.tianyancha.com/search?key=%E7%99%BE%E5%BA%A6&checkFrom=searchBox',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': ua.random
            }


def getHttpCookies():
    return {'aliyungf_tc': 'AQAAAI/MLmYAWQIA+++vO6M2xOECnhUp',
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
            'auth_token': 'eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxNzM1NDM0ODc5NiIsImlhdCI6MTU1NTY1MDk1MywiZXhwIjoxNTcxMjAyOTUzfQ.tAPywPcPwe_y7MvdhU4i3u5qnAn1eA5GSFf_MwX3_oWa3KgK_zmLAL3bdl6bNelFVwgPETcALdmBfmftAo_VEw; Hm_lpvt_e92c8d65d92d534b0fc290df538b4758=1555650954',
            '__insp_slim': '1547553988518',
            'Hm_lpvt_e92c8d65d92d534b0fc290df538b4758': '1547553989'
            }

if __name__ == '__main__':
    count = 0;
    while True:
        response = requests.get("https://www.tianyancha.com/search/t401/p1?key=腾讯", headers=getHttpHeaders(), cookies=getHttpCookies(), timeout=60000)
        time.sleep(3)
        print(response.status_code)
        if response and response.status_code == 200:
            count = count+1
        else:
            break
    print(count)
