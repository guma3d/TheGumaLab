import requests

def simulate_delete():
    url = "http://localhost:8085/api/photos"
    payload = {
        "filepath": "/app/data/organized/Unknown-Year/Unknown-Year_Unknown-Location/Unknown-Year_123.jpg",
        "point_id": "00000000-0000-0000-0000-000000000000"  # Dummy UUID since it failed to index
    }
    
    print(f"[*] 모달창의 '휴지통' 클릭 시뮬레이션 시작...")
    print(f"[*] 전송되는 API 페이로드: {payload}")
    
    try:
        response = requests.delete(url, json=payload)
        print(f"\n[HTTP 응답 상태 코드] {response.status_code}")
        print(f"[서버 처리 결과] {response.json()}")
    except Exception as e:
        print(f"API 요청 실패: {e}")

if __name__ == "__main__":
    simulate_delete()
