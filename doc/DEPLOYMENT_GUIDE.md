# 中国象棋AI助手 - 部署指南

## 部署概述

本文档提供了中国象棋AI助手在不同环境下的部署方法，包括本地开发、生产环境和容器化部署。

## 环境要求

### 系统要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+), Windows 10+, macOS 10.15+
- **Python**: 3.7 或更高版本
- **内存**: 最少 2GB RAM，推荐 4GB+
- **存储**: 最少 1GB 可用空间
- **网络**: 稳定的网络连接

### 软件依赖
- Python 3.7+
- OpenCV 4.5+
- Flask 2.0+
- NumPy 1.19+
- 其他依赖见 `requirements.txt`

## 本地开发环境部署

### 1. 环境准备

#### Ubuntu/Debian
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和pip
sudo apt install python3 python3-pip python3-venv -y

# 安装系统依赖
sudo apt install libopencv-dev python3-opencv -y
sudo apt install build-essential cmake pkg-config -y
```

#### CentOS/RHEL
```bash
# 安装Python
sudo yum install python3 python3-pip -y

# 安装开发工具
sudo yum groupinstall "Development Tools" -y
sudo yum install cmake -y

# 安装OpenCV依赖
sudo yum install opencv opencv-devel -y
```

#### Windows
```bash
# 下载并安装Python 3.7+
# 从 https://www.python.org/downloads/ 下载

# 安装Visual Studio Build Tools (用于编译OpenCV)
# 从 https://visualstudio.microsoft.com/downloads/ 下载
```

#### macOS
```bash
# 安装Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装Python
brew install python3

# 安装OpenCV
brew install opencv
```

### 2. 项目部署

```bash
# 1. 克隆项目
git clone <repository-url>
cd chess-helper

# 2. 创建虚拟环境
python3 -m venv venv

# 3. 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 设置环境变量
export FLASK_ENV=development
export FLASK_DEBUG=1

# 6. 运行应用
python run.py
```

### 3. 验证部署

访问 `http://localhost:5000` 检查应用是否正常运行。

## 生产环境部署

### 1. 使用 Gunicorn 部署

#### 安装 Gunicorn
```bash
pip install gunicorn
```

#### 创建 Gunicorn 配置文件
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

#### 启动服务
```bash
gunicorn -c gunicorn.conf.py run:app
```

### 2. 使用 Nginx 反向代理

#### 安装 Nginx
```bash
# Ubuntu/Debian
sudo apt install nginx -y

# CentOS/RHEL
sudo yum install nginx -y
```

#### 配置 Nginx
```nginx
# /etc/nginx/sites-available/chess-helper
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/chess-helper/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    client_max_body_size 10M;
}
```

#### 启用配置
```bash
sudo ln -s /etc/nginx/sites-available/chess-helper /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. 使用 Systemd 管理服务

#### 创建服务文件
```ini
# /etc/systemd/system/chess-helper.service
[Unit]
Description=Chinese Chess AI Helper
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/chess-helper
Environment=PATH=/path/to/chess-helper/venv/bin
ExecStart=/path/to/chess-helper/venv/bin/gunicorn -c gunicorn.conf.py run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable chess-helper
sudo systemctl start chess-helper
sudo systemctl status chess-helper
```

## Docker 容器化部署

### 1. 创建 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    build-essential \
    cmake \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建上传目录
RUN mkdir -p app/uploads

# 设置环境变量
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
```

### 2. 创建 Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  chess-helper:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./app/uploads:/app/app/uploads
      - ./app/json:/app/app/json
    environment:
      - FLASK_ENV=production
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./static:/usr/share/nginx/html/static
    depends_on:
      - chess-helper
    restart: unless-stopped
```

### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 云平台部署

### 1. AWS EC2 部署

#### 创建 EC2 实例
```bash
# 使用 AWS CLI 创建实例
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx
```

#### 配置安全组
- 开放端口 22 (SSH)
- 开放端口 80 (HTTP)
- 开放端口 443 (HTTPS)

#### 部署脚本
```bash
#!/bin/bash
# deploy.sh

# 更新系统
sudo yum update -y

# 安装Python和依赖
sudo yum install python3 python3-pip -y
sudo yum install nginx -y

# 克隆项目
git clone <repository-url>
cd chess-helper

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 配置Nginx
sudo cp nginx.conf /etc/nginx/nginx.conf
sudo systemctl enable nginx
sudo systemctl start nginx

# 配置Systemd服务
sudo cp chess-helper.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chess-helper
sudo systemctl start chess-helper
```

### 2. 阿里云 ECS 部署

#### 创建 ECS 实例
```bash
# 使用阿里云CLI
aliyun ecs CreateInstance \
    --ImageId ubuntu_20_04_64_20G_alibase_20200914.vhd \
    --InstanceType ecs.t5-lc1m1.small \
    --SecurityGroupId sg-xxxxxxxxx
```

#### 部署步骤
```bash
# 连接实例
ssh root@your-instance-ip

# 执行部署脚本
wget -O - https://raw.githubusercontent.com/your-repo/deploy.sh | bash
```

### 3. 腾讯云 CVM 部署

#### 创建 CVM 实例
```bash
# 使用腾讯云CLI
tccli cvm RunInstances \
    --ImageId img-xxxxxxxxx \
    --InstanceType S5.MEDIUM2 \
    --SecurityGroupIds sg-xxxxxxxxx
```

## 性能优化

### 1. 应用层优化

#### 调整 Gunicorn 配置
```python
# 高性能配置
bind = "0.0.0.0:5000"
workers = (2 * cpu_cores) + 1
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

#### 启用缓存
```python
# 使用Redis缓存
import redis
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})
```

### 2. 系统层优化

#### 调整系统参数
```bash
# /etc/sysctl.conf
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.core.netdev_max_backlog = 65535
```

#### 调整文件描述符限制
```bash
# /etc/security/limits.conf
* soft nofile 65535
* hard nofile 65535
```

### 3. 数据库优化（如果使用）

```python
# 连接池配置
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True
}
```

## 监控和日志

### 1. 日志配置

#### 应用日志
```python
# logging.conf
[loggers]
keys=root,chess_helper

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_chess_helper]
level=INFO
handlers=consoleHandler,fileHandler
qualname=chess_helper
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=simpleFormatter
args=('logs/chess_helper.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### 2. 监控配置

#### 使用 Prometheus + Grafana
```python
# 添加监控端点
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('http_requests_total', 'Total HTTP requests')
request_latency = Histogram('http_request_duration_seconds', 'HTTP request latency')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

## 安全配置

### 1. HTTPS 配置

#### 使用 Let's Encrypt
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. 防火墙配置

```bash
# 使用 UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. 应用安全

```python
# 添加安全头
from flask_talisman import Talisman

Talisman(app, 
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'"
    }
)
```

## 备份和恢复

### 1. 数据备份

```bash
#!/bin/bash
# backup.sh

# 备份上传文件
tar -czf backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz app/uploads/

# 备份配置文件
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz app/json/

# 备份数据库（如果有）
mysqldump -u username -p database_name > backups/db_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 自动备份

```bash
# 添加到 crontab
0 2 * * * /path/to/backup.sh
```

## 故障排除

### 1. 常见问题

#### 端口被占用
```bash
# 查看端口占用
sudo netstat -tlnp | grep :5000

# 杀死进程
sudo kill -9 <PID>
```

#### 权限问题
```bash
# 修复权限
sudo chown -R www-data:www-data /path/to/chess-helper
sudo chmod -R 755 /path/to/chess-helper
```

#### 内存不足
```bash
# 查看内存使用
free -h

# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 2. 日志分析

```bash
# 查看应用日志
tail -f logs/chess_helper.log

# 查看系统日志
sudo journalctl -u chess-helper -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/access.log
```

## 更新和维护

### 1. 应用更新

```bash
#!/bin/bash
# update.sh

# 备份当前版本
cp -r /path/to/chess-helper /path/to/backup/chess-helper_$(date +%Y%m%d_%H%M%S)

# 拉取最新代码
cd /path/to/chess-helper
git pull origin main

# 更新依赖
source venv/bin/activate
pip install -r requirements.txt

# 重启服务
sudo systemctl restart chess-helper
```

### 2. 定期维护

```bash
# 清理日志文件
find /path/to/logs -name "*.log" -mtime +30 -delete

# 清理上传文件
find /path/to/app/uploads -name "*.png" -mtime +7 -delete

# 更新系统包
sudo apt update && sudo apt upgrade -y
```

---

这个部署指南涵盖了从本地开发到生产环境的完整部署流程，包括容器化、云平台部署、性能优化、监控和安全配置等方面。根据具体需求选择合适的部署方式。 