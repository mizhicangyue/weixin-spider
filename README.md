![](https://img.shields.io/badge/python3-3.7-green.svg)
![](https://img.shields.io/badge/flask-1.0.2-green.svg)
![](https://img.shields.io/badge/weixin-2.6-green.svg)

# weixin-spider

```
 __        __       _    _      _      ____  ___       __       __  
 \ \      / /__  || \\  // ||  //\    //   \|   | ||   ||  __ //  \\
  \ \ /\ / / _ \ ||  \\//  || // \\  //\___ | __/ || __||/ _ \||__//     
   \ V  V /  __/ ||  //\\  ||//   \\//     \|     ||/  ||  __/|| \\
    \_/\_/ \___/ || //  \\ ||/     \/  \___/|     ||\__//\___/||  \\    

```

微信公众号爬虫，公众号历史文章，文章评论，文章阅读及在看数据，可视化web页面，可部署于Windows服务器。

#### 使用环境
```
基于Python3 ==> flask/mysql/redis/mitmproxy/pywin32等实现

查看及安装依赖文件 requirements.txt
    pip install -r requirements.txt

支持操作系统：Windows10 x64
必备软件：WeChat 微信PC版（非微信网页版）

开发环境：Python3.7（Python3.5+）+ DB(MySQL、redis)

```


#### 准备工作

确定使用环境安装完毕的情况下开始这一步，IDE建议使用PyCharm

将使用到默认端口：5000  8080 请确保端口不冲突，或者您可以修改端口

1、确定mysql 、redis服务开启状态
```
# 创建mysql数据库 weixin_spider  字符集utf8mb4
# cd ./webapp/ 运行models.py 生成数据库表
# 查看表结构是否生成正确
```

2、在webapp目录下解压dist.rar静态文件包到webapp目录，解压完成会有static及templates目录

3、使用 不太重要的微信小号 登录微信PC版（使用自己常用的账号登录也没有问题，为你考虑，万一被禁怎么办）。
```
# 登录微信PC版后，找到 文件传输助手 对话框， 双击 文件传输助手 ，文件传输助手会自动弹出单独的对话窗口来，此时及之后就不要关闭了

```

4、依次运行py脚本

```
运行 wx_monitor.py

# 运行 manage.py 打开网页 http://127.0.0.1:5000/   
# flask默认开启端口 5000 可自行修改端口， 默认开启debug

# 成功开启web界面后执行以下

# 在当前tools目录内打开cmd窗口（或cmd切换到tools文件目录内）
# 执行 mitmdump -s ./addons.py 开启miltmproxy代理 默认端口 8080
# 出现以下两行，及成功开启，否则核对错误。 当前cmd下ctrl + c可退出mitmproxy代理
# Loading script ./addons.py
# Proxy server listening at http://*:8080

# 打开系统设置，找到网络里的代理，开启使用代理服务器 地址：127.0.0.1 端口：8080 保存

```

5、完成以上无误后，网页端输入公众号文章链接进行添加公众号，启动或暂停用来控制你的公众号任务

注：
```
对于项目跑不起来及模块加载有问题或模块不存在的情况，建议使用PyCharm启动项目并运行相关脚本

如果发现公众号只爬取部分，请核对使用的微信号是否关注了该公众号，在关注的前提下使用

建议先通过文章链接加载需要爬取的公众号列表，再按需启动，以免IP限制访问详情导致导入公众号失败
```

#### 部署到Windows服务器

按照以上步骤在服务器上安装必要软件及环境后，在项目下依次运行以上步骤，运行成功后即可通过ip或域名进行网页访问


#### 关于更新

整体步骤将不会太大改变，关于音频及视频显示将在后续更新，对于部分单独发布的图片、音频、视频、分享链接的获取也将在后续更新

在tools模块，有部分没有用上，但也实用的功能，可自行按需扩展

想要了解更多对于pywin32操作微信PC版的功能，可访问： https://github.com/xzkzdx/WeChatPC

部分功能将在后续完善