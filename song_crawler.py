#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from bs4 import BeautifulSoup
import wikipls
import time
import os
import re

# 网易云音乐API地址（如果部署了请修改）
NETEASE_API_BASE = "http://localhost:3000"  # 改为你的实际地址，如 https://netease-api.onrender.com

SONG_LIST = [
    {"name": "成都", "artist": "赵雷"},
    {"name": "安和桥", "artist": "宋冬野"},
    {"name": "海阔天空", "artist": "Beyond"},
    {"name": "恭喜恭喜", "artist": "姚莉/姚敏"},
    {"name": "信仰", "artist": "廖昌永"},
    # 可以继续添加，最好与 regionSongLib 中的歌曲对应
]

def fetch_from_wikipedia(song_name, artist):
    """从维基百科获取信息"""
    try:
        page_title = f"{song_name}_(歌曲)"
        summary = wikipls.get_summary(page_title, lang='zh')
        page_data = wikipls.get_page_data(page_title, lang='zh')
        background = ""
        if 'sections' in page_data:
            for section in page_data['sections']:
                if '创作背景' in section.get('line', ''):
                    background = section.get('text', '')
                    break
        return {
            'summary': summary[:500] + "..." if len(summary) > 500 else summary,
            'background': background
        }
    except Exception as e:
        print(f"维基百科抓取失败: {song_name} - {e}")
        return None

def fetch_from_baidu(song_name, artist):
    """从百度百科抓取"""
    try:
        # 构造可能的关键词
        keywords = [f"{song_name}_{artist}歌曲", f"{song_name} {artist}", song_name]
        for kw in keywords:
            encoded = requests.utils.quote(kw)
            url = f"https://baike.baidu.com/item/{encoded}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                # 提取摘要
                summary_div = soup.find('div', class_='lemma-summary')
                summary = summary_div.get_text().strip() if summary_div else ""
                # 提取基本信息
                basic_info = {}
                info_div = soup.find('div', class_='basic-info')
                if info_div:
                    dt_list = info_div.find_all('dt')
                    dd_list = info_div.find_all('dd')
                    for dt, dd in zip(dt_list, dd_list):
                        key = dt.get_text().strip()
                        value = dd.get_text().strip()
                        basic_info[key] = value
                return {'baidu_summary': summary, 'basic_info': basic_info}
        return None
    except Exception as e:
        print(f"百度百科抓取失败: {song_name} - {e}")
        return None

def fetch_from_netease(song_name, artist):
    """从网易云音乐获取热评和歌词（需要部署API）"""
    if not NETEASE_API_BASE or NETEASE_API_BASE == "http://localhost:3000":
        print("未配置网易云API，跳过")
        return None
    try:
        # 搜索歌曲
        search_res = requests.get(
            f"{NETEASE_API_BASE}/search",
            params={'keywords': f"{song_name} {artist}"},
            timeout=5
        )
        search_data = search_res.json()
        if search_data.get('result') and search_data['result']['songs']:
            song_id = search_data['result']['songs'][0]['id']
            # 获取热门评论
            comment_res = requests.get(
                f"{NETEASE_API_BASE}/comment/music",
                params={'id': song_id, 'limit': 5},
                timeout=5
            )
            comment_data = comment_res.json()
            hot_comments = []
            if comment_data.get('hotComments'):
                for comment in comment_data['hotComments'][:3]:
                    hot_comments.append(comment['content'])
            # 获取歌词
            lyric_res = requests.get(
                f"{NETEASE_API_BASE}/lyric",
                params={'id': song_id},
                timeout=5
            )
            lyric_data = lyric_res.json()
            lyrics = []
            if lyric_data.get('lrc') and lyric_data['lrc'].get('lyric'):
                # 提取前几句歌词（去除时间戳）
                lines = lyric_data['lrc']['lyric'].split('\n')
                for line in lines[:10]:
                    # 去除时间戳 [00:12.34] 部分
                    clean = re.sub(r'\[.*?\]', '', line).strip()
                    if clean:
                        lyrics.append(clean)
            return {
                'hot_comments': hot_comments,
                'lyrics': lyrics[:5]
            }
    except Exception as e:
        print(f"网易云抓取失败: {song_name} - {e}")
    return None

def crawl_song_reviews():
    results = {}
    for song in SONG_LIST:
        print(f"正在抓取: {song['name']} - {song['artist']}")
        song_key = f"{song['name']} - {song['artist']}"
        song_data = {
            'name': song['name'],
            'artist': song['artist'],
            'background': '',
            'impact': '',
            'musicalFeatures': [],
            'reviews': [],
            'lyricHighlights': [],
            'source': []
        }

        # 1. 维基百科
        wiki_data = fetch_from_wikipedia(song['name'], song['artist'])
        if wiki_data:
            if wiki_data.get('background'):
                song_data['background'] = wiki_data['background']
                song_data['source'].append('wikipedia')
            if wiki_data.get('summary'):
                song_data['impact'] = wiki_data['summary']

        # 2. 百度百科（作为背景补充）
        baidu_data = fetch_from_baidu(song['name'], song['artist'])
        if baidu_data:
            if baidu_data.get('baidu_summary') and not song_data['background']:
                song_data['background'] = baidu_data['baidu_summary']
                song_data['source'].append('baidu')
            # 如果有基本信息，可以提取一些作为特征（简单处理）
            if baidu_data.get('basic_info'):
                for k, v in baidu_data['basic_info'].items():
                    if '风格' in k or '类型' in k:
                        song_data['musicalFeatures'].append(f"风格：{v}")

        # 3. 网易云音乐（热评和歌词）
        netease_data = fetch_from_netease(song['name'], song['artist'])
        if netease_data:
            if netease_data.get('hot_comments'):
                song_data['reviews'].extend(netease_data['hot_comments'])
                song_data['source'].append('netease')
            if netease_data.get('lyrics'):
                song_data['lyricHighlights'] = netease_data['lyrics']

        # 如果没有任何数据，添加默认提示
        if not song_data['background']:
            song_data['background'] = "暂无详细背景资料"
        if not song_data['reviews']:
            song_data['reviews'] = ["暂无乐评"]
        if not song_data['lyricHighlights']:
            song_data['lyricHighlights'] = ["暂无歌词片段"]

        results[song_key] = song_data
        time.sleep(1)  # 礼貌性延迟

    return results

def save_to_json(data, filename='song_reviews.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {filename}")

if __name__ == '__main__':
    print("开始抓取歌曲鉴赏信息...")
    results = crawl_song_reviews()
    save_to_json(results)
    print("抓取完成！")
