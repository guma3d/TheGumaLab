/**
 * GumaEarth Core Module
 * Initializes and controls the CesiumJS 3D interactive globe.
 */

const GumaEarth = (function() {
    let viewer = null;

    async function init() {
        if (viewer) return;

        console.log("[GumaEarth] Bootstrapping WebGL 3D Map Module...");
        
        try {
            // Instantiate the Cesium Engine on the DOM node
            viewer = new Cesium.Viewer('cesiumContainer', {
                animation: false,
                baseLayerPicker: false,
                fullscreenButton: false,
                vrButton: false,
                geocoder: false,
                homeButton: false,
                infoBox: false,
                sceneModePicker: false,
                selectionIndicator: false,
                timeline: false,
                navigationHelpButton: false,
                scene3DOnly: true,                  // Disable 2D/Columbus view
                requestRenderMode: false,           // [중요: 절전모드 해제] 클러스터링 연산이 화면 가장자리/밖에서 지연되어 렌더링이 튀는 현상(Popping)을 막기 위해 60fps 상시 렌더링 체제로 전환
                // maximumRenderTimeChange 속성 비활성화 (requestRenderMode가 false이므로 불필요)
                baseLayer: false                    // Prevent default Bing Maps (No Token error)
            });
            
            // Visual Styling: Cinematic Space Environment (Three.js Style)
            viewer.scene.backgroundColor = Cesium.Color.BLACK; 
            viewer.scene.globe.baseColor = Cesium.Color.BLACK;
            
            // Remove any auto-loaded ION components if they somehow snuck in
            viewer.scene.imageryLayers.removeAll();

            // 🎯 초고해상도 렌더링 강제 (Retina/4K 대응 및 스트리밍 해상도 향상)
            viewer.useBrowserRecommendedResolution = false;       // 브라우저의 프레임 우선 강제 다운스케일링 제어 해제 (1:1 네이티브 해상도 복원)
            viewer.scene.globe.maximumScreenSpaceError = 1.5;     // 기본값(2.0). 수치를 낮출수록 픽셀 왜곡을 허용하지 않고 즉시 고해상도 타일을 강제 스트리밍 (선명도 극대화)
            
            // 🎯 비동기 스트리밍 범위 전면 확장 (모바일 화면 가장자리 지연 로드 방지)
            viewer.scene.globe.preloadAncestors = true;
            viewer.scene.globe.preloadSiblings = true; // 현재 시야(중앙) 뿐만 아니라 주변 프러스텀 밖의 텍스쳐 타일들까지 과감히 미리 당겨서 로딩(Preload)


            // 1. Global Base Map (Esri World Imagery)
            const esriProvider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
                'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer', {
                enablePickFeatures: false
            });
            const baseLayer = viewer.imageryLayers.addImageryProvider(esriProvider);
            // Dim and saturated the satellite imagery slightly to look cinematic and preserve the Dark App Theme
            baseLayer.brightness = 0.75; 
            baseLayer.gamma = 0.8;
            baseLayer.saturation = 1.3;

            // 2. High-Resolution Text Overlay Layer (Esri Reference - World Boundaries and Places)
            // 기존 CartoDB 타일보다 훨씬 고해상도의 압도적으로 깔끔하고 정교한 공식 위성 지도 라벨(글자/국경선)입니다.
            const labelProvider = await Cesium.ArcGisMapServerImageryProvider.fromUrl(
                'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer', {
                enablePickFeatures: false
            });
            const textLayer = viewer.imageryLayers.addImageryProvider(labelProvider);
            
            // Bloom(글로우) 임계점에 하얀색 텍스트가 걸려 번쩍이는 현상(빛 번짐)을 우회 방지하기 위해, 
            // 텍스트 레이어의 자체 밝기(Brightness)를 0.95로 살짝 억눌러 Bloom 타겟에서 회피 처리.
            textLayer.brightness = 0.95; 
            textLayer.contrast = 1.0;

            // 🌟 Advanced Rendering & Atmosphere Effects (Three.js Style)
            viewer.scene.highDynamicRange = true; // HDR tone mapping
            viewer.scene.postProcessStages.fxaa.enabled = true; // Smooth edge anti-aliasing (High Quality)
            
            try {
                // Add Bloom for that thick atmospheric light bleed effect
                viewer.scene.postProcessStages.bloom.enabled = true;
                if (viewer.scene.postProcessStages.bloom.uniforms) {
                    viewer.scene.postProcessStages.bloom.uniforms.contrast = 110;
                    viewer.scene.postProcessStages.bloom.uniforms.brightness = -0.1;
                    viewer.scene.postProcessStages.bloom.uniforms.delta = 1.5;   // Increases the width of the glow
                    viewer.scene.postProcessStages.bloom.uniforms.sigma = 3.0;   // Higher blur radius
                    viewer.scene.postProcessStages.bloom.uniforms.stepSize = 1.5;// Wider steps for huge glow
                }
            } catch (e) {
                console.warn("[GumaEarth] Bloom uniforms not fully supported in this Engine version.", e);
            }

            viewer.scene.globe.enableLighting = true; // Show realistic Day/Night terminator shadow
            viewer.scene.globe.depthTestAgainstTerrain = false; // Prevent markers from being hidden behind terrain
            
            // Tweaking the Earth's glowing halo (Atmosphere) mimicking ThreeJS Fresnel edge glow
            if (viewer.scene.skyAtmosphere) {
                viewer.scene.skyAtmosphere.hueShift = -0.15; // Deeper blue/purple shift without breaking shader
                viewer.scene.skyAtmosphere.saturationShift = 0.8; // Safe saturation
                viewer.scene.skyAtmosphere.brightnessShift = 0.6; // Working brightness level
            }

            // Set initial camera view targeting the Korean peninsula
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(127.5, 36.0, 15000000.0),
                duration: 0 // Instant snap to prevent animation weirdness if hidden
            });
            

            
            // Hide the Cesium OS credit watermark for internal app styling
            const creditContainer = viewer.cesiumWidget.creditContainer;
            if (creditContainer) {
                creditContainer.style.display = 'none';
            }
            
            // Interaction Constraints: Disable Camera Tilt & Look (Focus strictly on top-down globe pan & zoom)
            viewer.scene.screenSpaceCameraController.enableTilt = false; // Disable pitch (two-finger tilt)
            viewer.scene.screenSpaceCameraController.enableLook = false; // Disable arbitrary camera twisting
            
            // Zoom Constraints: Lock outer space boundaries so the earth fits snugly without vanishing
            const MAX_ALTITUDE = 18000000.0; // 18,000km
            viewer.scene.screenSpaceCameraController.maximumZoomDistance = MAX_ALTITUDE; 

            // Set initial camera view targeting the Korean peninsula (At our new Max Zoom bounding)
            viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(127.5, 36.0, MAX_ALTITUDE),
                duration: 0 // Instant snap to prevent animation weirdness if hidden
            });
            
            // --- NEW: Load GeoJSON Markers dynamically from Qdrant ---
            try {
                const geoJsonUrl = '/api/map/geojson';
                const response = await fetch(geoJsonUrl);
                if (response.ok) {
                    const data = await response.json();
                    if (!data.features || data.features.length === 0) {
                        console.warn("[GumaEarth] No GPS locations found in Qdrant yet.");
                    } else {
                        const params = {
                            markerSize: 28,
                            markerColor: Cesium.Color.fromCssColorString('#f43f5e'), // Red-pink marker
                            markerSymbol: 'camera'
                        };
                        const ds = await Cesium.GeoJsonDataSource.load(data, params);
                        
                        // -- 3D Map Clustering Setup --
                        ds.clustering.enabled = true;
                        ds.clustering.pixelRange = 45; // Group markers within 45 pixels
                        ds.clustering.minimumClusterSize = 2; // 최소 2개부터 즉각 클러스터링 적용

                        // Create Canvas Caching Dictionary for gorgeous 3D dynamic cluster orbs
                        const clusterImageCache = {};

                        // 아우라 구슬(Aura Orb) 생성기 - 색상 테마 지원
                        function createAuraOrb(count, theme = 'blue') {
                            let clusterSize = count < 50 ? 50 : count < 500 ? 64 : 80;
                            const identifier = count + '_' + clusterSize + '_' + theme;
                            
                            if (clusterImageCache[identifier]) {
                                return clusterImageCache[identifier];
                            }
                            
                            const canvas = document.createElement('canvas');
                            canvas.width = clusterSize;
                            canvas.height = clusterSize;
                            const ctx = canvas.getContext('2d');
                            const center = clusterSize / 2;
                            
                            // 1. 중심 0% ~ 20%는 완전 불투명(1.0), 20% ~ 100%(가장자리)는 서서히 투명(0.0)해지며 퍼져나가는 후광(Aura) 그라데이션
                            const radius = center - 4; // Margin
                            const gradient = ctx.createRadialGradient(
                                center, center, 0, 
                                center, center, radius
                            );
                            
                            const rgb = theme === 'blue' ? '59, 130, 246' : 
                                       (theme === 'green' ? '34, 197, 94' : '244, 63, 94');

                            gradient.addColorStop(0, `rgba(${rgb}, 1.0)`);    // 중심~20% 완전 불투명 (Solid Core)
                            gradient.addColorStop(0.2, `rgba(${rgb}, 1.0)`);
                            gradient.addColorStop(1, `rgba(${rgb}, 0.0)`);    // 20% 지점에서 가장자리로 서서히 페이드 아웃
                            
                            ctx.beginPath();
                            ctx.arc(center, center, radius, 0, Math.PI * 2);
                            ctx.fillStyle = gradient;
                            ctx.fill();
                            
                            // 2. 선명한 텍스트 (단일 개체인 경우에도 통일성을 위해 캔버스는 구우나, 숫자 1 표기는 생략)
                            if (count > 1) {
                                ctx.font = 'bold ' + (count < 100 ? 14 : 16) + 'px Helvetica, Arial, sans-serif';
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                
                                const txt = count > 9999 ? '9.9k' : count.toString();
                                ctx.fillStyle = 'white';
                                ctx.fillText(txt, center, center + 1);
                            }

                            const dataUrl = canvas.toDataURL();
                            clusterImageCache[identifier] = dataUrl;
                            return dataUrl;
                        }

                        ds.clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
                            cluster.billboard.show = true;
                            cluster.label.show = false; // 글자는 구슬 위에 직접 캔버스로 박음
                            
                            // 클릭 모달 액션을 위해 데이터 임베딩
                            cluster.customData = clusteredEntities;

                            cluster.billboard.image = createAuraOrb(clusteredEntities.length, 'blue');
                            cluster.billboard.verticalOrigin = Cesium.VerticalOrigin.BOTTOM; 
                            cluster.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                        });
                        
                        // 기본 카메라 마커(빨간 핀) 전면 폐기 및 낱개 사진(1장)도 동일한 아우라 구슬로 렌더링 강제 교체
                        const entities = ds.entities.values;
                        const singleOrbBlue = createAuraOrb(1, 'blue'); // 1장짜리 단일 핀 미리 굽기 (텍스트 없음)
                        for (let i = 0; i < entities.length; i++) {
                            const evt = entities[i];
                            if (evt.billboard) {
                                evt.customData = [evt]; // 단일 파일도 동일한 배열 규칙으로 통일
                                evt.billboard.image = singleOrbBlue; // 촌스러운 기본 빨간 핀(Camera) 이미지를 날려버리고 오라 구슬로 덮어쓰기!
                                // 💡 중요: GeoJsonDataSource가 생성한 기존 마커는 markerColor(#f43f5e)의 '빨간색 틴트(Color)'가 Billboard에 먹혀있습니다.
                                // 이 틴트 속성을 White(순정)으로 지워주지 않으면, 캔버스 구슬 이미지 위에 또 빨간 셰이더가 곱해져 클러스터 구슬보다 어둡고 칙칙해 보임.
                                evt.billboard.color = Cesium.Color.WHITE; 
                                evt.billboard.verticalOrigin = Cesium.VerticalOrigin.BOTTOM; 
                                evt.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                            }
                        }

                        viewer.dataSources.add(ds);
                        console.log(`[GumaEarth] Successfully loaded ${entities.length} dynamic GPS markers! Clustering Enabled.`);
                        
                        // 🎯 --- 모달 UI 동적 주입 및 클릭 인터랙션 설계 ---
                        const modalOverlay = document.createElement('div');
                        modalOverlay.id = 'guma-earth-cluster-modal';
                        modalOverlay.style.cssText = `
                            position: absolute; bottom: 80px; left: 50%; transform: translateX(-50%);
                            width: 90%; max-width: 400px;
                            background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(12px);
                            border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px;
                            display: none; flex-direction: column; z-index: 9999;
                            box-shadow: 0 10px 30px rgba(0,0,0,0.5); overflow: hidden;
                        `;
                        
                        const modalHeader = document.createElement('div');
                        modalHeader.style.cssText = "padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: space-between; align-items: center; background: rgba(255, 255, 255, 0.05);";
                        const headerTitle = document.createElement('h3');
                        headerTitle.style.cssText = "margin: 0; font-size: 15px; color: #fff; font-weight: 600;";
                        
                        const closeBtn = document.createElement('button');
                        closeBtn.innerHTML = "✕";
                        closeBtn.style.cssText = "background: none; border: none; color: #fff; font-size: 16px; cursor: pointer; display: flex; align-items: center;";
                        
                        const modalContent = document.createElement('div');
                        modalContent.style.cssText = "display: flex; flex-wrap: wrap; gap: 8px; padding: 16px; overflow-y: auto; max-height: calc(50vh - 50px); justify-content: flex-start;";
                        
                        modalHeader.appendChild(headerTitle);
                        modalHeader.appendChild(closeBtn);
                        modalOverlay.appendChild(modalHeader);
                        modalOverlay.appendChild(modalContent);
                        document.body.appendChild(modalOverlay);
                        
                        let currSelectedEntity = null;
                        let currClusterCount = 0;
                        
                        function clearSelection() {
                            if (currSelectedEntity && currSelectedEntity.billboard) {
                                currSelectedEntity.billboard.image = createAuraOrb(currClusterCount, 'blue');
                                currSelectedEntity = null;
                            }
                            modalOverlay.style.display = 'none';
                            modalContent.innerHTML = '';
                        }
                        
                        closeBtn.onclick = clearSelection;
                        
                        const clickHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
                        clickHandler.setInputAction(function(click) {
                            const picked = viewer.scene.pick(click.position);
                            
                            if (!Cesium.defined(picked) || !picked.id || !picked.id.billboard) {
                                clearSelection();
                                return;
                            }
                            
                            const entity = picked.id;
                            if (!entity.customData) {
                                clearSelection();
                                return;
                            }
                            
                            if (currSelectedEntity !== entity) clearSelection();
                            
                            const photos = entity.customData;
                            currClusterCount = photos.length;
                            currSelectedEntity = entity;
                            
                            // 클릭된 클러스터를 초록색(Green)으로 변경!
                            currSelectedEntity.billboard.image = createAuraOrb(currClusterCount, 'green');
                            
                            headerTitle.innerText = `${currClusterCount} Photos In Area`;
                            modalContent.innerHTML = '';
                            
                            // 1. 역순(시간 최신순) 정렬을 위한 데이터 추출
                            let photoList = photos.map(p => {
                                return {
                                    url: p.properties.url ? p.properties.url.getValue() : '',
                                    date: p.properties.date ? p.properties.date.getValue() : '1970'
                                };
                            });
                            
                            photoList.sort((a,b) => b.date.localeCompare(a.date));
                            
                            // 2. DOM 삽입
                            photoList.forEach(data => {
                                if (data.url) {
                                    const img = document.createElement('img');
                                    img.src = data.url;
                                    img.style.cssText = "width: calc(33.3% - 6px); aspect-ratio: 1/1; object-fit: cover; border-radius: 6px; background: #333; cursor: pointer; opacity: 0; transition: opacity 0.3s ease;";
                                    img.onload = () => { img.style.opacity = 1; };
                                    img.onclick = () => { window.open(data.url, '_blank'); };
                                    modalContent.appendChild(img);
                                }
                            });
                            
                            modalOverlay.style.display = 'flex';
                            
                            // 모바일 클릭 흔들림 방지를 위해 선택된 핀으로 카메라 부드럽게 고정
                            viewer.camera.flyTo({
                                destination: Cesium.Cartesian3.fromDegrees(
                                    Cesium.Math.toDegrees(viewer.camera.positionCartographic.longitude),
                                    Cesium.Math.toDegrees(viewer.camera.positionCartographic.latitude),
                                    viewer.camera.positionCartographic.height
                                ),
                                duration: 0.1
                            });
                            
                        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
                    }
                } else {
                    console.warn(`[GumaEarth] Map markers fetch failed: ${response.status}`);
                }
            } catch(e) {
                console.error("[GumaEarth] Error loading dynamic GeoJSON markers:", e);
            }
            
            console.log("[GumaEarth] WebGL Engine successfully booted!");
            
        } catch (err) {
            console.error("[GumaEarth] Hardware/Engine Boot Failure: ", err);
        }
    }

    function onMapTabOpened() {
        if (!viewer) {
            init();
        } else {
            // Force WebGL Canvas resize calculations when breaking out of 'display: none'
            viewer.resize();
            viewer.scene.requestRender();
        }
    }

    return {
        init: init,
        onMapTabOpened: onMapTabOpened
    };
})();

// Attach interception to the map switch button locally
document.addEventListener('DOMContentLoaded', () => {
    const mapBtn = document.getElementById('nav-map-btn');
    if (mapBtn) {
        mapBtn.addEventListener('click', () => {
            // Delay 50ms allowing DOM layout to trigger out of display: none first
            // This grants WebGL the proper exact canvas sizing rect.
            setTimeout(() => {
                GumaEarth.onMapTabOpened();
            }, 50);
        });
    }
});
