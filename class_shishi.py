class FlightsInfo:
    __url_list = ['https://flights.ctrip.com/international/search/oneway-bjs-', '?depdate=',
                  '&cabin=y_s&adult=1&child=0&infant=0']

    def __init__(self, city, date):
        self.city = city
        self.date = date
        self.url = self.__url_list[0] + city + self.__url_list[1] + date + self.__url_list[2]
        self.airline_name = []
        self.plane_no = []
        self.dep_time = []
        self.arr_time = []
        self.price = []
        self.transfer_info = []

    def get_info(self):
        flight_details = self.airline_name + self.plane_no + self.dep_time + self.arr_time + \
                         self.price + self.transfer_info
        return flight_details
