<script lang="ts">
	import { bombingsStore } from '$lib/stores/bombings.svelte';
</script>

<header
	class="absolute top-0 left-0 right-0 z-[1000] flex items-center
		justify-between px-6 py-3 bg-abyss/90 backdrop-blur-sm
		border-b border-blood/30"
>
	<div class="flex items-center gap-3">
		<div class="relative flex items-center justify-center w-3 h-3">
			<span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-blood opacity-75"
			></span>
			<span class="relative inline-flex h-2 w-2 rounded-full bg-blood"></span>
		</div>
		<h1 class="text-blood font-bold text-lg tracking-[0.3em] uppercase glitch-text">WARZONE</h1>
		<span class="text-smoke text-xs tracking-widest hidden sm:inline">// IRAN CONFLICT MONITOR</span>
	</div>

	<div class="flex items-center gap-6 text-xs text-smoke tracking-wider">
		<span class="hidden md:inline">
			INCIDENTS: <span class="text-ember font-bold tabular-nums">{bombingsStore.totalIncidents}</span
			>
		</span>
		<span>
			KIA: <span class="text-blood font-bold tabular-nums">{bombingsStore.totalKilled}</span>
		</span>
		<span class="hidden md:inline">
			WIA: <span class="text-flame font-bold tabular-nums">{bombingsStore.totalWounded}</span>
		</span>
		{#if bombingsStore.loading}
			<span class="text-warning blink text-[10px]">SCANNING</span>
		{:else}
			<span class="text-green-600 text-[10px]">ONLINE</span>
		{/if}
	</div>
</header>
