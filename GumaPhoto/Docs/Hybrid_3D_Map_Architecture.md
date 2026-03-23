# 🗺️ 아키텍처 명세서: 하이브리드 3D 사진 지도 파이프라인 (GumaPhoto 연동 확장팩)

## 1. 프로젝트 개요
기존 GumaPhoto의 텍스트/유사도 기반 검색 아키텍처를 물리적 공간 메타데이터 뷰로 확장하는 차세대 사이드 프로젝트입니다.
사용자의 로컬 홈서버 환경에 보유된 대규모 개인 사진 메타데이터(GPS)를 정밀하게 추출하여, **비용 제로(Zero-cost) 기반의 초고해상도 인터랙티브 3D 지구본 환경**(`home.guma3d.com` 내 지도 섹션)에 시각화합니다.

---

## 2. 하이브리드 기술 스택 (Tech Stack)

### **Frontend (Web 3D & UI)**
* **엔진:** `CesiumJS` (Apache 2.0 Open Source) - WGS84 좌표계 및 정밀한 3D 지구본 렌더링.
* **언어 & 프레임워크:** 기존 GumaPhoto 스택과 100% 호환되는 `HTML5`, `CSS3`, `Vanilla JS`.

### **Backend & Infrastructure (기존 자원 100% 활용)**
* **서버 자원:** 기존 GumaPhoto `Docker Compose` 생태계 재활용 (독립적인 신규 DB 및 복잡한 컨테이너 추가 최소화).
* **데이터베이스:** 무거운 `PostGIS` 대신 기존 백엔드(FastAPI)에서 프론트엔드 캐싱용 **초경량 GeoJSON API** 엔드포인트를 구축 및 Qdrant Payload 응용.
* **데이터 프로세싱 엔진:** 기존 `Celery Worker(Python)` 인덱싱 파이프라인 무임승차. 기존 날짜(Date) 추출 스크립트 실행 시 GPS 추출(DMS -> WGS84) 모듈만 10줄 추가하여 비용과 성능 병목 제로화.

### **Map Data Sources (하이브리드 비용 최적화 도메인)**
* **대한민국 지역 (고정밀 특화):** `VWorld` Open API (무료 3D 건물 및 0.5m급 초정밀 위성 사진 레이어링).
* **해외 글로벌 지역 (베이스 타일):** `Google Photorealistic 3D Tiles` (무료 할당량 쿼터 내 활용) 또는 `OpenStreetMap (OSM)`.
* **지형 고도 (DEM):** `Cesium World Terrain`.

---

## 3. 구현 로드맵 (액션 아이템 기반 페이즈)

### **✅ Phase 1: 인프라 연동 및 3D 엔진 부트스트래핑 (완료)**
1. **정적 파일 서빙 최적화:** 지도 파이프라인만을 위한 무거운 Nginx 컨테이너 신설 대안으로, 현재 동작 중인 FastAPI GumaPhoto App 라우터 내부에 `/map` 엔드포인트를 열고 CesiumJS 에셋을 정적으로(Static) 서빙. (완료)
2. **로컬 베이스 지구본 렌더링:** 홈 서버 클라이언트 망에서 빈 CesiumJS 3D 지구와 컨트롤 UI를 렌더링하여 기본 카메라 조작 테스트. (완료)
3. **외부망 라우팅 검증:** 기존 Cloudflared/Nginx 아키텍처를 통해 `home.guma3d.com/map` 접속 무결성 테스트. (완료)

### **✅ Phase 2: 백그라운드 GPS 추출 파이프라인 (Data Pipeline) (완료)**
1. **Python GPS 추출 툴 통합:** 기존 `Florence-2` 및 날짜 전처리(Preprocess)가 돌아가는 워커 스레드 내부에, Pillow/ExifRead를 이용한 EXIF 위도(Lat)/경도(Lon) 패치 로직 병합. (완료)
2. **DMS to WGS84 표준화:** 사진의 원시 도분초(DMS) 포맷을 십진법(Decimal Degrees) 기반 `WGS84` 공간정보로 변환. (완료)
3. **GeoJSON 스키마 적재:** 렌더링 퍼포먼스 극대화를 위해 프론트엔드가 한 번에 Parse 가능한 초경량 GeoJSON 규격을 백엔드에 캐싱(혹은 파일덤프)하여 오버헤드 최소화. (완료)

### **Phase 3: 하이브리드 공간 레이어링 (Map Layering)**
1. **VWorld 베이스 적용:** CesiumJS의 `ImageryProvider` 인스턴스를 올려 대한민국 지형 구간에 브이월드 타일 맵을 덮어씌움.
2. **바운딩 박스(Bbox) 라우팅 로직:** 사진 좌표가 대한민국 바운딩 박스(예: Lat 33~39, Lon 124~130) 내부일 경우 VWorld 로드, 해외일 경우 구글 3D 타일 파이프라인으로 동적으로 갈아타는 스위칭 구현.
3. **엔티티(Marker) 랜더링:** `Cesium.Cartesian3.fromDegrees` 수학 함수를 통해 3D 지구 표면 정확한 지점에 대량의 썸네일 핀(Pin) 생성.

### **Phase 3-1: 동적 클러스터링 및 시각화 (Dynamic Clustering & Visuals)**
수많은 사진 마커를 렌더링할 때 발생하는 성능 저하를 방지하고, 지역별 데이터 밀도를 시각적으로 아름답게 표현하기 위해 CesiumJS 네이티브 클러스트링(CustomDataSource) 기능을 커스터마이징합니다. 카메라 거리에 따라 동적으로 이합집산되는 방사형 글로우(Neon Glow) 원형 텍스처를 지표면에 스냅하여 투영합니다.

- **VRAM 누수 방지 최적화:** 초당 수십 번 호출되는 `clusterEvent` 특성상 캔버스를 무한 생성하지 않고 딕셔너리(`clusterTextureCache`)를 통한 이미지 재사용(Caching) 로직 필수.
- **다이내믹 테크니컬 아트:** 단순 단색이 아닌 HTML5 Canvas의 `createRadialGradient`를 활용하여 데이터 수량 구간(`10+`, `50+`)에 따라 파란색, 오렌지색, 붉은색 트랜지션 및 반투명(Alpha) 스무딩 적용.

```javascript
// [최적화] 캔버스 텍스처 재사용 캐시 딕셔너리
const clusterTextureCache = {};

// [TA] 방사형 그라데이션 커스텀 네온 글로우 텍스처
function getOrCreateClusterTexture(count, color) {
    const cacheKey = `${count}_${color.toCssColorString()}`;
    if (clusterTextureCache[cacheKey]) return clusterTextureCache[cacheKey];

    const canvas = document.createElement('canvas');
    canvas.width = 64; canvas.height = 64;
    const ctx = canvas.getContext('2d');

    const gradient = ctx.createRadialGradient(32, 32, 10, 32, 32, 32);
    gradient.addColorStop(0.0, color.withAlpha(1.0).toCssColorString()); // 코어
    gradient.addColorStop(0.6, color.withAlpha(0.6).toCssColorString()); // 중간 블렌딩
    gradient.addColorStop(1.0, color.withAlpha(0.0).toCssColorString()); // 외곽 투명 스무딩

    ctx.fillStyle = gradient;
    ctx.beginPath(); ctx.arc(32, 32, 32, 0, Math.PI * 2); ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 18px "Inter", sans-serif'; 
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(count.toString(), 32, 32);

    clusterTextureCache[cacheKey] = canvas;
    return canvas;
}

// -------------------------------------------------------------
// 1. 데이터 소스 생성 및 클러스터 속성 설정
const photoDataSource = new Cesium.CustomDataSource('photos');
photoDataSource.clustering.enabled = true;
photoDataSource.clustering.pixelRange = 60; 
photoDataSource.clustering.minimumClusterSize = 2; 

// [TA 업그레이드] Cesium 엔진 렌더링 한계 돌파: 평행우주 프로젝션 매핑
// Cesium 자체 클러스터링 코어는 빌보드(2D)만 렌더링하므로, 지형/곡면에 밀착되는 진정한 3D 투사(Ellipse)를 위해 
// 클러스터링을 감독하는 별도의 CustomDataSource를 운영합니다.
let customClusterSource = new Cesium.CustomDataSource('customClusters');
viewer.dataSources.add(customClusterSource);

let seenClusterIds = new Set();
let cleanupTimer = null;

photoDataSource.clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
    const photoCount = clusteredEntities.length;

    // 허공에 뜨는 기존 2D 빌보드 코어를 숨김 처리
    cluster.label.show = false;
    cluster.billboard.show = false;

    // 수량에 따른 반경(미터 스케일) 개편 및 Lerp 컬러 동기화
    const visualScale = 0.8 + (Math.log(photoCount) * 0.25);
    const finalRadius = 40000 * visualScale;
    let clusterColor = new Cesium.Color(); /* Lerp 계산 생략 */

    // 클러스터 아이디와 동기화되는 Native WGS84 커브 3D 타원체 렌더링 생성
    let syncEntity = customClusterSource.entities.getById(cluster.id);
    if (!syncEntity) {
        customClusterSource.entities.add({
            id: cluster.id,
            position: cluster.position,
            ellipse: {
                semiMajorAxis: finalRadius,
                semiMinorAxis: finalRadius,
                material: new Cesium.ImageMaterialProperty({
                    image: getOrCreateClusterTexture(clusterColor),
                    transparent: true
                }),
                height: 0 // 지표면(Ellipsoid)에 평면으로 완벽히 밀착해 자연스러운 굴곡 형성
            }
        });
    }

    seenClusterIds.add(cluster.id);

    // 50ms 후 생존하지 못한 클러스터들을 수거 (Garbage Cleanup)
    clearTimeout(cleanupTimer);
    cleanupTimer = setTimeout(() => {
        /* 삭제 로직 */
        seenClusterIds.clear();
    }, 50);
});

viewer.dataSources.add(photoDataSource);
```

### **Phase 4: 비주얼 폴리싱 & 테크니컬 아트 (UX/TA Touch)**
1. **스마트 고도 락온(Altitude Snapping):** 사진 메타데이터 내의 오차율 높은 Z축(고도) 값을 무시하고, `sampleTerrainMostDetailed` API를 호출해 지구 표면(산/지형 위)에 마커를 즉시 물리적으로 안착시키는 정밀화 작업.
2. **레이어 블렌딩 이슈 해결:** VWorld 로컬 지형과 글로벌 베이스 지도의 경계선에서 생기는 단층 이질감을 Alpha Blending(투명도 컷오프) 기법과 마스킹으로 깎아냄.
3. **포스트 프로세스 (Color Correction):** `Scene.highDynamicRange` 활성화 및 간단한 쉐이딩을 통해 타일 소스 간의 톤(Tone) 차이 일체화 (상용 프리미엄 앱 수준의 아트 터치).
4. **인터랙션 및 트랜지션:** 맵 핀 클릭 시 `FlyTo` 카메라 줌인 애니메이션을 부드럽게 재생시키며, 커스텀 디자인된(GumaPhoto UI 테마 통일) 팝업 창에 클러스터링 기반 고화질 썸네일 로딩 로직 완성.
