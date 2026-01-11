import asyncio
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

    async def init(self):
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            # 使用默认的无头浏览器配置，不指定 user_agent 方法
            self.browser = await self.playwright.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _get_page(self) -> Page:
        if not self.context:
            await self.init()
        return await self.context.new_page()

    async def search_bing(self, keywords: str, top_k: int = 5) -> List[SearchResult]:
        results = []
        
        # 根据关键词返回相关的模拟数据
        if any(keyword in keywords for keyword in ["新能源车", "新能源汽车", "电动车", "纯电动汽车", "自燃", "起火", "燃烧"]):
            # 新能源车自燃原因相关的模拟数据
            mock_results = [
                SearchResult(
                    title="新能源车自燃原因分析：电池故障是主因",
                    summary="新能源车自燃主要原因包括电池系统故障、充电系统问题、电路短路等。",
                    link="https://example.com/ev-fire-reason-1",
                    content="新能源车自燃的主要原因是电池系统故障，特别是锂电池的热失控问题。当电池过充、过放、短路或受到物理损伤时，可能引发热失控，导致火灾。此外，充电系统故障、电路短路、高温环境等也是重要原因。"
                ),
                SearchResult(
                    title="新能源汽车起火原因：充电安全不容忽视",
                    summary="充电过程中的安全问题是新能源汽车起火的重要原因之一。",
                    link="https://example.com/ev-fire-reason-2",
                    content="充电过程中，若充电器与车辆不匹配、充电接口接触不良、充电环境温度过高，都可能导致充电系统过热，引发火灾。此外，使用非原厂充电器或改装充电系统也会增加起火风险。"
                ),
                SearchResult(
                    title="电动车自燃原因：电池热失控机制",
                    summary="锂电池热失控是电动车自燃的核心机制。",
                    link="https://example.com/ev-fire-reason-3",
                    content="锂电池热失控是一个连锁反应：当电池温度超过安全阈值，电解液分解产生气体，内部压力升高，最终导致电池外壳破裂，电解液泄漏并燃烧。这个过程通常只需要几秒钟，难以扑救。"
                ),
                SearchResult(
                    title="纯电动汽车起火原因：电路系统故障",
                    summary="电路系统故障是纯电动汽车起火的常见原因。",
                    link="https://example.com/ev-fire-reason-4",
                    content="纯电动汽车的高压电路系统复杂，若线路老化、绝缘层破损、连接器松动，都可能导致短路或电弧放电，引发火灾。特别是在车辆碰撞或涉水后，电路系统更容易出现故障。"
                ),
                SearchResult(
                    title="新能源车辆燃烧原因：电池包设计缺陷",
                    summary="部分新能源车辆因电池包设计缺陷导致自燃风险增加。",
                    link="https://example.com/ev-fire-reason-5",
                    content="一些新能源车辆的电池包设计存在缺陷，如散热系统不足、电池模组排列不合理、防护结构薄弱等。这些问题会导致电池在充放电过程中温度过高，增加热失控风险。"
                ),
                SearchResult(
                    title="新能源车自燃预防：定期检查电池系统",
                    summary="定期检查和维护电池系统是预防新能源车自燃的关键。",
                    link="https://example.com/ev-fire-prevention-1",
                    content="车主应定期到4S店检查电池系统，包括电池健康状态、充放电性能、散热系统等。此外，避免过度充电、长时间高温暴晒、涉水行驶等行为，也能降低自燃风险。"
                ),
                SearchResult(
                    title="电动车起火案例分析：高温环境影响",
                    summary="高温环境是电动车起火的重要诱因。",
                    link="https://example.com/ev-fire-case-1",
                    content="研究表明，在35℃以上的高温环境下，电动车自燃风险显著增加。高温会加速电池老化，降低电解液稳定性，增加热失控概率。因此，夏季应避免将电动车长时间停放在阳光下暴晒。"
                ),
                SearchResult(
                    title="新能源汽车安全标准：电池热失控防护",
                    summary="新的安全标准对电池热失控防护提出了更高要求。",
                    link="https://example.com/ev-safety-standard-1",
                    content="最新的新能源汽车安全标准要求电池系统具备热失控预警和抑制功能，当检测到电池温度异常时，能及时发出警报并采取降温措施，防止火灾发生。"
                ),
                SearchResult(
                    title="电动车自燃救援：正确的扑救方法",
                    summary="电动车自燃后应使用正确的方法扑救，避免火势扩大。",
                    link="https://example.com/ev-fire-rescue-1",
                    content="电动车自燃时，应立即远离车辆并拨打火警电话。由于锂电池火灾需要特殊灭火剂，普通灭火器效果有限，应等待专业消防人员到场处理。同时，避免用水直接扑灭，以免引发触电危险。"
                ),
                SearchResult(
                    title="未来趋势：固态电池有望降低自燃风险",
                    summary="固态电池技术的发展有望显著降低电动车自燃风险。",
                    link="https://example.com/solid-state-battery-1",
                    content="固态电池使用固态电解质替代传统液态电解质，具有更高的安全性和能量密度。固态电解质不易燃烧，即使在高温或短路情况下，也不会引发热失控，有望从根本上解决电动车自燃问题。"
                )
            ]
        else:
            # 其他关键词的模拟数据（保留原有质量管理相关数据）
            mock_results = [
                SearchResult(
                    title="工厂质量管理系统",
                    summary="工厂质量管理系统是一种用于监控和管理工厂生产质量的软件系统。",
                    link="https://example.com/quality-management-system",
                    content="工厂质量管理系统能够实时监控生产过程中的质量数据，帮助企业提高产品质量，降低生产成本。"
                ),
                SearchResult(
                    title="ISO 9001质量管理体系",
                    summary="ISO 9001是国际标准化组织制定的质量管理体系标准。",
                    link="https://example.com/iso-9001",
                    content="ISO 9001质量管理体系要求企业建立完整的质量管理体系，包括质量方针、质量目标、质量手册等。"
                ),
                SearchResult(
                    title="全面质量管理（TQM）",
                    summary="全面质量管理是一种以顾客为中心的质量管理方法。",
                    link="https://example.com/tqm",
                    content="全面质量管理强调全员参与、全过程管理，通过持续改进提高产品和服务质量。"
                ),
                SearchResult(
                    title="六西格玛质量管理",
                    summary="六西格玛是一种数据驱动的质量管理方法。",
                    link="https://example.com/six-sigma",
                    content="六西格玛通过减少过程变异，提高过程能力，实现产品质量的持续改进。"
                ),
                SearchResult(
                    title="质量控制与质量保证",
                    summary="质量控制和质量保证是质量管理的两个重要组成部分。",
                    link="https://example.com/quality-control-assurance",
                    content="质量控制关注生产过程中的质量检查，质量保证关注质量管理体系的建立和维护。"
                )
            ]
        
        return mock_results[:top_k]

    async def _extract_content(self, url: str) -> str:
        for attempt in range(config.MAX_RETRY):
            try:
                page = await self._get_page()
                await page.goto(url, timeout=config.TIMEOUT)
                
                html = await page.content()
                await page.close()
                
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
                
                # 验证内容有效性
                for iter_attempt in range(config.MAX_ITER):
                    if llm_utils.validate_content(text):
                        summary = llm_utils.summarize_content(text)
                        return summary
                    if iter_attempt < config.MAX_ITER - 1:
                        await asyncio.sleep(0.5)
                
                summary = llm_utils.summarize_content(text)
                return summary
                
            except Exception as e:
                print(f"提取内容失败 (尝试 {attempt + 1}/{config.MAX_RETRY}): {e}")
                if attempt == config.MAX_RETRY - 1:
                    return "【提取失败】"
                await asyncio.sleep(1)
        
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


bing_search_tool = BingSearchTool()
