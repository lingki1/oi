# Open WebUI Docker 完整部署教程

本教程将指导您完成从构建Docker镜像到VPS部署的完整流程。

## 目录
1. [本地Docker镜像构建](#1-本地docker镜像构建)
2. [镜像标签管理](#2-镜像标签管理)
3. [上传到Docker Hub](#3-上传到docker-hub)
4. [VPS Ubuntu安装Docker](#4-vps-ubuntu安装docker)
5. [VPS拉取和运行镜像](#5-vps拉取和运行镜像)
6. [常用命令参考](#6-常用命令参考)
7. [故障排除](#7-故障排除)

---

## 1. 本地Docker镜像构建

### 1.1 准备工作

确保您已安装Docker Desktop（Windows/Mac）或Docker Engine（Linux）。

```bash
# 检查Docker版本
docker --version
docker-compose --version
```

### 1.2 构建不包含Ollama的镜像

在项目根目录执行以下命令：

```bash
# 基础构建（不包含Ollama，CPU版本）
docker build --build-arg USE_OLLAMA=false -t open-webui:latest .

# 构建CUDA版本（如果需要GPU支持）
docker build --build-arg USE_OLLAMA=false --build-arg USE_CUDA=true -t open-webui:cuda .

# 自定义嵌入模型
docker build \
  --build-arg USE_OLLAMA=false \
  --build-arg USE_EMBEDDING_MODEL=intfloat/multilingual-e5-base \
  -t open-webui:custom .
```

### 1.3 验证构建结果

```bash
# 查看构建的镜像
docker images | grep open-webui

# 测试运行
docker run -d -p 3000:8080 --name test-webui open-webui:latest

# 检查容器状态
docker ps

# 访问测试（浏览器打开 http://localhost:3000）
# 测试完成后停止并删除容器
docker stop test-webui
docker rm test-webui
```

---

## 2. 镜像标签管理

### 2.1 为镜像添加标签

```bash
# 基础标签
docker tag open-webui:latest yourusername/open-webui:latest
docker tag open-webui:latest yourusername/open-webui:v1.0.0
docker tag open-webui:latest yourusername/open-webui:no-ollama

# 如果构建了CUDA版本
docker tag open-webui:cuda yourusername/open-webui:cuda
docker tag open-webui:cuda yourusername/open-webui:v1.0.0-cuda
```

### 2.2 查看所有标签

```bash
docker images yourusername/open-webui
```

---

## 3. 上传到Docker Hub

### 3.1 创建Docker Hub账户

1. 访问 [Docker Hub](https://hub.docker.com/)
2. 注册账户
3. 创建仓库（可选，推送时会自动创建）

### 3.2 登录Docker Hub

```bash
# 登录
docker login
# 输入用户名和密码
```

### 3.3 推送镜像

```bash
# 推送所有标签
docker push yourusername/open-webui:latest
docker push yourusername/open-webui:v1.0.0
docker push yourusername/open-webui:no-ollama

# 如果有CUDA版本
docker push yourusername/open-webui:cuda
docker push yourusername/open-webui:v1.0.0-cuda
```

### 3.4 验证上传

访问 `https://hub.docker.com/r/yourusername/open-webui` 查看上传的镜像。

---

## 4. VPS Ubuntu安装Docker

### 4.1 连接到VPS

```bash
# SSH连接到VPS
ssh username@your-vps-ip
```

### 4.2 更新系统

```bash
# 更新包列表
sudo apt update
sudo apt upgrade -y
```

### 4.3 安装Docker

#### 方法一：使用官方安装脚本（推荐）

```bash
# 下载并运行Docker安装脚本
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 将当前用户添加到docker组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使组权限生效
newgrp docker
```

#### 方法二：手动安装

```bash
# 安装必要的包
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加Docker仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 更新包列表并安装Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 将用户添加到docker组
sudo usermod -aG docker $USER
newgrp docker
```

### 4.4 验证Docker安装

```bash
# 检查Docker版本
docker --version
docker compose version

# 运行测试容器
docker run hello-world

# 启用Docker服务开机自启
sudo systemctl enable docker
sudo systemctl start docker
```

### 4.5 安装Docker Compose（如果需要）

```bash
# 下载Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 添加执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

---

## 5. VPS拉取和运行镜像

### 5.1 拉取镜像

```bash
# 拉取最新版本
docker pull yourusername/open-webui:latest

# 或拉取特定版本
docker pull yourusername/open-webui:v1.0.0

# 验证镜像
docker images | grep open-webui
```

### 5.2 创建数据目录

```bash
# 创建数据持久化目录
sudo mkdir -p /opt/open-webui/data
sudo chown $USER:$USER /opt/open-webui/data
```

### 5.3 运行容器

#### 基础运行

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

#### 连接外部Ollama服务

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://your-ollama-server:11434 \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

#### 使用OpenAI API

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OPENAI_API_KEY=your-openai-api-key \
  -e OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

#### 完整配置示例

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://localhost:11434 \
  -e OPENAI_API_KEY=your-openai-api-key \
  -e WEBUI_SECRET_KEY=your-secret-key \
  -e WEBUI_AUTH=True \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

### 5.4 使用Docker Compose（推荐）

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  open-webui:
    image: yourusername/open-webui:latest
    container_name: open-webui
    ports:
      - "3000:8080"
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_SECRET_KEY=your-secret-key
      - WEBUI_AUTH=True
    volumes:
      - ./data:/app/backend/data
    restart: unless-stopped
    depends_on:
      - ollama

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ./ollama:/root/.ollama
    restart: unless-stopped

volumes:
  data:
  ollama:
```

运行：

```bash
# 启动服务
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 5.5 配置反向代理（可选）

#### 使用Nginx

```bash
# 安装Nginx
sudo apt install -y nginx

# 创建配置文件
sudo nano /etc/nginx/sites-available/open-webui
```

添加以下配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用配置：

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/open-webui /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

#### 配置SSL（使用Let's Encrypt）

```bash
# 安装Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 6. 常用命令参考

### 6.1 容器管理

```bash
# 查看运行中的容器
docker ps

# 查看所有容器
docker ps -a

# 查看容器日志
docker logs open-webui
docker logs -f open-webui  # 实时查看

# 进入容器
docker exec -it open-webui bash

# 停止容器
docker stop open-webui

# 启动容器
docker start open-webui

# 重启容器
docker restart open-webui

# 删除容器
docker rm open-webui
```

### 6.2 镜像管理

```bash
# 查看本地镜像
docker images

# 删除镜像
docker rmi yourusername/open-webui:latest

# 清理未使用的镜像
docker image prune

# 清理所有未使用的资源
docker system prune -a
```

### 6.3 数据备份

```bash
# 备份数据卷
docker run --rm -v /opt/open-webui/data:/data -v $(pwd):/backup alpine tar czf /backup/open-webui-backup.tar.gz -C /data .

# 恢复数据
docker run --rm -v /opt/open-webui/data:/data -v $(pwd):/backup alpine tar xzf /backup/open-webui-backup.tar.gz -C /data
```

### 6.4 更新镜像

```bash
# 拉取最新镜像
docker pull yourusername/open-webui:latest

# 停止并删除旧容器
docker stop open-webui
docker rm open-webui

# 运行新容器
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

---

## 7. 故障排除

### 7.1 常见问题

#### 容器无法启动

```bash
# 查看详细错误信息
docker logs open-webui

# 检查端口占用
sudo netstat -tlnp | grep :3000

# 检查磁盘空间
df -h
```

#### 无法访问Web界面

```bash
# 检查容器状态
docker ps

# 检查防火墙设置
sudo ufw status
sudo ufw allow 3000

# 检查端口映射
docker port open-webui
```

#### 内存不足

```bash
# 查看系统资源使用
free -h
docker stats

# 限制容器内存使用
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  --memory=2g \
  -v /opt/open-webui/data:/app/backend/data \
  yourusername/open-webui:latest
```

### 7.2 性能优化

#### 启用Docker日志轮转

创建 `/etc/docker/daemon.json`：

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

重启Docker：

```bash
sudo systemctl restart docker
```

#### 配置资源限制

```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  --cpus="2.0" \
  --memory="4g" \
  --memory-swap="6g" \
  -v /opt/open-webui/data:/app/backend/data \
  yourusername/open-webui:latest
```

### 7.3 监控和日志

#### 设置日志监控

```bash
# 安装日志查看工具
sudo apt install -y multitail

# 实时监控多个日志
multitail -f /var/log/nginx/access.log -f /var/log/nginx/error.log
```

#### 容器健康检查

```bash
# 查看容器健康状态
docker inspect --format='{{.State.Health.Status}}' open-webui

# 手动健康检查
curl -f http://localhost:3000/health || echo "Health check failed"
```

---

## 8. 自动化脚本

### 8.1 构建和推送脚本

创建 `build-and-push.sh`：

```bash
#!/bin/bash

# 配置变量
IMAGE_NAME="open-webui"
DOCKER_USERNAME="yourusername"
VERSION="v1.0.0"

# 构建镜像
echo "构建镜像..."
docker build --build-arg USE_OLLAMA=false -t ${IMAGE_NAME}:latest .

# 打标签
echo "添加标签..."
docker tag ${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker tag ${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
docker tag ${IMAGE_NAME}:latest ${DOCKER_USERNAME}/${IMAGE_NAME}:no-ollama

# 推送镜像
echo "推送镜像到Docker Hub..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:latest
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${VERSION}
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:no-ollama

echo "完成！镜像已推送到 ${DOCKER_USERNAME}/${IMAGE_NAME}"
```

### 8.2 VPS部署脚本

创建 `deploy.sh`：

```bash
#!/bin/bash

# 配置变量
IMAGE_NAME="yourusername/open-webui:latest"
CONTAINER_NAME="open-webui"
DATA_DIR="/opt/open-webui/data"
PORT="3000"

# 创建数据目录
echo "创建数据目录..."
sudo mkdir -p ${DATA_DIR}
sudo chown $USER:$USER ${DATA_DIR}

# 停止并删除旧容器
echo "停止旧容器..."
docker stop ${CONTAINER_NAME} 2>/dev/null || true
docker rm ${CONTAINER_NAME} 2>/dev/null || true

# 拉取最新镜像
echo "拉取最新镜像..."
docker pull ${IMAGE_NAME}

# 运行新容器
echo "启动新容器..."
docker run -d \
  --name ${CONTAINER_NAME} \
  -p ${PORT}:8080 \
  -v ${DATA_DIR}:/app/backend/data \
  --restart unless-stopped \
  ${IMAGE_NAME}

# 检查容器状态
echo "检查容器状态..."
sleep 5
docker ps | grep ${CONTAINER_NAME}

echo "部署完成！访问 http://$(curl -s ifconfig.me):${PORT}"
```

### 8.3 备份脚本

创建 `backup.sh`：

```bash
#!/bin/bash

# 配置变量
DATA_DIR="/opt/open-webui/data"
BACKUP_DIR="/opt/backups/open-webui"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="open-webui-backup-${DATE}.tar.gz"

# 创建备份目录
mkdir -p ${BACKUP_DIR}

# 创建备份
echo "创建备份: ${BACKUP_FILE}"
tar -czf ${BACKUP_DIR}/${BACKUP_FILE} -C ${DATA_DIR} .

# 保留最近7天的备份
find ${BACKUP_DIR} -name "open-webui-backup-*.tar.gz" -mtime +7 -delete

echo "备份完成: ${BACKUP_DIR}/${BACKUP_FILE}"
```

---

## 9. 安全建议

### 9.1 基础安全配置

```bash
# 配置防火墙
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000  # 如果不使用反向代理

# 禁用root登录
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# 设置自动安全更新
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 9.2 Docker安全

```bash
# 以非root用户运行容器
docker run -d \
  --name open-webui \
  --user 1000:1000 \
  -p 3000:8080 \
  -v /opt/open-webui/data:/app/backend/data \
  yourusername/open-webui:latest

# 限制容器权限
docker run -d \
  --name open-webui \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  --read-only \
  --tmpfs /tmp \
  -p 3000:8080 \
  -v /opt/open-webui/data:/app/backend/data \
  yourusername/open-webui:latest
```

---

## 10. 结语

本教程涵盖了Open WebUI Docker部署的完整流程，从本地构建到生产环境部署。根据您的具体需求，可以选择相应的配置选项。

### 快速参考

- **本地测试**: `docker run -d -p 3000:8080 open-webui:latest`
- **生产部署**: 使用Docker Compose + Nginx + SSL
- **更新**: 拉取新镜像 → 停止旧容器 → 启动新容器
- **备份**: 定期备份数据卷
- **监控**: 查看容器日志和系统资源

如有问题，请参考故障排除章节或查看项目文档。