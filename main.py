#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse
from utils import log_in
from utils import read_case
from utils import interface

# 全局使用UTF-8编码
reload(sys)
sys.setdefaultencoding("utf-8")


def main():
    # 新增选项-p或--path，为测试用例所在的路径
    # 新增选项-r或--recipient，为收件人邮箱，多个邮箱用空格隔开
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", required=True, help="Path of test cases")
    parser.add_argument("-r", "--recipient", required=False, help="Email recipients")
    args = parser.parse_args()
    case_path = args.path
    recipient = args.recipient
    # 通过接口登录并获取登录cookie和返回值
    login_obj = log_in.LogInByInterface(case_path)
    cookie, login_return = login_obj.get_data()
    # 读取测试用例
    case_obj = read_case.ReadTestCase(case_path, login_return)
    case_list = case_obj.get_data()
    # 接口可用性测试
    interface_obj = interface.InterfaceTest(case_list, cookie)
    results = interface_obj.get_results()
    for result in results:
        print result
    # 发送邮件
    if recipient is not None:
        recipient_list = recipient.split()
        send_mail_obj = interface.SendResultByMail(results)
        send_mail_obj.send_mail(recipient_list)


if __name__ == "__main__":
    main()
