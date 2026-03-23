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
            
            // Visual Styling: Cinematic Space Environment
            viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#020408'); // Deep space blue/black
            
            // Remove any auto-loaded ION components if they somehow snuck in
            viewer.scene.imageryLayers.removeAll();

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

            // 2. High-Resolution Text Overlay Layer (CartoDB Dark Matter - Only Labels @2x Retina)
            // Appending '@2x.png' retrieves massive 512x512 tiles, completely eliminating blurriness when scaled/zoomed in.
            const labelProvider = new Cesium.UrlTemplateImageryProvider({
                url: 'https://{s}.basemaps.cartocdn.com/dark_only_labels/{z}/{x}/{y}@2x.png',
                subdomains: ['a', 'b', 'c', 'd'],
                maximumLevel: 19
            });
            const textLayer = viewer.imageryLayers.addImageryProvider(labelProvider);
            
            // 🔥 Force Text Color to Pure White via WebGL Shader Overrides
            textLayer.brightness = 3.5; // Blows out the standard light-grey CartoDB typography into pure white.
            textLayer.contrast = 1.5;   // sharpens the text halo edges against the dark background.

            // 🌟 Advanced Rendering & Atmosphere Effects
            viewer.scene.highDynamicRange = true; // HDR tone mapping
            viewer.scene.postProcessStages.fxaa.enabled = true; // Smooth edge anti-aliasing (High Quality)
            viewer.scene.globe.enableLighting = false; // Disable stark sun shadows for a clean UI map look
            viewer.scene.globe.depthTestAgainstTerrain = false; // Prevent markers from being hidden behind terrain

            
            // Tweaking the Earth's glowing halo (Atmosphere) to have a subtle Emerald/Blue tint
            if (viewer.scene.skyAtmosphere) {
                viewer.scene.skyAtmosphere.hueShift = -0.15; // Shift towards cyan/emerald
                viewer.scene.skyAtmosphere.saturationShift = 0.5; // Make the halo punchy
                viewer.scene.skyAtmosphere.brightnessShift = 0.2;
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
            
            // --- NEW: Load GeoJSON Markers ---
            try {
                const geoJsonUrl = window.location.pathname.startsWith('/GumaPhoto') ? '/GumaPhoto/frontend/photos_map.geojson' : '/frontend/photos_map.geojson';
                const response = await fetch(geoJsonUrl);
                if (response.ok) {
                    const params = {
                        markerSize: 28,
                        markerColor: Cesium.Color.fromCssColorString('#f43f5e'), // Red-pink marker
                        markerSymbol: 'camera'
                    };
                    const data = await response.json();
                    const ds = await Cesium.GeoJsonDataSource.load(data, params);
                    
                    const entities = ds.entities.values;
                    for (let i = 0; i < entities.length; i++) {
                        const evt = entities[i];
                        if (evt.billboard) {
                            evt.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                        }
                    }

                    // --- NEW: Dynamic Clustering & Radial Glow Textures ---
                    ds.clustering.enabled = true;
                    ds.clustering.pixelRange = 60;
                    ds.clustering.minimumClusterSize = 2;

                    const clusterTextureCache = {};

                    function getOrCreateClusterTexture(color) {
                        const cacheKey = color.toCssColorString();
                        if (clusterTextureCache[cacheKey]) return clusterTextureCache[cacheKey];

                        const canvas = document.createElement('canvas');
                        canvas.width = 64; 
                        canvas.height = 64;
                        const ctx = canvas.getContext('2d');

                        const gradient = ctx.createRadialGradient(32, 32, 10, 32, 32, 32);
                        gradient.addColorStop(0.0, color.withAlpha(0.9).toCssColorString()); // 코어
                        gradient.addColorStop(0.5, color.withAlpha(0.5).toCssColorString()); // 중간 블렌딩
                        gradient.addColorStop(1.0, color.withAlpha(0.0).toCssColorString()); // 외곽 투명 스무딩

                        ctx.fillStyle = gradient;
                        ctx.beginPath(); 
                        ctx.arc(32, 32, 32, 0, Math.PI * 2); 
                        ctx.fill();

                        clusterTextureCache[cacheKey] = canvas;
                        return canvas;
                    }

                    const minColor = Cesium.Color.fromCssColorString('#0ea5e9'); // 파랑
                    const midColor = Cesium.Color.fromCssColorString('#10b981'); // 초록
                    const maxColor = Cesium.Color.fromCssColorString('#f43f5e'); // 빨강

                    ds.clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
                        const photoCount = clusteredEntities.length;

                        // 1️⃣ 기본 라벨과 빌보드를 끄고 Ellipse로 대체 (지구 곡면 밀착 3D 클러스터)
                        cluster.label.show = false;
                        cluster.billboard.show = false;

                        // 수량에 따른 스케일 크기 증가율 시각화 조정
                        const visualScale = 0.8 + (Math.log(photoCount) * 0.25);

                        // 부드러운 색상 전환 (Lerp: 2~100장 기준)
                        const ratio = Math.max(0, Math.min((photoCount - 2) / 98, 1.0));
                        let clusterColor = new Cesium.Color();
                        if (ratio < 0.5) {
                            Cesium.Color.lerp(minColor, midColor, ratio * 2.0, clusterColor);
                        } else {
                            Cesium.Color.lerp(midColor, maxColor, (ratio - 0.5) * 2.0, clusterColor);
                        }
                        
                        // 2️⃣ 픽셀(Pixel) 스케일 대신 실제 지구상의 미터(Meter) 반경 설정
                        const baseRadiusMeters = 50000; 
                        const finalRadius = baseRadiusMeters * visualScale;

                        // 3️⃣ 지구 곡률에 착 달라붙는 타원(Ellipse) 기하학 생성
                        cluster.ellipse = new Cesium.EllipseGraphics({
                            semiMajorAxis: finalRadius,
                            semiMinorAxis: finalRadius,
                            // 직접 만든 캔버스 텍스처를 머티리얼로 매핑
                            material: new Cesium.ImageMaterialProperty({
                                image: getOrCreateClusterTexture(clusterColor),
                                transparent: true
                            }),
                            // 핵심: 지형(산, 계곡)에 완전히 밀착시킴
                            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND 
                        });
                    });

                    viewer.dataSources.add(ds);
                    console.log(`[GumaEarth] Successfully loaded ${entities.length} GeoJSON clustered markers!`);
                } else {
                    console.warn(`[GumaEarth] Map markers not found at ${geoJsonUrl} yet.`);
                }
            } catch(e) {
                console.error("[GumaEarth] Error loading GeoJSON map markers:", e);
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
