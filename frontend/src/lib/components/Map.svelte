<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import type { BombingIncident } from '$lib/types';
	import type L from 'leaflet';

	let mapContainer: HTMLDivElement;
	let map: L.Map | undefined;
	let markersLayer: L.LayerGroup | undefined;
	let leaflet: typeof L;

	const REGION_CENTER: [number, number] = [30.0, 45.0];
	const DEFAULT_ZOOM = 5;
	let mapReady = $state(false);

	function escapeHtml(str: string): string {
		const div = document.createElement('div');
		div.textContent = str;
		return div.innerHTML;
	}

	function getMarkerClass(killed: number): string {
		return killed >= 30 ? 'bombing-marker-lg' : 'bombing-marker';
	}

	function createPulsingIcon(killed: number): L.DivIcon {
		const cls = getMarkerClass(killed);
		const size = killed >= 30 ? 30 : 20;
		return leaflet.divIcon({
			className: cls,
			html: `
				<div class="ring"></div>
				<div class="ring ring-2"></div>
				<div class="dot"></div>
			`,
			iconSize: [size, size],
			iconAnchor: [size / 2, size / 2],
			popupAnchor: [0, -(size / 2 + 2)]
		});
	}

	function createPopupContent(incident: BombingIncident): string {
		const location = escapeHtml(incident.location);
		const title = escapeHtml(incident.title);
		const source = escapeHtml(incident.source);
		const sourceUrl = encodeURI(incident.source_url);
		const attacker = escapeHtml(incident.attacker);

		return `
			<div style="min-width:220px;font-family:'JetBrains Mono',monospace;">
				<div style="display:flex;align-items:center;justify-content:space-between;color:#dc2626;font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid rgba(220,38,38,0.3);padding-bottom:8px;margin-bottom:8px;">
					<span>${location}</span>
					<span style="font-size:9px;color:#dc2626;border:1px solid rgba(220,38,38,0.4);padding:1px 6px;border-radius:2px;">${attacker}</span>
				</div>
				<div style="color:#d1d5db;font-size:11px;line-height:1.5;margin-bottom:8px;">
					${title}
				</div>
				<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:11px;">
					<div>
						<span style="color:#6b6b6b;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;">Killed</span>
						<div style="color:#dc2626;font-weight:700;font-size:18px;">${incident.killed}</div>
					</div>
					<div>
						<span style="color:#6b6b6b;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;">Wounded</span>
						<div style="color:#f97316;font-weight:700;font-size:18px;">${incident.wounded}</div>
					</div>
				</div>
				<div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(58,58,58,0.3);font-size:9px;color:#6b6b6b;display:flex;justify-content:space-between;">
					<a href="${sourceUrl}" target="_blank" rel="noopener" style="color:#ef4444;text-decoration:none;">
						${source} &#8599;
					</a>
					<span>${new Date(incident.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} UTC</span>
				</div>
			</div>
		`;
	}

	function updateMarkers() {
		if (!map || !markersLayer || !leaflet) return;

		markersLayer.clearLayers();

		for (const incident of bombingsStore.incidents) {
			const icon = createPulsingIcon(incident.killed);
			const marker = leaflet.marker([incident.latitude, incident.longitude], { icon });
			marker.bindPopup(createPopupContent(incident), {
				maxWidth: 320,
				closeButton: true
			});
			marker.on('click', () => {
				bombingsStore.selectIncident(incident.id);
			});
			markersLayer.addLayer(marker);
		}
	}

	onMount(async () => {
		if (!browser) return;

		leaflet = await import('leaflet');

		map = leaflet.map(mapContainer, {
			center: REGION_CENTER,
			zoom: DEFAULT_ZOOM,
			zoomControl: true,
			attributionControl: true
		});

		leaflet
			.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
				attribution:
					'&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
				subdomains: 'abcd',
				maxZoom: 19
			})
			.addTo(map);

		markersLayer = leaflet.layerGroup().addTo(map);

		mapReady = true;
	});

	onDestroy(() => {
		if (map) {
			map.remove();
			map = undefined;
			mapReady = false;
		}
	});

	$effect(() => {
		if (!mapReady) return;
		const _trigger = bombingsStore.incidents;
		updateMarkers();
	});

	$effect(() => {
		const selected = bombingsStore.selected;
		if (selected && map) {
			map.flyTo([selected.latitude, selected.longitude], 7, {
				duration: 1.5
			});
		}
	});
</script>

<div class="absolute inset-0 z-0">
	<div bind:this={mapContainer} class="absolute inset-0"></div>
</div>
