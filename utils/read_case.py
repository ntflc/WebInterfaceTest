#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
import json
import urllib
import time


class ReadTestCase:
    def __init__(self, case_path, login_return={}):
        self.__case_path = case_path
        self.__login_return = login_return

    @staticmethod
    def __numerical_sort(value):
        numbers = re.compile(r"(\d+)")
        parts = numbers.split(value)
        parts[1::2] = map(int, parts[1::2])
        return parts

    def __get_value_by_type(self, data):
        login_return = self.__login_return
        return_data = {}
        for key in data:
            if isinstance(data[key], dict):
                try:
                    if data[key]["type"] == "get_return":
                        # 获取对应返回值
                        value = eval(data[key]["field"])
                        return_data[key] = value
                    elif data[key]["type"] == "get_timestamp":
                        # 获取单位
                        if "unit" in data[key]:
                            unit = data[key]["unit"]
                            if unit not in ("s", "ms"):
                                print "Warning: unit of timestamp must be 's' or 'ms'. Use 's' instead"
                                unit = "s"
                        else:
                            unit = "s"
                        # 获取当前时间戳
                        ts = time.time()
                        if unit == "ms":
                            ts *= 1000
                        ts = int(ts)
                        # 获取时间间隔
                        if "interval" in data[key]:
                            interval = data[key]["interval"]
                            if not isinstance(interval, int):
                                print "Warning: interval must be int. Ignore interval"
                                interval = 0
                        else:
                            interval = 0
                        # 将时间戳加上间隔
                        ts += interval
                        return_data[key] = ts
                    else:
                        print "Warning: type %s not support. Ignore this key" % data[key]["type"]
                        continue
                except Exception as e:
                    print "Warning:", e.message, "Ignore this key"
                    continue
            else:
                return_data[key] = data[key]
        return return_data

    def __get_case_json(self):
        if not os.path.exists(self.__case_path):
            print "Error: '%s' doesn't exist" % self.__case_path
            sys.exit(-1)
        # 获取case_path路径下所有test开头的.json文件
        json_list = []
        file_list = os.listdir(self.__case_path)
        for file_name in file_list:
            if file_name.startswith("test") and file_name.endswith(".json"):
                json_list.append("%s/%s" % (self.__case_path, file_name))
        # 按照文件名自然排序
        json_list = sorted(json_list, key=self.__numerical_sort)
        return json_list

    def __get_case_data(self):
        json_list = self.__get_case_json()
        case_list = []
        # 对每一个json文件，获取其内容，将无错误的用例存入case_list
        for case_file in json_list:
            with open(case_file) as json_file:
                try:
                    case_json = json.load(json_file)
                except Exception as e:
                    print "Warning:", e.message, "in %s. Ignore this case" % case_file
                    continue
            # 判断url字段是否存在，不存在则报错
            if "url" in case_json:
                url = case_json["url"]
            else:
                print "Warning: 'url' is required in %s. Ignore this case" % case_file
                continue
            # 判断param字段是否存在，不存在则忽略
            if "param" in case_json:
                param = case_json["param"]
                if not isinstance(param, dict):
                    print "Warning: 'param' must be json type. Ignore this case"
                    continue
                param = self.__get_value_by_type(param)
                # 将param并入url
                url += "?" + urllib.urlencode(param)
            # 判断headers字段是否存在，不存在则忽略
            if "headers" in case_json:
                headers = case_json["headers"]
                if not isinstance(headers, dict):
                    print "Warning: 'headers' must be json type. Ignore this case"
                    continue
            else:
                headers = {}
            # 判断type字段是否存在，不存在则报错
            if "type" in case_json:
                type_ = case_json["type"].upper()
                if type_ not in ("GET", "POST"):
                    print "Warning: type %s not support in %s. Ignore this case" % (type_, case_file)
                    continue
            else:
                print "Warning: 'type' is required in %s. Ignore this case" % case_file
                continue
            # 判断type为POST时，data字段是否存在，不存在则报错
            if type_ == "POST":
                if "data" in case_json:
                    post_data = case_json["data"]
                    if not isinstance(post_data, dict):
                        print "Warning: 'data' must be json type. Ignore this case"
                        continue
                    post_data = self.__get_value_by_type(post_data)
                    post_data = urllib.urlencode(post_data)
                else:
                    print "Warning: 'data' is required in %s. Ignore this case" % case_file
                    continue
            else:
                post_data = None
            # 判断expect字段是否存在，不存在则报错
            if "expect" in case_json:
                expect = case_json["expect"]
                if not isinstance(expect, dict):
                    print "Warning: 'expect' must be json type. Ignore this case"
                    continue
            else:
                print "Warning: 'expect' is required in %s. Ignore this case" % case_file
                continue
            # 写入case_list
            case = {
                "url": url,
                "headers": headers,
                "type": type_,
                "data": post_data,
                "expect": expect
            }
            case_list.append(case)
        return case_list

    def get_data(self):
        return self.__get_case_data()
