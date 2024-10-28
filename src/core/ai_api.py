# src/core/ai_api.py
import aiohttp
import asyncio
from loguru import logger
from typing import Dict, Any
import json

class AIAPI:
    """AI文本处理API"""
    
    def __init__(self):
        # API配置
        self.api_key = "sk-EhkxCDU3AlWnVAItUniykvcAW5oCHqTl6auer9vsmnmjXogv"  # 从配置文件读取
        self.api_base = "https://api.moonshot.cn/v1"
        self.model = "moonshot-v1-auto"
        
        # 风格提示语
        self.style_prompts = {
            '正式严谨': '使用严谨的学术语言',
            '轻松活泼': '使用轻松愉快的口语化表达',
            '新闻报道': '采用新闻报道的客观语气',
            '营销文案': '转换为吸引人的营销文案',
            '小说风格': '使用生动的小说叙述手法',
            '诗歌风格': '改写成诗歌的形式'
        }
        
        # 任务提示语
        self.task_prompts = {
            '文章改写': '保持原意，改写以下文本：',
            '风格转换': '转换文本风格：',
            '标题优化': '优化以下标题，使其更吸引人：',
            '扩写内容': '扩展以下内容���使其更详细：',
            '生成摘要': '为以下文章生成摘要：',
            '润色优化': '润色和优化以下文本：'
        }
    
    async def process(self, text: str, task: str, **options) -> str:
        """
        处理文本
        text: 原文本
        task: 任务类型
        options: 其他选项（temperature, style, keep_keywords等）
        """
        try:
            # 构建提示语
            task_prompt = self.task_prompts.get(task, '处理以下文本：')
            style = options.get('style', '')
            style_prompt = self.style_prompts.get(style, '') if style else ''
            temperature = options.get('temperature', 0.7)
            keep_keywords = options.get('keep_keywords', True)
            
            # 构建完整的提示语
            system_prompt = "你是一个专业的文本处理助手。"
            if keep_keywords:
                system_prompt += "请在处理时保留原文中的关键词和重要概念。"
                
            user_prompt = f"{task_prompt}\n"
            if style_prompt:
                user_prompt += f"要求使用{style_prompt}。\n"
            user_prompt += f"\n原文：{text}"
            
            # 构建API请求
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": temperature
            }
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=30
                ) as response:
                    result = await response.json()
                    
                    if response.status != 200:
                        error_msg = result.get('error', {}).get('message', '未知错误')
                        raise Exception(f"API请求失败: {error_msg}")
                    
                    return result['choices'][0]['message']['content']
                    
        except asyncio.TimeoutError:
            logger.error("AI API请求超时")
            raise Exception("处理超时，请稍后重试")
            
        except Exception as e:
            logger.error(f"AI处理失败: {str(e)}")
            raise Exception(f"AI处理失败: {str(e)}")
            
    def get_available_styles(self) -> list:
        """获取可用的风格列表"""
        return list(self.style_prompts.keys())
        
    def get_available_tasks(self) -> list:
        """获取可用的任务列表"""
        return list(self.task_prompts.keys())

