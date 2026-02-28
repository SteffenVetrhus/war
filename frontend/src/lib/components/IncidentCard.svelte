<script lang="ts">
	import type { BombingIncident } from '$lib/types';

	interface Props {
		incident: BombingIncident;
		isSelected: boolean;
		onSelect: () => void;
	}

	let { incident, isSelected, onSelect }: Props = $props();
</script>

<button
	onclick={onSelect}
	class="w-full text-left px-4 py-3 border-b border-ash/10 transition-colors cursor-pointer
		hover:bg-bunker/50
		{isSelected ? 'bg-blood/10 border-l-2 border-l-blood' : 'border-l-2 border-l-transparent'}"
>
	<div class="flex items-center justify-between mb-1">
		<div class="flex items-center gap-2">
			<span class="text-bone text-xs font-bold tracking-wider uppercase">
				{incident.location}
			</span>
		</div>
		<span class="text-smoke text-[10px] tabular-nums">
			{new Date(incident.date).toLocaleTimeString('en-US', {
				hour: '2-digit',
				minute: '2-digit',
				hour12: false
			})}
		</span>
	</div>

	<p class="text-smoke text-[11px] leading-relaxed mb-2 line-clamp-2">
		{incident.title}
	</p>

	<div class="flex items-center gap-4 text-[10px]">
		{#if incident.killed > 0}
			<span class="flex items-center gap-1">
				<span class="inline-block w-1.5 h-1.5 rounded-full bg-blood"></span>
				<span class="text-blood font-bold">{incident.killed}</span>
				<span class="text-smoke">KIA</span>
			</span>
		{/if}
		{#if incident.wounded > 0}
			<span class="flex items-center gap-1">
				<span class="inline-block w-1.5 h-1.5 rounded-full bg-flame"></span>
				<span class="text-flame font-bold">{incident.wounded}</span>
				<span class="text-smoke">WIA</span>
			</span>
		{/if}
	</div>

	{#if isSelected && incident.origin_location}
		<div class="mt-2 pt-2 border-t border-ash/20 text-[10px]">
			<span class="text-smoke tracking-widest uppercase">Origin:</span>
			<span class="text-ember font-semibold">
				{incident.origin_location}
			</span>
		</div>
	{/if}

	{#if isSelected}
		<div class="mt-2 pt-2 border-t border-ash/20 text-[11px] text-smoke leading-relaxed">
			{incident.description}
		</div>
	{/if}

	<div class="mt-1 text-[9px] text-smoke/50 tracking-wider">
		SRC: {incident.source}
	</div>
</button>
