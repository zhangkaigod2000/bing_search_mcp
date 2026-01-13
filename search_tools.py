import asyncio
import requests
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from readability import Document
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
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page_pool: List[Page] = []  # 页面池，用于复用页面
        self.active_pages: Set[Page] = set()  # 正在使用的页面
        self.max_pages = config.MAX_PAGES  # 最大页面数量

    async def init(self):
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            # 优化浏览器启动配置
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-gpu",
                    "--disable-extensions",
                    "--disable-features=NetworkService",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

    async def close(self):
        # 关闭所有页面
        for page in self.page_pool:
            await page.close()
        for page in self.active_pages:
            await page.close()
        # 关闭上下文和浏览器
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _get_page(self, max_retries: int = 10) -> Page:
        if not self.context:
            await self.init()
        
        # 优先从页面池获取可用页面
        if self.page_pool:
            page = self.page_pool.pop()
            self.active_pages.add(page)
            return page
        
        # 获取当前浏览器上下文的实际页面数量
        def get_current_page_count():
            """获取当前浏览器上下文的实际页面数量"""
            # Playwright的BrowserContext没有直接的页面数量属性，我们需要通过active_pages和page_pool来计算
            return len(self.active_pages) + len(self.page_pool)
        
        # 如果未达到最大页面数量，创建新页面
        if get_current_page_count() < self.max_pages:
            page = await self.context.new_page()
            self.active_pages.add(page)
            return page
        
        # 如果已达到最大页面数量，等待并复用
        # 这里采用简单的等待机制，实际生产环境可以考虑使用队列或事件
        if max_retries > 0:
            await asyncio.sleep(0.5)  # 等待0.5秒后重试，减少等待时间
            return await self._get_page(max_retries - 1)
        else:
            # 达到最大重试次数，返回一个错误或创建新页面
            # 这里我们选择直接创建新页面，避免无限等待
            print("已达到最大重试次数，创建新页面")
            page = await self.context.new_page()
            self.active_pages.add(page)
            return page
        
    async def _release_page(self, page: Page):
        """释放页面，将其放回页面池或关闭"""
        if page in self.active_pages:
            self.active_pages.remove(page)
            
            # 如果页面池未满，将页面放回页面池
            if len(self.page_pool) < self.max_pages:
                try:
                    # 重置页面状态
                    await page.goto("about:blank")
                    await page.wait_for_load_state("load")
                    self.page_pool.append(page)
                except Exception as e:
                    # 重置失败，关闭页面
                    print(f"重置页面失败，关闭页面: {e}")
                    await page.close()
            else:
                # 页面池已满，关闭页面
                await page.close()

    def _search_bing_with_requests(self, keywords: str, top_k: int = 5) -> List[SearchResult]:
        """使用requests库直接发送HTTP请求搜索Bing"""
        results = []
        try:
            # 过滤无效字符，只保留有效的搜索关键词
            # 移除#、*、"等特殊字符，只保留中文、英文、数字和常用标点
            import re
            filtered_keywords = re.sub(r'[#*"<>|%^&\(\)\[\]{}\\|]+', '', keywords)
            filtered_keywords = filtered_keywords.strip()
            print(f"过滤后的关键词: {filtered_keywords}")
            
            search_url = f"{config.BING_URL}/search?q={filtered_keywords}"
            print(f"使用requests访问搜索URL: {search_url}")
            
            # 设置headers模拟浏览器
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
            
            # 发送请求
            response = requests.get(search_url, headers=headers, timeout=config.TIMEOUT)
            response.raise_for_status()
            
            # 保存页面内容用于调试
            with open("bing_requests_page.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print("已保存requests搜索页面HTML到 bing_requests_page.html")
            
            # 使用BeautifulSoup解析页面
            soup = BeautifulSoup(response.text, "lxml")
            
            # 尝试多种方式提取搜索结果
            result_containers = []
            
            # 方法1：使用Bing特有的class
            result_containers.extend(soup.find_all(class_="b_algo"))
            
            # 方法2：查找包含h2和链接的div
            for div in soup.find_all("div"):
                h2 = div.find("h2")
                if h2 and h2.find("a"):
                    result_containers.append(div)
            
            print(f"找到 {len(result_containers)} 个搜索结果容器")
            
            # 遍历结果容器
            seen_links = set()
            for container in result_containers:
                try:
                    # 提取标题和链接
                    h2 = container.find("h2")
                    if not h2:
                        continue
                    
                    link = h2.find("a")
                    if not link:
                        continue
                    
                    title = link.get_text(strip=True)
                    href = link.get("href")
                    
                    if not href or not href.startswith("http") or len(title) < 5:
                        continue
                    
                    # 避免重复链接
                    if href in seen_links:
                        continue
                    seen_links.add(href)
                    
                    # 提取摘要
                    summary = ""
                    # 查找第一个p标签作为摘要
                    p_tag = container.find("p")
                    if p_tag:
                        summary = p_tag.get_text(strip=True)[:150]
                    
                    # 添加到结果
                    results.append(SearchResult(title=title, summary=summary, link=href))
                    print(f"添加结果: {title[:30]}...")
                    
                    if len(results) >= top_k:
                        break
                except Exception as e:
                    print(f"处理单个结果失败: {e}")
                    continue
        except Exception as e:
            print(f"requests搜索失败: {e}")
        
        return results
    
    async def search_bing(self, keywords: str, top_k: int = 5) -> List[SearchResult]:
        """搜索Bing，先尝试Playwright，失败则使用requests"""
        results = []
        
        # 过滤无效字符，只保留有效的搜索关键词
        # 移除#、*、"等特殊字符，只保留中文、英文、数字和常用标点
        import re
        filtered_keywords = re.sub(r'[#*"<>|%^&\(\)\[\]{}|]+', '', keywords)
        filtered_keywords = filtered_keywords.strip()
        print(f"过滤后的关键词: {filtered_keywords}")
        
        # 1. 先尝试使用Playwright搜索
        for attempt in range(config.MAX_RETRY):
            try:
                page = await self._get_page()
                
                # 直接构建搜索URL
                search_url = f"{config.BING_URL}/search?q={filtered_keywords}"
                print(f"直接访问搜索URL: {search_url}")
                
                await page.goto(search_url, timeout=config.TIMEOUT)
                await page.wait_for_load_state("load", timeout=config.TIMEOUT)
                await asyncio.sleep(2)
                
                # 尝试获取搜索结果
                try:
                    await page.wait_for_selector(".b_algo", timeout=config.TIMEOUT)
                    result_elements = await page.locator(".b_algo").all()
                    
                    if len(result_elements) > 0:
                        print(f"使用Playwright找到 {len(result_elements)} 个搜索结果")
                        
                        # 提取结果
                        seen_links = set()
                        for result_el in result_elements:
                            try:
                                title_el = result_el.locator("h2 a")
                                if await title_el.count() == 0:
                                    continue
                                
                                title = await title_el.inner_text()
                                href = await title_el.get_attribute("href")
                                
                                if not href or not href.startswith("http") or len(title) < 5:
                                    continue
                                
                                if href in seen_links:
                                    continue
                                seen_links.add(href)
                                
                                summary = ""
                                summary_el = result_el.locator(".b_caption p").first
                                if await summary_el.count() > 0:
                                    summary_text = await summary_el.inner_text()
                                    summary = summary_text[:150]
                                
                                results.append(SearchResult(title=title, summary=summary, link=href))
                                print(f"添加结果: {title[:30]}...")
                                
                                if len(results) >= top_k:
                                    break
                            except Exception as e:
                                continue
                except Exception as e:
                    print(f"Playwright获取结果失败: {e}")
                
                await self._release_page(page)
            except Exception as e:
                print(f"Playwright搜索失败 (尝试 {attempt + 1}/{config.MAX_RETRY}): {e}")
        
        # 2. 如果Playwright失败或没有结果，使用requests作为备选
        if not results:
            print("Playwright搜索失败或没有结果，尝试使用requests搜索...")
            results = self._search_bing_with_requests(keywords, top_k)
        
        # 移除模拟数据备用方案，确保只返回真实搜索结果
        
        # 处理结果，提取内容
        valid_results = []
        for result in results[:top_k]:  # 处理前top_k个结果
            try:
                content = await self._extract_content(result.link)
                if content not in ["【提取失败】", "【广告内容】"]:
                    result.content = content
                    valid_results.append(result)
                    print(f"成功提取内容: {result.title[:30]}...")
            except Exception as e:
                print(f"处理结果 '{result.title}' 失败: {e}")
                # 如果提取内容失败，仍然保留结果，只是内容为空
                valid_results.append(result)
        
        # 返回所有有效结果，即使数量不足top_k
        return valid_results

    async def _extract_content(self, url: str) -> str:
        for attempt in range(config.MAX_RETRY):
            try:
                page = await self._get_page()
                
                # 增加超时时间，处理连接问题
                await page.goto(url, timeout=config.TIMEOUT * 2)
                
                # 只等待load状态，不等待networkidle，减少超时风险
                await page.wait_for_load_state("load", timeout=config.TIMEOUT * 2)
                await asyncio.sleep(1)  # 额外等待1秒
                
                # 尝试获取HTML内容，处理页面导航问题
                html = await page.content()
                await self._release_page(page)
                
                # 过滤广告内容
                if any(ad in html.lower() for ad in ['广告', 'advertisement', 'sponsored', '推广', 'promoted']):
                    return "【广告内容】"
                
                # 提取正文
                doc = Document(html)
                content = doc.summary()
                
                soup = BeautifulSoup(content, 'lxml')
                text = soup.get_text(separator=' ', strip=True)
                
                # 过滤过短或无效内容
                if not text or len(text) < 50:
                    return "【提取失败】"
                
                # 过滤广告和无效内容
                if any(ad in text.lower() for ad in ['广告', '推广', '点击下载', '注册', '登录']):
                    return "【广告内容】"
                
                # 放宽验证条件，不依赖LLM验证，直接返回内容
                # 只过滤think标签，不过度摘要
                filtered_text = llm_utils.filter_content(text)
                
                # 确保返回的内容长度合理
                if len(filtered_text) < 100:
                    return "【提取失败】"
                
                return filtered_text
                
            except Exception as e:
                print(f"提取内容失败 (尝试 {attempt + 1}/{config.MAX_RETRY}): {e}")
                
                # 处理页面导航问题
                if "navigating and changing the content" in str(e):
                    await self._release_page(page)
                    continue
                
                if attempt == config.MAX_RETRY - 1:
                    return "【提取失败】"
                
                await asyncio.sleep(2)  # 增加重试间隔
        
        return "【提取失败】"

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
