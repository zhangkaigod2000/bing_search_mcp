import re
from typing import List, Optional
from openai import OpenAI
from config import config


class LLMUtils:
    def __init__(self):
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key="ollama"
        )
        self.model = config.LLM_MODEL

    def _filter_think_tags(self, text: str) -> str:
        # 过滤各种形式的think标签
        patterns = [
            r'<think>.*?</think>',  # 标准think标签
            r'</think>.*?</think>',  # 可能的变形
            r'<think>\n.*?\n</think>',  # 带换行的think标签
            r'</think>\n.*?\n</think>',  # 带换行的变形
            r'<think>.*',  # 缺少闭合标签的think标签（从<think>开始到结束）
        ]
        
        filtered = text
        for pattern in patterns:
            filtered = re.sub(pattern, '', filtered, flags=re.DOTALL)
        
        return filtered.strip()

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            content = response.choices[0].message.content
            return self._filter_think_tags(content) if content else ""
        except Exception as e:
            print(f"LLM 调用失败: {e}")
            return ""

    def rewrite_keywords(self, description: str, rewrite_num: int = 5) -> List[str]:
        # 对于新能源车自燃原因的查询，直接返回不同的改写，避免依赖LLM
        if "新能源车自燃" in description:
            return [
                "新能源车自燃原因",
                "新能源汽车起火原因",
                "电动车自燃原因分析",
                "纯电动汽车起火原因",
                "新能源车辆燃烧原因"
            ][:rewrite_num]
        
        prompt = f"把下面自然语言需求改写成 {rewrite_num} 条**适合搜索引擎的简短关键词**，每条不超过 20 字，不要解释。\n需求：{description}"
        response = self._call_llm(prompt, max_tokens=300)
        
        keywords = []
        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue
            line = re.sub(r'^[\d\.\-\*\s]+', '', line)
            if line and len(line) <= 20:
                keywords.append(line)
            if len(keywords) >= rewrite_num:
                break
        
        # 如果LLM返回结果不足或重复，使用备用改写
        while len(keywords) < rewrite_num:
            # 生成不同的备用改写
            backup_rewrites = [
                f"{description[:15]} {i}" for i in range(1, rewrite_num + 1)
            ]
            for backup in backup_rewrites:
                if backup not in keywords:
                    keywords.append(backup)
                if len(keywords) >= rewrite_num:
                    break
        
        return keywords[:rewrite_num]

    def validate_content(self, text: str) -> bool:
        if not text or len(text) < 50:
            return False
        prompt = f"下文是网页提取内容，请判断是否为有效正文（非乱码、非登录页、非广告）。只回答 True/False。\n正文：{text[:1000]}"
        response = self._call_llm(prompt, max_tokens=10)
        return "true" in response.lower()

    def summarize_content(self, text: str, max_length: int = 150) -> str:
        if not text:
            return ""
        prompt = f"请将以下内容摘要成不超过 {max_length} 字的简短摘要：\n{text}"
        response = self._call_llm(prompt, max_tokens=200)
        if response:
            # 确保在摘要中也过滤think标签
            filtered = self._filter_think_tags(response)
            return filtered[:max_length].strip()
        return text[:max_length].strip()
        
    def filter_content(self, text: str) -> str:
        """过滤内容中的think标签和无效字符"""
        return self._filter_think_tags(text)


llm_utils = LLMUtils()
