import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import threading
from queue import Queue
from class_shishi import FlightsInfo
import os
import psycopg2


# acuqire date information
def get_dates(days):
    input_time = datetime.date(2020, 10, 1)  # start date
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
        # chrome settings
        driveroption = Options()
        driveroption.add_argument('--headless')  # 无界模式
        driveroption.add_argument('--disable-plugins')  # 禁止加载插件提高速度
        driveroption.add_argument('--disable-javascript')  # 禁用Javascript提高速度
        driveroption.add_argument('--no-sandbox')  # 防止chrome+selenium报错
        driveroption.add_argument('--disable-dev-shm-usage')
        driveroption.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
        driveroption.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        wd = webdriver.Chrome(options=driveroption, executable_path=os.path.abspath("D:\Study\python\code\scarbber\chromedriver\chromedriver.exe"))
        # invisibly wait
        wd.implicitly_wait(20)
        input_info = in_q.get()
        wd.get(input_info.url)
        # time.sleep(3)
        # click pop-up window
        try:
            wd.find_element_by_link_text("确认").click()
        except Exception as e:
            pass

        # check whether there is a airline for current date
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

def scarb():
    start = time.time()
    queue = Queue()
    result_queue = Queue()
    arr_city = ['sel']  # destination
    dates_list = get_dates(4)  # dates
    for city in arr_city:
        for date in dates_list:
            t = FlightsInfo(city, date)
            queue.put(t)
    for i in range(5):
        thread = threading.Thread(target=get_flight_details, args=(queue, result_queue,))
        thread.daemon = True  # function will quit with the quit of main thread
        thread.start()
    queue.join()  # thread end when queue is empty
    end = time.time()
    print('total time consuming：%s' % (end - start))
    conn = psycopg2.connect(database="shishi_db", user="postgres", password="zzy999510", host="127.0.0.1", port="5432")
    cursor = conn.cursor()
    # SQL code construction
    sql_creat_table = """CREATE TABLE flights_info (
        city text, 
        date date,
        airline_name text,
        plane_no text,
        dep_time text,
        arr_time text,
        price text);"""
    # SQL execution
    cursor.execute(sql_creat_table)
    print("flights_info table created successfully")
    while result_queue.empty() is not True:
        a = result_queue.get()
        for i in range(len(a.airline_name)):
            sql1 = """INSERT INTO flights_info VALUES (%s, %s, %s, %s, %s, %s, %s)"""
            params = (a.city, a.date, a.airline_name[i], a.plane_no[i], a.dep_time[i], a.arr_time[i], a.price[i])
            cursor.execute(sql1, params)
    # commit event
    conn.commit()
    # close DB
    conn.close()

if __name__ == '__main__':
    # acquire current time
    now_time = datetime.datetime.now()
    now_day = now_time.date().day
    now_month = now_time.date().month
    now_year = now_time.date().year
    # acquire tomorrow time
    '''next_time = now_time + datetime.timedelta(days=+1)
    next_year = next_time.date().year
    next_month = next_time.date().month
    next_day = next_time.date().day'''
    # acuqire time object of tomorrow 10am
    next_time = datetime.datetime.strptime(str(now_year) + "-" + str(now_month) + "-" + str(now_day) + " 11:47:00",
                                           "%Y-%m-%d %H:%M:%S")

    # acuqire the time from now to tomorrow 10am unit:second
    timer_start_time = (next_time - now_time).total_seconds()
    print("time difference is " + str(timer_start_time))

    # timer
    timer = threading.Timer(timer_start_time, scarb)
    timer.start()



