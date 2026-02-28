import type { Handle } from '@sveltejs/kit';

const API_URL = process.env.API_URL || 'http://localhost:8000';

export const handle: Handle = async ({ event, resolve }) => {
	if (event.url.pathname.startsWith('/api')) {
		const target = `${API_URL}${event.url.pathname}${event.url.search}`;
		const res = await fetch(target, {
			method: event.request.method,
			headers: event.request.headers,
			body: event.request.method !== 'GET' ? await event.request.text() : undefined
		});

		return new Response(res.body, {
			status: res.status,
			statusText: res.statusText,
			headers: res.headers
		});
	}

	return resolve(event);
};
