<script lang="ts">
	import { onMount } from 'svelte';
	import Map from '$lib/components/Map.svelte';
	import CommandPanel from '$lib/components/CommandPanel.svelte';
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
	<CommandPanel />
</div>
