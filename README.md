# 功能

- 测试接口返回值与预期是否一致
- 用例支持JSON格式
- 支持GET和POST请求
- 支持测试需要登录的接口
- 登录参数支持动态取值
- 接口参数和POST请求参数支持动态取值
- 测试结果自动发送邮件给指定收件人

# 使用方法

``` python
python main.py -p PATH [-r RECIPIENT]
```

- `-p`是必带参数，`PATH`为测试用例所在路径，如`-p case/example`
- `-r`是选带参数，带此参数测试完成后会将测试结果通过邮件发送给收件人，`RECIPIENT`为收件人，如`-r "recipient1@gmail.com recipient2@gmail.com"`

# 配置参数

- `conf/mail.ini`为发件人邮箱信息
    - host为SMTP服务器地址
    - user为发件人账号（仅用于验证登录信息）
    - passwd为发件人密码（需进行base64处理）
    - name为发件人名称
    - sender为发件人邮箱（可与user不同，如同一公司邮箱拥有多个别名）

# 用例规则

## 命名规则

- 每次测试所用到的用例需要放在同一路径下，建议在case目录下新建文件夹用于存放用例
- 如果用例接口依赖于登录，需要在用例目录下添加login.json文件
- common.json文件用于存储固定的常用字段，供测试用例中的param和data调用。此文件非必须。
- 测试用例必须以“test”开头、以“.json”结尾，例如`testcase_1.json`
- 测试时会按照文件名排序，依次测试

## login.json

login.json格式形如：

``` json
{
  "description": "description of login.json",
  "url": "http://www.xxx.com/login",
  "headers": {
    "User-Agent": "Python by ntflc"
  },
  "data": {
    "email": "test@gmail.com",
    "password": "password",
    "token": {
      "type": "get_value",
      "url": "http://www.xxx.com/get_token",
      "field": "resp_dict['result']['token']"
    }
  }
}
```

- description为选填项，为注释
- url为必填项，其值格式为字符串，为登录接口的地址
- headers为选填项，其值格式为JSON，为请求登录接口时需要附加的headers，暂不支持动态取值
- data为必填项，其值格式为JSON，为请求登录接口时的参数
    - 对于普通参数，如email、password等，键值为字符串
    - 对于动态参数，如token，键值为一个新的JSON
        - 新JSON包括type、url和field
        - type为类型，暂时仅支持get_value
        - url和field代表从url的返回值（需为JSON格式）中取field字段对应的值
        - field遵循Python从字典中取值的格式，名称必须是resp_dict，[]中的值是键名，需要加引号
        - 上述示例表示从`http://www.xxx.com/get_token`的返回值中，取result下token对应的值
- 请求登录接口的返回值和data中的动态参数，会合并为一个JSON，用于后续用例中动态取值

## common.json

common.json格式形如：

``` json
{
  "description": "common.json用于存储固定的常用字段",
  "key1": "value1",
  "key2": "value2",
  "key3": {
    "key3-1": "value3-1",
    "key3-2": "value3-2"
  }
}
```

- 该文件只需要符合JSON格式即可，没有特定的字段要求

## testcase.json

testcase.json格式形如：

``` json
{
  "description": "description of testcase.json",
  "url": "http://www.xxx.com/api/test",
  "param": {
    "id": 1,
    "keyword": "test",
    "token": {
      "type": "get_return",
      "field": "login_return['data']['token']"
    },
    "key3-1": {
      "type": "get_common",
      "field": "common_data['key3']['key3-1']"
    },
    "ts": {
      "type": "get_timestamp",
      "unit": "s",
      "interval": -86400
    },
    "mts": {
      "type": "get_timestamp",
      "unit": "ms",
      "interval": -86400000
    }
  },
  "headers": {
    "User-Agent": "Python by ntflc"
  },
  "type": "POST",
  "data": {
    "id": 1,
    "keyword": "test",
    "token": {
      "type": "get_return",
      "field": "login_return['data']['token']"
    },
    "key3-1": {
      "type": "get_common",
      "field": "common_data['key3']['key3-1']"
    },
    "ts": {
      "type": "get_timestamp",
      "unit": "s",
      "interval": -86400
    },
    "mts": {
      "type": "get_timestamp",
      "unit": "ms",
      "interval": -86400000
    }
  },
  "expect": {
    "status_code": 200,
    "result": {
      "text": "Test passed"
    }
  }
}
```

- description为选填项，为注释
- url为必填项，其值格式为字符串，为测试接口的地址
- param为选填项，其值格式为JSON，为测试接口地址的参数
    - 对于普通参数，如id、page等，键值为字符串或数字
    - 对于动态参数，键值为一个新的JSON
	    - 新JSON包括必填项type，和选填项（视type而定）
	    - type为类型，支持get_return、get_common和get_timestamp
	    - get_return为从登录返回信息中取值（login.json中已经提到），包括必填参数field。field为取值字段，格式与login.json中的field类似，名称必须是login_return
	    - 上述示例的token表示从登录返回信息中取data下token对应的值
	    - get_common为从common.json中取值，包括必填参数field。field取值字段，格式同上，名称必须是common_data
	    - 上述示例的key3-1表示从common.json中取key3下key3-1对应的值
	    - get_timestamp为获取当前时间戳，包括选填项unit和interval。unit为单位，必须是s或ms，无此字段则默认为s；interval为时间差，必须是整数（可正可负），单位与unit一致，无此字段则默认为0
	    - 上述示例的ts、mts表示获取此刻前一天的时间戳，单位分别是秒和毫秒
- headers为选填项，其值格式为JSON，为请求登录接口时需要附加的headers，暂不支持动态取值
- type为必填项，其值格式为字符串，仅支持GET和POST
- data仅在type为POST时有效，其值格式为JSON，为POST请求的参数，规则与param一致
- expect为必填项，其值格式为JSON，为预期结果
    - 对比结果时，只需要预期结果包含于接口返回结果，就认为测试通过
