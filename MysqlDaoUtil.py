import pymysql


def selectUnFinishCompany():
    conn = pymysql.connect(host='localhost', user='root', passwd='123', db='tianyan', port=3306, charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "select * from zb_tbcompanyinfo"
    try:
        cur.execute(sql)
        results = cur.fetchall()
        return results

    except:
        print("数据库操作失败：公司获取失败")
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


def updateConpany(id):
    conn = pymysql.connect(host='localhost', user='root', passwd='123', db='tianyan', port=3306, charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "update company set done = 1 where id = '%d'"
    print(sql)
    try:
        cur.execute(sql % id)
    except:
        print("Error: unable to fecth data")
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


def updateConpanyFlase(id):
    conn = pymysql.connect(host='localhost', user='root', passwd='123', db='tianyan', port=3306, charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "update company set done = 0 where id = '%d'"
    print(sql)
    try:
        cur.execute(sql % id)
    except:
        print("Error: unable to fecth data")
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源


def insertCompany(values):
    conn = pymysql.connect(host='localhost', user='root', passwd='123', db='tianyan', port=3306, charset='utf8')
    cur = conn.cursor()  # 获取一个游标
    sql = "INSERT INTO result (id, companyname,pname, reg_code, creditcode , reg_address, tax_code) " \
          "VALUES ( '%d', '%s','%s', '%s','%s', '%s','%s') "
    print(sql)
    try:
        cur.execute(sql % values)
    except:
        print("Error: unable to fecth data")
    conn.commit()
    cur.close()  # 关闭游标
    conn.close()  # 释放数据库资源