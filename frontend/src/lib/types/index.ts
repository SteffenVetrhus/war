export interface BombingIncident {
	id: string;
	title: string;
	location: string;
	latitude: number;
	longitude: number;
	date: string;
	killed: number;
	wounded: number;
	notable_figures: string[];
	description: string;
	source: string;
	source_url: string;
	attacker: string;
	origin_location: string;
	origin_latitude: number | null;
	origin_longitude: number | null;
}

export interface StatsResponse {
	total_incidents: number;
	total_killed: number;
	total_wounded: number;
	sources_count: number;
	last_updated: string | null;
}
