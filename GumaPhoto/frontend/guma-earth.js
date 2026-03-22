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

            // 1. Premium Satellite Base Map (Esri World Imagery - Free, Public Server)
            // For modern Cesium (1.104+), fromUrl (async) is mandatory for ArcGIS providers to fetch JSON metadata securely.
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
                    // Force billboards to clamp to ground so they don't float or sink oddly
                    for (let i = 0; i < entities.length; i++) {
                        const evt = entities[i];
                        if (evt.billboard) {
                            evt.billboard.heightReference = Cesium.HeightReference.CLAMP_TO_GROUND;
                        }
                    }
                    viewer.dataSources.add(ds);
                    console.log(`[GumaEarth] Successfully loaded ${entities.length} GeoJSON markers!`);
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
