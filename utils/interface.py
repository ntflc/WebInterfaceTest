#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
import time
from libs import send_mail

# 设置接口请求最大时长
TIMEOUT = 5
# 设置不同用例间隔
TIME_INTERVAL = 3


class InterfaceTest:
    def __init__(self, case_list, cookie=None):
        self.__case_list = case_list
        self.__cookie = cookie

    @staticmethod
    def __is_equal(expect_value, get_value):
        if isinstance(get_value, bool):
            return expect_value.lower() == str(get_value).lower()
        else:
            return expect_value == str(get_value)

    def __check_resp(self, resp_dict, expect):
        reason = "condition not match"
        for pkey, pvalue in expect.iteritems():
            if isinstance(pvalue, dict):
                if not isinstance(resp_dict[pkey], dict):
                    reason = "key: %s, type of get is not dict" % pkey
                    result = False
                else:
                    result = self.__check_resp(resp_dict[pkey], pvalue)
            elif isinstance(pvalue, list) and len(pvalue) > 0 and isinstance(pvalue[0], dict):
                expect_list_len = len(pvalue)
                resp_list_len = len(resp_dict[pkey])
                if expect_list_len != resp_list_len:
                    reason = "key: %s, wrong value length, expect: %d, get: %d" % (pkey, expect_list_len, resp_list_len)
                    result = False
                else:
                    for i in range(expect_list_len):
                        result = self.__check_resp(resp_dict[pkey][i], pvalue[i])
                        if isinstance(result, tuple) and not result[0]:
                            return result
            else:
                if pkey not in resp_dict:
                    reason = "key: %s is not in resp_dict" % pkey
                    result = False
                elif resp_dict[pkey] != pvalue:
                    reason = "key: %s, expect: %s, get: %s" % (pkey, pvalue, resp_dict[pkey])
                    result = False
                else:
                    result = True
            if isinstance(result, bool) and not result:
                return False, reason
            elif isinstance(result, tuple) and not result[0]:
                return result
        return result

    def __request_interface(self):
        results = []
        for case in self.__case_list:
            # 获取该case的接口地址、类型、POST参数、预期结果
            url = case["url"]
            headers = case["headers"]
            type_ = case["type"]
            post_data = case["data"]
            expect = case["expect"]
            # 向headers中添加cookie
            if self.__cookie is not None:
                headers["cookie"] = self.__cookie
            # 初始化参数
            is_pass = False
            # 如果是GET或POST类型
            if type_ in ("GET", "POST"):
                # 初始化接口请求完毕的时间戳
                end_ts = 0
                try:
                    # 获取当前时间戳
                    start_ts = time.time()
                    # 请求接口
                    req = urllib2.Request(url, data=post_data, headers=headers)
                    resp = urllib2.urlopen(req, timeout=TIMEOUT)
                    # 获取当前时间戳
                    end_ts = time.time()
                    # 解析接口
                    resp_dict = json.loads(resp.read())
                    # 判断是否符合预期
                    result = self.__check_resp(resp_dict, expect)
                    if result is True:
                        is_pass = True
                        reason = None
                    else:
                        is_pass = result[0]
                        reason = result[1]
                except urllib2.HTTPError as e:
                    reason = "%s %s" % (e.code, e.reason)
                except urllib2.URLError as e:
                    reason = e.reason
                except Exception as e:
                    reason = e.message
                finally:
                    time_cost = end_ts - start_ts if end_ts != 0 else None
            # 如果非以上类型，不做处理
            else:
                print "Warning: Only support GET and POST interface"
                continue
            # 将结果写入列表result中
            result_dict = {
                "uri": url,
                "type": type_,
                "pass": is_pass,
                "reason": reason,
                "time": time_cost
            }
            results.append(result_dict)
            time.sleep(TIME_INTERVAL)
        return results

    def get_results(self):
        return self.__request_interface()


class SendResultByMail:
    def __init__(self, results):
        self.__results = results

    def __set_content(self):
        results = self.__results
        pass_results = [result for result in results if result["pass"]]
        unpass_results = [result for result in results if not result["pass"]]
        all_cnt = len(results)
        pass_cnt = len(pass_results)
        unpass_cnt = len(unpass_results)
        # 用例总览
        content = "<table border='1' cellspacing='0' cellpadding='0'><tr align='center'>" \
                  + "<th style='width:100px'>用例总数</th>" \
                  + "<th style='width:100px'>通过数</th>" \
                  + "<th style='width:100px'>不通过数</th></tr><tr align='center'>" \
                  + "<td><font style='font-weight:bold'>%d</font></td>" % all_cnt \
                  + "<td><font style='font-weight:bold' color='green'>%d</font></td>" % pass_cnt \
                  + "<td><font style='font-weight:bold' color='red'>%d</font></td>" % unpass_cnt \
                  + "</tr></table>"
        # 通过用例
        if pass_cnt > 0:
            content += "<br /><h1>通过用例</h1>" \
                       + "<table width='600px' border='1' cellspacing='0' cellpadding='0' " \
                         "style='table-layout:fixed;word-break:break-all;word-wrap:break-word;'><tr align='center'>" \
                       + "<th style='width:500px'>接口</th>" \
                       + "<th style='width:50px'>类型</th>" \
                       + "<th style='width:50px'>时间</th></tr>"
            for item in pass_results:
                uri = item["uri"]
                type_ = item["type"]
                time_ = item["time"]
                content += "<tr><td style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis' " \
                           "title='%s'>%s</td><td align='center'>%s</td>" % (uri, uri, type_)
                if time_ < 1:
                    content += "<td align='center'>%.2f</td></tr>" % time_
                elif 1 <= time_ < 2:
                    content += "<td align='center'><font style='font-weight:bold' color='red'>%.2f</font></td></tr>" \
                               % time_
                else:
                    content += "<td align='center'><font style='font-weight:bold' color='maroon'>%.2f</font></td>" \
                               "</tr>" % time_
            content += "</table>"
        # 未通过用例
        if unpass_cnt > 0:
            content += "<br /><h1>未通过用例</h1>" \
                       + "<table width='750px' border='1' cellspacing='0' cellpadding='0' " \
                         "style='table-layout:fixed;word-break:break-all;word-wrap:break-word;'><tr align='center'>" \
                       + "<th style='width:400px'>接口</th>" \
                       + "<th style='width:50px'>类型</th>" \
                       + "<th style='width:300px'>原因</th>"
            for item in unpass_results:
                uri = item["uri"]
                type_ = item["type"]
                reason = item["reason"]
                content += "<tr><td style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis' " \
                           "title='%s'>%s</td><td align='center'>%s</td>" \
                           "<td style='white-space:nowrap;overflow:hidden;text-overflow:ellipsis' " \
                           "title='%s'>%s</td></tr>" % (uri, uri, type_, reason, reason)
            content += "</table>"
        return content

    def send_mail(self, mailto_list):
        subject = u"NR Spark接口连通性测试结果"
        content = self.__set_content()
        send_mail_obj = send_mail.SendMail("conf/mail.ini", "gmail")
        status = send_mail_obj.send_mail("html", "AUTO BUILD", mailto_list, subject, content)
        if status:
            print "Succeed in sending mails"
        else:
            print "Failed to send mails"
