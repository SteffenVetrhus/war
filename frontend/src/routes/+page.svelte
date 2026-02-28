<script lang="ts">
	import { onMount } from 'svelte';
	import Map from '$lib/components/Map.svelte';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Header from '$lib/components/Header.svelte';
	import { bombingsStore } from '$lib/stores/bombings.svelte';

	onMount(() => {
		bombingsStore.fetchIncidents();
		bombingsStore.fetchIntegrations();
	});
</script>

<div class="relative h-screen w-screen overflow-hidden bg-void">
	<Header />
	<Map />
	<Sidebar />
</div>
