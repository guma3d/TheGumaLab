import os
import re
import hashlib
import subprocess
import requests
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for, send_file, after_this_request, session
from pathlib import Path
import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple
import json
import sqlite3
import threading
import queue
import uuid
from datetime import datetime
import zipfile
import shutil
import time
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from google import genai
from google.genai import types
from bs4 import BeautifulSoup
import markdown
from requests.auth import HTTPBasicAuth
import write_wiki

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.getenv("SECRET_KEY", "youtube-processor-secret-key-change-in-production")

# 설정
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Task queue 및 상태 관리
task_queue = queue.Queue()
task_status = {}  # {task_id: {"status": "queued/processing/completed/failed", "progress": "", "result": {}, "created_at": datetime}}
task_lock = threading.RLock()  # 재진입 가능한 락으로 변경 (데드락 방지)

# Task 상태 저장 파일 (Docker volume 지원)
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DATA_DIR.mkdir(exist_ok=True)
TASK_STATUS_FILE = DATA_DIR / "task_status.json"

# yt-dlp 쿠키 경로
COOKIE_PATH = str(DATA_DIR / "youtube_cookies.txt")

# yt-dlp 공통 옵션
YT_DLP_COMMON_OPTIONS = [
    "--js-runtimes", "node",
    "--remote-components", "ejs:github",
]
DATA_DIR.mkdir(exist_ok=True)
TASK_STATUS_FILE = DATA_DIR / "task_status.json"

# 데이터베이스 초기화 (Docker volume 지원)
DB_PATH = str(DATA_DIR / "settings.db")

def init_db():
    """데이터베이스 초기화 및 기본값 설정"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            system_prompt TEXT NOT NULL,
            user_prompt_template TEXT NOT NULL,
            whisper_model TEXT NOT NULL,
            translation_model TEXT NOT NULL,
            summary_system_prompt TEXT NOT NULL,
            summary_user_prompt_template TEXT NOT NULL,
            filter_system_prompt TEXT,
            filter_user_prompt_template TEXT
        )
    ''')
    
    # 조회수 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS view_counts (
            task_id TEXT PRIMARY KEY,
            summary_views INTEGER DEFAULT 0,
            detail_views INTEGER DEFAULT 0,
            last_viewed_at TEXT
        )
    ''')
    
    # 추천 테이블 생성
    c.execute('''
        CREATE TABLE IF NOT EXISTS recommendations (
            task_id TEXT PRIMARY KEY,
            recommend_count INTEGER DEFAULT 0
        )
    ''')
    
    # 설정 테이블 생성 (최대 Task 수 등)
    c.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')
    
    # 기본 설정값 삽입
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('max_tasks', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_cleanup', '1')")  # 1: 활성화, 0: 비활성화
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('skip_detail_html', '0')")  # 1: 상세보기 생성 안함, 0: 생성함
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('enable_reranking', '0')")  # 1: 활성화, 0: 비활성화
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('enable_search_answer', '0')")  # 1: AI 답변 생성, 0: 검색 결과만
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('min_similarity_threshold', '0.4')")  # 최소 유사도 임계값 (0.0~1.0)
    
    # 기본값이 없으면 삽입
    c.execute('SELECT COUNT(*) FROM prompts')
    if c.fetchone()[0] == 0:
        c.execute('''
            INSERT INTO prompts (id, system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template)
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "You are a translator. Translate the following English text to Korean. Only output the translated text, nothing else.",
            "{text}",
            "whisper-1",
            "gemini-3.1-flash-lite-preview",
            "You are a professional summarizer. Create a concise summary in Korean. Do NOT include the main title. 1. Start with a plain text introduction like '본 영상은...'. 2. Use small headings (### or ####) for organizing the content. 3. Include a '핵심 인사이트' section. 4. End with a single bold sentence as a one-line summary.",
            "다음은 영상의 전체 자막입니다. 다음 규칙에 따라 마크다운 형식으로 요약해주세요:\n- 메인 제목(# 또는 ##) 작성 금지\n- '본 영상은~' 으로 시작하는 간단한 소개 문단 작성\n- 소개 문단 직후에 구분선(---)을 필수로 추가\n- 작은 주제(### 또는 그 이하)로 내용 정리\n- '핵심 인사이트' 정리\n- 핵심 인사이트 정리 직후에 구분선(---)을 필수로 추가\n- 가장 마지막에 굵은 글씨(** **)로 핵심을 관통하는 한줄 요약 작성\n\n{text}",
            "You are an expert at identifying important information in video transcripts. Return only the indices of important segments as a JSON array of numbers.",
            "다음은 영상의 번역된 세그먼트들입니다. 핵심 정보를 담고 있는 중요한 세그먼트들의 인덱스만 JSON 배열로 반환해주세요 (예: [0, 3, 7]). 전체의 30-50% 정도만 선택하세요.\n\n{text}"
        ))
    
    # 기존 레코드에 필터링 프롬프트 컬럼이 없으면 추가
    c.execute("PRAGMA table_info(prompts)")
    columns = [column[1] for column in c.fetchall()]
    if 'filter_system_prompt' not in columns:
        c.execute("ALTER TABLE prompts ADD COLUMN filter_system_prompt TEXT")
        c.execute("ALTER TABLE prompts ADD COLUMN filter_user_prompt_template TEXT")
        c.execute('''
            UPDATE prompts SET 
                filter_system_prompt = ?,
                filter_user_prompt_template = ?
            WHERE id = 1
        ''', (
            "You are an expert at identifying important information in video transcripts. Return only the indices of important segments as a JSON array of numbers.",
            "다음은 영상의 번역된 세그먼트들입니다. 핵심 정보를 담고 있는 중요한 세그먼트들의 인덱스만 JSON 배열로 반환해주세요 (예: [0, 3, 7]). 전체의 30-50% 정도만 선택하세요.\n\n{text}"
        ))
    
    # 쿼리 확장 프롬프트 컬럼 추가
    if 'query_expansion_system_prompt' not in columns:
        c.execute("ALTER TABLE prompts ADD COLUMN query_expansion_system_prompt TEXT")
        c.execute("ALTER TABLE prompts ADD COLUMN query_expansion_model TEXT")
        c.execute('''
            UPDATE prompts SET 
                query_expansion_system_prompt = ?,
                query_expansion_model = ?
            WHERE id = 1
        ''', (
            "당신은 검색 전문가입니다. 사용자의 질문을 분석하고, 검색에 효과적인 키워드와 관련 용어를 추가하여 확장된 검색 쿼리를 생성해주세요. 고유명사(게임명, 기술명, 회사명 등), 관련 개념, 동의어를 포함하되, 자연스러운 한 문장으로 작성하세요.",
            "gemini-3.1-flash-lite-preview"
        ))
    
    # 답변 생성 프롬프트 컬럼 추가
    if 'answer_system_prompt' not in columns:
        c.execute("ALTER TABLE prompts ADD COLUMN answer_system_prompt TEXT")
        c.execute("ALTER TABLE prompts ADD COLUMN answer_model TEXT")
        c.execute('''
            UPDATE prompts SET 
                answer_system_prompt = ?,
                answer_model = ?
            WHERE id = 1
        ''', (
            "당신은 언리얼 엔진 전문가입니다. 검색된 영상 내용을 바탕으로 사용자의 질문에 200-300자 내외로 간결하게 마크다운형식으로 정리해주세요.",
            "gemini-3.1-flash-lite-preview"
        ))
    
    conn.commit()
    conn.close()

def get_prompts():
    """데이터베이스에서 프롬프트 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template, query_expansion_system_prompt, query_expansion_model, answer_system_prompt, answer_model FROM prompts WHERE id = 1')
    row = c.fetchone()
    conn.close()
    if row:
        prompts_dict = {
            "system_prompt": row[0], 
            "user_prompt_template": row[1],
            "whisper_model": row[2],
            "translation_model": row[3],
            "summary_system_prompt": row[4],
            "summary_user_prompt_template": row[5],
            "filter_system_prompt": row[6] or "You are an expert at identifying important information in video transcripts. Return only the indices of important segments as a JSON array of numbers.",
            "filter_user_prompt_template": row[7] or "다음은 영상의 번역된 세그먼트들입니다. 핵심 정보를 담고 있는 중요한 세그먼트들의 인덱스만 JSON 배열로 반환해주세요 (예: [0, 3, 7]). 전체의 30-50% 정도만 선택하세요.\n\n{text}",
            "query_expansion_system_prompt": row[8] if len(row) > 8 and row[8] else "당신은 검색 전문가입니다. 사용자의 질문을 분석하고, 검색에 효과적인 키워드와 관련 용어를 추가하여 확장된 검색 쿼리를 생성해주세요. 고유명사(게임명, 기술명, 회사명 등), 관련 개념, 동의어를 포함하되, 자연스러운 한 문장으로 작성하세요.",
            "query_expansion_model": row[9] if len(row) > 9 and row[9] else "gpt-3.5-turbo",
            "answer_system_prompt": row[10] if len(row) > 10 and row[10] else "당신은 언리얼 엔진 전문가입니다. 검색된 영상 내용을 바탕으로 사용자의 질문에 200-300자 내외로 간결하게 마크다운형식으로 정리해주세요.",
            "answer_model": row[11] if len(row) > 11 and row[11] else "gpt-3.5-turbo"
        }
        
        # 레거시 모델 또는 할당량 문제 모델을 3.1-flash-lite-preview로 강제 치환
        for k in ['whisper_model', 'translation_model', 'query_expansion_model', 'answer_model']:
            val = prompts_dict.get(k)
            if val and ('1.5-flash' in val or '2.0-flash' in val or '2.5-flash' in val):
                prompts_dict[k] = 'gemini-3.1-flash-lite-preview'
                
        return prompts_dict
    return {
        "system_prompt": "You are a translator. Translate the following English text to Korean. Only output the translated text, nothing else.",
        "user_prompt_template": "{text}",
        "whisper_model": "whisper-1",
        "translation_model": "gemini-3.1-flash-lite-preview",
        "summary_system_prompt": "You are a professional summarizer. Create a comprehensive summary in Korean with markdown formatting including headings, bullet points, and key insights.",
        "summary_user_prompt_template": "다음은 영상의 전체 자막입니다. 핵심 내용을 마크다운 형식으로 요약해주세요:\n\n{text}",
        "filter_system_prompt": "You are an expert at identifying important information in video transcripts. Return only the indices of important segments as a JSON array of numbers.",
        "filter_user_prompt_template": "다음은 영상의 번역된 세그먼트들입니다. 핵심 정보를 담고 있는 중요한 세그먼트들의 인덱스만 JSON 배열로 반환해주세요 (예: [0, 3, 7]). 전체의 30-50% 정도만 선택하세요.\n\n{text}",
        "query_expansion_system_prompt": "당신은 검색 전문가입니다. 사용자의 질문을 분석하고, 검색에 효과적인 키워드와 관련 용어를 추가하여 확장된 검색 쿼리를 생성해주세요. 고유명사(게임명, 기술명, 회사명 등), 관련 개념, 동의어를 포함하되, 자연스러운 한 문장으로 작성하세요.",
        "query_expansion_model": "gpt-3.5-turbo",
        "answer_system_prompt": "당신은 언리얼 엔진 전문가입니다. 검색된 영상 내용을 바탕으로 사용자의 질문에 200-300자 내외로 간결하게 마크다운형식으로 정리해주세요.",
        "answer_model": "gpt-3.5-turbo"
    }

def update_prompts(system_prompt: str, user_prompt_template: str, whisper_model: str, translation_model: str, summary_system_prompt: str = None, summary_user_prompt_template: str = None, filter_system_prompt: str = None, filter_user_prompt_template: str = None, query_expansion_system_prompt: str = None, query_expansion_model: str = None, answer_system_prompt: str = None, answer_model: str = None):
    """데이터베이스에 프롬프트 저장"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 모든 파라미터가 제공된 경우
    if all([summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template, query_expansion_system_prompt, query_expansion_model, answer_system_prompt, answer_model]):
        c.execute('''
            UPDATE prompts 
            SET system_prompt = ?, user_prompt_template = ?, whisper_model = ?, translation_model = ?, summary_system_prompt = ?, summary_user_prompt_template = ?, filter_system_prompt = ?, filter_user_prompt_template = ?, query_expansion_system_prompt = ?, query_expansion_model = ?, answer_system_prompt = ?, answer_model = ?
            WHERE id = 1
        ''', (system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template, query_expansion_system_prompt, query_expansion_model, answer_system_prompt, answer_model))
    elif summary_system_prompt is not None and summary_user_prompt_template is not None and filter_system_prompt is not None and filter_user_prompt_template is not None:
        c.execute('''
            UPDATE prompts 
            SET system_prompt = ?, user_prompt_template = ?, whisper_model = ?, translation_model = ?, summary_system_prompt = ?, summary_user_prompt_template = ?, filter_system_prompt = ?, filter_user_prompt_template = ?
            WHERE id = 1
        ''', (system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template))
    elif summary_system_prompt is not None and summary_user_prompt_template is not None:
        c.execute('''
            UPDATE prompts 
            SET system_prompt = ?, user_prompt_template = ?, whisper_model = ?, translation_model = ?, summary_system_prompt = ?, summary_user_prompt_template = ?
            WHERE id = 1
        ''', (system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template))
    else:
        c.execute('''
            UPDATE prompts 
            SET system_prompt = ?, user_prompt_template = ?, whisper_model = ?, translation_model = ?
            WHERE id = 1
        ''', (system_prompt, user_prompt_template, whisper_model, translation_model))
    
    conn.commit()
    conn.close()

def increment_view_count(task_id: str, view_type: str):
    """조회수 증가"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 기존 레코드 확인
    c.execute('SELECT summary_views, detail_views FROM view_counts WHERE task_id = ?', (task_id,))
    row = c.fetchone()
    
    current_time = datetime.now().isoformat()
    
    if row:
        # 기존 레코드 업데이트
        if view_type == 'summary':
            c.execute('UPDATE view_counts SET summary_views = summary_views + 1, last_viewed_at = ? WHERE task_id = ?', (current_time, task_id))
        else:
            c.execute('UPDATE view_counts SET detail_views = detail_views + 1, last_viewed_at = ? WHERE task_id = ?', (current_time, task_id))
    else:
        # 새 레코드 생성
        if view_type == 'summary':
            c.execute('INSERT INTO view_counts (task_id, summary_views, detail_views, last_viewed_at) VALUES (?, 1, 0, ?)', (task_id, current_time))
        else:
            c.execute('INSERT INTO view_counts (task_id, summary_views, detail_views, last_viewed_at) VALUES (?, 0, 1, ?)', (task_id, current_time))
    
    conn.commit()
    conn.close()

def get_view_counts(task_id: str) -> dict:
    """조회수 가져오기"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        c = conn.cursor()
        c.execute('SELECT summary_views, detail_views FROM view_counts WHERE task_id = ?', (task_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return {"summary_views": row[0], "detail_views": row[1]}
        return {"summary_views": 0, "detail_views": 0}
    except Exception as e:
        print(f"[DB Error] get_view_counts 실패: {e}")
        return {"summary_views": 0, "detail_views": 0}

def toggle_recommendation(task_id: str) -> dict:
    """추천 토글 (추천/추천 취소)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 기존 레코드 확인
    c.execute('SELECT recommend_count FROM recommendations WHERE task_id = ?', (task_id,))
    row = c.fetchone()
    
    if row:
        # 기존 추천 수 + 1
        new_count = row[0] + 1
        c.execute('UPDATE recommendations SET recommend_count = ? WHERE task_id = ?', (new_count, task_id))
    else:
        # 새 레코드 생성 (추천 1)
        new_count = 1
        c.execute('INSERT INTO recommendations (task_id, recommend_count) VALUES (?, 1)', (task_id,))
    
    conn.commit()
    conn.close()
    
    return {"recommend_count": new_count}

def get_recommendation_count(task_id: str) -> int:
    """추천 수 가져오기"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        c = conn.cursor()
        c.execute('SELECT recommend_count FROM recommendations WHERE task_id = ?', (task_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return row[0]
        return 0
    except Exception as e:
        print(f"[DB Error] get_recommendation_count 실패: {e}")
        return 0

def get_setting(key: str, default: str = "0") -> str:
    """설정값 가져오기"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = c.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return default

def update_setting(key: str, value: str):
    """설정값 업데이트"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def calculate_preference_score(task_id: str, created_at: datetime) -> dict:
    """선호도 점수 계산
    - 요약보기: 1점
    - 상세보기: 3점
    - 추천: 5점
    - 동일 점수 시 최신 Task가 높은 순위
    """
    print(f"[Score] {task_id[:8]} - 조회수 조회 중...")
    views = get_view_counts(task_id)
    print(f"[Score] {task_id[:8]} - 추천수 조회 중...")
    recommend_count = get_recommendation_count(task_id)
    
    summary_views = views.get('summary_views', 0)
    detail_views = views.get('detail_views', 0)
    
    score = (summary_views * 1) + (detail_views * 3) + (recommend_count * 5)
    
    print(f"[Score] {task_id[:8]} - 점수 계산 완료: {score} (요약:{summary_views}, 상세:{detail_views}, 추천:{recommend_count})")
    
    return {
        "task_id": task_id,
        "score": score,
        "summary_views": summary_views,
        "detail_views": detail_views,
        "recommend_count": recommend_count,
        "created_at": created_at
    }

def get_tasks_ranking() -> list:
    """모든 Task의 선호도 순위 반환"""
    global task_status
    
    ranking = []
    with task_lock:
        print(f"[Ranking] Task 개수: {len(task_status)}")
        for idx, (task_id, task_data) in enumerate(task_status.items(), 1):
            print(f"[Ranking] Task {idx}/{len(task_status)} 처리 중: {task_id[:8]}...")
            created_at = task_data.get('created_at', datetime.now())
            video_title = task_data.get('video_title', 'Unknown')
            status = task_data.get('status', 'unknown')
            
            try:
                pref = calculate_preference_score(task_id, created_at)
                pref['video_title'] = video_title
                pref['status'] = status
                ranking.append(pref)
                print(f"[Ranking] Task {idx}/{len(task_status)} 완료: 점수={pref['score']}")
            except Exception as e:
                print(f"[Ranking] Task {idx} 점수 계산 실패: {e}")
                import traceback
                traceback.print_exc()
    
    print(f"[Ranking] 정렬 중...")
    # 점수 내림차순, 동일 점수면 최신순
    ranking.sort(key=lambda x: (-x['score'], -x['created_at'].timestamp()))
    
    # 순위 번호 추가
    for idx, item in enumerate(ranking, 1):
        item['rank'] = idx
    
    print(f"[Ranking] 순위 계산 완료")
    return ranking

def auto_cleanup_tasks_by_preference():
    """선호도 기반 자동 삭제 - max_tasks 설정에 따라 낮은 순위 Task 삭제"""
    global task_status
    
    print("[AutoCleanup] 자동 클린업 시작...")
    
    # 자동 클린업 비활성화 체크
    auto_cleanup = int(get_setting('auto_cleanup', '1'))
    if auto_cleanup == 0:
        print("[AutoCleanup] 자동 클린업 비활성화됨")
        return
    
    max_tasks = int(get_setting('max_tasks', '0'))
    print(f"[AutoCleanup] max_tasks 설정: {max_tasks}")
    
    # 0이면 제한 없음
    if max_tasks <= 0:
        print("[AutoCleanup] max_tasks가 0 이하 - 제한 없음")
        return
    
    with task_lock:
        current_count = len(task_status)
        print(f"[AutoCleanup] 현재 Task 수: {current_count}")
        
        # 현재 Task 수가 max_tasks 이하면 삭제 불필요
        if current_count <= max_tasks:
            print(f"[AutoCleanup] 현재 Task 수({current_count}) <= max_tasks({max_tasks}) - 삭제 불필요")
            return
        
        # 순위 계산
        print("[AutoCleanup] 순위 계산 중...")
        ranking = get_tasks_ranking()
        print(f"[AutoCleanup] 순위 계산 완료 - 총 {len(ranking)}개")
        
        # 삭제할 개수 계산
        delete_count = current_count - max_tasks
        
        # 순위가 낮은 Task부터 삭제
        tasks_to_delete = ranking[-delete_count:]  # 하위 N개
        
        for task_info in tasks_to_delete:
            task_id = task_info['task_id']
            task_data = task_status.get(task_id)
            
            if not task_data:
                continue
            
            # 처리 중인 Task는 삭제하지 않음
            if task_data.get('status') == 'processing':
                continue
            
            # Task 디렉토리 삭제
            try:
                result = task_data.get('result', {})
                safe_title = result.get('title') or task_data.get('safe_title')
                video_title = task_data.get('video_title', safe_title or 'Unknown')
                if not safe_title:
                    safe_title = sanitize_filename(video_title)
                task_dir = OUTPUT_DIR / safe_title
                
                if task_dir.exists():
                    import shutil
                    shutil.rmtree(task_dir)
                    print(f"자동 삭제 완료: {video_title} (순위: {task_info['rank']}, 점수: {task_info['score']})")
            except Exception as e:
                print(f"디렉토리 삭제 실패: {e}")
            
            # Task 상태에서 제거
            del task_status[task_id]
        
        # 변경사항 저장
        save_task_status()
        
        print(f"선호도 기반 자동 삭제 완료: {delete_count}개 Task 삭제됨 (최대: {max_tasks}개)")

def cleanup_old_tasks():
    """동일 URL의 task 중 오래된 것 삭제 (최신 것만 유지)"""
    global task_status
    
    # URL별로 task 그룹화
    url_to_tasks = {}
    for task_id, task_data in task_status.items():
        url = task_data.get('url')
        if not url:
            continue
        
        if url not in url_to_tasks:
            url_to_tasks[url] = []
        
        # created_at을 datetime 객체로 변환
        created_at = task_data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.min
        
        url_to_tasks[url].append((task_id, created_at, task_data))
    
    # 각 URL별로 최신 것만 남기고 나머지 삭제
    tasks_to_delete = []
    for url, tasks in url_to_tasks.items():
        if len(tasks) <= 1:
            continue
        
        # created_at 기준 내림차순 정렬 (최신이 먼저)
        tasks.sort(key=lambda x: x[1], reverse=True)
        
        # 최신 task 제외하고 나머지 삭제 대상 추가
        for task_id, created_at, task_data in tasks[1:]:
            tasks_to_delete.append((task_id, task_data))
    
    # 삭제 대상 task의 리소스 정리
    for task_id, task_data in tasks_to_delete:
        # 완료된 task의 경우 출력 파일도 삭제
        if task_data.get('status') == 'completed':
            result = task_data.get('result', {})
            video_title = result.get('title')
            
            if video_title:
                video_dir = OUTPUT_DIR / video_title
                if video_dir.exists():
                    try:
                        import shutil
                        shutil.rmtree(video_dir)
                        print(f"[정리] 중복 task의 출력 디렉토리 삭제: {video_dir}")
                    except Exception as e:
                        print(f"[정리] 출력 디렉토리 삭제 실패: {e}")
        
        # task_status에서 삭제
        if task_id in task_status:
            del task_status[task_id]
            print(f"[정리] 중복 task 삭제: {task_id} (URL: {task_data.get('url')})")

def save_task_status():
    """Task 상태를 JSON 파일에 저장 (호출 전에 task_lock 필요)"""
    # 동일 URL의 task 정리: URL별로 최신 것만 유지
    cleanup_old_tasks()
    
    # datetime 객체를 문자열로 변환
    serializable_status = {}
    for task_id, status in task_status.items():
        serializable_status[task_id] = status.copy()
        if 'created_at' in serializable_status[task_id]:
            # datetime 객체인 경우에만 변환
            if isinstance(serializable_status[task_id]['created_at'], datetime):
                serializable_status[task_id]['created_at'] = serializable_status[task_id]['created_at'].isoformat()
    
    with open(TASK_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(serializable_status, f, ensure_ascii=False, indent=2)

def load_task_status():
    """JSON 파일에서 Task 상태를 로드"""
    global task_status
    if os.path.exists(TASK_STATUS_FILE):
        try:
            with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
                loaded_status = json.load(f)
            
            # 문자열을 datetime 객체로 변환
            for task_id, status in loaded_status.items():
                if 'created_at' in status and isinstance(status['created_at'], str):
                    status['created_at'] = datetime.fromisoformat(status['created_at'])
                
                # 서버 재시작 시 processing 상태는 failed로 변경
                if status.get('status') == 'processing':
                    status['status'] = 'failed'
                    status['progress'] = '서버가 재시작되어 처리가 실패했습니다.'
                    status['message'] = '서버가 재시작되어 처리가 실패했습니다. Retry 버튼을 눌러주세요.'
            
            with task_lock:
                task_status = loaded_status
            
            print(f"Loaded {len(task_status)} tasks from {TASK_STATUS_FILE}")
        except Exception as e:
            print(f"Error loading task status: {e}")

def resume_queued_tasks():
    """서버 시작 시 queued 상태의 task를 자동으로 queue에 추가"""
    with task_lock:
        queued_tasks = [(tid, t) for tid, t in task_status.items() if t.get('status') == 'queued']
    
    if queued_tasks:
        print(f"Found {len(queued_tasks)} queued tasks, adding to queue...")
        for task_id, task in queued_tasks:
            url = task.get('url')
            if url:
                task_queue.put((task_id, url))
                print(f"  - Re-queued task {task_id}")
        print(f"Resumed {len(queued_tasks)} queued tasks")

# 데이터베이스 초기화
init_db()

# Task 상태 로드
load_task_status()

# Gemini API 키 (환경변수에서 가져오기)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 관리자 비밀번호 (환경변수에서 가져오기, 기본값: admin)
ADMIN_PASSWORD = os.getenv("PASSWORD", "admin")

# Qdrant 서버 URL 및 API 키 (환경변수에서 가져오기)
QDRANT_URL = os.getenv("QDRANT_URL", "http://172.16.112.77:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "kwonsh-qdrant-apikey")

# Confluence 설정 (환경변수에서 가져오기)
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL", "https://krafton.atlassian.net/wiki")
CONFLUENCE_USERNAME = os.getenv("CONFLUENCE_USERNAME" )
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")
CONFLUENCE_PARENT_PAGE_ID = os.getenv("CONFLUENCE_PARENT_PAGE_ID")

# Qdrant 클라이언트 초기화 (원격 서버 모드)
try:
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, prefer_grpc=False)
    COLLECTION_NAME = "video_segments"
    print(f"[SUCCESS] Qdrant 연결 성공: {QDRANT_URL}")
except Exception as e:
    print(f"[FAIL] Qdrant 연결 실패: {e}")
    print(f"   검색 기능이 비활성화됩니다. 다른 기능은 정상 작동합니다.")
    qdrant_client = None
    COLLECTION_NAME = "video_segments"

# Gemini 클라이언트 초기화
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

if gemini_client:
    original_generate_content = gemini_client.models.generate_content
    _gemini_last_req_time = 0
    _gemini_req_lock = threading.Lock()
    
    import tenacity
    import time
    import re
    
    def _is_retryable_gemini_exception(exc):
        error_msg = str(exc)
        return '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg or '503' in error_msg or 'UNAVAILABLE' in error_msg
        
    def _my_before_sleep(retry_state):
        exc = retry_state.outcome.exception()
        error_msg = str(exc)
        error_type = "Quota/Rate Limit (429)" if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg else "Server Overloaded (503)"
        
        # Parse wait time if 429
        wait_time = retry_state.next_action.sleep
        match = re.search(r'retry in ([\d\.]+)s', error_msg)
        if match:
            try:
                parsed_wait = float(match.group(1)) + 2.0
                if parsed_wait > wait_time:
                    # Update sleep time manually in state info, though wait_exponential won't be bypassed directly,
                    # tenacity's next_action.sleep can be overridden in custom wait. For simplicity, just log it.
                    pass
            except ValueError:
                pass
                
        print(f"[Gemini API] {error_type}. {wait_time:.1f}초 후 재시도합니다... ({retry_state.attempt_number}/5)")

    class CustomWait(tenacity.wait.wait_base):
        def __init__(self, multiplier=15, min=30, max=120):
            self.multiplier = multiplier
            self.min = min
            self.max = max
            
        def __call__(self, retry_state):
            exc = retry_state.outcome.exception()
            error_msg = str(exc)
            
            # Default exponential backoff logic (like multiplier * 2^attempt)
            # Instead we'll use: wait_time = 30.0 + (attempt * 15.0) which is linear-ish, to match previous logic, 
            # but user asked for "exponential backoff", so let's do exponential.
            exp_wait = self.min * (2 ** (retry_state.attempt_number - 1))
            wait_time = min(exp_wait, self.max)
            
            # Check for specific "retry in Xs"
            match = re.search(r'retry in ([\d\.]+)s', error_msg)
            if match:
                try:
                    parsed_wait = float(match.group(1)) + 2.0
                    wait_time = max(wait_time, parsed_wait)
                except ValueError:
                    pass
            return wait_time

    @tenacity.retry(
        retry=tenacity.retry_if_exception(_is_retryable_gemini_exception),
        wait=CustomWait(min=30, max=120),
        stop=tenacity.stop_after_attempt(5),
        before_sleep=_my_before_sleep,
        reraise=True
    )
    def generate_content_with_retry(*args, **kwargs):
        global _gemini_last_req_time
        # 글로벌 15 RPM(분당 15회) 제한을 위해 요청 간 4.1초 간격 보장
        with _gemini_req_lock:
            elapsed = time.time() - _gemini_last_req_time
            if elapsed < 4.1:
                time.sleep(4.1 - elapsed)
            _gemini_last_req_time = time.time()
            
        return original_generate_content(*args, **kwargs)

    gemini_client.models.generate_content = generate_content_with_retry

def init_qdrant():
    """Qdrant 컬렉션 초기화"""
    if not qdrant_client:
        print("⚠️  Qdrant 클라이언트가 초기화되지 않았습니다.")
        return
    
    try:
        # 컬렉션 존재 여부 확인
        collections = qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if COLLECTION_NAME not in collection_names:
            # text-embedding-3-small 모델은 1536 차원
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )
            print(f"Qdrant 컬렉션 '{COLLECTION_NAME}' 생성 완료")
        else:
            print(f"Qdrant 컬렉션 '{COLLECTION_NAME}' 이미 존재")
    except Exception as e:
        print(f"Qdrant 초기화 오류: {e}")

# Qdrant 초기화
init_qdrant()

def get_embedding(text: str) -> List[float]:
    """Gemini API로 텍스트 임베딩 생성"""
    try:
        if not gemini_client:
            raise RuntimeError("Gemini 클라이언트가 초기화되지 않았습니다")
        
        response = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=text,
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"임베딩 생성 오류: {e}")
        return None

def filter_important_segments(segments: List['Segment']) -> List['Segment']:
    """LLM을 사용하여 중요한 세그먼트만 필터링"""
    if not gemini_client or not segments:
        return segments
    
    try:
        # 모든 세그먼트 텍스트를 하나로 합침
        all_texts = [f"[{i}] {seg.translated}" for i, seg in enumerate(segments)]
        combined_text = "\n".join(all_texts)
        
        # LLM에게 중요한 세그먼트 인덱스 요청
        prompts = get_prompts()
        translation_model = prompts.get("translation_model", "gemini-3.1-flash-lite-preview")
        if translation_model.startswith("gpt-") or "2.5-flash" in translation_model:
             translation_model = "gemini-3.1-flash-lite-preview"
             
        # 필터링 프롬프트 가져오기
        filter_system_prompt = prompts.get("filter_system_prompt", "You are an expert at identifying important information in video transcripts. Return only the indices of important segments as a JSON array of numbers.")
        filter_user_prompt_template = prompts.get("filter_user_prompt_template", "다음은 영상의 번역된 세그먼트들입니다. 핵심 정보를 담고 있는 중요한 세그먼트들의 인덱스만 JSON 배열로 반환해주세요 (예: [0, 3, 7]).\n\n{text}")
        
        response = gemini_client.models.generate_content(
             model=translation_model,
             contents=filter_user_prompt_template.format(text=combined_text),
             config=types.GenerateContentConfig(
                system_instruction=filter_system_prompt,
             )
        )
        
        # 응답에서 인덱스 추출
        content = response.text.strip()
        # 마크다운 블록이 있으면 제거
        if content.startswith("```"):
             lines = content.split('\n')
             if len(lines) >= 3:
                 content = '\n'.join(lines[1:-1])
        
        # JSON 파싱 시도
        import json
        indices = json.loads(content)
        
        # 선택된 세그먼트만 반환
        important_segments = [segments[i] for i in indices if 0 <= i < len(segments)]
        print(f"중요 세그먼트 필터링: {len(segments)}개 → {len(important_segments)}개")
        return important_segments
        
    except Exception as e:
        print(f"세그먼트 필터링 오류: {e}, 전체 세그먼트 사용")
        return segments

def get_available_models():
    """Gemini API에서 사용 가능한 모델 리스트 가져오기"""
    try:
        if not gemini_client:
             return []
        
        # Google GenAI 모델 리스트 가져오기
        models = []
        for m in gemini_client.models.list():
             if 'generateContent' in m.supported_actions:
                  name = m.name.replace('models/', '')
                  models.append(name)
        
        # 이름순으로 정렬
        return sorted(list(set(models)))
    except Exception as e:
        print(f"모델 리스트 가져오기 오류: {e}")
        return []

def store_segments_to_qdrant(segments: List['Segment'], task_id: str, youtube_url: str, video_title: str):
    """중요한 세그먼트를 Qdrant에 저장"""
    try:
        if not gemini_client:
            print("Gemini 클라이언트가 없어 벡터 저장 건너뜀")
            return
        
        # 중요한 세그먼트만 필터링
        important_segments = filter_important_segments(segments)
        
        if not important_segments:
            print("저장할 중요 세그먼트 없음")
            return
        
        points = []
        for i, seg in enumerate(important_segments):
            # 100글자 미만 세그먼트 필터링
            if not seg.translated or len(seg.translated.strip()) < 100:
                continue
            
            # 임베딩 생성
            embedding = get_embedding(seg.translated)
            if not embedding:
                continue
            
            # YouTube 타임스탬프 링크 생성
            timestamp_seconds = int(seg.start)
            youtube_link = f"{youtube_url}&t={timestamp_seconds}s"
            
            # 고유 UUID 생성 (task_id와 인덱스 조합)
            unique_string = f"{task_id}_{i}_{seg.start}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
            
            # Qdrant 포인트 생성
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "task_id": task_id,
                    "video_title": video_title,
                    "youtube_url": youtube_url,
                    "youtube_link": youtube_link,
                    "timestamp": seg.start,
                    "timestamp_str": f"{int(seg.start // 60):02d}:{int(seg.start % 60):02d}",
                    "text": seg.translated
                }
            )
            points.append(point)
        
        if points:
            # Qdrant에 일괄 저장
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"Qdrant에 {len(points)}개 세그먼트 저장 완료")
        else:
            print("임베딩 생성 실패로 저장할 포인트 없음")
            
    except Exception as e:
        print(f"Qdrant 저장 오류: {e}")

def rerank_with_llm(query: str, results: list, top_k: int = 10,llm_model="gemini-3.1-flash-lite-preview",):
    """LLM을 사용하여 검색 결과 재평가 및 재정렬"""
    try:
        if not gemini_client or not results:
            return results
        
        
        # 각 결과에 대해 관련성 점수 평가
        reranked_results = []
        
        for idx, result in enumerate(results):
            try:
                # LLM에게 관련성 평가 요청
                prompt = f"""사용자 질문: "{query}"

다음 영상 세그먼트가 사용자 질문과 얼마나 관련이 있는지 0-10 점수로 평가해주세요.

영상 제목: {result['video_title']}
세그먼트 내용: {result['text']}

평가 기준:
- 질문의 핵심 의도와 일치하는가?
- 구체적이고 유용한 정보를 제공하는가?
- 질문에 직접적으로 답변하는 내용인가?

응답 형식: 숫자 하나만 출력 (예: 7)"""

                response = gemini_client.models.generate_content(
                    model=llm_model,
                    contents=prompt
                )
                response_text = response.text
                
                if not response_text:
                    print(f"[Re-rank {idx+1}] LLM 빈 응답 - 기본값 5점 사용")
                    relevance_score = 5.0
                else:
                    response_text = response_text.strip()
                    
                    # 숫자만 추출 (정수 우선)
                    import re
                    # 먼저 단독 숫자 찾기 (0-10)
                    single_number = re.search(r'^\s*(\d+)\s*$', response_text)
                    if single_number:
                        relevance_score = float(single_number.group(1))
                    else:
                        # 소수점 포함 숫자 찾기
                        numbers = re.findall(r'\d+\.?\d*', response_text)
                        if numbers:
                            relevance_score = float(numbers[0])
                        else:
                            # 숫자를 찾을 수 없으면 기본값 5점
                            print(f"[Re-rank {idx+1}] LLM 응답 파싱 실패: '{response_text}' - 기본값 5점 사용")
                            relevance_score = 5.0
                
                relevance_score = max(0, min(10, relevance_score))  # 0-10 범위로 제한
                
                # 최종 점수 = (벡터 유사도 * 0.3) + (LLM 관련성 * 0.7)
                final_score = (result['score'] * 0.3) + (relevance_score / 10 * 0.7)
                
                result['relevance_score'] = relevance_score
                result['final_score'] = final_score
                reranked_results.append(result)
                
                print(f"[Re-rank {idx+1}] 벡터: {result['score']:.3f}, LLM: {relevance_score:.1f}/10, 최종: {final_score:.3f}")
                
            except Exception as e:
                print(f"Re-ranking 오류 (결과 {idx}): {e}")
                # 오류 발생 시 원본 점수 사용
                result['relevance_score'] = result['score'] * 10
                result['final_score'] = result['score']
                reranked_results.append(result)
        
        # 최종 점수로 정렬
        reranked_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # 상위 K개만 반환
        return reranked_results[:top_k]
        
    except Exception as e:
        print(f"Re-ranking 전체 오류: {e}")
        return results[:top_k]

def search_qdrant(query: str, limit: int = 5) -> List[dict]:
    """Qdrant에서 자연어 검색 (LLM Re-ranking 포함)"""
    try:
        if not openai_client:
            return []
        
        # 쿼리 임베딩 생성
        query_embedding = get_embedding(query)
        if not query_embedding:
            return []
        
        # Qdrant 검색 - Re-ranking을 위해 더 많은 후보 가져오기
        from qdrant_client.models import PointStruct, Distance
        search_limit = limit * 2  # 요청한 개수의 2배 가져오기 (속도 개선)
        search_result = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=search_limit
        ).points
        
        # 결과 포맷팅
        results = []
        for hit in search_result:
            task_id = hit.payload.get("task_id", "")
            
            # task_status.json에서 task 유효성 검증 및 원본 YouTube 제목 가져오기
            video_title = hit.payload.get("video_title", "")
            detail_page_exists = False
            summary_page_exists = False
            
            try:
                with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
                    task_status = json.load(f)
                    
                    if task_id in task_status:
                        task_info = task_status[task_id]
                        
                        # 원본 제목 가져오기
                        video_title = task_info.get("video_title", video_title)
                        
                        # detail 페이지 및 요약 페이지 파일 존재 확인
                        if "result" in task_info and task_info["result"]:
                            html_path = task_info["result"].get("html_path", "")
                            if html_path and os.path.exists(html_path):
                                detail_page_exists = True
                            
                            summary_html_path = task_info["result"].get("summary_html_path", "")
                            if summary_html_path and os.path.exists(summary_html_path):
                                summary_page_exists = True
                        
            except Exception as e:
                print(f"Task 검증 오류 (task_id: {task_id}): {e}")
            
            # 타임스탬프를 앵커 ID로 변환 (예: "08:30" -> "t_8_30")
            timestamp_str = hit.payload.get("timestamp_str", "")
            anchor_id = ""
            if timestamp_str:
                parts = timestamp_str.split(":")
                if len(parts) == 2:
                    anchor_id = f"t_{int(parts[0])}_{int(parts[1])}"
                elif len(parts) == 3:
                    anchor_id = f"t_{int(parts[0])*60 + int(parts[1])}_{int(parts[2])}"
            
            # YouTube 링크는 항상 제공, detail/summary 페이지는 존재 여부 표시
            results.append({
                "score": hit.score,
                "task_id": task_id,
                "video_title": video_title,
                "youtube_link": hit.payload.get("youtube_link", ""),
                "timestamp_str": timestamp_str,
                "anchor_id": anchor_id,
                "text": hit.payload.get("text", ""),
                "detail_page_exists": detail_page_exists,
                "summary_page_exists": summary_page_exists
            })
        
        # LLM Re-ranking 적용 (설정에 따라)
        enable_reranking = int(get_setting('enable_reranking', '1'))
        
        if results and enable_reranking == 1:
            print(f"[Search] Re-ranking 활성화: {len(results)}개 후보 → 상위 {limit}개 선택")
            results = rerank_with_llm(query, results, top_k=limit)
            # 최종 점수를 score로 업데이트
            for r in results:
                r['score'] = r.get('final_score', r['score'])
            
            # 최소 유사도 필터링
            min_threshold = float(get_setting('min_similarity_threshold', '0.5'))
            results = [r for r in results if r['score'] >= min_threshold]
            print(f"[Search] 유사도 {int(min_threshold*100)}% 이상 결과: {len(results)}개")
        elif results:
            print(f"[Search] Re-ranking 비활성화: 원본 점수 사용 ({len(results)}개)")
            # Re-ranking 없이 limit만큼만 반환
            results = results[:limit]
        
        print(results)
        return results
        
    except Exception as e:
        print(f"Qdrant 검색 오류: {e}")
        return []

def parse_html_segments(html_path: str) -> Tuple[List[dict], str, str]:
    """HTML 파일에서 세그먼트 정보 파싱"""
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 제목 추출
        title_tag = soup.find('h1')
        title = title_tag.text.strip() if title_tag else ""
        
        # YouTube URL 추출
        youtube_url = ""
        source_url = soup.find('p', class_='source-url')
        if source_url:
            link = source_url.find('a')
            if link:
                youtube_url = link.get('href', '')
        
        # 세그먼트 추출
        segments = []
        content_blocks = soup.find_all('div', class_='content-block')
        
        for block in content_blocks:
            # 이미지 컨테이너에서 타임스탬프 추출
            img_container = block.find('div', class_='image-container')
            if not img_container:
                continue
            
            timestamp = float(img_container.get('data-start-time', 0))
            
            # 캡션에서 번역된 텍스트 추출 (여러 클래스 시도)
            caption_div = block.find('div', class_='caption')
            if not caption_div:
                # markdown-body 클래스도 시도
                caption_div = block.find('div', class_='markdown-body')
            if not caption_div:
                # caption-container 안의 모든 텍스트 추출
                caption_container = block.find('div', class_='caption-container')
                if caption_container:
                    caption_div = caption_container
            if not caption_div:
                continue
            
            # 텍스트만 추출 (HTML 태그 제거)
            text = caption_div.get_text(strip=True)
            
            if text and len(text) > 10:
                segments.append({
                    'timestamp': timestamp,
                    'text': text
                })
        
        print(f"파싱 완료: {title}, {len(segments)}개 세그먼트")
        return segments, title, youtube_url
        
    except Exception as e:
        print(f"HTML 파싱 오류: {e}")
        return [], "", ""

def reindex_task_to_qdrant(task_id: str) -> dict:
    """기존 Task의 HTML을 파싱하여 Qdrant에 재인덱싱"""
    try:
        print(f"\n{'='*50}")
        print(f"재인덱싱 시작: Task ID {task_id}")
        print(f"{'='*50}")
        
        # Task 정보 가져오기
        with task_lock:
            if task_id not in task_status:
                return {"success": False, "error": "Task not found"}
            
            task = task_status[task_id]
            if task.get('status') != 'completed':
                return {"success": False, "error": "Task not completed"}
            
            result = task.get('result', {})
            # 원본 YouTube 제목 사용: task.video_title → result.original_title → result.title 순서
            video_title = task.get('video_title') or result.get('original_title') or result.get('title', '')
            html_path = result.get('html_path', '')
        
        if not html_path or not os.path.exists(html_path):
            return {"success": False, "error": "HTML file not found"}
        
        print(f"영상 제목: {video_title}")
        print(f"HTML 경로: {html_path}")
        
        # HTML 파싱
        print("\n[1/4] HTML 파일 파싱 중...")
        segments_data, parsed_title, youtube_url = parse_html_segments(html_path)
        
        if not segments_data:
            return {"success": False, "error": "No segments found in HTML"}
        
        print(f"✓ 파싱 완료: {len(segments_data)}개 세그먼트")
        
        # Segment 객체 생성 (translated 필드 사용)
        print("\n[2/4] Segment 객체 생성 중...")
        segments = []
        for i, seg_data in enumerate(segments_data):
            seg = Segment(
                start=seg_data['timestamp'],
                end=seg_data['timestamp'] + 5.0,  # 임시로 5초 간격
                texts=[seg_data['text']],
                image_path="",
                translated=seg_data['text']
            )
            segments.append(seg)
            if (i + 1) % 10 == 0:
                print(f"  - {i + 1}/{len(segments_data)} 세그먼트 처리됨")
        
        print(f"✓ {len(segments)}개 Segment 객체 생성 완료")
        
        # 중요 세그먼트 필터링
        print("\n[3/4] 중요 세그먼트 필터링 중 (LLM 사용)...")
        important_segments = filter_important_segments(segments)
        print(f"✓ 필터링 완료: {len(segments)}개 → {len(important_segments)}개")
        
        # Qdrant에 저장
        print("\n[4/4] Qdrant DB에 저장 중...")
        
        if not openai_client or not important_segments:
            return {"success": False, "error": "OpenAI client not available or no segments to store"}
        
        points = []
        for i, seg in enumerate(important_segments):
            # 100글자 미만 세그먼트 필터링
            if not seg.translated or len(seg.translated.strip()) < 100:
                continue
            
            # 임베딩 생성
            embedding = get_embedding(seg.translated)
            if not embedding:
                print(f"  ⚠ 세그먼트 {i}: 임베딩 생성 실패")
                continue
            
            # YouTube 타임스탬프 링크 생성
            timestamp_seconds = int(seg.start)
            youtube_link = f"{youtube_url}&t={timestamp_seconds}s"
            
            # 고유 UUID 생성 (task_id와 인덱스 조합)
            import hashlib
            unique_string = f"{task_id}_{i}_{seg.start}"
            point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, unique_string))
            
            # Qdrant 포인트 생성
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "task_id": task_id,
                    "video_title": video_title or parsed_title,
                    "youtube_url": youtube_url,
                    "youtube_link": youtube_link,
                    "timestamp": seg.start,
                    "timestamp_str": f"{int(seg.start // 60):02d}:{int(seg.start % 60):02d}",
                    "text": seg.translated
                }
            )
            points.append(point)
            
            if (i + 1) % 5 == 0:
                print(f"  - {i + 1}/{len(important_segments)} 임베딩 생성됨")
        
        if points:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"✓ Qdrant에 {len(points)}개 포인트 저장 완료")
        else:
            return {"success": False, "error": "No valid embeddings generated"}
        
        print(f"\n{'='*50}")
        print(f"재인덱싱 완료: {video_title}")
        print(f"{'='*50}\n")
        
        return {
            "success": True,
            "video_title": video_title or parsed_title,
            "total_segments": len(segments_data),
            "filtered_segments": len(important_segments),
            "stored_points": len(points)
        }
        
    except Exception as e:
        print(f"재인덱싱 오류: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@dataclass
class Caption:
    start: float
    end: float
    text: str

@dataclass
class Segment:
    start: float
    end: float
    texts: List[str]
    image_path: str
    translated: str = ""

def sanitize_filename(title: str, max_len: int = 50, suffix: str = "") -> str:
    """??????????????? ?????? ??????????????? ?????? ??????"""
    # ???????????? ??????
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    # ????????? ??????????????????
    safe = safe.replace(' ', '_').strip('_')
    if not safe:
        safe = "untitled"
    if len(safe) <= max_len:
        return safe

    # ??? ????????? ??????????????? ????????? ??????/????????? ??????
    suffix_safe = re.sub(r'[<>:"/\\|?* ]', '_', suffix).strip('_')
    if not suffix_safe:
        suffix_safe = hashlib.md5(title.encode("utf-8")).hexdigest()[:8]

    suffix_part = "_" + suffix_safe
    if len(suffix_part) >= max_len:
        suffix_part = "_" + suffix_safe[: max_len - 1]

    base_len = max_len - len(suffix_part)
    if base_len < 1:
        return safe[:max_len]
    return safe[:base_len] + suffix_part

def extract_youtube_video_id(url: str) -> str:
    """YouTube URL에서 video ID 추출"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'v=([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""

def update_ytdlp():
    """yt-dlp 업데이트"""
    print("[1/9] yt-dlp 업데이트 확인 중...")
    try:
        subprocess.run(["pip", "install", "--upgrade", "yt-dlp"], check=True)
        print("yt-dlp 업데이트 완료")
    except Exception as e:
        print(f"yt-dlp 업데이트 실패: {e}")

def download_video(url: str, output_path: Path) -> Tuple[str, str]:
    """YouTube 영상 다운로드 (1080p)"""
    print("[2/9] YouTube 영상 다운로드 중...")
    
    # 쿠키 파일 경로 확인
    cookie_file = DATA_DIR / "youtube_cookies.txt"
    
    # 먼저 제목 가져오기 (재시도 로직 포함)
    original_title = None
    max_title_retries = 3
    
    for retry in range(max_title_retries):
        try:
            # yt-dlp 명령 구성 (제목만 가져오기, 공통 옵션 사용)
            cmd = ["yt-dlp", *YT_DLP_COMMON_OPTIONS, "--no-playlist", "--get-title"]
            
            # 쿠키 파일이 있으면 사용
            if cookie_file.exists():
                cmd.extend(["--cookies", str(cookie_file)])
                print(f"쿠키 파일 사용: {cookie_file}")
            
            cmd.append(url)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=30
            )
            
            # stdout에서 제목 추출
            original_title = result.stdout.strip()
            
            if original_title and original_title.lower() != "unknown":
                print(f"제목 가져오기 성공: {original_title}")
                break
            else:
                print(f"제목 가져오기 실패 (종료 코드 {result.returncode}). 재시도 {retry + 1}/{max_title_retries}")
                if result.stderr:
                    print(f"오류 메시지: {result.stderr[:500]}")
                original_title = None
                time.sleep(2)
        except subprocess.TimeoutExpired:
            print(f"제목 가져오기 타임아웃. 재시도 {retry + 1}/{max_title_retries}")
            time.sleep(2)
        except Exception as e:
            print(f"제목 가져오기 실패: {e}. 재시도 {retry + 1}/{max_title_retries}")
            time.sleep(2)
    
    # 모든 재시도 실패 시
    if not original_title:
        raise RuntimeError("제목을 가져올 수 없습니다. 영상 URL을 확인해주세요.")
    
    video_id = extract_youtube_video_id(url)
    if video_id:
        safe_title = video_id
    else:
        safe_title = sanitize_filename(original_title, max_len=50)
    video_dir = output_path / safe_title
    video_dir.mkdir(parents=True, exist_ok=True)
    
    video_file = video_dir / f"{safe_title}.mp4"
    
    # 이미 파일이 존재하면 다운로드 생략
    if video_file.exists():
        print(f"비디오 파일이 이미 존재합니다. 다운로드 생략: {video_file}")
        return str(video_file), safe_title
    
    # 720p 영상 다운로드
    try:
        # yt-dlp 명령 구성 (공통 옵션 사용)
        cmd = ["yt-dlp", *YT_DLP_COMMON_OPTIONS, "--no-playlist"]
        
        # 쿠키 파일이 있으면 사용
        if cookie_file.exists():
            cmd.extend(["--cookies", str(cookie_file)])
        
        cmd.extend([
            "-f", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", str(video_file),
            "--no-part",
            "--no-continue",
            "--concurrent-fragments", "1",
            url
        ])
        
        subprocess.run(cmd, check=True)
        print(f"다운로드 완료: {video_file}")
        return str(video_file), safe_title
    except Exception as e:
        raise RuntimeError(f"영상 다운로드 실패: {e}")

def extract_audio(video_path: str, audio_path: str):
    """ffmpeg로 mp3 추출"""
    print("[3/9] 오디오 추출 중...")
    
    # 이미 파일이 존재하면 추출 생략
    if os.path.exists(audio_path):
        print(f"오디오 파일이 이미 존재합니다. 추출 생략: {audio_path}")
        return
    
    try:
        subprocess.run([
            "ffmpeg",
            "-i", video_path,
            "-vn",
            "-acodec", "libmp3lame",
            "-q:a", "2",
            "-y",
            audio_path
        ], check=True, capture_output=True)
        print(f"오디오 추출 완료: {audio_path}")
    except Exception as e:
        raise RuntimeError(f"오디오 추출 실패: {e}")

def split_audio_file(audio_path: str, max_size_mb: int = 12) -> List[str]:
    """MP3 파일을 크기 제한에 맞춰 분할"""
    file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
    
    if file_size_mb <= max_size_mb:
        return [audio_path]
    
    print(f"오디오 파일 크기: {file_size_mb:.2f}MB, 분할 필요")
    
    # ffprobe로 전체 길이 확인
    probe_cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        audio_path
    ]
    
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"오디오 길이 확인 실패: {e}")
    
    # 청크 개수 계산
    num_chunks = int(np.ceil(file_size_mb / max_size_mb))
    chunk_duration = total_duration / num_chunks
    
    print(f"총 {num_chunks}개 청크로 분할 (청크당 약 {chunk_duration:.1f}초)")
    
    # 청크 파일 생성
    chunk_files = []
    base_path = Path(audio_path)
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        chunk_path = base_path.parent / f"{base_path.stem}_chunk{i}{base_path.suffix}"
        
        split_cmd = [
            "ffmpeg",
            "-i", audio_path,
            "-ss", str(start_time),
            "-t", str(chunk_duration),
            "-acodec", "copy",
            "-y",
            str(chunk_path)
        ]
        
        try:
            subprocess.run(split_cmd, check=True, capture_output=True)
            chunk_files.append(str(chunk_path))
            print(f"청크 {i+1}/{num_chunks} 생성: {chunk_path}")
        except Exception as e:
            # 실패 시 생성된 청크들 삭제
            for cf in chunk_files:
                try:
                    os.remove(cf)
                except:
                    pass
            raise RuntimeError(f"오디오 분할 실패: {e}")
    
    return chunk_files

def merge_srt_segments(srt_texts: List[str], chunk_durations: List[float]) -> str:
    """여러 SRT 텍스트를 타임스탬프 조정하여 병합"""
    SRT_TS = re.compile(
        r"(?P<h1>\d{2}):(?P<m1>\d{2}):(?P<s1>\d{2}),(?P<ms1>\d{3})\s*-->\s*"
        r"(?P<h2>\d{2}):(?P<m2>\d{2}):(?P<s2>\d{2}),(?P<ms2>\d{3})"
    )
    
    def to_sec(h, m, s, ms):
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
    
    def to_srt_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    merged_blocks = []
    time_offset = 0.0
    global_index = 1
    
    for chunk_idx, srt_text in enumerate(srt_texts):
        if not srt_text.strip():
            continue
        
        blocks = re.split(r"\n{2,}", srt_text.strip())
        
        for block in blocks:
            lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if len(lines) < 2:
                continue
            
            # 타임스탬프 찾기
            ts_line = None
            for ln in lines:
                if SRT_TS.match(ln):
                    ts_line = ln
                    break
            
            if not ts_line:
                continue
            
            m = SRT_TS.match(ts_line)
            start = to_sec(m.group("h1"), m.group("m1"), m.group("s1"), m.group("ms1"))
            end = to_sec(m.group("h2"), m.group("m2"), m.group("s2"), m.group("ms2"))
            
            # 타임스탬프에 오프셋 추가
            adjusted_start = start + time_offset
            adjusted_end = end + time_offset
            
            # 텍스트 추출
            idx = lines.index(ts_line)
            text = "\n".join(lines[idx+1:])
            
            # 새로운 블록 생성
            new_block = f"{global_index}\n{to_srt_time(adjusted_start)} --> {to_srt_time(adjusted_end)}\n{text}"
            merged_blocks.append(new_block)
            global_index += 1
        
        # 다음 청크를 위한 오프셋 추가
        if chunk_idx < len(chunk_durations):
            time_offset += chunk_durations[chunk_idx]
    
    return "\n\n".join(merged_blocks)

def transcribe_audio(audio_path: str, srt_path: str):
    """Faster Whisper (로컬 버전)를 사용하여 스크립트 추출"""
    print("[4/10] Whisper AI로 자막 생성 중...")
    
    if os.path.exists(srt_path):
        print(f"SRT 파일이 이미 존재합니다. 생성 생략: {srt_path}")
        return
        
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise RuntimeError("faster-whisper 모듈이 설치되지 않았습니다. (pip install faster-whisper)")
        
    try:
        import time
        model_size = "turbo"
        
        print(f"[WHISPER] 📥 모델 로딩 중... (모델: {model_size})")
        # GPU 환경(CUDA)을 위한 설정 (YoutubeAnalyzer와 동일)
        device = "cuda"
        compute_type = "float16"
        
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(f"[WHISPER] ✓ 모델 로딩 완료")
        
        print(f"[WHISPER] 🧠 딥러닝 추론 시작 ({audio_path})...")
        segments, info = model.transcribe(audio_path, beam_size=5)
        
        print(f"[WHISPER]    - 감지된 언어: {info.language} ({info.language_probability*100:.2f}%)")
        print(f"[WHISPER] 📝 세그먼트 처리 및 SRT 생성 중...")
        
        def format_time(seconds):
            msec = int((seconds - int(seconds)) * 1000)
            sec = int(seconds)
            h = sec // 3600
            m = (sec % 3600) // 60
            s = sec % 60
            return f"{h:02d}:{m:02d}:{s:02d},{msec:03d}"
            
        srt_content = ""
        for idx, segment in enumerate(segments, start=1):
            start_fmt = format_time(segment.start)
            end_fmt = format_time(segment.end)
            text = segment.text.strip()
            # print(f"[{start_fmt} -> {end_fmt}] {text}")
            srt_content += f"{idx}\n{start_fmt} --> {end_fmt}\n{text}\n\n"
            
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
            
        print(f"✅ 자막 생성 완료: {srt_path}")
        
    except Exception as e:
        raise RuntimeError(f"자막 생성 실패: {e}")

def parse_srt(srt_path: str) -> List[Caption]:
    """SRT 파일 파싱"""
    print("[5/9] SRT 파싱 중...")
    
    SRT_TS = re.compile(
        r"(?P<h1>\d{2}):(?P<m1>\d{2}):(?P<s1>\d{2}),(?P<ms1>\d{3})\s*-->\s*"
        r"(?P<h2>\d{2}):(?P<m2>\d{2}):(?P<s2>\d{2}),(?P<ms2>\d{3})"
    )
    
    with open(srt_path, "r", encoding="utf-8") as f:
        raw = f.read()
    
    blocks = re.split(r"\n{2,}", raw.strip())
    captions = []
    
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        
        ts_line = None
        for ln in lines:
            if SRT_TS.match(ln):
                ts_line = ln
                break
        
        if not ts_line:
            continue
        
        m = SRT_TS.match(ts_line)
        
        def to_sec(h, m, s, ms):
            return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000.0
        
        start = to_sec(m.group("h1"), m.group("m1"), m.group("s1"), m.group("ms1"))
        end = to_sec(m.group("h2"), m.group("m2"), m.group("s2"), m.group("ms2"))
        
        idx = lines.index(ts_line)
        text = " ".join(lines[idx+1:]).strip()
        
        if text:
            captions.append(Caption(start=start, end=end, text=text))
    
    print(f"자막 세그먼트 수: {len(captions)}")
    return captions

def extract_frames(video_path: str, captions: List[Caption], images_dir: Path, task_id: str = None, max_workers: int = 10) -> List[Segment]:
    """자막 타임스탬프 중간 시점에서 프레임 추출 (ffmpeg 사용 + 병렬 처리)
    
    Args:
        max_workers: 동시에 실행할 최대 ffmpeg 프로세스 수 (기본값: 10)
                    값이 클수록 빠르지만 CPU/메모리 사용량 증가
    """
    print(f"[6/9] 프레임 추출 중 (병렬 처리: {max_workers}개)")
    
    def update_progress(message: str):
        """프레임 추출 진행상황 업데이트"""
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["progress"] = f"[6/10] {message}"
                    save_task_status()
    
    images_dir.mkdir(parents=True, exist_ok=True)
    
    # 기존 이미지 개수 확인
    existing_images = list(images_dir.glob("frame*.webp"))
    expected_count = len(captions)
    
    if len(existing_images) == expected_count:
        print(f"이미지 개수({len(existing_images)})가 자막 세그먼트 수({expected_count})와 일치합니다. 추출 생략.")
        # 기존 이미지로 세그먼트 생성
        segments = []
        for i, caption in enumerate(captions):
            img_path = images_dir / f"frame{i:04d}.webp"
            if img_path.exists():
                segments.append(Segment(
                    start=caption.start,
                    end=caption.end,
                    texts=[caption.text],
                    image_path=str(img_path)
                ))
        return segments
    elif len(existing_images) > 0:
        print(f"이미지 개수({len(existing_images)})가 자막 세그먼트 수({expected_count})와 다릅니다. 기존 이미지 삭제 후 재추출.")
        # 기존 이미지 모두 삭제
        import shutil
        shutil.rmtree(images_dir)
        images_dir.mkdir(parents=True, exist_ok=True)
    
    total_frames = len(captions)
    update_progress(f"프레임 추출 준비 완료 (총 {total_frames}개)")
    
    # 병렬 처리를 위한 함수
    def extract_single_frame(index: int, caption: Caption):
        """단일 프레임 추출"""
        mid_time = (caption.start + caption.end) / 2
        img_path = images_dir / f"frame{index:04d}.webp"
        
        try:
            # ffmpeg로 특정 시점의 프레임 추출
            process = subprocess.Popen([
                "ffmpeg",
                "-ss", str(mid_time),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "75",  # WebP 품질 75
                "-y",
                str(img_path)
            ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            
            # 프로세스를 낮은 우선순위로 설정
            try:
                import psutil
                p = psutil.Process(process.pid)
                p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == 'nt' else 10)
            except:
                pass
            
            # 프로세스 완료 대기
            process.wait(timeout=30)
            
            if process.returncode == 0:
                return Segment(
                    start=caption.start,
                    end=caption.end,
                    texts=[caption.text],
                    image_path=str(img_path)
                )
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"프레임 추출 타임아웃 [{index}]")
        except Exception as e:
            print(f"프레임 추출 실패 [{index}]: {e}")
        
        return None
    
    # ThreadPoolExecutor를 사용한 병렬 처리
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    segments = []
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 모든 프레임 추출 작업 제출
        future_to_index = {
            executor.submit(extract_single_frame, i, caption): i 
            for i, caption in enumerate(captions)
        }
        
        # 완료된 작업 처리
        for future in as_completed(future_to_index):
            completed_count += 1
            segment = future.result()
            
            if segment:
                segments.append(segment)
            
            # 진행상황 업데이트 (10% 단위)
            if completed_count % max(1, total_frames // 10) == 0 or completed_count == total_frames:
                percentage = completed_count * 100 // total_frames
                update_progress(f"프레임 추출 중 {completed_count}/{total_frames} ({percentage}%)")
                print(f"프레임 추출 진행: {completed_count}/{total_frames} ({percentage}%)")
    
    # 시작 시간 순으로 정렬
    segments.sort(key=lambda s: s.start)
    
    print(f"프레임 추출 완료: {len(segments)}개")
    update_progress(f"프레임 추출 완료 ({len(segments)}개)")
    return segments
    return segments

def deduplicate_segments(segments: List[Segment], threshold: float = 30.0, task_id: str = None) -> List[Segment]:
    """중복 이미지 감지 및 세그먼트 병합"""
    print("[7/9] 중복 이미지 감지 및 병합 중...")
    
    def update_progress(message: str):
        """중복 이미지 감지 진행상황 업데이트"""
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["progress"] = f"[7/10] {message}"
                    save_task_status()
    
    if not segments:
        return []
    
    total_segments = len(segments)
    update_progress(f"중복 이미지 감지 준비 (총 {total_segments}개)")
    
    merged = []
    prev_img = None
    current_seg = segments[0]
    
    for i, seg in enumerate(segments):
        # 진행상황 업데이트 (10% 단위)
        if i % max(1, total_segments // 10) == 0 or i == total_segments - 1:
            percentage = (i + 1) * 100 // total_segments
            update_progress(f"중복 이미지 감지 중 {i+1}/{total_segments} ({percentage}%)")
        
        # 이미지 로드 및 리사이징
        img = cv2.imread(seg.image_path)
        if img is None:
            continue
        
        # 해상도 0.5배로 축소
        h, w = img.shape[:2]
        small = cv2.resize(img, (int(w * 0.5), int(h * 0.5)))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        if prev_img is not None:
            # 픽셀 평균값 차이 계산
            diff = cv2.absdiff(prev_img, gray)
            score = diff.mean()
            
            if score < threshold:
                # 중복: 현재 세그먼트에 텍스트 추가
                current_seg.texts.extend(seg.texts)
                current_seg.end = seg.end
                # 중복 이미지 삭제
                try:
                    os.remove(seg.image_path)
                except:
                    pass
            else:
                # 중복 아님: 현재 세그먼트 저장하고 새로 시작
                merged.append(current_seg)
                current_seg = seg
        
        prev_img = gray
    
    # 마지막 세그먼트 추가
    if current_seg:
        merged.append(current_seg)
    
    print(f"병합 후 세그먼트 수: {len(merged)}개")
    update_progress(f"중복 제거 완료 ({total_segments}개 → {len(merged)}개)")
    return merged

def translate_segments(segments: List[Segment], task_id: str = None):
    """LLM으로 세그먼트 텍스트 번역"""
    print("[8/9] 번역 중...")
    
    def update_progress(message: str):
        """번역 진행상황 업데이트"""
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["progress"] = f"[8/10] {message}"
                    save_task_status()
    
    if not GEMINI_API_KEY:
        print("Gemini API 키가 없어 번역 생략")
        for seg in segments:
            seg.translated = " ".join(seg.texts)
        return
    
    total_segments = len(segments)
    update_progress(f"번역 준비 완료 (총 {total_segments}개 세그먼트)")
    
    # 데이터베이스에서 프롬프트 가져오기
    prompts = get_prompts()
    system_prompt = prompts["system_prompt"]
    user_prompt_template = prompts["user_prompt_template"]
    translation_model = prompts.get("translation_model", "gemini-3.1-flash-lite-preview")
    if translation_model.startswith("gpt-") or "2.5-flash" in translation_model:
         translation_model = "gemini-3.1-flash-lite-preview"
    
    import json
    batch_size = 50
    
    # 일괄 처리를 위한 시스템 프롬프트 강화
    batch_system_prompt = system_prompt + "\n\nIMPORTANT INSTRUCTION: The user provides a JSON array of objects `[{\"id\": 0, \"text\": \"English sentence...\"}, ...]`. You MUST translate the 'text' fields to Korean and return ONLY a valid JSON array of objects with the exact same 'id' and the translated 'text', e.g., `[{\"id\": 0, \"text\": \"한국어 번역...\"}, ...]`. Do not add any other keys. Make sure to return exactly as many objects as provided."

    for i in range(0, total_segments, batch_size):
        batch = segments[i:i + batch_size]
        percentage = (i + len(batch)) * 100 // total_segments
        update_progress(f"번역 중 {i+1}~{i+len(batch)}/{total_segments} ({percentage}%)")
        
        request_data = [{"id": j, "text": " ".join(seg.texts)} for j, seg in enumerate(batch)]
        batch_text = json.dumps(request_data, ensure_ascii=False)
        user_content = user_prompt_template.replace("{text}", batch_text)
        
        try:
            response = gemini_client.models.generate_content(
                model=translation_model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=batch_system_prompt,
                    response_mime_type="application/json"
                )
            )
            response_text = response.text.strip()
            # 마크다운 코드 블록 제거 (혹시 포함된 경우 방어코드)
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            batch_result = json.loads(response_text)
            
            meaningless_responses = [
                '', ' ', '  ', '   ', '.', '..', '...', '-', '--', '---', '_', '__', 
                'N/A', 'None', '없음', "'", "' '", "''", '"', '" "', '""', '?', '??', '!', '!!'
            ]
            
            for item in batch_result:
                idx = item.get("id")
                translated = item.get("text", "")
                if idx is not None and 0 <= idx < len(batch):
                    if not translated or translated.strip() in meaningless_responses:
                        batch[idx].translated = ""
                    else:
                        batch[idx].translated = str(translated).strip()
            print(f"번역 완료 [배치 {i//batch_size + 1}]")
            
        except Exception as e:
            print(f"번역 실패 [배치 {i//batch_size + 1}]: {e}")
            # 실패 시 원본 텍스트 유지 방어
            for j, seg in enumerate(batch):
                seg.translated = " ".join(seg.texts)
    
    update_progress(f"번역 완료 (총 {total_segments}개)")

def summarize_all_captions(captions: List[Caption], task_id: str = None) -> dict:
    """전체 자막을 하나로 합쳐서 LLM으로 요약 및 태그 생성"""
    print("[요약] 전체 자막 요약 및 태그 생성 중...")
    
    def update_progress(message: str):
        """요약 진행상황 업데이트"""
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["progress"] = f"[10/10] {message}"
                    save_task_status()
    
    if not GEMINI_API_KEY:
        print("Gemini API 키가 없어 요약 생략")
        return {"summary": "요약을 생성할 수 없습니다.", "tags": []}
    
    # API 키 확인 (디버깅용)
    print(f"[디버그] GEMINI_API_KEY 존재: {bool(GEMINI_API_KEY)}")
    
    update_progress("요약 생성 준비 중...")
    
    # 데이터베이스에서 요약 프롬프트 가져오기
    prompts = get_prompts()
    summary_system_prompt = prompts.get("summary_system_prompt", "You are a professional summarizer.")
    summary_user_prompt_template = prompts.get("summary_user_prompt_template", "{text}")
    translation_model = prompts.get("translation_model", "gemini-3.1-flash-lite-preview")
    if translation_model.startswith("gpt-") or "2.5-flash" in translation_model:
         translation_model = "gemini-3.1-flash-lite-preview"
    
    # 모든 자막 텍스트 합치기
    all_text = " ".join([cap.text for cap in captions])
    
    # 프롬프트 템플릿에 텍스트 삽입
    user_content = summary_user_prompt_template.replace("{text}", all_text)
    
    update_progress("요약 생성 중... (API 호출)")
    
    try:
        response = gemini_client.models.generate_content(
            model=translation_model,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=summary_system_prompt,
            )
        )
        summary = response.text.strip()
        print("요약 완료")
        
        # 태그 생성
        update_progress("태그 생성 중...")
        
        try:
            tag_response = gemini_client.models.generate_content(
                model=translation_model,
                contents=f"Extract 4 key English tags from this content:\n\n{all_text[:2000]}",
                config=types.GenerateContentConfig(
                    system_instruction="You are a content analyzer. Extract 4 relevant English tags from the given text. Return ONLY a JSON array of 4 English tags, nothing else. Use technical/professional terms in English. Example: [\"AI\", \"Machine Learning\", \"Neural Networks\", \"Computer Vision\"]",
                    response_mime_type="application/json"
                )
            )
            tag_content = tag_response.text.strip()
            
            print(f"태그 생성 응답: {tag_content}")
            
            # JSON 파싱
            tags = json.loads(tag_content)
            if not isinstance(tags, list):
                print(f"태그가 리스트가 아님: {type(tags)}")
                tags = []
            tags = tags[:4]  # 최대 4개
            print(f"태그 생성 완료: {tags}")
        except json.JSONDecodeError as e:
            print(f"태그 JSON 파싱 실패: {e}, 응답: {tag_content if 'tag_content' in locals() else 'N/A'}")
            tags = []
        except Exception as e:
            print(f"태그 생성 실패: {e}")
            tags = []
        
        update_progress("요약 및 태그 생성 완료")
        return {"summary": summary, "tags": tags}
    except Exception as e:
        print(f"요약 실패: {e}")
        update_progress(f"요약 생성 실패: {e}")
        return {"summary": f"요약 생성 실패: {str(e)}", "tags": []}

def generate_html(segments: List[Segment], output_path: Path, file_title: str, youtube_url: str = "", display_title: str = ""):
    """HTML 리포트 생성"""
    print("[9/9] HTML 생성 중...")
    
    html_path = output_path / f"{file_title}.html"
    page_title = display_title or file_title
    
    # YouTube video ID 추출
    video_id = ""
    if youtube_url:
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'v=([^&\n?#]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                video_id = match.group(1)
                break
    
    html = []
    html.append(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title}</title>
    <style>body {{ font-family: "나눔고딕","Malgun Gothic","맑은고딕","굴림","돋움","Helvetica","Apple SD Gothic Neo","sans-serif"; line-height: 1.6; margin: 0; padding: 0; background-color: #121212;color: #e0e0e0; }}
        .progress-container {{ width: 100%; height: 1px;  position: fixed; top: 0; left: 0; z-index: 100;}}
        .progress-bar {{ height: 1px; background: #007bff; width: 0%; transition: width 0.2s; }}
        .youtube-container {{
            position: fixed;
            z-index: 10;
            display: none;
            top: 0;
            z-index: 10;
            background: #11111100;
            padding-bottom: 0px;
            border-bottom: 1px solid #444;
        }}
        #player {{
            border-radius: 4px; 
        }}
        .image-container:hover {{
            cursor: pointer;
        }}
/* Markdown Table Styles */
.markdown-body table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    color: #ffffff;
    background-color: black;
}}
.markdown-body th,
.markdown-body td {{
    border: 1px solid #555;
    padding: 8px 12px;
    text-align: left;
}}

.markdown-body th {{
    background-color: #2a2a2a;
    font-weight: bold;
}}
.markdown-body hr {{
    height: 2px !important;
    background-color: #10b981 !important;
    border: none !important;
    margin: 25px 0 !important;
    opacity: 0.8 !important;
    display: block !important;
    width: 100% !important;
}}
.markdown-body * {{
    text-indent: 0.8 !important;
}}

/* garo */
@media (min-aspect-ratio: 1.1/1) {{
    
    .youtube-container {{
                width: 70%;
                float: left;
                margin-right: 1px;
            }}
    .container {{ max-width: 100%; margin: auto; background: transparent; padding: 0; }}
    .content-block {{ 
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1px;
        margin-bottom: 20px;
    }}
    .image-container {{
        flex-basis: 70%;
        flex-shrink: 0;
    }}
    .image-container img {{
        width: 100%;
        height: auto;
    }}
    .caption-container {{
        flex-basis: 30%;
    }}
    .content-block .caption {{ text-indent: 0.8em; font-size: 1em; padding: 5px 5px;margin:0; }}
    .markdown-body ul {{ padding-left: 10px; margin: 0; }}
    .markdown-body li {{ padding-right: 5px; margin:0; font-size: 1em; }}
    .markdown-body p {{ font-size: 1em; padding: 0px 0px;}}
}}
/* sero */
@media (max-aspect-ratio: 1.1/1) {{
        .container {{ max-width: 100%; margin: auto; background: transparent; padding: 0; }}
        .content-block {{ max-width: 100%; margin-bottom: 20px; text-align: left; }}
        .content-block img {{ max-width: 100%; padding: 0; margin: 1px auto; display: block; }}
        .caption {{ text-indent: 0.8em; font-size: 1em; width: 90%; padding: 5px 10px; margin: 0 auto 0 auto; box-sizing: border-box; }}
    .markdown-body ul {{ padding-left: 15px; margin: 0; }}
    .markdown-body li {{ padding-right: 5px; margin: 0; font-size: 1em; }}
    .markdown-body p {{ font-size: 1em; width: 100%; padding: 0px 0px; box-sizing: border-box; }}
}}
body {{ background-color: #121212; color: #e0e0e0; }} .content-block {{ background-color: #1e1e1e; }} h1 {{ color: #ffffff; }}</style>
</head>
<body>
    <div class="container">
        <h1 style="display: none;">{page_title}</h1>
        <p class="source-url" style="display: none;"><a href="{youtube_url}" target="_blank">{youtube_url}</a></p>
        <div class='youtube-container'><div id='player'></div></div>
        <div class="progress-container"><div class="progress-bar" id="myBar"></div></div>
        
""")
    
    # 번역 결과가 있는 세그먼트만 HTML에 포함
    for i, seg in enumerate(segments):
        # 번역 결과가 비어있으면 건너뛰기
        if not seg.translated or seg.translated.strip() == "":
            continue
        
        rel_img = Path(seg.image_path).relative_to(output_path).as_posix()
        mid_time = (seg.start + seg.end) / 2
        
        # 타임스탬프를 앵커 ID로 사용 (예: t_0_30 = 0분 30초)
        minutes = int(seg.start // 60)
        seconds = int(seg.start % 60)
        anchor_id = f"t_{minutes}_{seconds}"
        
        html.append(f"""            <div class="content-block" id="{anchor_id}">
                <div class="image-container" data-start-time="{seg.start}"><img src="{rel_img}" alt="Frame at {mid_time:.2f}s"></div>
                <div class="caption-container">
                    <div class="caption markdown-body">{seg.translated}</div>
                </div>
            </div>
            """)
    
    html.append("""    </div>
    <!-- Marked.js 라이브러리 추가 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        // 페이지 로드 시 마크다운 변환 실행
        document.addEventListener('DOMContentLoaded', function() {
            document.querySelectorAll('.markdown-body').forEach(function(element) {
                element.innerHTML = marked.parse(element.textContent || element.innerText);
            });
        });
    </script>
    <script>
        var player;
        var videoId = \"""" + video_id + """\";
        var timeUpdater;
        var lastActivatedBlock = null;

        if (videoId) {
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        }

        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', {
                videoId: videoId,
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        }

        function onPlayerReady(event) {
            updatePlayerSize();
            window.addEventListener('resize', updatePlayerSize);
        }

        function updatePlayerSize() {
            if (!player || typeof player.setSize !== 'function') return;

            const aspectRatio = window.innerWidth / window.innerHeight;
            const isLandscape = aspectRatio > 1.1;
            const youtubeContainer = document.querySelector('.youtube-container');
            const container = document.querySelector('.container');
            const newWidth = isLandscape ? container.clientWidth * 0.7 : container.clientWidth;
            const newHeight = newWidth * (9 / 16);
            
            player.setSize(newWidth, newHeight);
        }

        function onPlayerStateChange(event) {
            if (event.data == YT.PlayerState.PLAYING) {
                timeUpdater = setInterval(updateActiveImage, 250);
            } else {
                clearInterval(timeUpdater);
            }
        }

        function updateActiveImage() {
            if (!player || typeof player.getCurrentTime !== 'function') return;
            var currentTime = player.getCurrentTime();
            var contentBlocks = document.querySelectorAll('.image-container');
            var activeBlock = null;

            for (var i = 0; i < contentBlocks.length; i++) {
                var block = contentBlocks[i];
                var startTime = parseFloat(block.dataset.startTime);
                if (currentTime >= startTime) {
                    activeBlock = block;
                } else {
                    break;
                }
            }

            document.querySelectorAll('.content-block.active').forEach(b => b.classList.remove('active'));
            if (activeBlock) {
                activeBlock.closest('.content-block').classList.add('active');
            }
        }

        window.onscroll = function() { scrollFunction(); };
        function scrollFunction() {
            var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            var scrolled = (winScroll / height) * 100;
            document.getElementById("myBar").style.width = scrolled + "%";

            const youtubeContainer = document.querySelector('.youtube-container');
            if (youtubeContainer && youtubeContainer.style.display === 'block' && lastActivatedBlock) {
                const rect = lastActivatedBlock.getBoundingClientRect();
                if (rect.top < 0 || rect.bottom > window.innerHeight) {
                    youtubeContainer.style.display = 'none';
                    player.pauseVideo();
                }
            }
        }

        document.querySelectorAll('.image-container').forEach(el => {
            el.addEventListener('click', function() {
                if (player) {
                    const youtubeContainer = document.querySelector('.youtube-container');
                    if (youtubeContainer.style.display !== 'block') {
                        youtubeContainer.style.display = 'block';
                        updatePlayerSize();
                    }
                    lastActivatedBlock = this.closest('.content-block');
                    const seekTime = parseFloat(this.dataset.startTime);
                    player.seekTo(seekTime, true);
                    player.playVideo();
                }
            });
        });


    </script>
</body>
</html>
""")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    
    print(f"HTML 생성 완료: {html_path}")
    return str(html_path)

def generate_summary_html(summary_text: str, output_path: Path, file_title: str, youtube_url: str = "", display_title: str = ""):
    """요약 HTML 생성 (YouTube 썸네일 + 요약 텍스트)"""
    print("[요약] 요약 HTML 생성 중...")
    
    html_path = output_path / f"{file_title}-summary.html"
    page_title = display_title or file_title
    
    # YouTube video ID 추출
    video_id = ""
    if youtube_url:
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'v=([^&\n?#]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, youtube_url)
            if match:
                video_id = match.group(1)
                break
    
    # 항상 YouTube 썸네일 사용
    image_html = ""
    if video_id:
        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        image_html = f'<div class="image-container" data-start-time="0.0"><img src="{thumbnail_url}" alt="YouTube Thumbnail" onerror="this.src=\'https://img.youtube.com/vi/{video_id}/hqdefault.jpg\'"></div>'
    
    html = []
    html.append(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page_title} - 요약</title>
    <style>body {{ font-family: "나눔고딕","Malgun Gothic","맑은고딕","굴림","돋움","Helvetica","Apple SD Gothic Neo","sans-serif"; line-height: 1.6; margin: 0; padding: 0; background-color: #121212;color: #e0e0e0; }}
        .detail-link-container {{ text-align: center; margin: 20px 0; display: flex; justify-content: center; gap: 10px; }}
        .detail-link-btn {{ display: inline-block; padding: 12px 24px; background-color: #10b981; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; transition: background-color 0.3s; }}
        .detail-link-btn:hover {{ background-color: #059669; }}
        .delete-link-btn {{ display: inline-block; padding: 12px 24px; background-color: #ef4444; color: white; text-decoration: none; border-radius: 4px; font-weight: bold; transition: background-color 0.3s; }}
        .delete-link-btn:hover {{ background-color: #dc2626; }}
        .progress-container {{ width: 100%; height: 1px;  position: fixed; top: 0; left: 0; z-index: 100;}}
        .progress-bar {{ height: 1px; background: #007bff; width: 0%; transition: width 0.2s; }}
        .youtube-container {{
            position: fixed;
            z-index: 10;
            display: none;
            top: 0;
            z-index: 10;
            background: #11111100;
            padding-bottom: 0px;
            border-bottom: 1px solid #444;
        }}
        #player {{
            border-radius: 4px; 
        }}
        .image-container:hover {{
            cursor: pointer;
        }}
.markdown-body table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    color: #ffffff;
    background-color: black;
}}
.markdown-body th,
.markdown-body td {{
    border: 1px solid #555;
    padding: 8px 12px;
    text-align: left;
}}

.markdown-body th {{
    background-color: #2a2a2a;
    font-weight: bold;
}}
.markdown-body hr {{
    height: 2px !important;
    background-color: #10b981 !important;
    border: none !important;
    margin: 25px 0 !important;
    opacity: 0.8 !important;
    display: block !important;
    width: 100% !important;
}}
.markdown-body * {{
    text-indent: 0 !important;
}}

/* garo */
@media (min-aspect-ratio: 1/1) {{
    
    .youtube-container {{
                width: 70%;
                float: left;
                margin-right: 1px;
            }}
    .container {{ max-width: 100%; margin: auto; background: transparent; padding: 0; }}
    .content-block {{ 
        display: flex;
        flex-direction: row;
        align-items: flex-start;
        gap: 1px;
        margin-bottom: 20px;
    }}
    .image-container {{
        flex-basis: 70%;
        flex-shrink: 0;
    }}
    .image-container img {{
        width: 100%;
        height: auto;
    }}
    .caption-container {{
        flex-basis: 30%;
    }}
    .content-block .caption {{ text-indent: 0.8em; font-size: 0.9em; padding: 5px 5px;margin:0; }}
    .markdown-body ul {{ padding-left: 10px; margin: 0; }}
    .markdown-body li {{ padding-right: 5px; margin:0; font-size: 0.9em; }}
    .markdown-body p {{ font-size: 0.9em; padding: 0px 0px;margin:0; }}
}}
/* sero */
@media (max-aspect-ratio: 1/1) {{
        .container {{ max-width: 100%; margin: auto; background: transparent; padding: 0; }}
        .content-block {{ max-width: 100%; margin-bottom: 20px; text-align: left; }}
        .content-block img {{ max-width: 100%; padding: 0; margin: 1px auto; display: block; }}
        .caption {{ text-indent: 0.8em; font-size: 1em; width: 90%; padding: 5px 10px; margin: 0 auto 0 auto; box-sizing: border-box; }}
    .markdown-body ul {{ padding-left: 15px; margin: 0; }}
    .markdown-body li {{ padding-right: 5px; margin: 0; font-size: 1em; }}
    .markdown-body p {{ font-size: 1em; width: 100%; padding: 0px 0px; margin: 0 auto 0 auto; box-sizing: border-box; }}
}}
body {{ background-color: #121212; color: #e0e0e0; }} .content-block {{ background-color: #1e1e1e; }} h1 {{ color: #ffffff; }}</style>
</head>
<body>
    <div class="container">
        <h1 style="display: none;">{page_title} - 요약</h1>
        <p class="source-url" style="display: none;"><a href="{youtube_url}" target="_blank">{youtube_url}</a></p>
        <div class='youtube-container'><div id='player'></div></div>
        <div class="progress-container"><div class="progress-bar" id="myBar"></div></div>
        
            <div class="content-block">
                {image_html}
                <div class="caption-container">
                    <div class="caption markdown-body">{summary_text}</div>
                </div>
            </div>
            
            <div class="detail-link-container">
                <a href="detail" class="detail-link-btn">View Details</a>
                <a href="#" onclick="deleteRecord(); return false;" class="delete-link-btn">Delete</a>
            </div>
            
    </div>
    <!-- Marked.js 라이브러리 추가 -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script>
        // 페이지 로드 시 마크다운 변환 실행
        document.addEventListener('DOMContentLoaded', function() """ + """{
            document.querySelectorAll('.markdown-body').forEach(function(element) {
                // div 태그 안의 텍스트를 HTML로 변환
                element.innerHTML = marked.parse(element.textContent || element.innerText);
            });
        });
        
        function deleteRecord() {
            const taskIdMatch = window.location.pathname.match(/\\/view\\/([^\\/]+)/);
            const taskId = taskIdMatch ? taskIdMatch[1] : null;
            if (!taskId) {
                alert("문서 ID를 찾을 수 없습니다.");
                return;
            }
            if (confirm("정말로 이 문서를 제거하시겠습니까?\\n(서버에서 완전히 삭제되며 복구할 수 없습니다)")) {
                // 절대경로로 제거 API 호출
                const baseUrl = window.location.pathname.substring(0, window.location.pathname.indexOf('/view/'));
                fetch(baseUrl + '/delete/' + taskId, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        alert("문서가 제거되었습니다.");
                        if (window.opener) {
                            window.close();
                        } else {
                            window.location.href = baseUrl + '/';
                        }
                    } else {
                        alert("제거 실패: " + data.error);
                    }
                })
                .catch(e => alert("통신 중 오류 발생: " + e));
            }
        }
    </script>
    <script>
        var player;
        var videoId = \"""" + video_id + """\";
        var timeUpdater;
        var lastActivatedBlock = null;

        if (videoId) {
            var tag = document.createElement('script');
            tag.src = "https://www.youtube.com/iframe_api";
            var firstScriptTag = document.getElementsByTagName('script')[0];
            firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
        }

        function onYouTubeIframeAPIReady() {
            player = new YT.Player('player', {
                videoId: videoId,
                events: {
                    'onReady': onPlayerReady,
                    'onStateChange': onPlayerStateChange
                }
            });
        }

        function onPlayerReady(event) {
            updatePlayerSize();
            window.addEventListener('resize', updatePlayerSize);
        }

        function updatePlayerSize() {
            if (!player || typeof player.setSize !== 'function') return;

            const aspectRatio = window.innerWidth / window.innerHeight;
            const isLandscape = aspectRatio > 1.1;
            const youtubeContainer = document.querySelector('.youtube-container');
            const container = document.querySelector('.container');
            const newWidth = isLandscape ? container.clientWidth * 0.7 : container.clientWidth;
            const newHeight = newWidth * (9 / 16);
            
            player.setSize(newWidth, newHeight);
        }

        function onPlayerStateChange(event) {
            if (event.data == YT.PlayerState.PLAYING) {
                timeUpdater = setInterval(updateActiveImage, 250);
            } else {
                clearInterval(timeUpdater);
            }
        }

        function updateActiveImage() {
            if (!player || typeof player.getCurrentTime !== 'function') return;
            var currentTime = player.getCurrentTime();
            var contentBlocks = document.querySelectorAll('.image-container');
            var activeBlock = null;

            for (var i = 0; i < contentBlocks.length; i++) {
                var block = contentBlocks[i];
                var startTime = parseFloat(block.dataset.startTime);
                if (currentTime >= startTime) {
                    activeBlock = block;
                } else {
                    break;
                }
            }

            document.querySelectorAll('.content-block.active').forEach(b => b.classList.remove('active'));
            if (activeBlock) {
                activeBlock.closest('.content-block').classList.add('active');
            }
        }

        window.onscroll = function() """ + """{ scrollFunction(); };
        function scrollFunction() {
            var winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            var height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            var scrolled = (winScroll / height) * 100;
            document.getElementById("myBar").style.width = scrolled + "%";
            // 요약 페이지에서는 스크롤 시 YouTube 플레이어를 꺼지지 않도록 함
        }

        document.querySelectorAll('.image-container').forEach(el => {
            el.addEventListener('click', function() {
                if (player) {
                    const youtubeContainer = document.querySelector('.youtube-container');
                    if (youtubeContainer.style.display !== 'block') {
                        youtubeContainer.style.display = 'block';
                        updatePlayerSize();
                    }
                    lastActivatedBlock = this.closest('.content-block');
                    const seekTime = parseFloat(this.dataset.startTime);
                    player.seekTo(seekTime, true);
                    player.playVideo();
                }
            });
        });
    </script>
</body>
</html>
""")
    
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    
    print(f"요약 HTML 생성 완료: {html_path}")
    return str(html_path)

def cleanup_temp_files(video_dir: Path, safe_title: str, merged_segments: List[Segment]):
    """HTML과 실제 사용된 이미지만 유지하고 나머지 삭제"""
    print("[클린업] 임시 파일 삭제 중...")
    
    try:
        # 1. 비디오, 오디오, 자막 파일 삭제
        files_to_delete = [
            video_dir / f"{safe_title}.mp4",  # 비디오 파일
            video_dir / f"{safe_title}.mp3",  # 오디오 파일
            video_dir / f"{safe_title}.srt",  # 자막 파일
        ]
        
        # 청크 파일도 찾아서 삭제
        for chunk_file in video_dir.glob(f"{safe_title}_chunk*.mp3"):
            files_to_delete.append(chunk_file)
        
        deleted_count = 0
        deleted_size = 0
        
        for file_path in files_to_delete:
            if file_path.exists():
                try:
                    file_size = file_path.stat().st_size
                    os.remove(file_path)
                    deleted_count += 1
                    deleted_size += file_size
                    print(f"[클린업] 삭제: {file_path.name} ({file_size / (1024*1024):.2f}MB)")
                except Exception as e:
                    print(f"[클린업] 삭제 실패 {file_path.name}: {e}")
        
        # 2. 사용되지 않는 이미지 삭제
        images_dir = video_dir / "images"
        if images_dir.exists():
            # 실제 사용된 이미지 경로 수집
            used_images = set()
            for seg in merged_segments:
                if seg.image_path:
                    used_images.add(Path(seg.image_path).resolve())
            
            # 모든 이미지 파일 확인
            all_images = list(images_dir.glob("frame*.webp"))
            unused_count = 0
            unused_size = 0
            
            for img_path in all_images:
                if img_path.resolve() not in used_images:
                    try:
                        img_size = img_path.stat().st_size
                        os.remove(img_path)
                        unused_count += 1
                        unused_size += img_size
                        deleted_count += 1
                        deleted_size += img_size
                    except Exception as e:
                        print(f"[클린업] 이미지 삭제 실패 {img_path.name}: {e}")
            
            if unused_count > 0:
                print(f"[클린업] 미사용 이미지 삭제: {unused_count}개 ({unused_size / (1024*1024):.2f}MB)")
        
        if deleted_count > 0:
            print(f"[클린업] 완료: {deleted_count}개 파일 삭제 (총 {deleted_size / (1024*1024):.2f}MB 절약)")
        else:
            print("[클린업] 삭제할 임시 파일 없음")
            
    except Exception as e:
        print(f"[클린업] 오류: {e}")

def process_youtube_video(url: str, task_id: str = None) -> dict:
    """YouTube 영상 전체 처리 파이프라인"""
    def update_status(status: str, progress: str = "", video_title: str = None):
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["status"] = status
                    task_status[task_id]["progress"] = progress
                    if video_title:
                        task_status[task_id]["video_title"] = video_title
                    save_task_status()
    
    try:
        # 1. yt-dlp 업데이트
        update_status("processing", "[1/10] yt-dlp 업데이트 중...")
        update_ytdlp()
        
        # 2. 제목 가져오기 및 영상 다운로드
        update_status("processing", "[2/10] 영상 정보 확인 중...")
        try:
            # 공통 옵션 사용
            cmd = ["yt-dlp", *YT_DLP_COMMON_OPTIONS, "--no-playlist", "--get-title"]
            
            # 쿠키 파일이 있으면 사용
            cookie_file = Path(COOKIE_PATH)
            if cookie_file.exists():
                cmd.extend(["--cookies", COOKIE_PATH])
            
            cmd.append(url)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            original_title = result.stdout.strip()
            update_status("processing", f"[2/10] '{original_title}' 다운로드 중...", original_title)
        except Exception as e:
            print(f"제목 가져오기 실패: {e}")
            original_title = None
        
        video_path, safe_title = download_video(url, OUTPUT_DIR)
        if task_id:
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["safe_title"] = safe_title
                    save_task_status()
        
        # 원본 제목이 없으면 safe_title 사용
        if not original_title:
            original_title = safe_title
            update_status("processing", "[2/10] 영상 다운로드 완료", safe_title)
        video_dir = OUTPUT_DIR / safe_title
        
        # 3. 오디오 추출
        update_status("processing", "[3/10] 오디오 추출 중...")
        audio_path = str(video_dir / f"{safe_title}.mp3")
        extract_audio(video_path, audio_path)
        
        # 4. 자막 생성
        update_status("processing", "[4/10] 자막 생성 중...")
        srt_path = str(video_dir / f"{safe_title}.srt")
        transcribe_audio(audio_path, srt_path)
        
        # 5. SRT 파싱
        update_status("processing", "[5/10] SRT 파싱 중...")
        captions = parse_srt(srt_path)
        
        # 상세보기 HTML 생성 여부 확인
        skip_detail_html = int(get_setting('skip_detail_html', '0'))
        
        # 6. 프레임 추출 (상세보기 필요 시에만)
        segments = []
        merged_segments = []
        if skip_detail_html == 0:
            update_status("processing", "[6/10] 프레임 추출 준비 중...")
            images_dir = video_dir / "images"
            # max_workers: 동시 실행 ffmpeg 프로세스 수
            # 낮은 값(5): 안정적, CPU 부하 낮음
            # 중간 값(10): 균형잡힌 성능 (기본값)
            # 높은 값(20): 매우 빠름, CPU/메모리 부하 높음
            segments = extract_frames(video_path, captions, images_dir, task_id, max_workers=10)
            
            # 7. 중복 이미지 제거 및 병합
            update_status("processing", "[7/10] 중복 이미지 제거 중...")
            merged_segments = deduplicate_segments(segments, threshold=30.0, task_id=task_id)
            
            # 8. 번역
            update_status("processing", "[8/10] 번역 준비 중...")
            translate_segments(merged_segments, task_id)
        else:
            update_status("processing", "[6-8/10] 상세보기 건너뛰기 - 프레임 추출, 중복 제거, 번역 생략")
        
        # 9. HTML 생성 (옵션)
        html_path = None
        if skip_detail_html == 0:
            update_status("processing", "[9/10] 상세보기 HTML 생성 중...")
            html_path = generate_html(merged_segments, video_dir, safe_title, url, original_title)
        else:
            update_status("processing", "[9/10] 상세보기 HTML 생성 건너뜀")
        
        # 10. 요약 생성 및 요약 HTML 생성
        update_status("processing", "[10/10] 요약 및 태그 생성 중...")
        summary_result = summarize_all_captions(captions, task_id)
        summary_text = summary_result.get("summary", "")
        tags = summary_result.get("tags", [])
        
        # 요약 HTML은 항상 YouTube 썸네일 사용
        summary_html_path = generate_summary_html(summary_text, video_dir, safe_title, url, original_title)
        
        # 11. Qdrant에 세그먼트 저장 (원본 YouTube 제목 사용)
        update_status("processing", "[11/11] 벡터 DB 저장 중...")
        store_segments_to_qdrant(merged_segments, task_id, url, original_title)
        
        # 12. 임시 파일 클린업 (HTML과 실제 사용된 이미지만 유지)
        # auto_cleanup 설정이 활성화된 경우에만 클린업 수행
        auto_cleanup = int(get_setting('auto_cleanup', '1'))
        if auto_cleanup == 1 and skip_detail_html == 0:
            cleanup_temp_files(video_dir, safe_title, merged_segments)
        
        result = {
            "success": True,
            "title": safe_title,
            "original_title": original_title,
            "video_path": video_path,
            "html_path": html_path,
            "summary_html_path": summary_html_path,
            "segments": len(merged_segments),
            "tags": tags
        }
        
        update_status("completed", "완료")
        return result
    
    except Exception as e:
        update_status("failed", f"오류: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

def auto_publish_to_wiki(task_id: str, summary_html_path: str) -> bool:
    """Task 완료 후 자동으로 위키에 발행"""
    try:
        # Confluence 설정 확인
        if not all([CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN]):
            print(f"[Wiki] Confluence 설정이 없어 위키 발행을 건너뜁니다.")
            return False
        
        if not summary_html_path or not os.path.exists(summary_html_path):
            print(f"[Wiki] 요약 HTML 파일을 찾을 수 없어 위키 발행을 건너뜁니다.")
            return False
        
        print(f"[Wiki] Task {task_id} 위키 발행 시작...")
        
        # write_wiki 모듈 사용
        page_title, markdown_content = write_wiki.extract_markdown_from_html(summary_html_path)
        confluence_content = write_wiki.markdown_to_confluence(markdown_content)
        
        # Confluence 클라이언트 생성
        wiki = write_wiki.ConfluenceWiki(CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
        
        # 페이지 생성 또는 업데이트
        result = wiki.create_or_update_page(
            space_key=CONFLUENCE_SPACE_KEY,
            title=page_title,
            content=confluence_content,
            parent_id=CONFLUENCE_PARENT_PAGE_ID if CONFLUENCE_PARENT_PAGE_ID else None
        )
        
        page_url = f"{CONFLUENCE_URL}/pages/viewpage.action?pageId={result['id']}"
        print(f"[Wiki] ✅ 위키 발행 완료: {page_title}")
        print(f"[Wiki] URL: {page_url}")
        
        return True
        
    except Exception as e:
        print(f"[Wiki] ⚠️  위키 발행 실패: {e}")
        return False

def task_worker():
    """백그라운드에서 task queue를 처리하는 worker"""
    while True:
        try:
            task_id, url = task_queue.get()
            print(f"[Worker] Processing task {task_id}: {url}")
            
            try:
                with task_lock:
                    if task_id in task_status:
                        # 취소된 task는 처리하지 않음
                        if task_status[task_id]["status"] == "cancelled":
                            print(f"[Worker] Task {task_id} was cancelled, skipping...")
                            continue
                        
                        task_status[task_id]["status"] = "processing"
                        save_task_status()
                
                result = process_youtube_video(url, task_id)
                
                with task_lock:
                    if task_id in task_status:
                        task_status[task_id]["result"] = result
                        # process_youtube_video에서 이미 status를 "completed"로 설정하지만
                        # 명시적으로 다시 확인
                        if result.get("success"):
                            task_status[task_id]["status"] = "completed"
                        save_task_status()
                
                # Task 완료 후 자동 위키 발행
                if result.get("success"):
                    summary_html_path = result.get("summary_html_path")
                    if summary_html_path:
                        try:
                            auto_publish_to_wiki(task_id, summary_html_path)
                        except Exception as wiki_error:
                            print(f"[Worker] 위키 발행 실패 (계속 진행): {wiki_error}")
                
                # Task 완료 후 선호도 기반 자동 삭제 실행
                print(f"[Worker] Task 완료 - 자동 클린업 시작")
                try:
                    auto_cleanup_tasks_by_preference()
                    print(f"[Worker] 자동 클린업 완료")
                except Exception as cleanup_error:
                    print(f"[Worker] 자동 삭제 실패: {cleanup_error}")
                    import traceback
                    traceback.print_exc()
                        
                print(f"[Worker] Task {task_id} completed successfully")
                        
            except Exception as e:
                print(f"[Worker] Task {task_id} failed: {e}")
                with task_lock:
                    if task_id in task_status:
                        task_status[task_id]["status"] = "failed"
                        task_status[task_id]["progress"] = f"오류: {str(e)}"
                        task_status[task_id]["result"] = {"success": False, "error": str(e)}
                        save_task_status()
            finally:
                task_queue.task_done()
                print(f"[Worker] Task {task_id} done, waiting for next task...")
                
        except Exception as e:
            print(f"[Worker] Fatal error: {e}")
            import traceback
            traceback.print_exc()

@app.route('/')
def index():
    """메인 페이지"""
    return send_file('index.html')

@app.route('/ranking')
def ranking():
    """선호도 순위 페이지 (관리자 전용)"""
    from flask import session
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    return render_template('ranking.html')

@app.route('/search')
def search_page():
    """검색 페이지"""
    return render_template('search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    """자연어 검색 API"""
    try:
        print("\n" + "="*50)
        print("검색 API 호출됨")
        print("="*50)
        
        data = request.get_json()
        query = data.get('query', '').strip()
        
        print(f"원본 쿼리: {query}")
        
        if not query:
            return jsonify({"error": "검색어를 입력해주세요"}), 400
        
        # 1단계: LLM으로 쿼리 분석 및 확장
        expanded_query = query
        if gemini_client:
            try:
                print("쿼리 분석 및 확장 중...")
                prompts = get_prompts()
                query_expansion_system_prompt = prompts.get("query_expansion_system_prompt", "당신은 검색 전문가입니다. 사용자의 질문을 분석하고, 검색에 효과적인 키워드와 관련 용어를 추가하여 확장된 검색 쿼리를 생성해주세요.")
                query_expansion_model = prompts.get("query_expansion_model", "gemini-3.1-flash-lite-preview")
                if query_expansion_model.startswith("gpt-"):
                     query_expansion_model = "gemini-3.1-flash-lite-preview"
                
                expansion_response = gemini_client.models.generate_content(
                    model=query_expansion_model,
                    contents=f"다음 질문을 분석하고 검색에 최적화된 확장 쿼리를 생성해주세요:\n\n질문: {query}\n\n확장된 검색 쿼리:",
                    config=types.GenerateContentConfig(
                        system_instruction=query_expansion_system_prompt,
                    )
                )
                expanded_query = expansion_response.text.strip()
                print(f"확장된 쿼리: {expanded_query}")
            except Exception as e:
                print(f"쿼리 확장 실패 (원본 사용): {e}")
                expanded_query = query
        
        # 2단계: Qdrant 검색
        print("Qdrant 검색 시작...")
        results = search_qdrant(expanded_query, limit=5)
        print(f"검색 완료: {len(results)}개 결과")
        
        # LLM으로 답변 생성 (설정에 따라)
        answer = None
        enable_search_answer = int(get_setting('enable_search_answer', '1'))
        
        if results and gemini_client and enable_search_answer == 1:
            try:
                print("LLM 답변 생성 중...")
                prompts = get_prompts()
                answer_system_prompt = prompts.get("answer_system_prompt", "당신은 언리얼 엔진 전문가입니다. 검색된 영상 내용을 바탕으로 사용자의 질문에 200-300자 내외로 간결하게 마크다운형식으로 정리해주세요.")
                answer_model = prompts.get("answer_model", "gemini-3.1-flash-lite-preview")
                if answer_model.startswith("gpt-"):
                     answer_model = "gemini-3.1-flash-lite-preview"
                
                # 검색 결과를 컨텍스트로 변환
                context_parts = []
                for i, r in enumerate(results, 1):
                    context_parts.append(f"[{i}] {r['video_title']} ({r['timestamp_str']})\n{r['text']}")
                
                context = "\n\n".join(context_parts)
                
                response = gemini_client.models.generate_content(
                    model=answer_model,
                    contents=f"질문: {query}\n\n검색된 내용:\n{context}\n\n위 내용을 바탕으로 질문에 대한 답변을 작성해주세요.",
                    config=types.GenerateContentConfig(
                        system_instruction=answer_system_prompt,
                    )
                )
                answer = response.text.strip()
                print(f"답변 생성 완료: {len(answer)}자")
            except Exception as e:
                print(f"답변 생성 오류: {e}")
        elif enable_search_answer == 0:
            print("AI 답변 생성 비활성화 - 검색 결과만 반환")
        
        return jsonify({
            "query": query,
            "results": results,
            "count": len(results),
            "answer": answer
        })
        
    except Exception as e:
        print(f"검색 API 오류: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/ranking')
def api_ranking():
    """선호도 순위 API (공개)"""
    try:
        ranking_data = get_tasks_ranking()
        
        # task_status에서 html_path 정보 추가
        with task_lock:
            for item in ranking_data:
                task_id = item.get('task_id')
                if task_id in task_status:
                    task = task_status[task_id]
                    result = task.get('result', {})
                    item['summary_html_path'] = result.get('summary_html_path', '')
                    item['html_path'] = result.get('html_path', '')
                else:
                    item['summary_html_path'] = ''
                    item['html_path'] = ''
                
                # datetime 객체를 문자열로 변환
                if isinstance(item.get('created_at'), datetime):
                    item['created_at'] = item['created_at'].isoformat()
        
        return jsonify({
            "success": True,
            "ranking": ranking_data
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/admin')
def admin():
    """관리자 페이지 (비밀번호 필요)"""
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """관리자 로그인"""
    data = request.get_json()
    password = data.get('password', '')
    
    if password == ADMIN_PASSWORD:
        # 세션에 admin 권한 저장
        from flask import session
        session['is_admin'] = True
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "비밀번호가 틀렸습니다."})

@app.route('/admin/check')
def admin_check():
    """관리자 권한 확인"""
    from flask import session
    is_admin = session.get('is_admin', False)
    return jsonify({"is_admin": is_admin})

@app.route('/admin/logout')
def admin_logout():
    """관리자 로그아웃"""
    from flask import session
    session.pop('is_admin', None)
    return redirect(url_for('index'))

@app.route('/admin/settings')
def admin_settings():
    """관리자 설정 페이지"""
    from flask import session
    if not session.get('is_admin'):
        return redirect(url_for('admin'))
    
    prompts = get_prompts()
    max_tasks = get_setting('max_tasks', '0')
    auto_cleanup = get_setting('auto_cleanup', '1')
    skip_detail_html = get_setting('skip_detail_html', '0')
    enable_reranking = get_setting('enable_reranking', '1')
    enable_search_answer = get_setting('enable_search_answer', '1')
    min_similarity_threshold = get_setting('min_similarity_threshold', '0.5')
    available_models = get_available_models()
    
    return render_template('admin.html', 
                         system_prompt=prompts["system_prompt"],
                         user_prompt_template=prompts["user_prompt_template"],
                         whisper_model=prompts["whisper_model"],
                         translation_model=prompts["translation_model"],
                         summary_system_prompt=prompts.get("summary_system_prompt", ""),
                         summary_user_prompt_template=prompts.get("summary_user_prompt_template", ""),
                         filter_system_prompt=prompts.get("filter_system_prompt", ""),
                         filter_user_prompt_template=prompts.get("filter_user_prompt_template", ""),
                         query_expansion_system_prompt=prompts.get("query_expansion_system_prompt", ""),
                         query_expansion_model=prompts.get("query_expansion_model", "gpt-3.5-turbo"),
                         answer_system_prompt=prompts.get("answer_system_prompt", ""),
                         answer_model=prompts.get("answer_model", "gpt-3.5-turbo"),
                         max_tasks=max_tasks,
                         auto_cleanup=auto_cleanup,
                         skip_detail_html=skip_detail_html,
                         enable_reranking=enable_reranking,
                         enable_search_answer=enable_search_answer,
                         min_similarity_threshold=min_similarity_threshold,
                         available_models=available_models)

@app.route('/admin/save', methods=['POST'])
def admin_save():
    """프롬프트 설정 저장"""
    data = request.get_json()
    system_prompt = data.get('system_prompt', '')
    user_prompt_template = data.get('user_prompt_template', '')
    whisper_model = data.get('whisper_model', 'whisper-1')
    translation_model = data.get('translation_model', 'gemini-3.1-flash-lite-preview')
    summary_system_prompt = data.get('summary_system_prompt', '')
    summary_user_prompt_template = data.get('summary_user_prompt_template', '')
    filter_system_prompt = data.get('filter_system_prompt', '')
    filter_user_prompt_template = data.get('filter_user_prompt_template', '')
    query_expansion_system_prompt = data.get('query_expansion_system_prompt', '')
    query_expansion_model = data.get('query_expansion_model', 'gemini-3.1-flash-lite-preview')
    answer_system_prompt = data.get('answer_system_prompt', '')
    answer_model = data.get('answer_model', 'gemini-3.1-flash-lite-preview')
    max_tasks = data.get('max_tasks', '0')
    auto_cleanup = data.get('auto_cleanup', '1')
    skip_detail_html = data.get('skip_detail_html', '0')
    enable_reranking = data.get('enable_reranking', '1')
    enable_search_answer = data.get('enable_search_answer', '1')
    min_similarity_threshold = data.get('min_similarity_threshold', '0.5')
    
    update_prompts(system_prompt, user_prompt_template, whisper_model, translation_model, summary_system_prompt, summary_user_prompt_template, filter_system_prompt, filter_user_prompt_template, query_expansion_system_prompt, query_expansion_model, answer_system_prompt, answer_model)
    update_setting('max_tasks', str(max_tasks))
    update_setting('auto_cleanup', str(auto_cleanup))
    update_setting('skip_detail_html', str(skip_detail_html))
    update_setting('enable_reranking', str(enable_reranking))
    update_setting('enable_search_answer', str(enable_search_answer))
    update_setting('min_similarity_threshold', str(min_similarity_threshold))
    
    # 자동 클린업이 활성화된 경우에만 즉시 실행
    if auto_cleanup == '1':
        try:
            auto_cleanup_tasks_by_preference()
        except Exception as e:
            print(f"자동 삭제 실패: {e}")
    
    return jsonify({"success": True, "message": "설정이 저장되었습니다."})

@app.route('/admin/reindex/<task_id>', methods=['POST'])
def admin_reindex(task_id):
    """관리자 전용: Task를 Qdrant에 재인덱싱"""
    from flask import session
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    
    result = reindex_task_to_qdrant(task_id)
    
    if result.get('success'):
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/admin/reindex-all', methods=['POST'])
def admin_reindex_all():
    """관리자 전용: 모든 완료된 Task를 Qdrant에 재인덱싱 (컬렉션 재생성)"""
    from flask import session
    if not session.get('is_admin'):
        return jsonify({"error": "Unauthorized"}), 403
    
    print(f"\n{'='*60}")
    print("전체 재인덱싱 시작: 컬렉션 재생성")
    print(f"{'='*60}")
    
    # 1. 기존 컬렉션 삭제
    try:
        print("\n[1/3] 기존 컬렉션 삭제 중...")
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"✓ 컬렉션 '{COLLECTION_NAME}' 삭제 완료")
    except Exception as e:
        print(f"⚠ 컬렉션 삭제 오류 (무시): {e}")
    
    # 2. 새 컬렉션 생성
    try:
        print("\n[2/3] 새 컬렉션 생성 중...")
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        print(f"✓ 컬렉션 '{COLLECTION_NAME}' 생성 완료 (1536-dim, COSINE)")
    except Exception as e:
        print(f"✗ 컬렉션 생성 실패: {e}")
        return jsonify({"error": f"컬렉션 생성 실패: {str(e)}"}), 500
    
    # 3. 모든 완료된 Task 재인덱싱
    print("\n[3/3] 모든 Task 재인덱싱 중...")
    with task_lock:
        completed_tasks = [(tid, t) for tid, t in task_status.items() if t.get('status') == 'completed']
    
    print(f"✓ {len(completed_tasks)}개의 완료된 Task 발견\n")
    
    results = []
    for idx, (task_id, task) in enumerate(completed_tasks, 1):
        title = task.get('result', {}).get('title', task_id)
        print(f"\n[{idx}/{len(completed_tasks)}] 처리 중: {title}")
        result = reindex_task_to_qdrant(task_id)
        results.append({
            "task_id": task_id,
            "title": title,
            "result": result
        })
    
    success_count = sum(1 for r in results if r['result'].get('success'))
    
    return jsonify({
        "success": True,
        "total": len(completed_tasks),
        "success_count": success_count,
        "failed_count": len(completed_tasks) - success_count,
        "details": results
    })

@app.route('/admin/regenerate-html', methods=['POST'])
def admin_regenerate_html():
    """관리자 전용: 모든 완료된 Task의 상세 HTML을 앵커 포함 버전으로 재생성"""
    from flask import session
    
    print(f"\n{'='*60}")
    print("전체 HTML 재생성 시작 (앵커 추가)")
    print(f"{'='*60}")
    
    with task_lock:
        completed_tasks = [(tid, t) for tid, t in task_status.items() if t.get('status') == 'completed']
    
    print(f"✓ {len(completed_tasks)}개의 완료된 Task 발견\n")
    
    results = []
    for idx, (task_id, task) in enumerate(completed_tasks, 1):
        result_data = task.get('result', {})
        title = result_data.get('title', task_id)
        display_title = result_data.get('original_title') or title
        html_path = result_data.get('html_path', '')
        
        if not html_path or not os.path.exists(html_path):
            print(f"\n[{idx}/{len(completed_tasks)}] 건너뜀: {title} (HTML 없음)")
            results.append({
                "task_id": task_id,
                "title": title,
                "success": False,
                "error": "HTML file not found"
            })
            continue
        
        print(f"\n[{idx}/{len(completed_tasks)}] 재생성 중: {title}")
        
        try:
            output_path = Path(html_path).parent
            youtube_url = task.get('url', '')
            
            # 1. 세그먼트 데이터 로드 시도 (pkl 파일)
            merged_path = output_path / "merged_segments.pkl"
            segments_path = output_path / "segments.pkl"
            segments = None
            
            if merged_path.exists():
                try:
                    with open(merged_path, "rb") as f:
                        import pickle
                        segments = pickle.load(f)
                    print(f"  ✓ merged_segments.pkl 로드: {len(segments)}개")
                except Exception as e:
                    print(f"  ⚠ pkl 로드 실패: {e}")
            elif segments_path.exists():
                try:
                    with open(segments_path, "rb") as f:
                        import pickle
                        segments = pickle.load(f)
                    print(f"  ✓ segments.pkl 로드: {len(segments)}개")
                except Exception as e:
                    print(f"  ⚠ pkl 로드 실패: {e}")
            
            # 2. pkl 없으면 기존 HTML에서 파싱
            if not segments:
                print(f"  ℹ pkl 파일 없음, HTML 파싱으로 세그먼트 재구성")
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # content-block에서 세그먼트 재구성
                content_blocks = soup.find_all('div', class_='content-block')
                segments = []
                
                for block in content_blocks:
                    # image-container에서 timestamp와 이미지 경로 추출
                    img_container = block.find('div', class_='image-container')
                    if not img_container:
                        continue
                    
                    start_time = float(img_container.get('data-start-time', 0))
                    
                    img_tag = img_container.find('img')
                    if not img_tag:
                        continue
                    
                    img_src = img_tag.get('src', '')
                    
                    # caption-container에서 텍스트 추출
                    caption_container = block.find('div', class_='caption-container')
                    if not caption_container:
                        continue
                    
                    # caption은 <div> 또는 <p> 태그일 수 있음
                    caption_elem = caption_container.find('div', class_='caption')
                    if not caption_elem:
                        caption_elem = caption_container.find('p', class_='caption')
                    if not caption_elem:
                        continue
                    
                    # 텍스트 추출 (get_text()로 간단하게)
                    caption_text = caption_elem.get_text(separator='\n', strip=True)
                    
                    # 이미지 경로 처리 (상대 경로 → 절대 경로)
                    if img_src:
                        img_path = output_path / img_src
                    else:
                        img_path = ""
                    
                    seg = Segment(
                        start=start_time,
                        end=start_time + 5.0,
                        texts=[caption_text],
                        image_path=str(img_path),
                        translated=caption_text
                    )
                    segments.append(seg)
                
                print(f"  ✓ HTML 파싱: {len(segments)}개 세그먼트 재구성")
                
                if not segments:
                    print(f"  ⚠ HTML에서 세그먼트를 찾을 수 없음 (스킵)")
                    results.append({
                        "task_id": task_id,
                        "title": title,
                        "success": False,
                        "error": "HTML 파싱 실패 - content-block을 찾을 수 없음"
                    })
                    continue
            
            # 3. generate_html()로 최신 양식 HTML 생성
            print(f"  ℹ 최신 상세 HTML 양식으로 재생성 중...")
            generate_html(segments, output_path, title, youtube_url, display_title)
            print(f"  ✓ 상세 HTML 재생성 완료")
            
            # 4. summary HTML도 재생성 (있는 경우)
            summary_html_path = result_data.get('summary_html_path', '')
            if summary_html_path and os.path.exists(summary_html_path):
                try:
                    print(f"  ℹ 요약 HTML 양식으로 재생성 중...")
                    
                    # task에서 summary_text 가져오기, 없으면 기존 HTML 파싱
                    summary_text = result_data.get('summary', result_data.get('summary_text', ''))
                    
                    if not summary_text:
                        # 기존 요약 HTML에서 요약 텍스트 추출
                        with open(summary_html_path, 'r', encoding='utf-8') as f:
                            summary_html_content = f.read()
                        
                        from bs4 import BeautifulSoup
                        summary_soup = BeautifulSoup(summary_html_content, 'html.parser')
                        
                        # caption-container에서 텍스트 추출
                        caption_container = summary_soup.find('div', class_='caption-container')
                        if caption_container:
                            caption_div = caption_container.find('div', class_='caption')
                            if caption_div:
                                # HTML 구조를 유지하면서 텍스트 추출
                                summary_text = caption_div.decode_contents()
                                print(f"  ✓ 기존 HTML에서 요약 텍스트 추출 완료 ({len(summary_text)} 문자)")
                    
                    if summary_text:
                        generate_summary_html(summary_text, output_path, title, youtube_url, display_title)
                        print(f"  ✓ 요약 HTML 재생성 완료")
                    else:
                        print(f"  ⚠ 요약 텍스트 추출 실패, 요약 HTML 재생성 스킵")
                except Exception as e:
                    print(f"  ⚠ 요약 HTML 재생성 실패: {e}")
            
            results.append({
                "task_id": task_id,
                "title": title,
                "success": True,
                "segments_count": len(segments)
            })
            
        except Exception as e:
            print(f"  ✗ 오류: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "task_id": task_id,
                "title": title,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r.get('success'))
    
    print(f"\n{'='*60}")
    print(f"HTML 재생성 완료: 성공 {success_count}/{len(completed_tasks)}")
    print(f"{'='*60}\n")
    
    return jsonify({
        "success": True,
        "total": len(completed_tasks),
        "success_count": success_count,
        "failed_count": len(completed_tasks) - success_count,
        "details": results
    })

@app.route('/task/<task_id>')
def get_task_status(task_id):
    """Task 상태 조회"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task_status[task_id])

@app.route('/tasks')
def get_all_tasks():
    """모든 Task 목록 조회 (URL이 같으면 최신 것만)"""
    with task_lock:
        # URL별로 가장 최신 task만 유지
        url_to_task = {}
        
        for task_id, task_data in task_status.items():
            url = task_data.get('url')
            if not url:
                continue
            
            task_info = task_data.copy()
            task_info['task_id'] = task_id
            
            # 조회수 정보 추가
            view_counts = get_view_counts(task_id)
            task_info['summary_views'] = view_counts['summary_views']
            task_info['detail_views'] = view_counts['detail_views']
            
            # 추천 수 정보 추가
            task_info['recommend_count'] = get_recommendation_count(task_id)
            
            # datetime 객체를 KST 문자열로 변환
            created_at_raw = task_info.get('created_at')
            if isinstance(created_at_raw, datetime):
                created_at = created_at_raw
            elif isinstance(created_at_raw, str):
                try:
                    created_at = datetime.fromisoformat(created_at_raw)
                except:
                    created_at = datetime.min
            else:
                created_at = datetime.min
            
            # UTC를 KST로 변환 (+9시간)
            from datetime import timedelta
            kst_time = created_at + timedelta(hours=9)
            task_info['created_at'] = kst_time.isoformat()
            task_info['created_at_display'] = kst_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # URL이 처음 나오거나, 더 최신이면 업데이트
            if url not in url_to_task:
                url_to_task[url] = (created_at, task_info)
            else:
                existing_created_at, _ = url_to_task[url]
                if created_at > existing_created_at:
                    url_to_task[url] = (created_at, task_info)
        
        # created_at 기준 내림차순 정렬 (최신 것이 먼저)
        tasks_list = [task_info for _, task_info in url_to_task.values()]
        tasks_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return jsonify({"tasks": tasks_list})

@app.route('/process', methods=['POST'])
def process():
    """YouTube URL 처리 엔드포인트 - Task Queue에 추가"""
    data = request.get_json()
    url = data.get('url')
    force = data.get('force', False)  # 강제 실행 플래그
    
    # 요청 출처 확인 (웹 UI인지 외부 API인지)
    is_web_ui = request.headers.get('X-Source') == 'web'
    
    if not url:
        return jsonify({"success": False, "error": "URL이 필요합니다."})
    
    # URL에서 video_id 추출
    current_video_id = extract_youtube_video_id(url)
    if not current_video_id:
        return jsonify({"success": False, "error": "유효하지 않은 YouTube URL입니다."})
    
    # 같은 video_id의 기존 task 확인
    existing_task_id = None
    existing_task_data = None
    with task_lock:
        for tid, tdata in task_status.items():
            task_url = tdata.get('url', '')
            task_video_id = extract_youtube_video_id(task_url)
            
            # video_id가 같으면 중복으로 간주
            if task_video_id == current_video_id:
                existing_task_id = tid
                existing_task_data = tdata
                break
    
    # 웹 UI: force 플래그 사용 (팝업 처리)
    # 외부 API: 중복이면 무조건 거부
    if existing_task_id:
        if is_web_ui and not force:
            # 웹 UI에서 중복 확인 팝업용
            with task_lock:
                existing_task = task_status[existing_task_id]
                video_title = existing_task.get('video_title', 'Unknown')
                
                return jsonify({
                    "success": False,
                    "duplicate": True,
                    "task_id": existing_task_id,
                    "video_title": video_title,
                    "message": "이미 존재하는 영상입니다."
                })
        elif not is_web_ui:
            # 외부 API 요청은 무조건 거부
            with task_lock:
                existing_task = task_status[existing_task_id]
                video_title = existing_task.get('video_title', 'Unknown')
                
                return jsonify({
                    "success": False,
                    "duplicate": True,
                    "task_id": existing_task_id,
                    "video_title": video_title,
                    "message": "이미 존재하는 영상입니다. 중복 처리가 불가능합니다."
                })
    
    # 새로운 Task 생성
    task_id = str(uuid.uuid4())
    
    # Task 상태 초기화
    with task_lock:
        task_status[task_id] = {
            "status": "queued",
            "progress": "대기 중...",
            "result": {},
            "created_at": datetime.now(),
            "url": url
        }
        save_task_status()
    
    # Queue에 추가
    task_queue.put((task_id, url))
    
    return jsonify({
        "success": True,
        "task_id": task_id,
        "message": "Task가 Queue에 추가되었습니다."
    })

@app.route('/retry/<task_id>', methods=['POST'])
def retry_task(task_id):
    """Task를 재시도 (모든 상태에서 가능)"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"success": False, "error": "Task를 찾을 수 없습니다."})
        
        task = task_status[task_id]
        
        # 현재 처리 중인 task는 재시작 불가
        if task["status"] == "processing":
            return jsonify({"success": False, "error": "현재 처리 중인 Task는 재시작할 수 없습니다."})
        
        url = task.get("url")
        if not url:
            return jsonify({"success": False, "error": "URL 정보가 없습니다."})
        
        # 상태 초기화
        task_status[task_id]["status"] = "queued"
        task_status[task_id]["progress"] = "재시도 대기 중..."
        task_status[task_id]["result"] = {}
        task_status[task_id]["video_title"] = task.get("video_title", "")  # 기존 제목 유지
        save_task_status()
    
    # Queue에 다시 추가
    task_queue.put((task_id, url))
    
    return jsonify({
        "success": True,
        "message": "Task가 재시도 Queue에 추가되었습니다."
    })

@app.route('/cancel/<task_id>', methods=['POST'])
def cancel_task(task_id):
    """대기 중인 Task 취소"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"success": False, "error": "Task를 찾을 수 없습니다."})
        
        task = task_status[task_id]
        
        # queued 상태만 취소 가능
        if task["status"] != "queued":
            return jsonify({"success": False, "error": "대기 중인 Task만 취소할 수 있습니다."})
        
        # 상태를 cancelled로 변경
        task_status[task_id]["status"] = "cancelled"
        task_status[task_id]["progress"] = "사용자에 의해 취소되었습니다."
        save_task_status()
    
    return jsonify({
        "success": True,
        "message": "Task가 취소되었습니다."
    })

@app.route('/delete/<task_id>', methods=['POST'])
def delete_task(task_id):
    """Task 삭제 (공개 전환)"""
    # from flask import session
    # if not session.get('is_admin'):
    #     return jsonify({"success": False, "error": "관리자 권한이 필요합니다."}), 403
    
    with task_lock:
        if task_id not in task_status:
            return jsonify({"success": False, "error": "Task를 찾을 수 없습니다."})
        
        task = task_status[task_id]
        
        # processing 중인 task는 삭제 불가
        if task["status"] == "processing":
            return jsonify({"success": False, "error": "처리 중인 Task는 삭제할 수 없습니다."})
        
        # 출력 디렉토리 삭제 (result/title 누락된 경우에도 삭제되도록 보강)
        result = task.get("result", {})
        video_title = result.get("title")
        safe_title = task.get("safe_title") or result.get("safe_title")
        task_video_title = task.get("video_title")

        candidate_dirs = set()
        if video_title:
            candidate_dirs.add(OUTPUT_DIR / video_title)
        if safe_title:
            candidate_dirs.add(OUTPUT_DIR / safe_title)
        if task_video_title:
            candidate_dirs.add(OUTPUT_DIR / sanitize_filename(task_video_title))

        for path_key in ("video_path", "html_path", "summary_html_path"):
            path_value = result.get(path_key)
            if path_value:
                candidate_dirs.add(Path(path_value).parent)

        output_root = OUTPUT_DIR.resolve()
        for video_dir in candidate_dirs:
            try:
                resolved_dir = video_dir.resolve()
                resolved_dir.relative_to(output_root)
            except Exception:
                continue
            if resolved_dir.exists():
                try:
                    shutil.rmtree(resolved_dir)
                    print(f"삭제됨: {resolved_dir}")
                except Exception as e:
                    print(f"디렉토리 삭제 실패: {e}")

        # ZIP 파일도 삭제
        zip_titles = {t for t in (video_title, safe_title) if t}
        if task_video_title:
            zip_titles.add(sanitize_filename(task_video_title))
        for title in zip_titles:
            zip_path = OUTPUT_DIR / f"{title}.zip"
            if zip_path.exists():
                try:
                    os.remove(zip_path)
                    print(f"삭제됨: {zip_path}")
                except Exception as e:
                    print(f"ZIP 파일 삭제 실패: {e}")
        
        # task_status에서 제거
        del task_status[task_id]
        save_task_status()
    
    # 조회수 및 추천 데이터 삭제
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM view_counts WHERE task_id = ?', (task_id,))
        c.execute('DELETE FROM recommendations WHERE task_id = ?', (task_id,))
        conn.commit()
        conn.close()
        print(f"조회수 및 추천 데이터 삭제: {task_id}")
    except Exception as e:
        print(f"조회수/추천 데이터 삭제 실패: {e}")
    
    return jsonify({
        "success": True,
        "message": "Task가 삭제되었습니다."
    })

@app.route('/recommend/<task_id>', methods=['POST'])
def recommend_task(task_id):
    """Task 추천하기"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"success": False, "error": "Task를 찾을 수 없습니다."})
        
        task = task_status[task_id]
        
        # 완료된 task만 추천 가능
        if task["status"] != "completed":
            return jsonify({"success": False, "error": "완료된 Task만 추천할 수 있습니다."})
    
    # 추천 토글
    result = toggle_recommendation(task_id)
    
    return jsonify({
        "success": True,
        "recommend_count": result["recommend_count"],
        "message": "추천했습니다!"
    })

@app.route('/view/<task_id>/<view_type>')
def view_result(task_id, view_type):
    """완료된 Task의 HTML 결과 보기"""
    # 관리자가 아닐 때만 조회수 증가
    from flask import session
    if not session.get('is_admin'):
        increment_view_count(task_id, view_type)
    
    with task_lock:
        if task_id not in task_status:
            return "Task를 찾을 수 없습니다.", 404
        
        task = task_status[task_id]
        if task["status"] != "completed":
            return "Task가 아직 완료되지 않았습니다.", 400
        
        result = task.get("result", {})
        
        if view_type == "summary":
            html_path = result.get("summary_html_path")
        elif view_type == "detail":
            html_path = result.get("html_path")
        else:
            return "잘못된 view type입니다.", 400
        
        if not html_path or not os.path.exists(html_path):
            return "HTML 파일을 찾을 수 없습니다.", 404
        
        # HTML 파일 읽기 및 이미지 경로 수정
        video_title = result.get("title")
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 상대 경로를 Flask 및 Nginx 환경 모두에서 호환되도록 상대 경로(../../)로 변경
        if video_title:
            import urllib.parse
            # URL 인코딩을 적용 (제목에 공백/특수문자가 있을 수 있으므로)
            safe_title_url = urllib.parse.quote(video_title)
            # /view/<task_id>/detail 의 경로는 깊이가 3이므로 ../../output/ 으로 접근하면 루트의 proxy 위치로 매칭됨
            base_img_path = f"../../output/{safe_title_url}/images/"
            
            html_content = html_content.replace('src="images/', f'src="{base_img_path}')
            html_content = html_content.replace("src='images/", f"src='{base_img_path}")
            
        # [NEW] 이전에 이미 완성된 영상(Summary)의 HTML에도 '제거' 버튼과 로직을 동적으로 삽입
        if view_type == "summary" and "deleteRecord()" not in html_content:
            css_injection = """
        .detail-link-btn { background-color: #10b981 !important; color: white !important; }
        .detail-link-btn:hover { background-color: #059669 !important; }
        .delete-link-btn { display: inline-block; padding: 12px 24px; background-color: #ef4444 !important; color: white !important; text-decoration: none; border-radius: 4px; font-weight: bold; transition: background-color 0.3s; margin-left: 10px; }
        .delete-link-btn:hover { background-color: #dc2626 !important; }
</style>"""
            html_content = html_content.replace('</style>', css_injection)
            
            button_html = '<a href="detail" class="detail-link-btn">View Details</a>\n                <a href="#" onclick="deleteRecord(); return false;" class="delete-link-btn">Delete</a>'
            html_content = html_content.replace('<a href="detail" class="detail-link-btn">📋 상세 보기</a>', button_html)
            # 호환성을 위해 영어 텍스트이거나 버튼이 다른 텍스트로 되어 있는 경우도 치환
            html_content = html_content.replace('<a href="detail" class="detail-link-btn">View Details</a>\n                <a href="#" onclick="deleteRecord(); return false;" class="delete-link-btn">🗑️ 제거</a>', button_html)
            
            js_injection = r"""
<script>
    function deleteRecord() {
        const taskIdMatch = window.location.pathname.match(/\/view\/([^\/]+)/);
        const taskId = taskIdMatch ? taskIdMatch[1] : null;
        if (!taskId) {
            alert("문서 ID를 찾을 수 없습니다.");
            return;
        }
        if (confirm("정말로 이 문서를 제거하시겠습니까?\n(서버에서 완전히 삭제되며 복구할 수 없습니다)")) {
            const baseUrl = window.location.pathname.substring(0, window.location.pathname.indexOf('/view/'));
            fetch(baseUrl + '/delete/' + taskId, { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    alert("문서가 제거되었습니다.");
                    if (window.opener) {
                        window.close();
                    } else {
                        window.location.href = baseUrl + '/';
                    }
                } else {
                    alert("제거 실패: " + data.error);
                }
            })
            .catch(e => alert("통신 중 오류 발생: " + e));
        }
    }
</script>
</body>"""
            html_content = html_content.replace('</body>', js_injection)
        
        return html_content

@app.route('/download/<task_id>')
def download_result(task_id):
    """완료된 Task의 결과를 ZIP으로 다운로드"""
    with task_lock:
        if task_id not in task_status:
            return jsonify({"success": False, "error": "Task를 찾을 수 없습니다."}), 404
        
        task = task_status[task_id]
        if task["status"] != "completed":
            return jsonify({"success": False, "error": "Task가 아직 완료되지 않았습니다."}), 400
        
        result = task.get("result", {})
        video_title = result.get("title")
        
        if not video_title:
            return jsonify({"success": False, "error": "비디오 정보를 찾을 수 없습니다."}), 400
    
    # 비디오 디렉토리 경로
    video_dir = OUTPUT_DIR / video_title
    if not video_dir.exists():
        return jsonify({"success": False, "error": "출력 디렉토리를 찾을 수 없습니다."}), 404
    
    # 임시 ZIP 파일 생성
    import tempfile
    import threading
    
    try:
        # 임시 파일 생성
        temp_zip = tempfile.NamedTemporaryFile(mode='wb', suffix='.zip', delete=False)
        temp_zip_path = temp_zip.name
        temp_zip.close()
        
        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # images 폴더의 모든 파일 추가
            images_dir = video_dir / "images"
            if images_dir.exists():
                for img_file in images_dir.iterdir():
                    if img_file.is_file():
                        zipf.write(img_file, f"images/{img_file.name}")
            
            # HTML 파일들 추가
            detail_html = video_dir / f"{video_title}.html"
            if detail_html.exists():
                zipf.write(detail_html, f"{video_title}.html")
            
            summary_html = video_dir / f"{video_title}-summary.html"
            if summary_html.exists():
                zipf.write(summary_html, f"{video_title}-summary.html")
        
        # 백그라운드 스레드에서 임시 파일 삭제
        def delayed_delete(file_path, delay=10):
            """지연 후 파일 삭제"""
            import time
            time.sleep(delay)  # 파일 전송이 완료될 시간 확보
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"임시 ZIP 파일 삭제 완료: {file_path}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        print(f"임시 ZIP 파일 삭제 실패: {e}")
        
        # 백그라운드 스레드 시작
        cleanup_thread = threading.Thread(target=delayed_delete, args=(temp_zip_path,), daemon=True)
        cleanup_thread.start()
        
        return send_file(
            temp_zip_path,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{video_title}.zip"
        )
    
    except Exception as e:
        return jsonify({"success": False, "error": f"ZIP 생성 실패: {str(e)}"}), 500

@app.route('/output/<path:filename>')
def serve_output(filename):
    """출력 파일 제공"""
    return send_from_directory('output', filename)

@app.route('/publish-to-wiki/<task_id>', methods=['POST'])
def publish_to_wiki_endpoint(task_id):
    """Summary HTML을 Confluence 위키로 발행"""
    try:
        # Confluence 설정 확인
        if not all([CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN]):
            return jsonify({
                "success": False,
                "error": "Confluence 설정이 필요합니다. 환경변수를 확인하세요."
            }), 400
        
        # Task 정보 가져오기
        with task_lock:
            if task_id not in task_status:
                return jsonify({
                    "success": False,
                    "error": "Task를 찾을 수 없습니다."
                }), 404
            
            task_data = task_status[task_id]
            summary_html_path = task_data.get('result', {}).get('summary_html_path')
        
        if not summary_html_path or not os.path.exists(summary_html_path):
            return jsonify({
                "success": False,
                "error": "요약 HTML 파일을 찾을 수 없습니다."
            }), 404
        
        # write_wiki 모듈 사용
        page_title, markdown_content = write_wiki.extract_markdown_from_html(summary_html_path)
        confluence_content = write_wiki.markdown_to_confluence(markdown_content)
        
        # Confluence 클라이언트 생성
        wiki = write_wiki.ConfluenceWiki(CONFLUENCE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
        
        # 페이지 생성 또는 업데이트
        result = wiki.create_or_update_page(
            space_key=CONFLUENCE_SPACE_KEY,
            title=page_title,
            content=confluence_content,
            parent_id=CONFLUENCE_PARENT_PAGE_ID if CONFLUENCE_PARENT_PAGE_ID else None
        )
        
        page_url = f"{CONFLUENCE_URL}/pages/viewpage.action?pageId={result['id']}"
        
        return jsonify({
            "success": True,
            "message": "위키 페이지가 발행되었습니다.",
            "page_url": page_url,
            "page_title": page_title
        })
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"Confluence API 오류: {e}"
        if e.response:
            error_msg += f" - {e.response.text}"
        return jsonify({
            "success": False,
            "error": error_msg
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Flask 세션 시크릿 키 설정
    app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # Worker thread 시작
    worker_thread = threading.Thread(target=task_worker, daemon=True)
    worker_thread.start()
    
    # 대기 중인 task 재개
    resume_queued_tasks()
    
    # print("=" * 60)
    # print("YouTube Video Processor 시작")
    # print("=" * 60)
    # print("필수 요구사항:")
    # print("1. yt-dlp 설치: pip install yt-dlp")
    # print("2. ffmpeg 설치 및 PATH 등록")
    # print("3. OpenCV 설치: pip install opencv-python")
    # print("4. 환경변수 OPENAI_API_KEY 설정")
    # print("=" * 60)
    # print("서버 실행: http://localhost:5000")
    # print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
