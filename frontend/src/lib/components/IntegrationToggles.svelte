<script lang="ts">
	import { bombingsStore } from '$lib/stores/bombings.svelte';

	let expanded = $state(false);
</script>

<div class="border-b border-ash/20">
	<button
		onclick={() => (expanded = !expanded)}
		class="flex items-center justify-between w-full px-4 py-2 text-[10px] tracking-widest uppercase
			text-smoke hover:text-dust transition-colors cursor-pointer"
	>
		<span>
			SOURCES
			<span class="text-ember tabular-nums">
				({bombingsStore.integrations.filter((i) => i.enabled).length}/{bombingsStore.integrations.length})
			</span>
		</span>
		<span class="transition-transform" class:rotate-180={expanded}>&#9660;</span>
	</button>

	{#if expanded}
		<div class="px-3 pb-3 flex flex-col gap-1">
			{#each bombingsStore.integrations as integration (integration.id)}
				<button
					onclick={() => bombingsStore.toggleIntegration(integration.id, !integration.enabled)}
					class="flex items-center gap-2 px-2 py-1.5 rounded text-left w-full
						transition-colors cursor-pointer group
						{integration.enabled
						? 'bg-blood/10 border border-blood/30 hover:bg-blood/20'
						: 'bg-trench/50 border border-ash/20 hover:bg-trench/80'}"
				>
					<!-- Toggle indicator -->
					<span
						class="shrink-0 w-2 h-2 rounded-full transition-colors
							{integration.enabled ? 'bg-blood shadow-[0_0_6px_rgba(220,38,38,0.6)]' : 'bg-ash/50'}"
					></span>

					<!-- Label -->
					<span
						class="text-[10px] tracking-wider uppercase truncate
							{integration.enabled ? 'text-dust' : 'text-smoke/60'}"
					>
						{integration.name}
					</span>

					<!-- Status -->
					<span
						class="ml-auto text-[9px] tracking-wider shrink-0
							{integration.enabled ? 'text-blood/70' : 'text-ash'}"
					>
						{integration.enabled ? 'ON' : 'OFF'}
					</span>
				</button>
			{/each}
		</div>
	{/if}
</div>
