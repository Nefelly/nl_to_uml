# coding: utf-8
import json
import geoip2.database
import logging
import sys

logger = logging.getLogger(__name__)


class Ip2AddressService(object):
    READER = geoip2.database.Reader('litatom/data/GeoLite2-City.mmdb')
    READER_COUNTRY = geoip2.database.Reader('litatom/data/GeoLite2-Country.mmdb')
    '''
    docs :https://www.jianshu.com/p/eb756fc2d3b8
    '''

    @classmethod
    def get_ip_all_info(cls, ip):
        '''
        should be litatom/data/GeoLite2-City.mmdb and  may have some bug
        '''
        response = cls.READER.city(ip)
        # 有多种语言，我们这里主要输出英文和中文
        print(u"你查询的IP的地理位置是:")

        print(u"地区：{}({})".format(response.continent.names["es"],
                                 response.continent.names["zh-CN"]))

        print(u"国家：{}({}) ，简称:{}".format(response.country.name,
                                        response.country.names["zh-CN"],
                                        response.country.iso_code))

        # print(u"洲／省：{}({})".format(response.subdivisions.most_specific.name,
        #                           response.subdivisions.most_specific.names["zh-CN"]))

        print(u"城市：{}({})".format(response.city.name,
                                 response.city.names["zh-CN"]))

        print(u"经度：{}，纬度{}".format(response.location.longitude,
                                  response.location.latitude))

        print(u"时区：{}".format(response.location.time_zone))

        print(u"邮编:{}".format(response.postal.code))

    @classmethod
    def ip_country(cls, ip):
        '''scenes could be ads, pulp...'''
        try:
            return cls.READER_COUNTRY.country(ip).country.name
        except Exception, e:
            logger.error('get ip country failed,  error:%s',  e)
            return ''

    @classmethod
    def ip_country_city(cls, ip):
        '''scenes could be ads, pulp...'''
        try:
            return cls.READER.city(ip).country.name, cls.READER.city(ip).country.name
        except Exception, e:
            logger.error('get ip country failed,  error:%s',  e)
            return ''