import os
import yaml
from typing import Dict, Any


class Config:
    def __init__(self):
        self.config: Dict[str, Any] = {
            "LLM_BASE_URL": "http://192.168.3.153:11434/v1",
            "LLM_MODEL": "qwen3:14b",
            "MCP_PORT": 8903,
            "MAX_RETRY": 3,
            "TOP_K": 5,
            "MAX_TOKEN": 150,
            "TIMEOUT": 30000,  # 30秒超时
            "MAX_ITER": 3,     # 最大迭代次数
            "BING_URL": "https://www.bing.com",
            "HEADLESS": True   # 无头浏览器模式
        }
        
        # 加载本地配置文件
        self._load_local_config()
        
        # 加载环境变量
        self._load_environment_vars()
    
    def _load_local_config(self):
        config_path = "config.yaml"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    local_config = yaml.safe_load(f)
                    if local_config:
                        self.config.update(local_config)
            except Exception as e:
                print(f"加载本地配置文件失败: {e}")
    
    def _load_environment_vars(self):
        env_vars = {
            "LLM_BASE_URL": "BING_SEARCH_LLM_BASE_URL",
            "LLM_MODEL": "BING_SEARCH_LLM_MODEL",
            "MCP_PORT": "BING_SEARCH_MCP_PORT",
            "MAX_RETRY": "BING_SEARCH_MAX_RETRY",
            "TOP_K": "BING_SEARCH_TOP_K",
            "MAX_TOKEN": "BING_SEARCH_MAX_TOKEN"
        }
        
        for config_key, env_key in env_vars.items():
            env_value = os.environ.get(env_key)
            if env_value is not None:
                # 根据配置类型转换值
                if config_key in ["MCP_PORT", "MAX_RETRY", "TOP_K", "MAX_TOKEN"]:
                    try:
                        self.config[config_key] = int(env_value)
                    except ValueError:
                        print(f"环境变量 {env_key} 转换为整数失败，使用默认值")
                else:
                    self.config[config_key] = env_value
    
    def __getattr__(self, name: str) -> Any:
        return self.config.get(name, None)


config = Config()
