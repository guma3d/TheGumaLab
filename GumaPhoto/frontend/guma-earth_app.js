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
                requestRenderMode: true,            // Save battery: only render on interact
                maximumRenderTimeChange: Infinity,
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
                        ds.clustering.minimumClusterSize = 3;

                        // Create Canvas Caching Dictionary for gorgeous 3D dynamic cluster orbs
                        const clusterImageCache = {};

                        ds.clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
                            const count = clusteredEntities.length;
                            
                            // Cesium의 내부 클러스터 처리 엔진(EntityCluster)은 오직 Billboard, Label, Point 세 가지만 지원하며 
                            // Ellipse나 Ellipsoid 같은 3D 입체 도형은 성능 문제로 자체 렌더링을 완전히 무시(패스)해버립니다.
                            // 따라서 Canvas API를 활용하여 완벽한 '입체 3D 구슬' 홀로그램을 그려 Billboard에 매핑합니다.
                            
                            cluster.billboard.show = true;
                            cluster.label.show = false; // 글자는 구슬 위에 직접 캔버스로 박음

                            let clusterSize = count < 50 ? 50 : count < 500 ? 64 : 80;
                            const identifier = count + '_' + clusterSize + '_3DOrb';
                            
                            if (!clusterImageCache[identifier]) {
                                const canvas = document.createElement('canvas');
                                canvas.width = clusterSize;
                                canvas.height = clusterSize;
                                const ctx = canvas.getContext('2d');
                                const center = clusterSize / 2;
                                
                                // 1. 중심 0% ~ 20%는 완전 불투명(1.0)한 코어를 갖고, 20% ~ 100%(가장자리)는 서서히 투명(0.0)해지며 퍼져나가는 후광(Aura) 그라데이션
                                const radius = center - 4; // Margin
                                const gradient = ctx.createRadialGradient(
                                    center, center, 0, 
                                    center, center, radius
                                );
                                
                                const rgb = '244, 63, 94'; // Rose Theme
                                gradient.addColorStop(0, `rgba(${rgb}, 1.0)`);    // 중심~20% 완전 불투명 (Solid Core)
                                gradient.addColorStop(0.2, `rgba(${rgb}, 1.0)`);
                                gradient.addColorStop(1, `rgba(${rgb}, 0.0)`);    // 20% 지점에서 가장자리로 갈수록 부드럽게 완전 투명으로 페이드 아웃
                                
                                ctx.beginPath();
                                ctx.arc(center, center, radius, 0, Math.PI * 2);
                                ctx.fillStyle = gradient;
                                ctx.fill();
                                
                                // 2. 선명한 텍스트 (반구 트릭 롤백: 다시 정중앙으로 배치)
                                ctx.font = 'bold ' + (count < 100 ? 14 : 16) + 'px Helvetica, Arial, sans-serif';
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                
                                const txt = count > 9999 ? '9.9k' : count.toString();
                                ctx.fillStyle = 'white';
                                ctx.fillText(txt, center, center + 1);

                                clusterImageCache[identifier] = canvas.toDataURL();
                            }
                            
                            cluster.billboard.image = clusterImageCache[identifier];
                            // 핵심 롤백: 돔(Dome) 트릭을 해제하고 다시 'BOTTOM' 속성으로 핀처럼 지면에 서게 만듦
                            cluster.billboard.verticalOrigin = Cesium.VerticalOrigin.BOTTOM; 
                            cluster.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                        });
                        
                        const entities = ds.entities.values;
                        for (let i = 0; i < entities.length; i++) {
                            const evt = entities[i];
                            if (evt.billboard) {
                                // Anchor pins to ground
                                evt.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                            }
                        }

                        viewer.dataSources.add(ds);
                        console.log(`[GumaEarth] Successfully loaded ${entities.length} dynamic GPS markers! Clustering Enabled.`);
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
