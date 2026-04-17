# GumaPhoto Diagnostic Run

- Run: `24553564061`
- Commit: `f65af9426916a6d0acaa6dfdde81ce30bd0458de`
- Timestamp (UTC): 2026-04-17 07:34:06

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

2026-04-16  ���� 08:58         4,828,352 timeline_cache.json
               1�� ����           4,828,352 ����Ʈ
               0�� ���͸�  427,835,211,776 ����Ʈ ����
```

## 3. uploads_raw/ recent files (stuck = Organizer didn't pick up)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures\uploads_raw ���͸�

2026-04-16  ���� 08:57    <DIR>          .
2026-04-12  ���� 05:15    <DIR>          ..
               0�� ����                   0 ����Ʈ
               2�� ���͸�  427,835,211,776 ����Ʈ ����
```

## 4. Pictures/ recently modified folders (Organizer output)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures ���͸�

2026-04-16  ���� 08:57    <DIR>          uploads_raw
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
              23�� ���͸�  427,835,211,776 ����Ʈ ����
```

## 5. Celery worker — last 200 log lines
```
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25336 ~ 25350 / 26344
[2026-04-15 23:57:57,478: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25351 ~ 25365 / 26344
[2026-04-15 23:57:57,479: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25366 ~ 25380 / 26344
[2026-04-15 23:57:57,479: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25381 ~ 25395 / 26344
[2026-04-15 23:57:57,479: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25396 ~ 25410 / 26344
[2026-04-15 23:57:57,479: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25411 ~ 25425 / 26344
[2026-04-15 23:57:57,479: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25426 ~ 25440 / 26344
[2026-04-15 23:57:57,480: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25441 ~ 25455 / 26344
[2026-04-15 23:57:57,480: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25456 ~ 25470 / 26344
[2026-04-15 23:57:57,480: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25471 ~ 25485 / 26344
[2026-04-15 23:57:57,480: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25486 ~ 25500 / 26344
[2026-04-15 23:57:57,480: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25501 ~ 25515 / 26344
[2026-04-15 23:57:57,481: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25516 ~ 25530 / 26344
[2026-04-15 23:57:57,481: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25531 ~ 25545 / 26344
[2026-04-15 23:57:57,481: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25546 ~ 25560 / 26344
[2026-04-15 23:57:57,481: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25561 ~ 25575 / 26344
[2026-04-15 23:57:57,481: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25576 ~ 25590 / 26344
[2026-04-15 23:57:57,482: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25591 ~ 25605 / 26344
[2026-04-15 23:57:57,482: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25606 ~ 25620 / 26344
[2026-04-15 23:57:57,482: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25621 ~ 25635 / 26344
[2026-04-15 23:57:57,482: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25636 ~ 25650 / 26344
[2026-04-15 23:57:57,482: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25651 ~ 25665 / 26344
[2026-04-15 23:57:57,483: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25666 ~ 25680 / 26344
[2026-04-15 23:57:57,483: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25681 ~ 25695 / 26344
[2026-04-15 23:57:57,483: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25696 ~ 25710 / 26344
[2026-04-15 23:57:57,483: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25711 ~ 25725 / 26344
[2026-04-15 23:57:57,483: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25726 ~ 25740 / 26344
[2026-04-15 23:57:57,484: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25741 ~ 25755 / 26344
[2026-04-15 23:57:57,484: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25756 ~ 25770 / 26344
[2026-04-15 23:57:57,484: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25771 ~ 25785 / 26344
[2026-04-15 23:57:57,484: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25786 ~ 25800 / 26344
[2026-04-15 23:57:57,484: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25801 ~ 25815 / 26344
[2026-04-15 23:57:57,485: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25816 ~ 25830 / 26344
[2026-04-15 23:57:57,485: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25831 ~ 25845 / 26344
[2026-04-15 23:57:57,485: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25846 ~ 25860 / 26344
[2026-04-15 23:57:57,485: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25861 ~ 25875 / 26344
[2026-04-15 23:57:57,485: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25876 ~ 25890 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25891 ~ 25905 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25906 ~ 25920 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25921 ~ 25935 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25936 ~ 25950 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25951 ~ 25965 / 26344
[2026-04-15 23:57:57,486: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25966 ~ 25980 / 26344
[2026-04-15 23:57:57,487: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25981 ~ 25995 / 26344
[2026-04-15 23:57:57,487: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 25996 ~ 26010 / 26344
[2026-04-15 23:57:57,487: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26011 ~ 26025 / 26344
[2026-04-15 23:57:57,487: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26026 ~ 26040 / 26344
[2026-04-15 23:57:57,487: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26041 ~ 26055 / 26344
[2026-04-15 23:57:57,488: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26056 ~ 26070 / 26344
[2026-04-15 23:57:57,488: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26071 ~ 26085 / 26344
[2026-04-15 23:57:57,488: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26086 ~ 26100 / 26344
[2026-04-15 23:57:57,731: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26101 ~ 26115 / 26344
[2026-04-15 23:58:01,276: WARNING/ForkPoolWorker-2] DEBUG: /app/data/organized/2026/2026-04/2026-04_09.jpeg => date_str: 2026-04, sort_date: 20260401
[2026-04-15 23:58:01,308: INFO/ForkPoolWorker-2] HTTP Request: PUT http://qdrant:6333/collections/gumaphoto_hybrid_kr/points?wait=true "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,442: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26116 ~ 26130 / 26344
[2026-04-15 23:58:01,442: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26131 ~ 26145 / 26344
[2026-04-15 23:58:01,443: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26146 ~ 26160 / 26344
[2026-04-15 23:58:01,443: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26161 ~ 26175 / 26344
[2026-04-15 23:58:01,444: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26176 ~ 26190 / 26344
[2026-04-15 23:58:01,444: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26191 ~ 26205 / 26344
[2026-04-15 23:58:01,444: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26206 ~ 26220 / 26344
[2026-04-15 23:58:01,445: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26221 ~ 26235 / 26344
[2026-04-15 23:58:01,448: WARNING/ForkPoolWorker-2]       ⚠️ 이미지 로드 오류 (Skip): UnknownDate_0127.jpg - cannot identify image file '/app/data/organized/UnknownDate/UnknownDate_0127.jpg'
[2026-04-15 23:58:01,449: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26236 ~ 26250 / 26344
[2026-04-15 23:58:01,449: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26251 ~ 26265 / 26344
[2026-04-15 23:58:01,449: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26266 ~ 26280 / 26344
[2026-04-15 23:58:01,449: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26281 ~ 26295 / 26344
[2026-04-15 23:58:01,449: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26296 ~ 26310 / 26344
[2026-04-15 23:58:01,450: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26311 ~ 26325 / 26344
[2026-04-15 23:58:01,450: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26326 ~ 26340 / 26344
[2026-04-15 23:58:01,450: WARNING/ForkPoolWorker-2] 
[*] 📦 배치 진행 중 (CPU+GPU 풀가동): 26341 ~ 26344 / 26344
[2026-04-15 23:58:01,450: WARNING/ForkPoolWorker-2] 
✅ 모든 사진의 [얼굴 + 배경 상황] 벡터 데이터베이스 컴파일이 완료되었습니다!
[2026-04-15 23:58:01,451: WARNING/ForkPoolWorker-2] ✅ [Celery] Vector Indexer 작업 완료!
[2026-04-15 23:58:01,464: WARNING/ForkPoolWorker-2] [Family Profile] 가족 프로필 로드 완료: ['성욱', '송이', '준우', '지우', '원길', '현숙']
[2026-04-15 23:58:01,522: WARNING/ForkPoolWorker-2] [Timeline Cache] Celery context: Qdrant client lazy-initialized.
[2026-04-15 23:58:01,530: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,552: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,554: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,558: INFO/ForkPoolWorker-2] HTTP Request: GET http://qdrant:6333 "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,606: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,661: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,665: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,669: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,718: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,766: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,767: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,769: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,771: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,773: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,780: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,835: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,837: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,847: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,907: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,909: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,912: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,914: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,917: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,919: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,923: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:01,968: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,018: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,028: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,081: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,090: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,092: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,094: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,096: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,103: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,158: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,160: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,161: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,162: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,163: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,173: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,187: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,188: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,189: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,191: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,194: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,197: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,199: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,202: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,205: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,214: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,265: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,268: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,270: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,314: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,316: INFO/ForkPoolWorker-2] HTTP Request: POST http://qdrant:6333/collections/gumaphoto_hybrid_kr/points/scroll "HTTP/1.1 200 OK"
[2026-04-15 23:58:02,661: WARNING/ForkPoolWorker-2] ✅ [Timeline Cache] 재생성 완료: recent=500장, 인물 53명
[2026-04-15 23:58:02,723: INFO/ForkPoolWorker-2] Task tasks.indexer[e8e8c450-1ec2-42a7-bfd4-d69ab57f6c3d] succeeded in 19.237956878000205s: None
```

## 6. Celery — errors / tracebacks in last 24h
```
```

## 7. FastAPI app — last 100 log lines
```
[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:34042 - "POST /api/search HTTP/1.0" 200 OK
INFO:     172.24.0.1:34058 - "GET /photos/2026/2026-02/2026-02_0142_heic.webp HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34104 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.560214803771708 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34130 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.775312810141012 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34074 - "GET /photos/UnknownDate/Unknown-Year_01_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34076 - "GET /photos/2026/2026-03/2026-03_03_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34084 - "GET /photos/2026/2026-04/2026-04_07_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34090 - "GET /photos/2026/2026-04/2026-04_04_jpeg.webp HTTP/1.0" 304 Not Modified
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34220 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.39156841377894835 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34232 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.3596738978640318 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34236 - "GET /api/feedback_v2/unknown?_rnd=1776397556034_0.07259310610476721 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34254 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.735742551733102 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34262 - "GET /api/feedback_v2/unknown?_rnd=1776397556034_0.7405966850242488 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34112 - "GET /photos/UnknownDate/Unknown-Year_02_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34110 - "GET /photos/2026/2026-04/2026-04_06_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34120 - "GET /photos/2026/2026-04/2026-04_08_jpeg.webp HTTP/1.0" 304 Not Modified
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34280 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.7531668707967012 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34290 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.3066879383946016 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34302 - "GET /api/feedback_v2/unknown?_rnd=1776397556035_0.40956811522812786 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34188 - "GET /photos/2026/2026-03/2026-03_02_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34134 - "GET /photos/2026/2026-02/2026-02_0171_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34140 - "GET /photos/2026/2026-02/2026-02_0231_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34192 - "GET /photos/2026/2026-02/2026-02_0182_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34178 - "GET /photos/2026/2026-02/2026-02_0220_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34244 - "GET /photos/2026/2026-02/2026-02_0245_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34270 - "GET /photos/2026/2026-03/2026-03_01_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34156 - "GET /photos/2026/2026-04/2026-04_05_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34206 - "GET /photos/2026/2026-04/2026-04_03_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34164 - "GET /photos/2026/2026-04/2026-04_01_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34264 - "GET /photos/2026/2026-04/2026-04_02_jpeg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34316 - "GET /sw.js HTTP/1.0" 200 OK
INFO:     172.24.0.1:34278 - "GET /photos/2026/2026-04/2026-04_09_jpeg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:34338 - "GET /photos/2011/2011-08/2011-08_0003_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34332 - "GET /photos/2020/2020-01/2020-01_0029_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34346 - "GET /photos/2019/2019-12/2019-12_0868_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34356 - "GET /photos/2023/2023-08/2023-08_0081_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34366 - "GET /photos/2024/2024-06/2024-06_0217_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34392 - "GET /photos/2024/2024-06/2024-06_0169_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34386 - "GET /photos/2023/2023-09/2023-09_0016_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34374 - "GET /photos/2017/2017-03/2017-03_0460_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34398 - "GET /photos/2025/2025-01/2025-01_0031_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34408 - "GET /photos/2024/2024-10/2024-10_0095_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34190 - "GET / HTTP/1.0" 200 OK
INFO:     172.24.0.1:34200 - "GET /frontend/js_modules/utils.js?v=2 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34196 - "GET /frontend/js_modules/state/store.js?v=2 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34208 - "GET /frontend/main.js?v=12 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34210 - "GET /frontend/apple-touch-icon.png HTTP/1.0" 200 OK
INFO:     172.24.0.1:34256 - "GET /frontend/style.css?v=150 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34222 - "GET /frontend/js_modules/components/lightbox.js?v=3 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34242 - "GET /frontend/js_modules/components/feedback.js?v=8 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34226 - "GET /frontend/js_modules/components/upload.js?v=2 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34262 - "GET /frontend/js_modules/components/gallery.js?v=2 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34268 - "GET /frontend/js_modules/api/fetcher.js?v=4 HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:34284 - "POST /api/search HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34292 - "GET /api/feedback_v2/unknown?_rnd=1776409963106_0.48060848591930816 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34304 - "GET /api/feedback_v2/unknown?_rnd=1776409963106_0.3419501238819729 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34306 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.6825235798948105 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34310 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.6206829383006917 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34326 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.4871248247500839 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34342 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.3824851601739573 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34356 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.4138675979150499 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34370 - "GET /api/feedback_v2/unknown?_rnd=1776409963107_0.9440523541030651 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34372 - "GET /api/feedback_v2/unknown?_rnd=1776409963106_0.17837516188546587 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:34378 - "GET /api/feedback_v2/unknown?_rnd=1776409963106_0.7413115307453114 HTTP/1.0" 200 OK
INFO:     172.24.0.1:34388 - "GET /sw.js HTTP/1.0" 200 OK
INFO:     172.24.0.1:34418 - "GET /photos/2025/2025-12/2025-12_0221_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34406 - "GET /photos/2022/2022-09/2022-09_0125_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34398 - "GET /photos/2023/2023-01/2023-01_0036_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34446 - "GET /photos/2019/2019-12/2019-12_0573_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34460 - "GET /photos/2023/2023-02/2023-02_0104_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34432 - "GET /photos/2021/2021-03/2021-03_0178_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34466 - "GET /photos/2023/2023-12/2023-12_0110_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34448 - "GET /photos/2025/2025-10/2025-10_0102_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34476 - "GET /photos/2024/2024-07/2024-07_0082_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:34490 - "GET /photos/2017/2017-03/2017-03_0427_jpg.webp HTTP/1.0" 200 OK
```

## 8. Redis — queue keys / celery queue length
```
0
_kombu.binding.reply.celery.pidbox
_kombu.binding.celeryev
gumaphoto_logs_history
_kombu.binding.celery.pidbox
_kombu.binding.celery
```

## 9. Qdrant — collection stats
```
{"result":{"status":"green","optimizer_status":"ok","indexed_vectors_count":0,"points_count":26343,"segments_count":8,"config":{"params":{"vectors":{"face":{"size":512,"distance":"Cosine"},"scene":{"size":768,"distance":"Cosine"}},"shard_number":1,"replication_factor":1,"write_consistency_factor":1,"on_disk_payload":true},"hnsw_config":{"m":16,"ef_construct":100,"full_scan_threshold":10000,"max_indexing_threads":0,"on_disk":false},"optimizer_config":{"deleted_threshold":0.2,"vacuum_min_vector_number":1000,"default_segment_number":0,"max_segment_size":null,"memmap_threshold":null,"indexing_threshold":10000,"flush_interval_sec":5,"max_optimization_threads":null,"prevent_unoptimized":null},"wal_config":{"wal_capacity_mb":32,"wal_segments_ahead":0,"wal_retain_closed":1},"quantization_config":null},"payload_schema":{"caption":{"data_type":"text","points":26343},"filepath":{"data_type":"keyword","points":26343},"people":{"data_type":"keyword","points":26343},"objects":{"data_type":"keyword","points":26220},"geo_point":{"data_type":"geo","points":25236},"location":{"data_type":"text","points":26343},"sort_date":{"data_type":"integer","points":26343},"hash":{"data_type":"keyword","points":26343},"original_context":{"data_type":"text","points":26343}},"update_queue":{"length":0}},"status":"ok","time":0.000374174}```

