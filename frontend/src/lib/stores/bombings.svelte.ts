import type { BombingIncident, Integration } from '$lib/types';

let _incidents = $state<BombingIncident[]>([]);
let _selectedId = $state<string | null>(null);
let _loading = $state(false);
let _error = $state<string | null>(null);
let _lastUpdated = $state<string | null>(null);
let _integrations = $state<Integration[]>([]);

export const bombingsStore = {
	get incidents() {
		return _incidents;
	},
	get selected() {
		return _selectedId ? _incidents.find((i) => i.id === _selectedId) ?? null : null;
	},
	get selectedId() {
		return _selectedId;
	},
	set selectedId(id: string | null) {
		_selectedId = id;
	},
	get loading() {
		return _loading;
	},
	get error() {
		return _error;
	},
	get lastUpdated() {
		return _lastUpdated;
	},
	get totalKilled() {
		return _incidents.reduce((sum, i) => sum + i.killed, 0);
	},
	get totalWounded() {
		return _incidents.reduce((sum, i) => sum + i.wounded, 0);
	},
	get totalIncidents() {
		return _incidents.length;
	},
	get integrations() {
		return _integrations;
	},

	async fetchIncidents() {
		_loading = true;
		_error = null;
		try {
			const res = await fetch('/api/incidents');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const data: BombingIncident[] = await res.json();
			_incidents = data;
			_lastUpdated = new Date().toISOString();
		} catch (e) {
			_error = e instanceof Error ? e.message : 'Failed to fetch incidents';
		} finally {
			_loading = false;
		}
	},

	async triggerScrape() {
		_loading = true;
		_error = null;
		try {
			const res = await fetch('/api/scrape', { method: 'POST' });
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			// Refresh incidents after scrape
			await this.fetchIncidents();
		} catch (e) {
			_error = e instanceof Error ? e.message : 'Scrape failed';
			_loading = false;
		}
	},

	async fetchIntegrations() {
		try {
			const res = await fetch('/api/integrations');
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			_integrations = await res.json();
		} catch (e) {
			console.error('Failed to fetch integrations:', e);
		}
	},

	async toggleIntegration(id: string, enabled: boolean) {
		try {
			const res = await fetch(`/api/integrations/${id}`, {
				method: 'PUT',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ enabled })
			});
			if (!res.ok) throw new Error(`HTTP ${res.status}`);
			const updated: Integration = await res.json();
			_integrations = _integrations.map((i) => (i.id === updated.id ? updated : i));
		} catch (e) {
			console.error(`Failed to toggle integration ${id}:`, e);
		}
	},

	selectIncident(id: string | null) {
		_selectedId = id;
	}
};
