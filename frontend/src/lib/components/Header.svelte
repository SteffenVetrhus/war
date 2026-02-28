<script lang="ts">
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import { Crosshair, Skull, HeartPulse, Radar, RefreshCw, Wifi, WifiOff } from 'lucide-svelte';
</script>

<header
	class="absolute top-0 left-0 right-0 z-[1000] flex items-center
		justify-between px-3 py-2 md:px-5 md:py-2.5 bg-abyss/90 backdrop-blur-md
		border-b border-blood/30"
>
	<!-- Left: Branding -->
	<div class="flex items-center gap-2 md:gap-3">
		<div class="relative flex items-center justify-center w-3 h-3">
			<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-blood opacity-75"></span>
			<span class="relative inline-flex h-2 w-2 rounded-full bg-blood"></span>
		</div>
		<h1 class="text-blood font-bold text-sm md:text-base tracking-[0.25em] uppercase glitch-text">WARZONE</h1>
		<span class="text-ash text-[10px] tracking-widest hidden sm:inline">COMMAND CENTER</span>
	</div>

	<!-- Center: Stat Widgets -->
	<div class="flex items-center gap-1.5 md:gap-3">
		<!-- Strikes -->
		<div class="stat-widget">
			<Crosshair size={13} class="text-ember" strokeWidth={2.5} />
			<div class="flex flex-col items-center leading-none">
				<span class="text-ember font-bold text-sm tabular-nums">{bombingsStore.totalIncidents}</span>
				<span class="text-smoke text-[7px] tracking-[0.2em] hidden md:block">STRIKES</span>
			</div>
		</div>

		<div class="w-px h-6 bg-ash/30 hidden md:block"></div>

		<!-- KIA -->
		<div class="stat-widget">
			<Skull size={13} class="text-blood" strokeWidth={2.5} />
			<div class="flex flex-col items-center leading-none">
				<span class="text-blood font-bold text-sm tabular-nums">{bombingsStore.totalKilled}</span>
				<span class="text-smoke text-[7px] tracking-[0.2em] hidden md:block">KIA</span>
			</div>
		</div>

		<div class="w-px h-6 bg-ash/30 hidden md:block"></div>

		<!-- WIA -->
		<div class="stat-widget">
			<HeartPulse size={13} class="text-flame" strokeWidth={2.5} />
			<div class="flex flex-col items-center leading-none">
				<span class="text-flame font-bold text-sm tabular-nums">{bombingsStore.totalWounded}</span>
				<span class="text-smoke text-[7px] tracking-[0.2em] hidden md:block">WIA</span>
			</div>
		</div>
	</div>

	<!-- Right: Status + Rescan -->
	<div class="flex items-center gap-2 md:gap-3">
		<button
			onclick={() => bombingsStore.triggerScrape()}
			disabled={bombingsStore.loading}
			class="flex items-center gap-1.5 px-2.5 py-1 text-[9px] tracking-widest uppercase
				bg-blood/10 text-blood border border-blood/30
				hover:bg-blood/20 hover:border-blood/50 transition-all
				disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer rounded-sm"
		>
			<RefreshCw size={11} class={bombingsStore.loading ? 'animate-spin' : ''} />
			<span class="hidden sm:inline">{bombingsStore.loading ? 'SCANNING' : 'RESCAN'}</span>
		</button>

		<div class="flex items-center gap-1.5">
			{#if bombingsStore.loading}
				<Radar size={14} class="text-warning animate-pulse" />
				<span class="text-warning text-[9px] tracking-wider blink hidden md:inline">SCANNING</span>
			{:else}
				<Wifi size={14} class="text-green-500" />
				<span class="text-green-500 text-[9px] tracking-wider hidden md:inline">ONLINE</span>
			{/if}
		</div>
	</div>
</header>

<style>
	.stat-widget {
		display: flex;
		align-items: center;
		gap: 0.375rem;
		padding: 0.25rem 0.5rem;
		border-radius: 0.25rem;
		background: rgba(34, 34, 44, 0.6);
		border: 1px solid rgba(68, 68, 79, 0.3);
	}
</style>
