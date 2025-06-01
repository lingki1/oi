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
为镜像打标签 (Tag)
您的本地镜像名称是 open-webui，标签是 latest。在推送到 Docker Hub 之前，您需要给它打上一个符合 Docker Hub 命名规范的标签：<您的 Docker Hub 用户名>/<仓库名>:<标签>。

docker tag open-webui:latest <您的 Docker Hub 用户名>/open-webui:latest

```bash
# 推送所有标签
docker push yourusername/open-webui:latest
docker push yourusername/open-webui:v1.0.0
docker push yourusername/open-webui:no-ollama
# 推送标签镜像
docker push <您的 Docker Hub 用户名>/open-webui:latest

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

### 5.3 Docker数据卷说明

#### 5.3.1 官方推荐的数据卷配置

根据Open WebUI官方文档 <mcreference link="https://docs.openwebui.com/getting-started/quick-start/" index="2">2</mcreference>，推荐使用以下数据卷配置：

```bash
# 官方推荐：使用命名卷（Named Volume）
docker run -d -p 3000:8080 -v open-webui:/app/backend/data --name open-webui ghcr.io/open-webui/open-webui:main
```

#### 5.3.2 数据卷的作用和重要性

**数据持久化存储**：`-v open-webui:/app/backend/data` 参数的作用是：<mcreference link="https://docs.openwebui.com/getting-started/quick-start/" index="2">2</mcreference>
- **确保数据持久化**：防止容器重启或删除时数据丢失
- **自动数据恢复**：当使用相同的卷名重新启动容器时，会自动加载之前保存的所有数据
- **包含的数据类型**：
  - 聊天历史记录
  - 用户配置和设置
  - 上传的文档和文件
  - 数据库文件
  - 自定义模型配置

#### 5.3.3 两种数据卷配置方式

**方式一：命名卷（推荐）**
```bash
# 使用Docker管理的命名卷
-v open-webui:/app/backend/data
```

**优点**：
- Docker自动管理存储位置
- 跨平台兼容性好
- 自动处理权限问题
- 便于备份和迁移

**方式二：绑定挂载**
```bash
# 绑定到主机特定目录
-v /opt/open-webui/data:/app/backend/data
```

**优点**：
- 直接访问主机文件系统
- 便于手动备份
- 可以直接编辑配置文件

#### 5.3.4 数据卷位置查看

```bash
# 查看命名卷详细信息
docker volume inspect open-webui

# 查看所有卷
docker volume ls

# 在不同系统中的存储位置：
# Linux: /var/lib/docker/volumes/open-webui/_data
# Windows (WSL2): \\wsl$\docker-desktop\mnt\docker-desktop-disk\data\docker\volumes\open-webui\_data
# macOS: ~/Library/Containers/com.docker.docker/Data/vms/0/data/docker/volumes/open-webui/_data
```

### 5.4 运行容器

#### 基础运行

**方式一：使用命名卷（官方推荐）**
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

**方式二：使用绑定挂载**
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -v /opt/open-webui/data:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

#### 连接外部Ollama服务

**使用命名卷（推荐）**
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://your-ollama-server:11434 \
  -v open-webui:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

**使用绑定挂载**
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

**使用命名卷（推荐）**
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OPENAI_API_KEY=your-openai-api-key \
  -e OPENAI_API_BASE_URL=https://api.openai.com/v1 \
  -v open-webui:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

#### 完整配置示例

**使用命名卷（推荐）**
```bash
docker run -d \
  --name open-webui \
  -p 3000:8080 \
  -e OLLAMA_BASE_URL=http://localhost:11434 \
  -e OPENAI_API_KEY=your-openai-api-key \
  -e WEBUI_SECRET_KEY=your-secret-key \
  -e WEBUI_AUTH=True \
  -v open-webui:/app/backend/data \
  --restart unless-stopped \
  yourusername/open-webui:latest
```

### 5.5 使用Docker Compose（推荐）

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

### 5.6 配置反向代理（可选）

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

## 7. 数据卷推送和拉取教程

### 7.1 数据卷备份和导出

#### 7.1.1 备份命名卷到本地文件

```bash
# 备份命名卷（推荐方式）
docker run --rm \
  -v open-webui:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/open-webui-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Windows PowerShell版本
docker run --rm `
  -v open-webui:/data `
  -v ${PWD}:/backup `
  alpine tar czf /backup/open-webui-backup-$(Get-Date -Format "yyyyMMdd-HHmmss").tar.gz -C /data .
```

#### 7.1.2 备份绑定挂载目录

```bash
# 如果使用绑定挂载，直接压缩目录
tar czf open-webui-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /opt/open-webui/data .

# Windows版本
Compress-Archive -Path "C:\opt\open-webui\data\*" -DestinationPath "open-webui-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss').zip"
```

### 7.2 数据卷恢复和导入

#### 7.2.1 从备份文件恢复到命名卷

```bash
# 创建新的命名卷（如果不存在）
docker volume create open-webui

# 从备份文件恢复数据
docker run --rm \
  -v open-webui:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/open-webui-backup-20231201-143000.tar.gz -C /data

# Windows PowerShell版本
docker run --rm `
  -v open-webui:/data `
  -v ${PWD}:/backup `
  alpine tar xzf /backup/open-webui-backup-20231201-143000.tar.gz -C /data
```

#### 7.2.2 恢复到绑定挂载目录

```bash
# 创建目录（如果不存在）
sudo mkdir -p /opt/open-webui/data

# 恢复数据
tar xzf open-webui-backup-20231201-143000.tar.gz -C /opt/open-webui/data

# Windows版本
Expand-Archive -Path "open-webui-backup-20231201-143000.zip" -DestinationPath "C:\opt\open-webui\data"
```

### 7.3 跨服务器数据迁移

#### 7.3.1 从源服务器导出数据

```bash
# 在源服务器上备份数据
docker run --rm \
  -v open-webui:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/migration-$(date +%Y%m%d).tar.gz -C /data .

# 将备份文件传输到目标服务器
scp migration-20231201.tar.gz user@target-server:/tmp/
```

#### 7.3.2 在目标服务器导入数据

```bash
# 在目标服务器上创建卷并导入数据
docker volume create open-webui

docker run --rm \
  -v open-webui:/data \
  -v /tmp:/backup \
  alpine tar xzf /backup/migration-20231201.tar.gz -C /data
```

### 7.4 数据卷同步和推送

#### 7.4.1 使用rsync同步数据

```bash
# 同步到远程服务器（绑定挂载方式）
rsync -avz --progress /opt/open-webui/data/ user@remote-server:/opt/open-webui/data/

# 从远程服务器同步
rsync -avz --progress user@remote-server:/opt/open-webui/data/ /opt/open-webui/data/
```

#### 7.4.2 使用Docker Registry推送数据卷镜像

```bash
# 创建包含数据的镜像
docker run --rm \
  -v open-webui:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/data.tar.gz -C /data .

# 创建数据镜像的Dockerfile
cat > Dockerfile.data << EOF
FROM alpine:latest
COPY data.tar.gz /
CMD ["tar", "xzf", "/data.tar.gz", "-C", "/data"]
EOF

# 构建数据镜像
docker build -f Dockerfile.data -t yourusername/open-webui-data:latest .

# 推送数据镜像
docker push yourusername/open-webui-data:latest
```

#### 7.4.3 从Registry拉取数据卷

```bash
# 拉取数据镜像
docker pull yourusername/open-webui-data:latest

# 创建卷并导入数据
docker volume create open-webui

docker run --rm \
  -v open-webui:/data \
  yourusername/open-webui-data:latest
```

### 7.5 自动化数据卷管理脚本

#### 7.5.1 备份脚本

```bash
#!/bin/bash
# backup-volume.sh

VOLUME_NAME="open-webui"
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${VOLUME_NAME}-backup-${DATE}.tar.gz"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据卷
docker run --rm \
  -v ${VOLUME_NAME}:/data \
  -v ${BACKUP_DIR}:/backup \
  alpine tar czf /backup/${VOLUME_NAME}-backup-${DATE}.tar.gz -C /data .

echo "备份完成: $BACKUP_FILE"

# 清理7天前的备份
find $BACKUP_DIR -name "${VOLUME_NAME}-backup-*.tar.gz" -mtime +7 -delete
```

#### 7.5.2 恢复脚本

```bash
#!/bin/bash
# restore-volume.sh

if [ $# -ne 2 ]; then
    echo "用法: $0 <备份文件> <卷名称>"
    echo "示例: $0 /opt/backups/open-webui-backup-20231201-143000.tar.gz open-webui"
    exit 1
fi

BACKUP_FILE=$1
VOLUME_NAME=$2

if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

# 创建卷（如果不存在）
docker volume create $VOLUME_NAME

# 恢复数据
docker run --rm \
  -v ${VOLUME_NAME}:/data \
  -v $(dirname $BACKUP_FILE):/backup \
  alpine tar xzf /backup/$(basename $BACKUP_FILE) -C /data

echo "恢复完成: $VOLUME_NAME"
```

### 7.6 数据卷管理最佳实践

#### 7.6.1 定期备份策略

```bash
# 添加到crontab进行定期备份
# 每天凌晨2点备份
0 2 * * * /opt/scripts/backup-volume.sh

# 每周日凌晨3点同步到远程服务器
0 3 * * 0 rsync -avz /opt/backups/ user@backup-server:/opt/open-webui-backups/
```

#### 7.6.2 数据验证

```bash
# 验证备份文件完整性
tar tzf open-webui-backup-20231201-143000.tar.gz > /dev/null && echo "备份文件完整" || echo "备份文件损坏"

# 检查数据卷大小
docker system df -v | grep open-webui
```

#### 7.6.3 安全注意事项

- **加密备份**: 对敏感数据进行加密备份
- **访问控制**: 限制备份文件的访问权限
- **网络传输**: 使用安全的传输方式（SSH、HTTPS）
- **存储位置**: 将备份存储在不同的物理位置

```bash
# 加密备份示例
gpg --symmetric --cipher-algo AES256 open-webui-backup-20231201.tar.gz

# 解密备份
gpg --decrypt open-webui-backup-20231201.tar.gz.gpg > open-webui-backup-20231201.tar.gz
```

---

## 8. 故障排除

### 8.1 常见问题

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

### 8.2 性能优化

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

### 8.3 监控和日志

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

## 9. 自动化脚本

### 9.1 构建和推送脚本

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

### 9.2 VPS部署脚本

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

### 9.3 备份脚本

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

## 10. 安全建议

### 10.1 基础安全配置

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

### 10.2 Docker安全

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

## 11. 结语

本教程涵盖了Open WebUI Docker部署的完整流程，从本地构建到生产环境部署。根据您的具体需求，可以选择相应的配置选项。

### 快速参考

- **本地测试**: `docker run -d -p 3000:8080 open-webui:latest`
- **生产部署**: 使用Docker Compose + Nginx + SSL
- **更新**: 拉取新镜像 → 停止旧容器 → 启动新容器
- **备份**: 定期备份数据卷
- **监控**: 查看容器日志和系统资源

如有问题，请参考故障排除章节或查看项目文档。