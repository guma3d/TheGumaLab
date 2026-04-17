# GumaPhoto Diagnostic Run

- Run: `24553773216`
- Commit: `da65e27601199738c3d1fa1e2d321dff19f9d85a`
- Timestamp (UTC): 2026-04-17 07:39:47

## 1. Container status
```
NAMES              STATUS        CREATED
gumaphoto_app      Up 33 hours   2 days ago
gumaphoto_celery   Up 33 hours   2 days ago
gumaphoto_redis    Up 33 hours   3 weeks ago
gumaphoto_qdrant   Up 33 hours   4 weeks ago
```

## 2. Timeline cache file (mtime / size)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\TheGumaLab\GumaPhoto\data\caches ���͸�

2026-04-17  ���� 04:38         4,827,717 timeline_cache.json
               1�� ����           4,827,717 ����Ʈ
               0�� ���͸�  427,833,847,808 ����Ʈ ����
```

## 3. uploads_raw/ recent files (stuck = Organizer didn't pick up)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures\uploads_raw ���͸�

2026-04-17  ���� 04:38    <DIR>          .
2026-04-12  ���� 05:15    <DIR>          ..
               0�� ����                   0 ����Ʈ
               2�� ���͸�  427,833,847,808 ����Ʈ ����
```

## 4. Pictures/ recently modified folders (Organizer output)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures ���͸�

2026-04-17  ���� 04:38    <DIR>          uploads_raw
2026-04-15  ���� 12:42    <DIR>          UnknownDate
2026-04-12  ���� 05:15    <DIR>          2026
2026-04-12  ���� 05:15    <DIR>          .
2026-03-29  ���� 06:39    <DIR>          2005
2026-03-29  ���� 06:39    <DIR>          2007
2026-03-29  ���� 06:39    <DIR>          2008
2026-03-29  ���� 06:39    <DIR>          2010
2026-03-29  ���� 06:39    <DIR>          2011
2026-03-29  ���� 06:39    <DIR>          2012
2026-03-29  ���� 06:39    <DIR>          2013
2026-03-29  ���� 06:38    <DIR>          2014
2026-03-29  ���� 06:38    <DIR>          2015
2026-03-29  ���� 06:38    <DIR>          2016
2026-03-29  ���� 06:38    <DIR>          2017
2026-03-29  ���� 06:38    <DIR>          2018
2026-03-29  ���� 06:38    <DIR>          2019
2026-03-29  ���� 06:38    <DIR>          2020
2026-03-29  ���� 06:38    <DIR>          2021
2026-03-29  ���� 06:37    <DIR>          2022
2026-03-29  ���� 06:37    <DIR>          2023
2026-03-29  ���� 06:37    <DIR>          2024
2026-03-29  ���� 06:37    <DIR>          2025
               0�� ����                   0 ����Ʈ
              23�� ���͸�  427,833,847,808 ����Ʈ ����
```

## 5. Celery worker — last 200 log lines
```
[2026-04-17 07:38:26,984: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25321 ~ 25335 / 26345
[2026-04-17 07:38:26,984: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25336 ~ 25350 / 26345
[2026-04-17 07:38:26,984: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25351 ~ 25365 / 26345
[2026-04-17 07:38:26,985: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25366 ~ 25380 / 26345
[2026-04-17 07:38:26,985: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25381 ~ 25395 / 26345
[2026-04-17 07:38:26,985: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25396 ~ 25410 / 26345
[2026-04-17 07:38:26,985: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25411 ~ 25425 / 26345
[2026-04-17 07:38:26,986: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25426 ~ 25440 / 26345
[2026-04-17 07:38:26,986: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25441 ~ 25455 / 26345
[2026-04-17 07:38:26,986: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25456 ~ 25470 / 26345
[2026-04-17 07:38:26,986: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25471 ~ 25485 / 26345
[2026-04-17 07:38:26,987: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25486 ~ 25500 / 26345
[2026-04-17 07:38:26,987: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25501 ~ 25515 / 26345
[2026-04-17 07:38:26,987: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25516 ~ 25530 / 26345
[2026-04-17 07:38:26,987: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25531 ~ 25545 / 26345
[2026-04-17 07:38:26,988: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25546 ~ 25560 / 26345
[2026-04-17 07:38:26,988: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25561 ~ 25575 / 26345
[2026-04-17 07:38:26,988: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25576 ~ 25590 / 26345
[2026-04-17 07:38:26,989: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25591 ~ 25605 / 26345
[2026-04-17 07:38:26,989: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25606 ~ 25620 / 26345
[2026-04-17 07:38:26,989: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25621 ~ 25635 / 26345
[2026-04-17 07:38:26,989: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25636 ~ 25650 / 26345
[2026-04-17 07:38:26,990: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25651 ~ 25665 / 26345
[2026-04-17 07:38:26,990: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25666 ~ 25680 / 26345
[2026-04-17 07:38:26,990: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25681 ~ 25695 / 26345
[2026-04-17 07:38:26,990: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25696 ~ 25710 / 26345
[2026-04-17 07:38:26,991: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25711 ~ 25725 / 26345
[2026-04-17 07:38:26,991: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25726 ~ 25740 / 26345
[2026-04-17 07:38:26,991: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25741 ~ 25755 / 26345
[2026-04-17 07:38:26,991: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25756 ~ 25770 / 26345
[2026-04-17 07:38:26,992: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25771 ~ 25785 / 26345
[2026-04-17 07:38:26,992: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25786 ~ 25800 / 26345
[2026-04-17 07:38:26,992: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25801 ~ 25815 / 26345
[2026-04-17 07:38:26,992: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25816 ~ 25830 / 26345
[2026-04-17 07:38:26,993: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25831 ~ 25845 / 26345
[2026-04-17 07:38:26,993: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25846 ~ 25860 / 26345
[2026-04-17 07:38:26,993: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25861 ~ 25875 / 26345
[2026-04-17 07:38:26,994: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25876 ~ 25890 / 26345
[2026-04-17 07:38:26,994: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25891 ~ 25905 / 26345
[2026-04-17 07:38:26,994: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25906 ~ 25920 / 26345
[2026-04-17 07:38:26,994: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25921 ~ 25935 / 26345
[2026-04-17 07:38:26,995: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25936 ~ 25950 / 26345
[2026-04-17 07:38:26,995: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25951 ~ 25965 / 26345
[2026-04-17 07:38:26,995: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25966 ~ 25980 / 26345
[2026-04-17 07:38:26,995: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25981 ~ 25995 / 26345
[2026-04-17 07:38:26,996: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25996 ~ 26010 / 26345
[2026-04-17 07:38:26,996: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26011 ~ 26025 / 26345
[2026-04-17 07:38:26,996: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26026 ~ 26040 / 26345
[2026-04-17 07:38:26,996: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26041 ~ 26055 / 26345
[2026-04-17 07:38:26,997: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26056 ~ 26070 / 26345
[2026-04-17 07:38:26,997: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26071 ~ 26085 / 26345
[2026-04-17 07:38:26,997: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26086 ~ 26100 / 26345
[2026-04-17 07:38:26,997: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26101 ~ 26115 / 26345
[2026-04-17 07:38:27,143: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26116 ~ 26130 / 26345
[2026-04-17 07:38:30,064: WARNING/ForkPoolWorker-2] DEBUG: /app/data/organized/2026/2026-04/2026-04_10.jpeg => date_str: 2026-04, sort_date: 20260401
[2026-04-17 07:38:30,087: INFO/ForkPoolWorker-2] HTTP Request: PUT http://qdrant:6333/collections/gumaphoto_hybrid_kr/points?wait=true "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,222: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26131 ~ 26145 / 26345
[2026-04-17 07:38:30,222: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26146 ~ 26160 / 26345
[2026-04-17 07:38:30,223: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26161 ~ 26175 / 26345
[2026-04-17 07:38:30,223: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26176 ~ 26190 / 26345
[2026-04-17 07:38:30,223: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26191 ~ 26205 / 26345
[2026-04-17 07:38:30,224: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26206 ~ 26220 / 26345
[2026-04-17 07:38:30,224: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26221 ~ 26235 / 26345
[2026-04-17 07:38:30,230: WARNING/ForkPoolWorker-2]       ⚠️ 이미지 로드 오류 (Skip): UnknownDate_0127.jpg - cannot identify image file '/app/data/organized/UnknownDate/UnknownDate_0127.jpg'
[2026-04-17 07:38:30,230: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26236 ~ 26250 / 26345
[2026-04-17 07:38:30,231: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26251 ~ 26265 / 26345
[2026-04-17 07:38:30,231: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26266 ~ 26280 / 26345
[2026-04-17 07:38:30,231: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26281 ~ 26295 / 26345
[2026-04-17 07:38:30,231: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26296 ~ 26310 / 26345
[2026-04-17 07:38:30,232: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26311 ~ 26325 / 26345
[2026-04-17 07:38:30,232: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26326 ~ 26340 / 26345
[2026-04-17 07:38:30,232: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26341 ~ 26345 / 26345
[2026-04-17 07:38:30,233: WARNING/ForkPoolWorker-2] 
✅ 모든 사진의 [얼굴 + 배경 상황] 벡터 데이터베이스 컴파일이 완료되었습니다!
[2026-04-17 07:38:30,233: WARNING/ForkPoolWorker-2] ✅ [Celery] Vector Indexer 작업 완료!
[2026-04-17 07:38:30,241: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,276: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,278: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,324: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,371: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,373: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,375: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,422: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,469: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,470: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,472: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,474: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,476: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,482: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,533: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,535: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,540: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,594: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,596: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,597: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,599: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,600: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,602: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,606: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,651: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,695: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,699: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,745: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,748: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,750: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,751: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,753: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,758: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,805: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,807: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,808: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,810: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,811: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,816: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,826: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,827: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,829: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,830: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,833: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,835: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,837: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,839: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,841: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,845: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,892: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,893: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,894: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,938: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:30,939: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-17 07:38:31,156: WARNING/ForkPoolWorker-2] ✅ [Timeline Cache] 재생성 완료: recent=500장, 인물 53명
[2026-04-17 07:38:31,197: INFO/ForkPoolWorker-2] Task tasks.indexer[0b15633f-f50d-4c5c-9f62-479895c70c60] succeeded in 16.65736523999658s: None
```

## 6. Celery — errors / tracebacks in last 24h
```
[2026-04-17 07:38:11,711: WARNING/ForkPoolWorker-2] 👂 [Event Subscriber] 'FileUploaded' 수신. 워커 출동.
[2026-04-17 07:38:11,715: WARNING/ForkPoolWorker-2] 🚀 [Celery] Organizer 파이프라인 가동 시작...
[2026-04-17 07:38:11,715: WARNING/ForkPoolWorker-2] [*] 파이프라인(ORM 기반)을 초기화합니다...
[2026-04-17 07:38:11,722: WARNING/ForkPoolWorker-2] 🚀 [GumaPhoto Pipeline] 데이터 정리를 시작합니다...
[2026-04-17 07:38:11,725: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:12,723: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:12,723: WARNING/ForkPoolWorker-2] [*] 스캔 완료. 찌꺼기 0개 삭제됨. 이제 하드디스크 이동을 시작합니다.
[2026-04-17 07:38:12,893: WARNING/ForkPoolWorker-2] [*] ✅ 배치 이동 완료! (배치 끝)
[2026-04-17 07:38:12,895: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:12,895: WARNING/ForkPoolWorker-2] 📢 [Event Bus 📡] 'FileOrganized' 이벤트가 전역(Global)으로 방송되었습니다. (Payload: {'total_items_organized': 1, 'timestamp': '2026-04-17T07:38:12.895489'})
[2026-04-17 07:38:14,536: WARNING/ForkPoolWorker-2] ✅ [Celery] Organizer 작업 완료!
[2026-04-17 07:38:14,538: WARNING/ForkPoolWorker-2] 👂 [Event Subscriber] 'FileOrganized' 수신. 워커 출동.
[2026-04-17 07:38:14,540: WARNING/ForkPoolWorker-2] 🚀 [Celery] Vector Indexer (딥러닝 VRAM 가동) 시작...
[2026-04-17 07:38:14,540: WARNING/ForkPoolWorker-2] [*] 벡터 DB (Qdrant) 접속 초기화... (http://qdrant:6333)
[2026-04-17 07:38:14,584: WARNING/ForkPoolWorker-2]   [-] 기존 Qdrant 컬렉션 'gumaphoto_hybrid_kr' 을 재사용합니다.
[2026-04-17 07:38:14,584: WARNING/ForkPoolWorker-2] [*] Qdrant에서 기존 인덱싱 된 파일 목록 캐싱 중...
[2026-04-17 07:38:15,763: WARNING/ForkPoolWorker-2]   [+] 총 26343개의 기존 처리 완료 파일이 캐시되었습니다.
[2026-04-17 07:38:15,763: WARNING/ForkPoolWorker-2] [*] 🖼️ 초정밀 SigLIP 이미지 인코더 로드 중 (google/siglip-base-patch16-224) ...
[2026-04-17 07:38:20,510: WARNING/ForkPoolWorker-2] [*] 👤 InsightFace 얼굴 인식 모델 로드 중 (buffalo_l) ...
[2026-04-17 07:38:20,876: WARNING/ForkPoolWorker-2] Applied providers: ['CUDAExecutionProvider', 'CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}, 'CUDAExecutionProvider': {'sdpa_kernel': '0', 'use_tf32': '1', 'fuse_conv_bias': '0', 'prefer_nhwc': '0', 'tunable_op_max_tuning_duration_ms': '0', 'enable_skip_layer_norm_strict_mode': '0', 'tunable_op_tuning_enable': '0', 'tunable_op_enable': '0', 'use_ep_level_unified_stream': '0', 'device_id': '0', 'has_user_compute_stream': '0', 'gpu_external_empty_cache': '0', 'cudnn_conv_algo_search': 'EXHAUSTIVE', 'cudnn_conv1d_pad_to_nc1d': '0', 'gpu_mem_limit': '18446744073709551615', 'gpu_external_alloc': '0', 'gpu_external_free': '0', 'arena_extend_strategy': 'kNextPowerOfTwo', 'do_copy_in_default_stream': '1', 'enable_cuda_graph': '0', 'user_compute_stream': '0', 'cudnn_conv_use_max_workspace': '1'}}
[2026-04-17 07:38:21,006: WARNING/ForkPoolWorker-2] find model:
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2] /root/.insightface/models/buffalo_l/1k3d68.onnx
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2] landmark_3d_68
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2] ['None', 3, 192, 192]
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2] 0.0
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,007: WARNING/ForkPoolWorker-2] 1.0
[2026-04-17 07:38:21,025: WARNING/ForkPoolWorker-2] Applied providers: ['CUDAExecutionProvider', 'CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}, 'CUDAExecutionProvider': {'sdpa_kernel': '0', 'use_tf32': '1', 'fuse_conv_bias': '0', 'prefer_nhwc': '0', 'tunable_op_max_tuning_duration_ms': '0', 'enable_skip_layer_norm_strict_mode': '0', 'tunable_op_tuning_enable': '0', 'tunable_op_enable': '0', 'use_ep_level_unified_stream': '0', 'device_id': '0', 'has_user_compute_stream': '0', 'gpu_external_empty_cache': '0', 'cudnn_conv_algo_search': 'EXHAUSTIVE', 'cudnn_conv1d_pad_to_nc1d': '0', 'gpu_mem_limit': '18446744073709551615', 'gpu_external_alloc': '0', 'gpu_external_free': '0', 'arena_extend_strategy': 'kNextPowerOfTwo', 'do_copy_in_default_stream': '1', 'enable_cuda_graph': '0', 'user_compute_stream': '0', 'cudnn_conv_use_max_workspace': '1'}}
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] find model:
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] /root/.insightface/models/buffalo_l/2d106det.onnx
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] landmark_2d_106
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] ['None', 3, 192, 192]
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] 0.0
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,028: WARNING/ForkPoolWorker-2] 1.0
[2026-04-17 07:38:21,106: WARNING/ForkPoolWorker-2] Applied providers: ['CUDAExecutionProvider', 'CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}, 'CUDAExecutionProvider': {'sdpa_kernel': '0', 'use_tf32': '1', 'fuse_conv_bias': '0', 'prefer_nhwc': '0', 'tunable_op_max_tuning_duration_ms': '0', 'enable_skip_layer_norm_strict_mode': '0', 'tunable_op_tuning_enable': '0', 'tunable_op_enable': '0', 'use_ep_level_unified_stream': '0', 'device_id': '0', 'has_user_compute_stream': '0', 'gpu_external_empty_cache': '0', 'cudnn_conv_algo_search': 'EXHAUSTIVE', 'cudnn_conv1d_pad_to_nc1d': '0', 'gpu_mem_limit': '18446744073709551615', 'gpu_external_alloc': '0', 'gpu_external_free': '0', 'arena_extend_strategy': 'kNextPowerOfTwo', 'do_copy_in_default_stream': '1', 'enable_cuda_graph': '0', 'user_compute_stream': '0', 'cudnn_conv_use_max_workspace': '1'}}
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] find model:
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] /root/.insightface/models/buffalo_l/det_10g.onnx
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] detection
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] [1, 3, '?', '?']
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] 127.5
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,107: WARNING/ForkPoolWorker-2] 128.0
[2026-04-17 07:38:21,134: WARNING/ForkPoolWorker-2] Applied providers: ['CUDAExecutionProvider', 'CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}, 'CUDAExecutionProvider': {'sdpa_kernel': '0', 'use_tf32': '1', 'fuse_conv_bias': '0', 'prefer_nhwc': '0', 'tunable_op_max_tuning_duration_ms': '0', 'enable_skip_layer_norm_strict_mode': '0', 'tunable_op_tuning_enable': '0', 'tunable_op_enable': '0', 'use_ep_level_unified_stream': '0', 'device_id': '0', 'has_user_compute_stream': '0', 'gpu_external_empty_cache': '0', 'cudnn_conv_algo_search': 'EXHAUSTIVE', 'cudnn_conv1d_pad_to_nc1d': '0', 'gpu_mem_limit': '18446744073709551615', 'gpu_external_alloc': '0', 'gpu_external_free': '0', 'arena_extend_strategy': 'kNextPowerOfTwo', 'do_copy_in_default_stream': '1', 'enable_cuda_graph': '0', 'user_compute_stream': '0', 'cudnn_conv_use_max_workspace': '1'}}
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] find model:
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] /root/.insightface/models/buffalo_l/genderage.onnx
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] genderage
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] ['None', 3, 96, 96]
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] 0.0
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,136: WARNING/ForkPoolWorker-2] 1.0
[2026-04-17 07:38:21,449: WARNING/ForkPoolWorker-2] Applied providers: ['CUDAExecutionProvider', 'CPUExecutionProvider'], with options: {'CPUExecutionProvider': {}, 'CUDAExecutionProvider': {'sdpa_kernel': '0', 'use_tf32': '1', 'fuse_conv_bias': '0', 'prefer_nhwc': '0', 'tunable_op_max_tuning_duration_ms': '0', 'enable_skip_layer_norm_strict_mode': '0', 'tunable_op_tuning_enable': '0', 'tunable_op_enable': '0', 'use_ep_level_unified_stream': '0', 'device_id': '0', 'has_user_compute_stream': '0', 'gpu_external_empty_cache': '0', 'cudnn_conv_algo_search': 'EXHAUSTIVE', 'cudnn_conv1d_pad_to_nc1d': '0', 'gpu_mem_limit': '18446744073709551615', 'gpu_external_alloc': '0', 'gpu_external_free': '0', 'arena_extend_strategy': 'kNextPowerOfTwo', 'do_copy_in_default_stream': '1', 'enable_cuda_graph': '0', 'user_compute_stream': '0', 'cudnn_conv_use_max_workspace': '1'}}
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] find model:
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] /root/.insightface/models/buffalo_l/w600k_r50.onnx
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] recognition
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] ['None', 3, 112, 112]
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] 127.5
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] 127.5
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2] set det-size:
[2026-04-17 07:38:21,650: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,651: WARNING/ForkPoolWorker-2] (640, 640)
[2026-04-17 07:38:21,651: WARNING/ForkPoolWorker-2] [*] ❤️ HSEmotion 표정 인식기 로드 중 (enet_b0_8_best_vgaf) ...
[2026-04-17 07:38:21,751: WARNING/ForkPoolWorker-2] /root/.hsemotion/enet_b0_8_best_vgaf.pt
[2026-04-17 07:38:21,751: WARNING/ForkPoolWorker-2]  
[2026-04-17 07:38:21,752: WARNING/ForkPoolWorker-2] Compose(
[2026-04-17 07:38:21,829: WARNING/ForkPoolWorker-2] [*] 📝 Florence-2-base VLM 상황 묘사 AI 로드 중 ...
[2026-04-17 07:38:25,685: WARNING/ForkPoolWorker-2]   [+] Florence-2-base 로드 완료!
[2026-04-17 07:38:25,685: WARNING/ForkPoolWorker-2]   [+] 모든 시각 초거대 AI 모델 로딩 완료!
[2026-04-17 07:38:25,685: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,428: WARNING/ForkPoolWorker-2] [*] 총 26345장의 대상 사진을 발견했습니다. (동영상 제외)
[2026-04-17 07:38:26,430: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,430: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,430: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,431: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,431: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,431: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,432: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,432: WARNING/ForkPoolWorker-2] 
[2026-04-17 07:38:26,432: WARNING/ForkPoolWorker-2] 
```

## 7. FastAPI app — last 100 log lines
```
INFO:     172.24.0.1:48426 - "GET /api/feedback_v2/unknown?_rnd=1776411493985_0.21342505804470113 HTTP/1.0" 200 OK
INFO:     172.24.0.1:48450 - "GET /photos/2026/2026-04/2026-04_01_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48494 - "GET /photos/2026/2026-04/2026-04_05_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48440 - "GET /photos/UnknownDate/Unknown-Year_02_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48442 - "GET /photos/2026/2026-04/2026-04_07_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48506 - "GET /photos/2026/2026-04/2026-04_03_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48480 - "GET /photos/2026/2026-04/2026-04_02_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48468 - "GET /photos/2026/2026-03/2026-03_02_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48462 - "GET /photos/2026/2026-04/2026-04_06_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48542 - "GET /photos/2026/2026-04/2026-04_08_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48472 - "GET /photos/2026/2026-03/2026-03_01_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48528 - "GET /photos/2026/2026-04/2026-04_04_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48546 - "GET /photos/2026/2026-02/2026-02_0142_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48590 - "GET /photos/2026/2026-02/2026-02_0182_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48576 - "GET /photos/2026/2026-02/2026-02_0220_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48514 - "GET /photos/2026/2026-02/2026-02_0245_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48584 - "GET /photos/2026/2026-02/2026-02_0171_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48570 - "GET /photos/2026/2026-04/2026-04_09_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48598 - "GET /photos/2026/2026-03/2026-03_03_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48560 - "GET /photos/UnknownDate/Unknown-Year_01_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:48614 - "GET /photos/2013/2013-08/2013-08_0450_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48662 - "GET /photos/2023/2023-03/2023-03_0095_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48668 - "GET /photos/2020/2020-07/2020-07_0261_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48652 - "GET /photos/2023/2023-08/2023-08_0147_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48672 - "GET /photos/2023/2023-01/2023-01_0045_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48626 - "GET /photos/2026/2026-02/2026-02_0141_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48632 - "GET /photos/2025/2025-03/2025-03_0158_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48654 - "GET /photos/2017/2017-03/2017-03_0475_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48636 - "GET /photos/2025/2025-01/2025-01_0075_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:48628 - "GET /photos/2026/2026-02/2026-02_0188_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60806 - "GET / HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:60816 - "POST /api/search HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60826 - "GET /api/feedback_v2/unknown?_rnd=1776411526284_0.8653800567363844 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60842 - "GET /api/feedback_v2/unknown?_rnd=1776411526284_0.4229947718168229 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60856 - "GET /api/feedback_v2/unknown?_rnd=1776411526284_0.5624488622035185 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60870 - "GET /api/feedback_v2/unknown?_rnd=1776411526285_0.8822717755815919 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60888 - "GET /api/feedback_v2/unknown?_rnd=1776411526284_0.447521790328653 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60892 - "GET /api/feedback_v2/unknown?_rnd=1776411526285_0.4851119305519358 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60894 - "GET /api/feedback_v2/unknown?_rnd=1776411526285_0.6277517870897923 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60910 - "GET /api/feedback_v2/unknown?_rnd=1776411526285_0.953543024833546 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60926 - "GET /api/feedback_v2/unknown?_rnd=1776411526285_0.6753803146916897 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60934 - "GET /api/feedback_v2/unknown?_rnd=1776411526284_0.1455688489728102 HTTP/1.0" 200 OK
INFO:     172.24.0.1:60876 - "GET /photos/2026/2026-04/2026-04_10_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35508 - "GET /photos/2023/2023-05/2023-05_0116_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:35492 - "GET /photos/2023/2023-10/2023-10_0187_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35478 - "GET /photos/2025/2025-08/2025-08_0134_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35462 - "GET /photos/2023/2023-03/2023-03_0042_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35522 - "GET /photos/2017/2017-03/2017-03_0424_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35568 - "GET /photos/2023/2023-06/2023-06_0025_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35546 - "GET /photos/2023/2023-01/2023-01_0113_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35524 - "GET /photos/2019/2019-11/2019-11_0097_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35560 - "GET /photos/2021/2021-09/2021-09_0075_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:35534 - "GET /photos/2024/2024-10/2024-10_0047_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:42904 - "GET / HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:42916 - "POST /api/search HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:42926 - "GET /api/feedback_v2/unknown?_rnd=1776411539864_0.3747597370083181 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:42940 - "GET /api/feedback_v2/unknown?_rnd=1776411539864_0.3055643992443753 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42956 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.20226704616766178 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42968 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.11216645496351607 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42984 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.10477454897533311 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42986 - "GET /api/feedback_v2/unknown?_rnd=1776411539866_0.7654054967020294 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42988 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.2709966940661299 HTTP/1.0" 200 OK
INFO:     172.24.0.1:42990 - "GET /api/feedback_v2/unknown?_rnd=1776411539864_0.09922648463204664 HTTP/1.0" 200 OK
INFO:     172.24.0.1:43000 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.4453453088684918 HTTP/1.0" 200 OK
INFO:     172.24.0.1:43002 - "GET /api/feedback_v2/unknown?_rnd=1776411539865_0.6309767689691037 HTTP/1.0" 200 OK
INFO:     172.24.0.1:43020 - "GET /photos/2012/2012-04/2012-04_0063_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:43018 - "GET /photos/2025/2025-07/2025-07_0165_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:39232 - "GET / HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:39238 - "POST /api/search HTTP/1.0" 200 OK
INFO:     172.24.0.1:39240 - "GET /api/feedback_v2/unknown?_rnd=1776411568677_0.009835532400031655 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39246 - "GET /api/feedback_v2/unknown?_rnd=1776411568677_0.9288643253248132 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39248 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.0841369793593103 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39260 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.7397760927041056 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39270 - "GET /api/feedback_v2/unknown?_rnd=1776411568677_0.34829392068403453 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39284 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.7599777377433765 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39288 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.9152028051718039 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39300 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.1527277194070482 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39316 - "GET /api/feedback_v2/unknown?_rnd=1776411568678_0.6527699585644211 HTTP/1.0" 200 OK
INFO:     172.24.0.1:39318 - "GET /api/feedback_v2/unknown?_rnd=1776411568679_0.19252074286321474 HTTP/1.0" 200 OK
```

## 8. Redis — queue keys / celery queue length
```
0
_kombu.binding.reply.celery.pidbox
celery-task-meta-66b50aeb-7ef3-4853-b12e-396356fe1940
_kombu.binding.celeryev
gumaphoto_logs_history
celery-task-meta-0b15633f-f50d-4c5c-9f62-479895c70c60
celery-task-meta-4251ae54-18eb-4e05-8f40-f30c0899e3a4
_kombu.binding.celery.pidbox
_kombu.binding.celery
celery-task-meta-825dff40-33fd-4db1-a39f-bfdc12839b28
```

## 9. Qdrant — collection stats
```
{"result":{"status":"green","optimizer_status":"ok","indexed_vectors_count":0,"points_count":26344,"segments_count":8,"config":{"params":{"vectors":{"face":{"size":512,"distance":"Cosine"},"scene":{"size":768,"distance":"Cosine"}},"shard_number":1,"replication_factor":1,"write_consistency_factor":1,"on_disk_payload":true},"hnsw_config":{"m":16,"ef_construct":100,"full_scan_threshold":10000,"max_indexing_threads":0,"on_disk":false},"optimizer_config":{"deleted_threshold":0.2,"vacuum_min_vector_number":1000,"default_segment_number":0,"max_segment_size":null,"memmap_threshold":null,"indexing_threshold":10000,"flush_interval_sec":5,"max_optimization_threads":null,"prevent_unoptimized":null},"wal_config":{"wal_capacity_mb":32,"wal_segments_ahead":0,"wal_retain_closed":1},"quantization_config":null},"payload_schema":{"caption":{"data_type":"text","points":26344},"filepath":{"data_type":"keyword","points":26344},"hash":{"data_type":"keyword","points":26344},"people":{"data_type":"keyword","points":26344},"location":{"data_type":"text","points":26344},"original_context":{"data_type":"text","points":26344},"objects":{"data_type":"keyword","points":26221},"geo_point":{"data_type":"geo","points":25237},"sort_date":{"data_type":"integer","points":26344}},"update_queue":{"length":0}},"status":"ok","time":0.000551274}```

