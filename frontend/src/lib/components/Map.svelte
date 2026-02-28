<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import type { BombingIncident } from '$lib/types';
	import type L from 'leaflet';

	let mapContainer: HTMLDivElement;
	let svgOverlay: SVGSVGElement;
	let map: L.Map | undefined;
	let markersLayer: L.LayerGroup | undefined;
	let leaflet: typeof L;

	const REGION_CENTER: [number, number] = [30.0, 45.0];
	const DEFAULT_ZOOM = 5;
	let mapReady = $state(false);

	// Flag colors for each attacking country
	const FLAG_COLORS: Record<string, string[]> = {
		Israel: ['#0038b8', '#ffffff', '#0038b8'],
		USA: ['#bf0a30', '#ffffff', '#002868'],
		Iran: ['#239f40', '#ffffff', '#da0000']
	};

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
		const notableNames = incident.notable_figures.map(escapeHtml);
		const attacker = escapeHtml(incident.attacker);
		const originLoc = escapeHtml(incident.origin_location);
		const colors = FLAG_COLORS[incident.attacker] || ['#dc2626'];
		const attackerColor = colors[0];

		const notable =
			notableNames.length > 0
				? `<div style="margin-top:8px;color:#f97316;">
					<span style="color:#6b6b6b;font-size:9px;letter-spacing:0.1em;text-transform:uppercase;">Notable KIA:</span><br/>
					${notableNames.join(', ')}
				</div>`
				: '';

		const originInfo = originLoc
			? `<div style="margin-top:6px;font-size:10px;color:#6b6b6b;">
				<span style="letter-spacing:0.1em;text-transform:uppercase;">Origin:</span>
				<span style="color:${attackerColor};font-weight:600;"> ${originLoc}</span>
			</div>`
			: '';

		return `
			<div style="min-width:220px;font-family:'JetBrains Mono',monospace;">
				<div style="display:flex;align-items:center;justify-content:space-between;color:#dc2626;font-weight:700;font-size:13px;text-transform:uppercase;letter-spacing:0.1em;border-bottom:1px solid rgba(220,38,38,0.3);padding-bottom:8px;margin-bottom:8px;">
					<span>${location}</span>
					<span style="font-size:9px;color:${attackerColor};border:1px solid ${attackerColor};padding:1px 6px;border-radius:2px;">${attacker}</span>
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
				${notable}
				${originInfo}
				<div style="margin-top:8px;padding-top:8px;border-top:1px solid rgba(58,58,58,0.3);font-size:9px;color:#6b6b6b;display:flex;justify-content:space-between;">
					<a href="${sourceUrl}" target="_blank" rel="noopener" style="color:#ef4444;text-decoration:none;">
						${source} &#8599;
					</a>
					<span>${new Date(incident.date).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })} UTC</span>
				</div>
			</div>
		`;
	}

	function computeBezierPoints(
		start: { x: number; y: number },
		end: { x: number; y: number },
		numPoints = 60
	): { x: number; y: number }[] {
		const points: { x: number; y: number }[] = [];

		// Midpoint
		const midX = (start.x + end.x) / 2;
		const midY = (start.y + end.y) / 2;

		// Distance between points
		const dx = end.x - start.x;
		const dy = end.y - start.y;
		const dist = Math.sqrt(dx * dx + dy * dy);

		// Control point: perpendicular offset at midpoint (curve upward on screen)
		const offsetAmount = dist * 0.25;
		// Perpendicular direction (rotated 90 degrees)
		const nx = -dy / dist;
		const ny = dx / dist;
		// Choose the direction that curves upward (negative Y = up on screen)
		const sign = nx * 0 + ny < 0 ? 1 : -1;
		const ctrlX = midX + nx * offsetAmount * sign;
		const ctrlY = midY + ny * offsetAmount * sign;

		for (let i = 0; i <= numPoints; i++) {
			const t = i / numPoints;
			const x = (1 - t) * (1 - t) * start.x + 2 * (1 - t) * t * ctrlX + t * t * end.x;
			const y = (1 - t) * (1 - t) * start.y + 2 * (1 - t) * t * ctrlY + t * t * end.y;
			points.push({ x, y });
		}

		return points;
	}

	function buildSvgPath(points: { x: number; y: number }[]): string {
		if (points.length === 0) return '';
		let d = `M ${points[0].x},${points[0].y}`;
		for (let i = 1; i < points.length; i++) {
			d += ` L ${points[i].x},${points[i].y}`;
		}
		return d;
	}

	function updateAttackArcs() {
		if (!map || !svgOverlay) return;

		const size = map.getSize();
		svgOverlay.setAttribute('width', String(size.x));
		svgOverlay.setAttribute('height', String(size.y));
		svgOverlay.setAttribute('viewBox', `0 0 ${size.x} ${size.y}`);

		// Clear previous content
		svgOverlay.innerHTML = '';

		// Create defs for gradients and filters
		const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
		svgOverlay.appendChild(defs);

		// Glow filter
		const filter = document.createElementNS('http://www.w3.org/2000/svg', 'filter');
		filter.setAttribute('id', 'arc-glow');
		filter.setAttribute('x', '-50%');
		filter.setAttribute('y', '-50%');
		filter.setAttribute('width', '200%');
		filter.setAttribute('height', '200%');
		const blur = document.createElementNS('http://www.w3.org/2000/svg', 'feGaussianBlur');
		blur.setAttribute('stdDeviation', '4');
		blur.setAttribute('result', 'blur');
		filter.appendChild(blur);
		const merge = document.createElementNS('http://www.w3.org/2000/svg', 'feMerge');
		const mergeNode1 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
		mergeNode1.setAttribute('in', 'blur');
		merge.appendChild(mergeNode1);
		const mergeNode2 = document.createElementNS('http://www.w3.org/2000/svg', 'feMergeNode');
		mergeNode2.setAttribute('in', 'SourceGraphic');
		merge.appendChild(mergeNode2);
		filter.appendChild(merge);
		defs.appendChild(filter);

		let arcIndex = 0;
		for (const incident of bombingsStore.incidents) {
			if (incident.origin_latitude == null || incident.origin_longitude == null) continue;

			const originPx = map.latLngToContainerPoint([
				incident.origin_latitude,
				incident.origin_longitude
			]);
			const targetPx = map.latLngToContainerPoint([incident.latitude, incident.longitude]);

			const colors = FLAG_COLORS[incident.attacker] || ['#dc2626', '#ffffff', '#dc2626'];
			const points = computeBezierPoints(originPx, targetPx);
			const pathD = buildSvgPath(points);

			if (!pathD) continue;

			// Create gradient along the arc direction
			const gradId = `arc-grad-${arcIndex}`;
			const grad = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
			grad.setAttribute('id', gradId);
			grad.setAttribute('gradientUnits', 'userSpaceOnUse');
			grad.setAttribute('x1', String(originPx.x));
			grad.setAttribute('y1', String(originPx.y));
			grad.setAttribute('x2', String(targetPx.x));
			grad.setAttribute('y2', String(targetPx.y));
			const stops = [
				{ offset: '0%', color: colors[0], opacity: '0.9' },
				{ offset: '35%', color: colors[0], opacity: '1' },
				{ offset: '50%', color: colors[1], opacity: '1' },
				{ offset: '65%', color: colors[2], opacity: '1' },
				{ offset: '100%', color: colors[2], opacity: '0.9' }
			];
			for (const s of stops) {
				const stop = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
				stop.setAttribute('offset', s.offset);
				stop.setAttribute('stop-color', s.color);
				stop.setAttribute('stop-opacity', s.opacity);
				grad.appendChild(stop);
			}
			defs.appendChild(grad);

			// Create a group for this arc
			const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');

			// 1. Glow base layer (wide, blurred)
			const glowPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
			glowPath.setAttribute('d', pathD);
			glowPath.setAttribute('fill', 'none');
			glowPath.setAttribute('stroke', colors[0]);
			glowPath.setAttribute('stroke-width', '6');
			glowPath.setAttribute('stroke-opacity', '0.15');
			glowPath.setAttribute('filter', 'url(#arc-glow)');
			g.appendChild(glowPath);

			// 2. Main gradient path (the "rainbow" streak)
			const mainPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
			mainPath.setAttribute('d', pathD);
			mainPath.setAttribute('fill', 'none');
			mainPath.setAttribute('stroke', `url(#${gradId})`);
			mainPath.setAttribute('stroke-width', '3');
			mainPath.setAttribute('stroke-linecap', 'round');
			mainPath.setAttribute('stroke-opacity', '0.85');

			// Get total path length for animation
			g.appendChild(mainPath);
			svgOverlay.appendChild(g);
			const totalLength = mainPath.getTotalLength();

			// Animated flowing dashes
			mainPath.style.strokeDasharray = `${totalLength * 0.15} ${totalLength * 0.05}`;
			mainPath.style.animation = `arc-flow-dash ${2 + arcIndex * 0.3}s linear infinite`;

			// 3. Thin bright center line
			const centerPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
			centerPath.setAttribute('d', pathD);
			centerPath.setAttribute('fill', 'none');
			centerPath.setAttribute('stroke', colors[1]);
			centerPath.setAttribute('stroke-width', '1');
			centerPath.setAttribute('stroke-linecap', 'round');
			centerPath.setAttribute('stroke-opacity', '0.5');
			centerPath.style.strokeDasharray = `${totalLength * 0.15} ${totalLength * 0.05}`;
			centerPath.style.animation = `arc-flow-dash ${2 + arcIndex * 0.3}s linear infinite`;
			g.appendChild(centerPath);

			// 4. Animated missile head (bright dot traveling along path)
			const missileHead = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
			missileHead.setAttribute('r', '4');
			missileHead.setAttribute('fill', colors[1]);
			missileHead.setAttribute('opacity', '0.9');
			missileHead.style.filter = `drop-shadow(0 0 6px ${colors[0]}) drop-shadow(0 0 3px ${colors[1]})`;
			g.appendChild(missileHead);

			// Animate along path
			const animateMotion = document.createElementNS(
				'http://www.w3.org/2000/svg',
				'animateMotion'
			);
			animateMotion.setAttribute('dur', `${3 + arcIndex * 0.2}s`);
			animateMotion.setAttribute('repeatCount', 'indefinite');
			animateMotion.setAttribute('path', pathD);
			missileHead.appendChild(animateMotion);

			// 5. Origin marker (small pulsing dot)
			const originDot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
			originDot.setAttribute('cx', String(originPx.x));
			originDot.setAttribute('cy', String(originPx.y));
			originDot.setAttribute('r', '5');
			originDot.setAttribute('fill', colors[0]);
			originDot.setAttribute('opacity', '0.7');
			originDot.style.filter = `drop-shadow(0 0 4px ${colors[0]})`;
			g.appendChild(originDot);

			// Pulsing ring at origin
			const originRing = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
			originRing.setAttribute('cx', String(originPx.x));
			originRing.setAttribute('cy', String(originPx.y));
			originRing.setAttribute('r', '5');
			originRing.setAttribute('fill', 'none');
			originRing.setAttribute('stroke', colors[0]);
			originRing.setAttribute('stroke-width', '1.5');
			originRing.classList.add('origin-pulse-ring');
			g.appendChild(originRing);

			arcIndex++;
		}
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

		// Listen for map movement to update SVG arcs
		map.on('move zoom moveend zoomend resize', () => {
			updateAttackArcs();
		});

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
		updateAttackArcs();
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
	<svg
		bind:this={svgOverlay}
		class="absolute inset-0 pointer-events-none z-[500]"
		style="overflow:visible;"
	></svg>
</div>
