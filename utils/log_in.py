#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import cookielib
import urllib
import urllib2
import json


class LogInByInterface:
    def __init__(self, case_path):
        self.__login_json_path = "%s/login.json" % case_path

    def __get_login_json(self):
        with open(self.__login_json_path) as json_file:
            try:
                login_json = json.load(json_file)
            except Exception as e:
                print "Error:", e.message
                sys.exit(-2)
        return login_json

    def __get_login_data(self):
        login_json = self.__get_login_json()
        # 判断url字段是否存在，不存在则报错
        if "url" in login_json:
            url = login_json["url"]
        else:
            print "Error: 'url' is required in login.json"
            sys.exit(-3)
        # 判断headers字段是否存在，不存在则忽略
        if "headers" in login_json:
            headers = login_json["headers"]
            if not isinstance(headers, dict):
                print "Error: 'headers' must be json type"
                sys.exit(-4)
        else:
            headers = {}
        # 判断data字段是否存在，不存在则报错
        if "data" in login_json:
            data = login_json["data"]
            if not isinstance(data, dict):
                print "Error: 'data' must be json type"
                sys.exit(-5)
        else:
            print "Error: 'data' is required in login.json"
            sys.exit(-6)
        return url, headers, data

    @staticmethod
    def __get_value_from_url(url, field):
        try:
            req = urllib2.Request(url)
            resp = urllib2.urlopen(req)
            resp_dict = json.loads(resp.read())
            value = eval(field)
        except Exception as e:
            print "Error:", e.message
            sys.exit(-7)
        return value

    def __log_in(self):
        url, headers, data = self.__get_login_data()
        # 安装cookie
        cj = cookielib.LWPCookieJar()
        cookie_support = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(cookie_support, urllib2.HTTPHandler)
        urllib2.install_opener(opener)
        # 生成POST参数
        post_data = {}
        # 逐一判断data中的字段，如果为key:value格式，则直接存入post_data；如果为key:dict格式，则获取对应value再存入post_data
        # 如果为key:dict格式，同时将对于key和value写入return_data以备后用
        return_data = {}
        for key in data:
            if isinstance(data[key], dict):
                try:
                    if data[key]["type"] == "get_value":
                        value = self.__get_value_from_url(data[key]["url"], data[key]["field"])
                        post_data[key] = value
                        # 将key和value写入return_data以备后用
                        return_data[key] = value
                    else:
                        print "Error: type %s not support in login.json" % data[key]["type"]
                        sys.exit(-8)
                except Exception as e:
                    print "Error:", e.message
                    sys.exit(-9)
            else:
                post_data[key] = data[key]
        post_data = urllib.urlencode(post_data)
        # 请求登录接口
        try:
            req = urllib2.Request(url, data=post_data, headers=headers)
            resp = urllib2.urlopen(req)
            resp_dict = json.loads(resp.read())
            return_data = dict(return_data.items() + resp_dict.items())
        except Exception as e:
            print "Error:", e.message
            sys.exit(-10)
        return cj, return_data

    def get_data(self):
        if not os.path.exists(self.__login_json_path):
            print "Warning: '%s' doesn't exist, ignore logging" % self.__login_json_path
            return None, {}
        cj, return_data = self.__log_in()
        cookies = [item.name + "=" + item.value for item in cj]
        cookie = ';'.join(item for item in cookies)
        return cookie, return_data
