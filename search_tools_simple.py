import asyncio
import requests
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from config import config
from llm_utils import llm_utils


class SearchResult:
    def __init__(self, title: str, summary: str, link: str, content: str = ""):
        self.title = title
        self.summary = summary
        self.link = link
        self.content = content

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "content": self.content
        }


class BingSearchTool:
    def __init__(self):
        pass

    async def init(self):
        # 不需要初始化，直接使用requests
        pass

    async def close(self):
        # 不需要关闭资源
        pass

    async def search_bing(self, keywords: str, top_k: int = 5) -> List[SearchResult]:
        results = []
        
        try:
            # 直接使用requests库访问Bing搜索
            search_url = f"{config.BING_URL}/search?q={keywords}"
            print(f"使用requests访问搜索URL: {search_url}")
            
            # 发送请求
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(search_url, headers=headers, timeout=config.TIMEOUT)
            response.encoding = 'utf-8'
            
            print(f"请求状态码: {response.status_code}")
            
            # 保存页面内容用于调试
            with open("bing_requests.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("已保存requests获取的页面到 bing_requests.html")
            
            # 使用BeautifulSoup解析页面
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 尝试找到搜索结果
            # 搜索结果通常在class为b_algo的div中
            result_divs = soup.find_all("li", class_="b_algo")
            print(f"找到 {len(result_divs)} 个搜索结果")
            
            for result_div in result_divs[:top_k]:
                try:
                    # 提取标题和链接
                    h2 = result_div.find("h2")
                    if not h2:
                        continue
                    
                    a = h2.find("a", href=True)
                    if not a:
                        continue
                    
                    title = a.get_text(strip=True)
                    link = a["href"]
                    
                    # 提取摘要
                    summary = ""
                    p_tag = result_div.find("p")
                    if p_tag:
                        summary = p_tag.get_text(strip=True)
                    
                    # 添加到结果中
                    results.append(SearchResult(title=title, summary=summary, link=link))
                    print(f"添加结果: {title[:30]}...")
                    
                    if len(results) >= top_k:
                        break
                except Exception as e:
                    print(f"解析搜索结果失败: {e}")
                    continue
        except Exception as e:
            print(f"搜索失败: {e}")
        
        # 处理结果，提取内容
        valid_results = []
        for result in results[:top_k]:
            try:
                # 这里可以添加内容提取逻辑
                # 为了简化，我们暂时跳过内容提取
                result.content = "【内容提取暂未实现】"
                valid_results.append(result)
            except Exception as e:
                print(f"处理结果 '{result.title}' 失败: {e}")
                continue
        
        return valid_results

    async def search_bing_rewrite(self, description: str, rewrite_num: int = 5, top_k: int = 5) -> List[SearchResult]:
        keywords_list = llm_utils.rewrite_keywords(description, rewrite_num)
        
        all_results = []
        seen_links = set()
        
        for keywords in keywords_list:
            try:
                results = await self.search_bing(keywords, top_k=10)
                for result in results:
                    if result.link not in seen_links:
                        all_results.append(result)
                        seen_links.add(result.link)
            except Exception as e:
                print(f"搜索关键词 '{keywords}' 失败: {e}")
                continue
        
        return all_results[:top_k]


# 创建全局实例
bing_search_tool = BingSearchTool()
