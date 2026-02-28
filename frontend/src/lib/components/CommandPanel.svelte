<script lang="ts">
	import { bombingsStore } from '$lib/stores/bombings.svelte';
	import {
		ChevronUp,
		ChevronDown,
		Rss,
		Globe,
		Newspaper,
		Radio,
		Tv,
		BookOpen,
		Satellite,
		AlertTriangle
	} from 'lucide-svelte';
	import type { Integration } from '$lib/types';

	let expanded = $state(true);

	const ICON_MAP: Record<string, typeof Rss> = {
		'al jazeera': Globe,
		reuters: Newspaper,
		bbc: Globe,
		'ap ': Rss,
		cnn: Tv,
		vg: BookOpen,
		google: Satellite,
		radio: Radio
	};

	function getIcon(name: string): typeof Rss {
		const lower = name.toLowerCase();
		for (const [key, icon] of Object.entries(ICON_MAP)) {
			if (lower.includes(key)) return icon;
		}
		return Rss;
	}

	function handleToggle(integration: Integration) {
		bombingsStore.toggleIntegration(integration.id, !integration.enabled);
	}

	const enabledCount = $derived(bombingsStore.integrations.filter((i) => i.enabled).length);
</script>

<div class="absolute bottom-0 left-0 right-0 z-[999] flex flex-col transition-all duration-300 ease-in-out">
	<!-- Toggle bar -->
	<button
		onclick={() => (expanded = !expanded)}
		class="flex items-center justify-between mx-auto w-fit px-4 py-1.5 rounded-t-lg
			bg-abyss/95 backdrop-blur-md border border-b-0 border-ash/30
			text-smoke hover:text-dust transition-colors cursor-pointer"
	>
		<div class="flex items-center gap-2 text-[10px] tracking-[0.2em] uppercase">
			<Satellite size={12} class="text-ember" />
			<span>INTEL SOURCES</span>
			<span class="text-ember tabular-nums font-bold">{enabledCount}/{bombingsStore.integrations.length}</span>
		</div>
		<div class="ml-3">
			{#if expanded}
				<ChevronDown size={14} />
			{:else}
				<ChevronUp size={14} />
			{/if}
		</div>
	</button>

	<!-- Panel body -->
	{#if expanded}
		<div class="bg-abyss/95 backdrop-blur-md border-t border-ash/30">
			{#if bombingsStore.error}
				<div class="flex items-center gap-2 px-4 py-2 bg-blood/10 border-b border-blood/30 text-blood text-[10px]">
					<AlertTriangle size={12} />
					<span>{bombingsStore.error}</span>
				</div>
			{/if}

			<!-- Integration grid -->
			<div class="px-3 py-3 flex flex-wrap gap-2 justify-center max-w-4xl mx-auto">
				{#each bombingsStore.integrations as integration (integration.id)}
					{@const Icon = getIcon(integration.name)}
					<button
						onclick={() => handleToggle(integration)}
						class="integration-card group cursor-pointer transition-all duration-200
							{integration.enabled
							? 'bg-blood/10 border-blood/40 hover:bg-blood/20 hover:border-blood/60'
							: 'bg-trench/40 border-ash/20 hover:bg-trench/60 hover:border-ash/40'}"
						title={integration.description}
					>
						<!-- Status LED -->
						<span
							class="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full transition-colors
								{integration.enabled ? 'bg-green-500 shadow-[0_0_4px_rgba(34,197,94,0.6)]' : 'bg-ash/40'}"
						></span>

						<!-- Icon -->
						<div class="mb-1 {integration.enabled ? 'text-ember' : 'text-ash'}">
							<Icon size={18} strokeWidth={1.5} />
						</div>

						<!-- Name -->
						<span
							class="text-[8px] tracking-wider uppercase leading-tight text-center
								{integration.enabled ? 'text-dust' : 'text-smoke/50'}"
						>
							{integration.name}
						</span>
					</button>
				{/each}
			</div>

			<!-- Footer -->
			<div class="flex items-center justify-center gap-4 px-4 py-1.5 border-t border-ash/15 text-[8px] text-smoke/40 tracking-widest">
				{#if bombingsStore.lastUpdated}
					<span>LAST SCAN: {new Date(bombingsStore.lastUpdated).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}</span>
				{:else}
					<span>AWAITING INITIAL SCAN</span>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.integration-card {
		position: relative;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		width: 5.5rem;
		height: 4rem;
		padding: 0.5rem 0.25rem;
		border-radius: 0.375rem;
		border: 1px solid;
	}
</style>
