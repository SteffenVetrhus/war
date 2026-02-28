<script lang="ts">
	import { browser } from '$app/environment';
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import IncidentCard from './IncidentCard.svelte';

	let collapsed = $state(browser ? window.innerWidth < 768 : false);

	const sortedIncidents = $derived(
		[...bombingsStore.incidents].sort(
			(a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
		)
	);
</script>

<aside
	class="absolute z-[999] flex transition-transform duration-300 ease-in-out
		bottom-0 left-0 right-0 flex-col
		md:top-14 md:right-0 md:left-auto md:flex-row"
	class:sidebar-collapsed={collapsed}
>
	<!-- Toggle button -->
	<button
		onclick={() => (collapsed = !collapsed)}
		class="flex items-center justify-center bg-bunker/90 backdrop-blur-sm
			border border-ash/30 text-smoke hover:text-ember hover:border-blood/50
			transition-colors cursor-pointer shrink-0
			w-full h-8 rounded-t-md border-b-0
			md:w-10 md:h-20 md:self-start md:mt-4 md:rounded-l-md md:rounded-tr-none md:border-r-0 md:border-b"
		aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
	>
		<!-- Mobile: up/down chevron -->
		<span class="text-xs md:hidden transition-transform" class:rotate-180={!collapsed}>&#9650;</span>
		<!-- Desktop: left/right chevron -->
		<span class="text-xs hidden md:inline transition-transform" class:rotate-180={!collapsed}>&#9666;</span>
	</button>

	<!-- Sidebar content -->
	<div
		class="h-[50vh] w-full bg-abyss/95 backdrop-blur-sm border-t border-blood/20
			overflow-hidden flex flex-col
			md:w-96 md:h-full md:border-t-0 md:border-l"
	>
		<!-- Sidebar header -->
		<div class="px-4 py-3 border-b border-ash/20">
			<h2 class="text-blood text-xs font-bold tracking-[0.25em] uppercase">Strike Log // Feb 26</h2>
			<div class="flex items-center justify-between mt-2">
				<span class="text-smoke text-[10px] tracking-wider">
					{bombingsStore.totalIncidents} STRIKES // {bombingsStore.totalKilled} KIA
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

<style>
	.sidebar-collapsed {
		transform: translateY(calc(100% - 2rem));
	}

	@media (min-width: 768px) {
		.sidebar-collapsed {
			transform: translateX(calc(100% - 2.5rem));
		}
	}
</style>
