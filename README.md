### 概述：

该项目是运行在Linux环境下的一个flask应用，作用是为JLink提供远程调试服务。将项目部署在linux设备上在同一局域网下通过浏览器访问`http:服务器Ip:8000`即可浏览所连Jlink信息，在修改在本地调试配置文件之后即可进行无线调试。

### 部署：

1. 复制文件到服务器的项目目录
2. 创建python虚拟环境
3. 安装依赖：`flask,gunicorn`
4. 将bash.sh脚本添加到cron任务

注意将`bash.sh和configurations.py`文件中的路径改为你的路径





