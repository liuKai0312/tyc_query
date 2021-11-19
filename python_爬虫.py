
# -*- coding: utf-8 -*-
import urllib.request as req 
import json
import bs4
import csv
import xlwt

#抓取原始码（HTML）
base_url = "http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2018/"
url= "{}index.html".format(base_url)

#建立一个request(模拟请求，模拟点击）
def request(url):
    request = req.Request(url, headers= {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"
    })
    with req.urlopen(request) as  response:
        data = response.read().decode("gbk")
    return data


#解析原始码
def get_data(data, tag, condition):
    root = bs4.BeautifulSoup(data,"html.parser")
    province_lists = root.find_all(tag, class_=condition)
    provinces = []
    urls = []
    for element in province_lists:
        a_tags = element.find_all("a")
        for a_tag in a_tags:
            href = a_tag['href']
            subUrl= "{}{}".format(base_url, href)
            province = a_tag.getText()
            provinces.append(province)
            urls.append(subUrl)
    return provinces, urls


#保存文本到CSV文件中
def save_to_csv(f,provinces, urls):
    
        writer = csv.writer(f)
        writer.writerow(["Provinces","URL"])
        for index in range(len(provinces)):
            writer.writerow([provinces[index], urls[index]])


def main():
    fileObj = open("test2.csv", "w")
    page = request(url)
    provinces, urls = get_data(page, "tr", "provincetr")
    save_to_csv(fileObj,provinces, urls)


    page = request(url)
    cities, urls = get_data(page, "table", "citytable")
    save_to_csv(fileObj,cities, urls)

    page = request(url)
    countries, urls = get_data(page, "table", "countytable")
    save_to_csv(fileObj,countries, urls)

    page = request(url)
    towns, urls = get_data(page, "table", "towntable")
    save_to_csv(fileObj,towns, urls)

    page = request(url)
    villages, urls = get_data(page, "tr", "villagetr")
    save_to_csv(fileObj,villages, urls)

    fileObj.close()

main()






