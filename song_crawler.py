#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import requests
from bs4 import BeautifulSoup
import wikipls
import time
import os

SONG_LIST = [
    {"name": "成都", "artist": "赵雷"},
    {"name": "安和桥", "artist": "宋冬野"},
    {"name": "海阔天空", "artist": "Beyond"},
    {"name": "恭喜恭喜", "artist": "姚莉/姚敏"},
    {"name": "信仰", "artist": "廖昌永"},
]

def fetch_from_wikipedia(song_name, artist):
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
    try:
        encoded_name = requests.utils.quote(f"{song_name}_{artist}歌曲")
        url = f"https://baike.baidu.com/item/{encoded_name}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        summary_div = soup.find('div', class_='lemma-summary')
        summary = summary_div.get_text().strip() if summary_div else ""
        return {'baidu_summary': summary}
    except Exception as e:
        print(f"百度百科抓取失败: {song_name} - {e}")
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

        wiki_data = fetch_from_wikipedia(song['name'], song['artist'])
        if wiki_data:
            if wiki_data.get('background'):
                song_data['background'] = wiki_data['background']
                song_data['source'].append('wikipedia')
            if wiki_data.get('summary'):
                song_data['impact'] = wiki_data['summary']

        baidu_data = fetch_from_baidu(song['name'], song['artist'])
        if baidu_data and baidu_data.get('baidu_summary') and not song_data['background']:
            song_data['background'] = baidu_data['baidu_summary']
            song_data['source'].append('baidu')

        results[song_key] = song_data
        time.sleep(1)

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