# Bing 搜索 MCP Server

基于 FastMCP 的 Bing 搜索服务，支持自然语言改写搜索和正文提取。

## 功能特性

- ✅ **关键词搜索**：直接使用关键词进行 Bing 搜索
- ✅ **自然语言改写**：将自然语言描述转换为多个关键词进行搜索
- ✅ **正文提取**：使用 readability 提取网页正文，并通过 LLM 生成摘要
- ✅ **Think 标签过滤**：自动过滤 LLM 返回的 `

...` 标签内容
- ✅ **重试机制**：搜索和提取失败自动重试（最多 3 次）
- ✅ **LLM 自评迭代**：提取后让 LLM 判断有效性，无效则重试
- ✅ **优雅关闭**：支持 graceful shutdown
- ✅ **多环境配置**：支持环境变量和本地配置文件

## 项目结构

```
bing_search_mcp/
├─ config.py              # 配置管理
├─ config.yaml.example    # 配置文件示例
├─ CONFIG.md              # 配置说明文档
├─ llm_utils.py           # LLM 工具
├─ search_tools.py        # Bing 搜索 + 正文提取
├─ mcp_server.py          # MCP Server 主入口
├─ requirements.txt       # 依赖列表
├─ tests/                 # 测试文件
└─ README.md              # 项目说明
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置服务

#### 方式一：环境变量配置

**Windows**
```cmd
set BING_SEARCH_LLM_BASE_URL=http://192.168.3.153:11434/v1
set BING_SEARCH_LLM_MODEL=qwen3:14b
set BING_SEARCH_MCP_PORT=8903
```

**Linux**
```bash
export BING_SEARCH_LLM_BASE_URL=http://192.168.3.153:11434/v1
export BING_SEARCH_LLM_MODEL=qwen3:14b
export BING_SEARCH_MCP_PORT=8903
```

#### 方式二：本地配置文件

复制配置文件示例并修改：

```bash
cp config.yaml.example config.yaml
# 编辑 config.yaml 文件
```

### 3. 启动服务

```bash
python mcp_server.py
```

服务将监听 `http://0.0.0.0:8903/sse` 供 MCP Client 连接。

## 工具列表

### 1. search_bing

直接使用关键词进行 Bing 搜索。

```python
@mcp.tool()
async def search_bing(keywords: str, top_k: int = 5) -> list[dict[str, Any]]:
    """
    Bing 关键词搜索并返回详情
    
    Args:
        keywords: 搜索关键词
        top_k: 返回结果数量，默认 5
    
    Returns:
        搜索结果列表，每项包含 title, summary, link, content
    """
```

### 2. search_bing_rewrite

将自然语言描述转换为多个关键词进行搜索。

```python
@mcp.tool()
async def search_bing_rewrite(description: str, rewrite_num: int = 5, top_k: int = 5) -> list[dict[str, Any]]:
    """
    自然语言→多关键词→Bing 搜索并返回合并详情
    
    Args:
        description: 自然语言描述
        rewrite_num: 改写关键词数量，默认 5
        top_k: 返回结果数量，默认 5
    
    Returns:
        搜索结果列表，每项包含 title, summary, link, content
    """
```

## 配置优先级

1. **环境变量**（最高优先级）
2. **本地配置文件**（`config.yaml`）
3. **默认配置**（最低优先级）

## 测试

运行测试套件：

```bash
pytest tests/ -v
```

## 开发说明

### 依赖说明

- `fastmcp`: MCP 协议框架
- `aiohttp`: 异步 HTTP 请求
- `beautifulsoup4`: HTML 解析
- `readability-lxml`: 网页正文提取
- `pyyaml`: YAML 配置文件解析
- `openai`: LLM 调用
- `playwright`: 浏览器自动化（用于复杂网页提取）

### 核心流程

1. **关键词改写**：使用 LLM 将自然语言描述转换为多个关键词
2. **Bing 搜索**：使用关键词进行 Bing 搜索
3. **正文提取**：使用 readability 提取网页正文
4. **LLM 摘要**：使用 LLM 生成简短摘要（≤150 字）
5. **内容验证**：使用 LLM 判断内容有效性，无效则重试

## 许可证

MIT
