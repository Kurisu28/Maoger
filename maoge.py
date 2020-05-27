import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
from queue import Queue
from class_shishi import FlightsInfo
import psycopg2


# 获取某天往后days天内的日期
def get_dates(days):
    input_time = datetime.date(2020, 10, 1)  # 起始日期
    end_date = (input_time + datetime.timedelta(days=days)).strftime("%Y-%m-%d")
    date_list = []
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    begin_date = datetime.datetime.strptime(input_time.strftime("%Y-%m-%d"), "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list


def get_flight_details(in_q, out_q):
    while in_q.empty() is not True:
        # chrome浏览器配置
        driveroption = Options()
        driveroption.add_argument('--headless')  # 无界模式
        driveroption.add_argument('--disable-plugins')  # 禁止加载插件提高速度
        driveroption.add_argument('--disable-javascript')  # 禁用Javascript提高速度
        driveroption.add_argument('--no-sandbox')  # 防止chrome+selenium报错
        driveroption.add_argument('--disable-dev-shm-usage')
        driveroption.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
        driveroption.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        wd = webdriver.Chrome(options=driveroption)
        # 隐性等待，最长等20秒
        wd.implicitly_wait(20)
        input_info = in_q.get()
        wd.get(input_info.url)
        # time.sleep(3)
        # 点击弹窗
        try:
            wd.find_element_by_link_text("确认").click()
        except Exception as e:
            pass

        # 判断当天有无航班
        def is_element_exist(xpath):
            s = wd.find_elements_by_xpath(xpath=xpath)
            if len(s) == 0:
                return False
            elif len(s) == 1:
                return True

        if is_element_exist("//div[@class='result-header']"):
            index_num = 0
            while is_element_exist('//div[@index=' + str(index_num) + ']'):
                flight = wd.find_element_by_xpath('//div[@index=' + str(index_num) + ']')
                wd.execute_script("arguments[0].scrollIntoView();", flight)
                time.sleep(1)
                input_info.airline_name.append(flight.find_element_by_xpath("//*[@class='airline-name']").text)
                input_info.plane_no.append(flight.find_element_by_xpath("//div[@class='plane']").text)
                input_info.dep_time.append(flight.find_element_by_xpath("//div[@class='depart-box']/div[@class='time']").text)
                input_info.arr_time.append(flight.find_element_by_xpath("//div[@class='arrive-box']/div[@class='time']").text)
                input_info.price.append(flight.find_element_by_xpath("//*[@class='price-box']").text)
                input_info.transfer_info.append(flight.find_element_by_xpath("//div[@class='arrow-box']").text)
                index_num += 1
            out_q.put(input_info)
        wd.quit()
        in_q.task_done()


if __name__ == '__main__':
    start = time.time()
    queue = Queue()
    result_queue = Queue()
    arr_city = ['sel']  # 目的地城市
    dates_list = get_dates(4)  # 时间段
    for city in arr_city:
        for date in dates_list:
            t = FlightsInfo(city, date)
            queue.put(t)
    for i in range(5):
        thread = threading.Thread(target=get_flight_details, args=(queue, result_queue,))
        thread.daemon = True  # 随主线程退出而退出
        thread.start()
    queue.join()  # 队列消费完 线程结束
    end = time.time()
    print('总耗时：%s' % (end - start))
    conn = psycopg2.connect(database="shishi_db", user="postgres", password="zzy999510", host="127.0.0.1", port="5432")
    cursor = conn.cursor()
    # sql语句 建表
    sql_creat_table = """CREATE TABLE flights_info (
    city text, 
    date date,
    airline_name text,
    plane_no text,
    dep_time text,
    arr_time text,
    price text);"""
    # 执行语句
    cursor.execute(sql_creat_table)
    print("flights_info table created successfully")
    while result_queue.empty() is not True:
        a = result_queue.get()
        for i in range(len(a.airline_name)):
            sql1 = """INSERT INTO flights_info VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            params = (a.city, a.date, a.airline_name[i], a.plane_no[i], a.dep_time[i], a.arr_time[i], a.price[i])
            cursor.execute(sql1, params)
    # 事物提交
    conn.commit()
    # 关闭数据库连接
    conn.close()


