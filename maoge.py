import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from tomorrow import threads
# 开始计时
# start = time.perf_counter()
@threads(n=10)  # 多线程
def get_flight_details(ctrip_url):
    # chrome浏览器配置
    driverOption = Options()
    driverOption.add_argument('--disable-plugins')  # 禁止加载插件提高速度
    driverOption.add_argument('--disable-javascript')  # 禁用Javascript提高速度
    driverOption.add_argument('--no-sandbox')   # 防止chrome+selenium报错
    driverOption.add_argument('--disable-dev-shm-usage')
    driverOption.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
    driverOption.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
    #wd = webdriver.Chrome(options=driverOption)
    wd = webdriver.Chrome(ChromeDriverManager().install())
    # 隐性等待，最长等10秒
    wd.implicitly_wait(10)
    wd.get(ctrip_url)
    # 点击弹窗
    try:
        wd.find_element_by_link_text("确认").click()
        time.sleep(1)
    except Exception:
        pass

    # 判断当天有无航班
    def is_element_exist(xpath):
        s = wd.find_elements_by_xpath(xpath=xpath)
        if len(s) == 0:
            return False
        elif len(s) == 1:
            return True
    if is_element_exist("//div[@class='result-header']"):
        # 拉到底端
        for a in range(30):
            wd.execute_script("document.documentElement.scrollTop=10000")
        # 获取价格条数index_max
        last_index = wd.find_element_by_xpath('//div[@index][last()]')
        index_max = last_index.get_attribute('index')
        for index_num in range(int(index_max) + 1):
            flight = wd.find_element_by_xpath('//div[@index=' + str(index_num) + ']')
            wd.execute_script("arguments[0].scrollIntoView();", flight)
            time.sleep(0.1)
            airline_name = flight.find_element_by_xpath("//*[@class='airline-name']").text
            plane_no = flight.find_element_by_xpath("//div[@class='plane']").text
            dep_time = flight.find_element_by_xpath("//div[@class='depart-box']/div[@class='time']").text
            arr_time = flight.find_element_by_xpath("//div[@class='arrive-box']/div[@class='time']").text
            price = flight.find_element_by_xpath("//*[@class='price-box']").text
            transfer_info = flight.find_element_by_xpath("//div[@class='arrow-box']").text
            print(airline_name + '\t' + plane_no + '\t' + dep_time + '--' + arr_time + '\t' + price + transfer_info)
        wd.quit()
    else:
        print("当天没有航班")
        wd.quit()


'''
# 获取当天往后一个月内的日期
def get_dates():
    end_date = (datetime.datetime.now() + datetime.timedelta(days=3)).strftime("%Y-%m-%d")
    date_list = []
    end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    begin_date = datetime.datetime.strptime(time.strftime('%Y-%m-%d', time.localtime(time.time())), "%Y-%m-%d")
    while begin_date <= end_date:
        date_str = begin_date.strftime("%Y-%m-%d")
        date_list.append(date_str)
        begin_date += datetime.timedelta(days=1)
    return date_list
'''


def main():
    start = time.perf_counter()
    arr_city = ['sel']
    dates_list = ['2020-10-14']
    for city in arr_city:
        for date in dates_list:
            ctrip_url = 'https://flights.ctrip.com/international/search/oneway-bjs-%s?depdate=%s&cabin=y_s&adult=1&child=0&infant=0' % (city, date)
            print(city, ' ', date)
            get_flight_details(ctrip_url)
    # 结束计时并打印运行时间
    end = time.perf_counter()
    print("final time slice is in ", end-start)


if __name__ == '__main__':
    main()



