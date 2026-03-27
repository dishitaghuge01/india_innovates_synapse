import React, { useEffect, useRef } from 'react';
import * as Cesium from 'cesium';
import { geocode } from '../services/geocode';

const GlobeView = ({ entities }) => {
    const viewerRef = useRef(null);
    const cesiumViewer = useRef(null);

    useEffect(() => {
        if (!cesiumViewer.current && viewerRef.current) {
            cesiumViewer.current = new Cesium.Viewer(viewerRef.current, {
                animation: false,
                baseLayerPicker: false,
                fullscreenButton: false,
                geocoder: false,
                homeButton: false,
                infoBox: false,
                sceneModePicker: false,
                selectionIndicator: false,
                timeline: false,
                navigationHelpButton: false,
                navigationInstructionsInitiallyVisible: false,
            });

            // Google Photorealistic 3D Tiles
            const loadTiles = async () => {
                try {
                    const tileset = await Cesium.Cesium3DTileset.fromUrl(
                        "https://tile.googleapis.com/v1/3dtiles/root.json?key=YOUR_GOOGLE_TILE_KEY"
                    );
                    cesiumViewer.current.scene.primitives.add(tileset);
                } catch (e) {
                    console.warn("Failed to load 3D tiles (probably missing valid API key):", e);
                }
            };

            loadTiles();
        }

        return () => {
            if (cesiumViewer.current) {
                cesiumViewer.current.destroy();
                cesiumViewer.current = null;
            }
        };
    }, []);

    useEffect(() => {
        if (!cesiumViewer.current || !entities) return;

        const viewer = cesiumViewer.current;
        viewer.entities.removeAll();

        entities.forEach(async (ent) => {
            let lat = ent.lat;
            let lon = ent.lon;

            if (!lat || !lon) {
                const coords = await geocode(ent.name);
                if (coords) {
                    lat = coords.lat;
                    lon = coords.lon;
                }
            }

            if (lat && lon) {
                viewer.entities.add({
                    name: ent.name,
                    position: Cesium.Cartesian3.fromDegrees(lon, lat),
                    point: {
                        pixelSize: 10,
                        color: Cesium.Color.CYAN,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 2,
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    },
                    label: {
                        text: ent.name,
                        font: '14pt monospace',
                        style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                        fillColor: Cesium.Color.CYAN,
                        outlineColor: Cesium.Color.BLACK,
                        outlineWidth: 2,
                        verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                        pixelOffset: new Cesium.Cartesian2(0, -15),
                        disableDepthTestDistance: Number.POSITIVE_INFINITY
                    }
                });
            }
        });
    }, [entities]);

    return <div ref={viewerRef} className="w-screen h-screen absolute top-0 left-0" />;
};

export default GlobeView;