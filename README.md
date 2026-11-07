# InspIRCd for TerraMaster TOS 7 · 4.12.1.1 Beta

在 NAS 本机运行独立 IRC 服务，支持频道和一对一聊天。需要 x86_64、Docker Engine、Compose。一个容器，无数据库、无 Web 入口。仅在宿主回环 127.0.0.1:16667 发布明文 IRC；请勿将此端口转发到公网。共用服务器口令控制加入权限，昵称不是已验证身份。本包不保存历史记录、频道或昵称，也不提供文件传输或跨服互联。

首次安装：在实际 Compose 项目目录创建 .env，已有文件请保留并手动追加变量。通过可信渠道分发口令，仅使用本机客户端。
~~~sh
(umask 077; set -C; printf 'IRC_SECRET=%s\n' "$(openssl rand -hex 32)" > .env)
docker compose up -d
~~~
客户端连接 127.0.0.1:16667，填写服务器密码并选择昵称；两位客户端加入同一频道（例如 #lobby）后即可聊天。服务只接受 64 位小写十六进制配置口令。Docker 管理员可以查看容器环境；不要公开 .env、完整 inspect 或展开后的 Compose 配置。重建后复用 .env；若更换口令，更新 .env 并重新创建容器。停止与移除用 docker compose down，妥善处理保留的 .env。

镜像约 25 MB（压缩），限制 128 MiB、64 个进程，UID 10000，只读根文件系统。安装包只含四个适配文件和自绘图标，不含镜像或上游二进制。[上游 4.12.1 源码](https://github.com/inspircd/inspircd/tree/v4.12.1)、[GPL v2 许可全文](licenses/InspIRCd.txt)、[镜像工程](https://github.com/inspircd/inspircd-docker)、[镜像工程 MIT 许可](licenses/Image-project.md)。Docker Hub 使用上游标签加 linux/amd64 manifest 摘要锁定。

在本目录执行 python3 build.py（需 Ruby/Psych），在 dist 内执行 shasum -a 256 -c SHA256SUMS。test.py 用于专用 Linux Docker 测试主机，要求已拉取固定摘要、容器名和端口空闲。TOS 实机验证为离线 Compose，应用中心安装、卸载及首次 .env 配置时机未验证。
