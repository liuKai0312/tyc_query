# -*- coding: utf-8 -*-

import requests

userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
header = {
    # "origin": "https://passport.mafengwo.cn",
    "Referer": "https://passport.mafengwo.cn/",
    'User-Agent': userAgent,
}

def mafengwoLogin(account, password):
    # 马蜂窝模仿 登录
    print ("开始模拟登录马蜂窝")
    
    postUrl = "https://passport.mafengwo.cn/login/"
    postData = {
        "passport": account,
        "password": password,
    }
    responseRes = requests.post(postUrl, data = postData, headers = header)
    # 无论是否登录成功，状态码一般都是 statusCode = 200
    print(f"statusCode = {responseRes.status_code}")
    print(f"text = {responseRes.text}")

if __name__ == "__main__":
    # 从返回结果来看，有登录成功
    mafengwoLogin("13756567832", "000000001")

#提取到的请求信息：
Headers：
    Request URL:https://passport.mafengwo.cn/login/
    Request Method:POST	
    origin:https://passport.mafengwo.cn	
    referer:https://passport.mafengwo.cn/	
    User-Agent:Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)     Chrome/63.0.3239.132 Safari/537.36	

Form Data:
    passport:13725168940
    password:aaa00000000


# -*- coding: utf-8 -*-

import requests

# python2 和 python3的兼容代码
try:
    # python2 中
    import cookielib
    print(f"user cookielib in python2.")
except:
    # python3 中
    import http.cookiejar as cookielib
    print(f"user cookielib in python3.")

# session代表某一次连接
mafengwoSession = requests.session()
# 因为原始的session.cookies 没有save()方法，所以需要用到cookielib中的方法LWPCookieJar，这个类实例化的cookie对象，就可以直接调用save方法。
mafengwoSession.cookies = cookielib.LWPCookieJar(filename = "mafengwoCookies.txt")

userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
header = {
    # "origin": "https://passport.mafengwo.cn",
    "Referer": "https://passport.mafengwo.cn/",
    'User-Agent': userAgent,
}

def mafengwoLogin(account, password):
    # 马蜂窝模仿 登录
    print("开始模拟登录马蜂窝")

    postUrl = "https://passport.mafengwo.cn/login/"
    postData = {
        "passport": account,
        "password": password,
    }
    # 使用session直接post请求
    responseRes = mafengwoSession.post(postUrl, data = postData, headers = header)
    # 无论是否登录成功，状态码一般都是 statusCode = 200
    print(f"statusCode = {responseRes.status_code}")
    print(f"text = {responseRes.text}")
    # 登录成功之后，将cookie保存在本地文件中，好处是，以后再去获取马蜂窝首页的时候，就不需要再走mafengwoLogin的流程了，因为已经从文件中拿到cookie了
    mafengwoSession.cookies.save()


if __name__ == "__main__":
    # 从返回结果来看，有登录成功
    # mafengwoLogin("13756567832", "000000001")

