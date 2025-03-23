# GitHub Paper Trends API

一个自动获取GitHub上最新trending学术论文，并形成摘要newsletter的API服务。

## 功能特点

- 每日自动获取GitHub上trending的学术论文仓库
- 使用AI为每篇论文生成摘要
- 生成格式美观的Markdown格式newsletter
- 提供REST API供其他服务集成
- 简洁的Web界面展示最新论文

## 快速开始

### 前提条件

- Python 3.7+
- OpenAI API密钥（用于生成摘要）

### 安装

1. 克隆仓库

```bash
git clone https://github.com/quentinzhang/github-paper-trends-api.git
cd github-paper-trends-api
```

2. 安装依赖项

```bash
pip install -r requirements.txt
```

3. 设置环境变量

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### 运行

```bash
python app.py
```

现在，API服务将在 http://localhost:8080 上运行。

## API端点

### 获取趋势论文

```
GET /api/trending-papers
```

**参数：**
- `language`（可选）：编程语言
- `since`（可选）：时间范围（daily, weekly, monthly），默认为daily

**响应：**

```json
{
  "count": 5,
  "papers": [
    {
      "author": "username",
      "name": "repo-name",
      "description": "Repository description",
      "url": "https://github.com/username/repo-name",
      "language": "Python",
      "stars": 1200,
      "forks": 150,
      "currentPeriodStars": 50
    },
    ...
  ]
}
```

### 生成论文摘要

```
GET /api/summarize-paper
```

**参数：**
- `repo_url`（必填）：GitHub仓库URL

**响应：**

```json
{
  "repo": {
    "name": "repo-name",
    "author": "username",
    "url": "https://github.com/username/repo-name",
    "description": "Repository description"
  },
  "summary": "AI生成的论文摘要..."
}
```

### 获取最新的newsletter

```
GET /api/newsletter
```

**响应：**

```json
{
  "date": "2025-03-23",
  "papers": [...],
  "newsletter": "# GitHub Trending Academic Papers - 2025-03-23\n..."
}
```

### 下载最新的newsletter

```
GET /api/newsletter/download
```

返回Markdown格式的文件下载。

## 自动化

本项目使用GitHub Actions配置了自动化工作流：

- 每天早上8:00 UTC自动运行，生成最新的论文newsletter
- 自动提交newsletter文件到仓库

## 部署

### 使用Docker

```bash
# 构建Docker镜像
docker build -t github-paper-trends-api .

# 运行容器
docker run -p 8080:8080 -e OPENAI_API_KEY="your-openai-api-key" github-paper-trends-api
```

### 部署到云服务

本项目可以轻松部署到各种云服务平台，例如Heroku、Google Cloud Run、AWS Lambda等。

## 贡献

欢迎贡献！请随时提出问题或提交拉取请求。

## 许可证

MIT