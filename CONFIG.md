# 配置项说明

## 环境变量配置

### Windows 配置方式

```cmd
set BING_SEARCH_LLM_BASE_URL=http://192.168.3.153:11434/v1
set BING_SEARCH_LLM_MODEL=qwen3:14b
set BING_SEARCH_MCP_PORT=8903
set BING_SEARCH_MAX_RETRY=3
set BING_SEARCH_TOP_K=5
set BING_SEARCH_MAX_TOKEN=150
```

### Linux 配置方式

```bash
export BING_SEARCH_LLM_BASE_URL=http://192.168.3.153:11434/v1
export BING_SEARCH_LLM_MODEL=qwen3:14b
export BING_SEARCH_MCP_PORT=8903
export BING_SEARCH_MAX_RETRY=3
export BING_SEARCH_TOP_K=5
export BING_SEARCH_MAX_TOKEN=150
```

## 本地配置文件

在项目根目录创建 `config.yaml` 文件，配置项优先级高于默认值，但低于环境变量。

```yaml
# 示例配置文件
LLM_BASE_URL: "http://192.168.3.153:11434/v1"
LLM_MODEL: "qwen3:14b"
MCP_PORT: 8903
MAX_RETRY: 3
TOP_K: 5
MAX_TOKEN: 150
```

## 配置项说明

| 配置项 | 环境变量名 | 类型 | 默认值 | 说明 |
|--------|------------|------|--------|------|
| LLM_BASE_URL | BING_SEARCH_LLM_BASE_URL | str | http://192.168.3.153:11434/v1 | LLM 服务地址 |
| LLM_MODEL | BING_SEARCH_LLM_MODEL | str | qwen3:14b | LLM 模型名称 |
| MCP_PORT | BING_SEARCH_MCP_PORT | int | 8903 | MCP Server 监听端口 |
| MAX_RETRY | BING_SEARCH_MAX_RETRY | int | 3 | 搜索和提取失败重试次数 |
| TOP_K | BING_SEARCH_TOP_K | int | 5 | 搜索结果返回数量 |
| MAX_TOKEN | BING_SEARCH_MAX_TOKEN | int | 150 | 摘要最大长度 |
