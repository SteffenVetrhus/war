<script lang="ts">
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import IncidentCard from './IncidentCard.svelte';

	let collapsed = $state(false);

	const sortedIncidents = $derived(
		[...bombingsStore.incidents].sort(
			(a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
		)
	);
</script>

<aside
	class="absolute top-14 right-0 bottom-0 z-[999] flex transition-transform duration-300 ease-in-out"
	class:translate-x-[calc(100%-2.5rem)]={collapsed}
>
	<!-- Toggle button -->
	<button
		onclick={() => (collapsed = !collapsed)}
		class="self-start mt-4 w-10 h-20 bg-bunker/90 backdrop-blur-sm
			border border-r-0 border-ash/30 rounded-l-md flex items-center
			justify-center text-smoke hover:text-ember hover:border-blood/50
			transition-colors cursor-pointer"
		aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
	>
		<span class="text-xs transition-transform" class:rotate-180={!collapsed}>&#9666;</span>
	</button>

	<!-- Sidebar content -->
	<div
		class="w-96 h-full bg-abyss/95 backdrop-blur-sm border-l border-blood/20
			overflow-hidden flex flex-col"
	>
		<!-- Sidebar header -->
		<div class="px-4 py-3 border-b border-ash/20">
			<h2 class="text-blood text-xs font-bold tracking-[0.25em] uppercase">Incident Log</h2>
			<div class="flex items-center justify-between mt-2">
				<span class="text-smoke text-[10px] tracking-wider">
					{bombingsStore.totalIncidents} RECORDS // {bombingsStore.totalKilled} KIA
				</span>
				<button
					onclick={() => bombingsStore.triggerScrape()}
					disabled={bombingsStore.loading}
					class="px-3 py-1 text-[10px] tracking-widest uppercase
						bg-blood/20 text-blood border border-blood/40
						hover:bg-blood/30 hover:border-blood/60 transition-colors
						disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
				>
					{bombingsStore.loading ? 'SCANNING...' : 'RESCAN'}
				</button>
			</div>
		</div>

		{#if bombingsStore.error}
			<div class="px-4 py-2 bg-blood/10 border-b border-blood/30 text-blood text-xs">
				ERR: {bombingsStore.error}
			</div>
		{/if}

		<!-- Incident list -->
		<div class="flex-1 overflow-y-auto">
			{#each sortedIncidents as incident (incident.id)}
				<IncidentCard
					{incident}
					isSelected={bombingsStore.selectedId === incident.id}
					onSelect={() => bombingsStore.selectIncident(incident.id)}
				/>
			{:else}
				{#if bombingsStore.loading}
					<div class="flex items-center justify-center h-32 text-smoke text-xs tracking-widest">
						<span class="animate-pulse">ACQUIRING DATA...</span>
					</div>
				{:else}
					<div
						class="flex items-center justify-center h-32 text-smoke text-xs tracking-widest"
					>
						NO INCIDENTS LOGGED
					</div>
				{/if}
			{/each}
		</div>

		<!-- Footer -->
		<div class="px-4 py-2 border-t border-ash/20 text-[9px] text-smoke/50 tracking-wider">
			{#if bombingsStore.lastUpdated}
				LAST SCAN: {new Date(bombingsStore.lastUpdated).toLocaleString()}
			{:else}
				AWAITING INITIAL SCAN
			{/if}
		</div>
	</div>
</aside>
