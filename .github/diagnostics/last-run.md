# GumaPhoto Diagnostic Run

- Run: `24555306115`
- Commit: `9b7c7a9ddd16069d0b226343971ab4191a2a45bd`
- Timestamp (UTC): 2026-04-17 08:19:54

## 1. Container status
```
NAMES              STATUS        CREATED
gumaphoto_app      Up 33 hours   2 days ago
gumaphoto_celery   Up 33 hours   2 days ago
gumaphoto_redis    Up 33 hours   3 weeks ago
gumaphoto_qdrant   Up 33 hours   4 weeks ago
```

## 1b. Migration process probe (celery container)
```
UID        PID  PPID  C STIME TTY          TIME CMD
root       375     0  0 08:04 ?        00:00:08 python /app/Scripts/migrate_sort_date_from_exif.py --dry-run
--- celery container top (5s sample) ---
cpu=26.96% mem=2.784GiB / 15.48GiB
```

## 2. Timeline cache file (mtime / size)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\TheGumaLab\GumaPhoto\data\caches ���͸�

2026-04-17  ���� 04:38         4,827,717 timeline_cache.json
               1�� ����           4,827,717 ����Ʈ
               0�� ���͸�  427,846,246,400 ����Ʈ ����
```

## 3. uploads_raw/ recent files (stuck = Organizer didn't pick up)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures\uploads_raw ���͸�

2026-04-17  ���� 04:38    <DIR>          .
2026-04-12  ���� 05:15    <DIR>          ..
               0�� ����                   0 ����Ʈ
               2�� ���͸�  427,846,246,400 ����Ʈ ����
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
              23�� ���͸�  427,846,246,400 ����Ʈ ����
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
INFO:     172.24.0.1:54568 - "GET /photos/2026/2026-02/2026-02_0128_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54562 - "GET /photos/2026/2026-02/2026-02_0217_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54654 - "GET /photos/2026/2026-02/2026-02_0224_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54620 - "GET /photos/2026/2026-02/2026-02_0228_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54658 - "GET /photos/2026/2026-02/2026-02_0107_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54660 - "GET /photos/2026/2026-02/2026-02_0100_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54666 - "GET /photos/2026/2026-02/2026-02_0106_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54570 - "GET /photos/2026/2026-02/2026-02_0134_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54672 - "GET /photos/2026/2026-02/2026-02_0099_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54698 - "GET /photos/2026/2026-02/2026-02_0108_jpg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:54708 - "GET /photos/2026/2026-02/2026-02_0225_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54702 - "GET /photos/2026/2026-02/2026-02_0095_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54704 - "GET /photos/2026/2026-02/2026-02_0102_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:54718 - "GET /photos/2026/2026-02/2026-02_0104_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54732 - "GET /photos/2026/2026-02/2026-02_0097_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:54748 - "GET /photos/2026/2026-02/2026-02_0121_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54762 - "GET /photos/2026/2026-02/2026-02_0124_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54778 - "GET /photos/2026/2026-02/2026-02_0101_heic.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:54792 - "GET /photos/2026/2026-02/2026-02_0109_jpg.webp HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=140, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (140~160장)
INFO:     172.24.0.1:54884 - "POST /api/search HTTP/1.0" 200 OK
INFO:     172.24.0.1:54808 - "GET /photos/2026/2026-02/2026-02_0237_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54810 - "GET /photos/2026/2026-02/2026-02_0236_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54818 - "GET /photos/2026/2026-02/2026-02_0105_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54824 - "GET /photos/2026/2026-02/2026-02_0241_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54838 - "GET /photos/2026/2026-02/2026-02_0120_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54862 - "GET /photos/2026/2026-02/2026-02_0113_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54836 - "GET /photos/2026/2026-02/2026-02_0239_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54848 - "GET /photos/2026/2026-02/2026-02_0103_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54872 - "GET /photos/2026/2026-02/2026-02_0098_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54878 - "GET /photos/2026/2026-02/2026-02_0110_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54870 - "GET /photos/2026/2026-02/2026-02_0115_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54896 - "GET /photos/2026/2026-02/2026-02_0112_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54912 - "GET /photos/2026/2026-02/2026-02_0117_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54928 - "GET /photos/2026/2026-02/2026-02_0111_jpg.webp HTTP/1.0" 304 Not Modified
INFO:     172.24.0.1:54942 - "GET /photos/2026/2026-02/2026-02_0116_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54976 - "GET / HTTP/1.0" 200 OK
INFO:     172.24.0.1:54954 - "GET /photos/2026/2026-02/2026-02_0037_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54966 - "GET /photos/2026/2026-02/2026-02_0004_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54982 - "GET /photos/2026/2026-02/2026-02_0118_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55024 - "GET /photos/2026/2026-02/2026-02_0122_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55038 - "GET /photos/2026/2026-02/2026-02_0123_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:54992 - "GET /photos/2026/2026-02/2026-02_0002_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55010 - "GET /photos/2026/2026-02/2026-02_0119_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55008 - "GET /photos/2026/2026-02/2026-02_0114_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55046 - "GET /photos/2026/2026-02/2026-02_0001_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55070 - "GET /photos/2026/2026-02/2026-02_0003_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55054 - "GET /photos/2026/2026-02/2026-02_0044_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55074 - "GET /photos/2026/2026-02/2026-02_0038_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55076 - "GET /photos/2026/2026-02/2026-02_0041_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55086 - "GET /photos/2026/2026-02/2026-02_0045_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55098 - "GET /photos/2026/2026-02/2026-02_0039_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55100 - "GET /photos/2026/2026-02/2026-02_0047_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55110 - "GET /photos/2026/2026-02/2026-02_0049_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55114 - "GET /photos/2026/2026-02/2026-02_0042_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:55116 - "GET /photos/2026/2026-02/2026-02_0036_heic.webp HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=0, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (0~20장)
INFO:     172.24.0.1:60054 - "POST /api/search HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60058 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.5640714413107584 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60074 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.33885715814686135 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60076 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.3331909345124737 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60086 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.6304806927103263 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60102 - "GET /api/feedback_v2/unknown?_rnd=1776411827437_0.5697911436819734 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60114 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.5836947107633986 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60118 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.3508210862190587 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60124 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.05796540234439429 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60134 - "GET /api/feedback_v2/unknown?_rnd=1776411827437_0.36011960728469594 HTTP/1.0" 200 OK
[FeedbackCache] 💾 Successfully saved queue to disk persistence.
INFO:     172.24.0.1:60148 - "GET /api/feedback_v2/unknown?_rnd=1776411827436_0.8592108981196586 HTTP/1.0" 200 OK
INFO:     172.24.0.1:60152 - "GET /photos/2026/2026-01/2026-01_0182_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60226 - "GET /photos/2023/2023-10/2023-10_0183_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60176 - "GET /photos/2023/2023-10/2023-10_0207_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60224 - "GET /photos/2023/2023-10/2023-10_0205_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60204 - "GET /photos/2013/2013-01/2013-01_0001_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60234 - "GET /photos/UnknownDate/UnknownDate_0050_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60194 - "GET /photos/2013/2013-01/2013-01_0293_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60168 - "GET /photos/2025/2025-11/2025-11_0141_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60186 - "GET /photos/2017/2017-03/2017-03_0275_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:60218 - "GET /photos/2021/2021-04/2021-04_0195_jpg.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:56166 - "GET /photos/2026/2026-02/2026-02_0232_heic.webp HTTP/1.0" 200 OK

[🔍 Search API] 요청 수신: 쿼리='timeline_dummy', offset=20, limit=20
🚀 [Baking Cache Hit] Guma Family 통합 아키텍처 JSON 반환: recent (20~40장)
INFO:     172.24.0.1:56170 - "POST /api/search HTTP/1.0" 200 OK
INFO:     172.24.0.1:56180 - "GET /photos/2026/2026-02/2026-02_0232_heic.webp HTTP/1.0" 200 OK
INFO:     172.24.0.1:39076 - "GET /photos/2026/2026-04/2026-04_10.jpeg HTTP/1.0" 200 OK
INFO:     172.24.0.1:39090 - "GET /photos/2026/2026-04/2026-04_06.jpeg HTTP/1.0" 200 OK
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
{"result":{"status":"green","optimizer_status":"ok","indexed_vectors_count":0,"points_count":26344,"segments_count":8,"config":{"params":{"vectors":{"face":{"size":512,"distance":"Cosine"},"scene":{"size":768,"distance":"Cosine"}},"shard_number":1,"replication_factor":1,"write_consistency_factor":1,"on_disk_payload":true},"hnsw_config":{"m":16,"ef_construct":100,"full_scan_threshold":10000,"max_indexing_threads":0,"on_disk":false},"optimizer_config":{"deleted_threshold":0.2,"vacuum_min_vector_number":1000,"default_segment_number":0,"max_segment_size":null,"memmap_threshold":null,"indexing_threshold":10000,"flush_interval_sec":5,"max_optimization_threads":null,"prevent_unoptimized":null},"wal_config":{"wal_capacity_mb":32,"wal_segments_ahead":0,"wal_retain_closed":1},"quantization_config":null},"payload_schema":{"sort_date":{"data_type":"integer","points":26344},"objects":{"data_type":"keyword","points":26221},"people":{"data_type":"keyword","points":26344},"original_context":{"data_type":"text","points":26344},"filepath":{"data_type":"keyword","points":26344},"location":{"data_type":"text","points":26344},"geo_point":{"data_type":"geo","points":25237},"caption":{"data_type":"text","points":26344},"hash":{"data_type":"keyword","points":26344}},"update_queue":{"length":0}},"status":"ok","time":0.000385265}```

## 9b. Qdrant — top 5 newest by sort_date (latest photos)
```
{"result":{"points":[{"id":"96078aa0-daf4-5867-9937-fe643d944ac1","version":0,"score":1.0,"payload":{"filepath":"/app/data/organized/UnknownDate/Unknown-Year_02.jpeg","filename":"Unknown-Year_02.jpeg","original_context":"UnknownDate","face_count":1,"people":["준우"],"date":"2026-04","sort_date":20260414,"location":"대한민국 경기도 하남시 학암동","season":"봄","time_of_day":"낮","objects":["boy","flower","human face","5세","5살"],"caption":"The image shows a young boy standing in front of a bush with white flowers. He is wearing a white t-shirt with the word \"Essential\" written on it and a blue lanyard around his neck. He has a black headband with small white flowers on it. The boy is making a peace sign with his right hand and is smiling at the camera. The background appears to be a garden or park with a stone wall and a fence.","hash":"e172899571d4fdaa6205ac020ad441d71e7851ef180c8c29e83f49debbf09548","age":5,"gender":"남성","face_bbox":[239,332,456,596],"emotion":"neutral","geo_point":{"lat":37.476964,"lon":127.14947}},"order_value":20260414},{"id":"67061911-86de-5e5a-a446-91b1cd55227a","version":0,"score":1.0,"payload":{"filepath":"/app/data/organized/UnknownDate/Unknown-Year_01.jpeg","filename":"Unknown-Year_01.jpeg","original_context":"UnknownDate","face_count":1,"people":["준우"],"date":"2026-04","sort_date":20260414,"location":"대한민국 경기도 하남시 학암동","season":"봄","time_of_day":"낮","objects":["boy","hat","human face","26세","26살"],"caption":"The image is a close-up portrait of a young boy. He is wearing a black baseball cap and a blue and white plaid shirt. He has a big smile on his face and is holding up his hand with his fingers. The background shows a park with trees and a stone wall. The boy appears to be happy and relaxed.","hash":"31232e3413a8edd7892f451674fa8e1bdd51280a6c6071d15271436256d295d3","age":26,"gender":"남성","face_bbox":[306,245,646,671],"emotion":"neutral","geo_point":{"lat":37.476964,"lon":127.14947}},"order_value":20260414},{"id":"d904c649-cabf-5186-acae-21af961482a5","version":0,"score":1.0,"payload":{"filepath":"/app/data/organized/2026/2026-04/2026-04_04.jpeg","filename":"2026-04_04.jpeg","original_context":"2026-04","face_count":0,"people":["No People"],"date":"2026-04","sort_date":20260401,"location":"대한민국 경기도 성남시 위례동","season":"봄","time_of_day":"아침","objects":["flower"],"caption":"The image shows a pathway lined with trees on both sides. The trees are covered in white cherry blossom flowers, creating a beautiful contrast against the green foliage. The pathway is made of concrete and has a small patch of grass on the right side. The sky is overcast and the overall mood of the image is peaceful and serene.<pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad>","hash":"3fe1959af5c39e83ced07b41cae6ab1d633fcdac1ef8c3d6ec8e05cb08d7c02c","geo_point":{"lat":37.47495,"lon":127.155839}},"order_value":20260401},{"id":"a44a9790-d68f-5d0f-a992-ae53ae90a4ce","version":0,"score":1.0,"payload":{"filepath":"/app/data/organized/2026/2026-04/2026-04_09.jpeg","filename":"2026-04_09.jpeg","original_context":"2026-04","face_count":1,"people":["지우"],"date":"2026-04","sort_date":20260401,"location":"Unknown Location","season":"봄","time_of_day":"아침","objects":["boy","flower","footwear","human face","5세","5살"],"caption":"The image shows a young boy standing in front of a large bed of red tulips. He is wearing a plaid shirt, green pants, and colorful shoes. He has a backpack slung over his shoulder and is smiling at the camera. The tulips are in full bloom and are arranged in a neat and orderly manner. The background shows a park with trees and a bench. The sky is blue and the weather appears to be sunny and pleasant.","hash":"847e98248635068b8ec312115bfb320d91d10b0459ce152b97d07bbc142752ba","age":5,"gender":"남성","face_bbox":[1959,817,2288,1085],"emotion":"neutral"},"order_value":20260401},{"id":"8511e86f-d6a9-5e07-a714-b0df161ebec2","version":0,"score":1.0,"payload":{"filepath":"/app/data/organized/2026/2026-04/2026-04_07.jpeg","filename":"2026-04_07.jpeg","original_context":"2026-04","face_count":1,"people":["지우"],"date":"2026-04","sort_date":20260401,"location":"대한민국 경기도 하남시 학암동","season":"봄","time_of_day":"아침","objects":["footwear","human face","5세","5살"],"caption":"The image shows a young boy standing on a tree branch in a park. He is wearing a black jacket, black pants, and colorful shoes. He has a yellow backpack on his back and is holding an umbrella in his hand. The boy is looking up at the camera with a big smile on his face. In the background, there are tall buildings and trees. The ground is covered in grass and there is a dirt path leading up to the tree.<pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad><pad>","hash":"fee1a77a0e7dbe8588c12c4b72a773f0e70ddc486ab0afdf8a3b8f825a37a26b","age":5,"gender":"남성","face_bbox":[1459,1059,1795,1314],"emotion":"neutral","geo_point":{"lat":37.475241,"lon":127.152457}},"order_value":20260401}]},"status":"ok","time":0.000792404}```

## 9c. Today's 2026/2026-04/ folder contents
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures\2026\2026-04 ���͸�

2026-04-17  ���� 04:38             6,648 2026-04_10_jpeg.webp
2026-04-17  ���� 04:38    <DIR>          .
2026-04-17  ���� 04:38         1,363,282 2026-04_10.jpeg
2026-04-16  ���� 08:57            20,334 2026-04_09_jpeg.webp
2026-04-16  ���� 08:57         6,421,448 2026-04_09.jpeg
2026-04-14  ���� 08:50         7,574,853 2026-04_07.jpeg
2026-04-14  ���� 10:17             4,794 2026-04_08_jpeg.webp
2026-04-14  ���� 10:17            21,836 2026-04_07_jpeg.webp
2026-04-14  ���� 10:17         3,478,120 2026-04_08.jpeg
2026-04-12  ���� 05:15    <DIR>          ..
2026-04-12  ���� 05:04            13,412 2026-04_06_jpeg.webp
2026-04-12  ���� 05:04            19,776 2026-04_05_jpeg.webp
2026-04-12  ���� 05:04            19,744 2026-04_04_jpeg.webp
2026-04-12  ���� 05:04            19,902 2026-04_03_jpeg.webp
2026-04-12  ���� 05:04        12,240,529 2026-04_03.jpeg
2026-04-12  ���� 05:04        12,280,571 2026-04_05.jpeg
2026-04-12  ���� 05:04        12,232,835 2026-04_04.jpeg
2026-04-12  ���� 05:04         8,717,634 2026-04_06.jpeg
2026-04-04  ���� 07:32             7,892 2026-04_02_jpeg.webp
2026-04-04  ���� 07:32             9,692 2026-04_01_jpeg.webp
2026-04-04  ���� 07:32         3,995,426 2026-04_01.jpeg
2026-04-04  ���� 07:31         3,894,227 2026-04_02.jpeg
              20�� ����          72,342,955 ����Ʈ
               2�� ���͸�  427,846,246,400 ����Ʈ ����
```

## 9d. UnknownDate/ folder contents (recent)
```
 D ����̺��� ����: Guma3D
 ���� �Ϸ� ��ȣ: 94C1-E58D

 D:\Pictures\UnknownDate ���͸�

2026-04-15  ���� 12:42    <DIR>          .
2026-04-15  ���� 12:42           258,231 Unknown-Year_01.jpeg
2026-04-15  ���� 12:42           412,358 Unknown-Year_02.jpeg
2026-04-14  ���� 08:16            20,248 Unknown-Year_02_jpeg.webp
2026-04-14  ���� 08:16            12,308 Unknown-Year_01_jpeg.webp
2026-04-12  ���� 05:15    <DIR>          ..
2026-04-05  ���� 11:07           223,630 UnknownDate_0164.jpg
2026-04-05  ���� 07:35           762,890 UnknownDate_0049.jpg
2026-04-05  ���� 07:12           111,717 UnknownDate_0090.jpg
2026-04-05  ���� 07:12           120,849 UnknownDate_0186.jpg
```

## 9e. Timeline cache — first photo entry (what the home page actually shows at top)
```
{
  "id": "96078aa0-daf4-5867-9937-fe643d944ac1",
  "url": "/photos/UnknownDate/Unknown-Year_02.jpeg",
  "original_path": "/app/data/organized/UnknownDate/Unknown-Year_02.jpeg",
  "date": "2026-04",
  "location": "대한민국 경기도 하남시 학암동",
  "people": [
    "준우"
  ],
  "caption": "The image shows a young boy standing in front of a bush with white flowers. He is wearing a white t-shirt with the word \"Essential\" written on it and a blue lanyard around his neck. He has a black headband with small white flowers on it. The boy is making a peace sign with his right hand and is smiling at the camera. The background appears to be a garden or park with a stone wall and a fence.",
  "season": "봄",
  "time_of_day": "낮"
}
```

