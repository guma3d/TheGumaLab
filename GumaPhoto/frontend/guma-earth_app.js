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
            
            // [수정] WebGL 셰이더 조절 기능을 원복하여 CartoDB 본연의 깔끔하고 얇은 글씨체를 살립니다.
            // (강제 조정 시 픽셀들의 검은 테두리가 과도하게 뻥튀기되어 '두꺼운 아웃라인'으로 안 예쁘게 보임)
            textLayer.brightness = 1.0; 
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

                        // Create Canvas Caching Dictionary for gorgeous dynamic cluster icons
                        const clusterImageCache = {};

                        ds.clustering.clusterEvent.addEventListener(function(clusteredEntities, cluster) {
                            // Turn off default text label and billboard
                            cluster.label.show = false;
                            cluster.billboard.show = false; // We are completely abandoning Camera-Facing Billboards!
                            
                            const count = clusteredEntities.length;
                            
                            // Scale the bubble slowly as count grows (Using high-res Canvas for sharp projection)
                            let clusterSize = count < 50 ? 64 : count < 500 ? 80 : 96; 
                            const identifier = count + '_' + clusterSize + '_decal';
                            
                            if (!clusterImageCache[identifier]) {
                                const canvas = document.createElement('canvas');
                                canvas.width = clusterSize;
                                canvas.height = clusterSize;
                                const ctx = canvas.getContext('2d');
                                const center = clusterSize / 2;
                                
                                // 1. Outer Soft Glow Ring (Glassmorphism inspired, blending on terrain)
                                ctx.beginPath();
                                ctx.arc(center, center, center - 2, 0, Math.PI * 2);
                                ctx.fillStyle = 'rgba(244, 63, 94, 0.4)'; // Primary theme color transparent
                                ctx.fill();
                                
                                // 2. Inner Solid Core
                                ctx.beginPath();
                                ctx.arc(center, center, center - 12, 0, Math.PI * 2);
                                ctx.fillStyle = 'rgba(244, 63, 94, 0.85)'; // Slightly transparent to let terrain show
                                ctx.fill();
                                
                                // 3. Crisp Text with Outline
                                ctx.font = 'bold ' + (count < 100 ? 20 : 18) + 'px sans-serif';
                                ctx.textAlign = 'center';
                                ctx.textBaseline = 'middle';
                                
                                const txt = count > 9999 ? '9.9k' : count.toString();
                                ctx.fillStyle = 'white';
                                ctx.fillText(txt, center, center + 1);

                                clusterImageCache[identifier] = canvas.toDataURL();
                            }
                            
                            // 4. Transform into a 3D Decal (Ellipse Graphics)
                            // We use a CallbackProperty so the physical size on the globe shrinks/grows as the camera zooms, 
                            // ensuring the decal remains approximately the same visual size on the screen.
                            const dynamicRadius = new Cesium.CallbackProperty(function(time, result) {
                                if (!cluster.position) return 50000.0;
                                const pos = cluster.position.getValue(time);
                                if (!pos) return 50000.0;
                                
                                const dist = Cesium.Cartesian3.distance(viewer.camera.positionWC, pos);
                                // Multiplier controls how much ground the decal covers relative to camera distance
                                const multiplier = count < 50 ? 0.03 : count < 500 ? 0.04 : 0.05;
                                return dist * multiplier;
                            }, false);

                            cluster.ellipse = new Cesium.EllipseGraphics({
                                semiMajorAxis: dynamicRadius,
                                semiMinorAxis: dynamicRadius,
                                material: new Cesium.ImageMaterialProperty({
                                    image: clusterImageCache[identifier],
                                    transparent: true
                                }),
                                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND // Project onto terrain/globe
                            });
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
