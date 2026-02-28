<script lang="ts">
	import '../app.css';
	import 'leaflet/dist/leaflet.css';

	let { children } = $props();
</script>

<svelte:head>
	<link
		href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&display=swap"
		rel="stylesheet"
	/>
	<title>WARZONE MONITOR // IRAN CONFLICT TRACKER</title>
	<meta name="description" content="Real-time tracking of bombing incidents in the Iran conflict" />
</svelte:head>

<div class="scanlines vignette">
	{@render children()}
</div>
