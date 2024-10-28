import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from loguru import logger
import re
from playwright.sync_api import sync_playwright

class ArticleProcessor:
    def __init__(self):
        self.temp_dir = Path("data/temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
    def extract_article(self, url):
        """提取文章内容"""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle")
                
                # 根据不同平台使用不同的提取规则
                if "toutiao.com" in url:
                    content = self._extract_toutiao(page)
                elif "mp.weixin.qq.com" in url:
                    content = self._extract_wechat(page)
                elif "weibo.com" in url:
                    content = self._extract_weibo(page)
                elif "zhihu.com" in url:
                    content = self._extract_zhihu(page)
                else:
                    content = self._extract_general(page)
                    
                browser.close()
                return content
                
        except Exception as e:
            logger.error(f"提取文章失败: {str(e)}")
            return None
            
    def save_temp_article(self, title, content, platform, original_url):
        """保存临时文章"""
        try:
            # 生成唯一文件名
            url_hash = hashlib.md5(original_url.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{url_hash}_{timestamp}.json"
            
            article_data = {
                "title": title,
                "content": content,
                "platform": platform,
                "original_url": original_url,
                "created_at": datetime.now().isoformat(),
                "status": "raw"  # raw, processed, published
            }
            
            filepath = self.temp_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
                
            return filepath
            
        except Exception as e:
            logger.error(f"保存临时文章失败: {str(e)}")
            return None
            
    def _extract_toutiao(self, page):
        """提取今日头条文章"""
        title = page.evaluate('() => document.querySelector(".article-title").innerText')
        content = page.evaluate('''() => {
            const article = document.querySelector(".article-content");
            if (!article) return "";
            
            // 移除无关元素
            article.querySelectorAll("img, video, iframe, script, style").forEach(el => el.remove());
            
            // 获取纯文本
            return article.innerText.trim();
        }''')
        return {"title": title, "content": content}
        
    def _extract_wechat(self, page):
        """提取微信公众号文章"""
        title = page.evaluate('() => document.querySelector("#activity-name").innerText')
        content = page.evaluate('''() => {
            const article = document.querySelector("#js_content");
            if (!article) return "";
            
            // 移除无关元素
            article.querySelectorAll("img, video, iframe, script, style, mp-miniprogram").forEach(el => el.remove());
            
            // 获取纯文本
            return article.innerText.trim();
        }''')
        return {"title": title, "content": content}
        
    def _extract_zhihu(self, page):
        """提取知乎文章"""
        title = page.evaluate('() => document.querySelector(".Post-Title").innerText')
        content = page.evaluate('''() => {
            const article = document.querySelector(".Post-RichText");
            if (!article) return "";
            
            // 移除无关元素
            article.querySelectorAll("img, video, iframe, script, style, button, .LinkCard").forEach(el => el.remove());
            
            // 获取纯文本
            return article.innerText.trim();
        }''')
        return {"title": title, "content": content}
        
    def _extract_general(self, page):
        """通用文章提取"""
        title = page.evaluate('() => document.title')
        content = page.evaluate('''() => {
            // 移除常见的无关元素
            document.querySelectorAll("nav, header, footer, aside, script, style, iframe, img, video").forEach(el => el.remove());
            
            // 尝试查找文章主体
            const article = document.querySelector("article") || 
                          document.querySelector(".article") || 
                          document.querySelector(".post") || 
                          document.querySelector("main") || 
                          document.body;