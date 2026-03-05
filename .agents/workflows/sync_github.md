---
description: 깃허브 동기화 및 푸시 워크플로우 (Sync and Push)
---

사용자가 코드 작업을 마치고 동기화, 백업, 혹은 깃허브 업로드를 요청할 때 실행할 자동화 워크플로우입니다. 변경 사항을 모두 처리하고 리포지토리에 푸시합니다.

// turbo-all

### 1단계: 모든 변경사항을 Staging Area에 추가
```powershell
git add .
```

### 2단계: 커밋 (Commit)
수정 내역에 대한 메시지와 함께 커밋을 진행합니다. (사용자가 별도의 메시지를 요청하지 않았다면, 기본 메시지로 처리합니다.)
```powershell
git commit -m "Auto-sync update from Antigravity"
```

### 3단계: 깃허브 리포지토리로 푸시 (Push)
저장소 서버(원격)의 메인 브랜치에 변경 사항을 최종적으로 업로드합니다.
```powershell
git push origin main
```

---

*(참고 사항)*
만약 사용자가 **홈서버와 랩탑(Gram) 간의 다운로드(동기화)**를 먼저 진행해 달라고 요청한 경우에는, 위 깃허브 작업을 하기 전에 폴더를 먼저 덮어쓰기 형태로 백업해옵니다.
```powershell
scp -r HomeServer:"D:/TheGumaLab/*" "C:\Users\guma3d\Documents\TheGumaLab\"
```
