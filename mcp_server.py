import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any
from fastmcp import FastMCP
from config import config
from search_tools import bing_search_tool


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    await bing_search_tool.init()
    yield
    await bing_search_tool.close()


mcp = FastMCP("Bing Search MCP Server", lifespan=lifespan)


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
    results = await bing_search_tool.search_bing(keywords, top_k)
    return [result.to_dict() for result in results]


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
    results = await bing_search_tool.search_bing_rewrite(description, rewrite_num, top_k)
    return [result.to_dict() for result in results]


def main():
    import uvicorn
    
    def signal_handler(sig, frame):
        print("\n正在关闭服务...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print(f"启动 Bing 搜索 MCP Server...")
    print(f"监听端口: {config.MCP_PORT}")
    print(f"LLM 地址: {config.LLM_BASE_URL}")
    print(f"LLM 模型: {config.LLM_MODEL}")
    
    # 输出调用MCP所需的配置参数
    import json
    config_params = {
        "mcpServers": {
            "bing": {
                "url": f"http://localhost:{config.MCP_PORT}/mcp"
            }
        }
    }
    print(f"MCP 配置参数:")
    print(json.dumps(config_params, indent=2, ensure_ascii=False))
    
    # 使用streamable-http传输协议，配置为仅返回JSON响应，避免406错误
    app = mcp.http_app(
        path="/mcp",
        transport="streamable-http",
        json_response=True,
        stateless_http=True
    )
    uvicorn.run(app, host="0.0.0.0", port=config.MCP_PORT)


if __name__ == "__main__":
    main()
