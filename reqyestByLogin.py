# -*- coding: utf-8 -*-

import requests

userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
header = {
    # "origin": "https://passport.mafengwo.cn",
    "Referer": "https://passport.mafengwo.cn/",
    'User-Agent': userAgent,
}

def mafengwoLogin(account, password):
    # �����ģ�� ��¼
    print ("��ʼģ���¼�����")
    
    postUrl = "https://passport.mafengwo.cn/login/"
    postData = {
        "passport": account,
        "password": password,
    }
    responseRes = requests.post(postUrl, data = postData, headers = header)
    # �����Ƿ��¼�ɹ���״̬��һ�㶼�� statusCode = 200
    print(f"statusCode = {responseRes.status_code}")
    print(f"text = {responseRes.text}")

if __name__ == "__main__":
    # �ӷ��ؽ���������е�¼�ɹ�
    mafengwoLogin("13756567832", "000000001")

#��ȡ����������Ϣ��
Headers��
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

# python2 �� python3�ļ��ݴ���
try:
    # python2 ��
    import cookielib
    print(f"user cookielib in python2.")
except:
    # python3 ��
    import http.cookiejar as cookielib
    print(f"user cookielib in python3.")

# session����ĳһ������
mafengwoSession = requests.session()
# ��Ϊԭʼ��session.cookies û��save()������������Ҫ�õ�cookielib�еķ���LWPCookieJar�������ʵ������cookie���󣬾Ϳ���ֱ�ӵ���save������
mafengwoSession.cookies = cookielib.LWPCookieJar(filename = "mafengwoCookies.txt")

userAgent = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
header = {
    # "origin": "https://passport.mafengwo.cn",
    "Referer": "https://passport.mafengwo.cn/",
    'User-Agent': userAgent,
}

def mafengwoLogin(account, password):
    # �����ģ�� ��¼
    print("��ʼģ���¼�����")

    postUrl = "https://passport.mafengwo.cn/login/"
    postData = {
        "passport": account,
        "password": password,
    }
    # ʹ��sessionֱ��post����
    responseRes = mafengwoSession.post(postUrl, data = postData, headers = header)
    # �����Ƿ��¼�ɹ���״̬��һ�㶼�� statusCode = 200
    print(f"statusCode = {responseRes.status_code}")
    print(f"text = {responseRes.text}")
    # ��¼�ɹ�֮�󣬽�cookie�����ڱ����ļ��У��ô��ǣ��Ժ���ȥ��ȡ�������ҳ��ʱ�򣬾Ͳ���Ҫ����mafengwoLogin�������ˣ���Ϊ�Ѿ����ļ����õ�cookie��
    mafengwoSession.cookies.save()


if __name__ == "__main__":
    # �ӷ��ؽ���������е�¼�ɹ�
    # mafengwoLogin("13756567832", "000000001")

