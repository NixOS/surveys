// lib/site/src/echarts-init.ts
import * as echarts from 'echarts/core';
import {
  BarChart,
  HeatmapChart,
  SankeyChart,
  LineChart,
  ScatterChart,
  PictorialBarChart,
} from 'echarts/charts';
import { GridComponent, TooltipComponent, VisualMapComponent, LegendComponent, TitleComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import colors from '@nixos/branding/colors/tailwind.js';
import { formatHex } from 'culori';

echarts.use([
  BarChart,
  HeatmapChart,
  SankeyChart,
  LineChart,
  ScatterChart,
  PictorialBarChart,
  GridComponent,
  TooltipComponent,
  VisualMapComponent,
  LegendComponent,
  TitleComponent,
  SVGRenderer,
]);

// @nixos/branding ships every color as oklch(), which ECharts can't interpolate
// (heatmap gradients) and which some browsers won't resolve in chart fills:
// Chromium leaves an oklch() string unchanged where Firefox normalizes it to
// sRGB. Convert each to #rrggbb up front with culori; formatHex returns
// undefined for anything it can't parse, so fall back to the input unchanged.
const _colorCache = new Map<string, string>();
function resolveColor(input: string): string {
  let out = _colorCache.get(input);
  if (out === undefined) {
    out = formatHex(input) ?? input;
    _colorCache.set(input, out);
  }
  return out;
}

const PALETTE = [
  resolveColor(colors['secondary-afghani-blue'].DEFAULT),
  resolveColor(colors['accent-zambian-green'][55]),
  resolveColor(colors['accent-italian-violet'][55]),
  resolveColor(colors['accent-persian-orange'][55]),
  resolveColor(colors['accent-norwegian-pink'][55]),
  resolveColor(colors['accent-chinese-magenta'][55]),
  resolveColor(colors['accent-indian-gold'][55]),
];

function makeTheme(mode: 'light' | 'dark') {
  const text = resolveColor(mode === 'light' ? colors['primary-black'][15] : colors['primary-white'][85]);
  const axis = resolveColor(mode === 'light' ? colors['primary-black'][75] : colors['primary-black'][35]);
  const grid = resolveColor(mode === 'light' ? colors['primary-black'][85] : colors['primary-black'][25]);
  const bg = resolveColor(mode === 'light' ? colors['primary-white'].DEFAULT : colors['secondary-afghani-blue'][15]);
  return {
    color: PALETTE,
    backgroundColor: 'transparent',
    textStyle: { color: text },
    axisLine: { lineStyle: { color: axis } },
    splitLine: { lineStyle: { color: grid } },
    title: { textStyle: { color: text } },
    legend: { textStyle: { color: text } },
    tooltip: {
      backgroundColor: bg,
      borderColor: axis,
      borderWidth: 1,
      textStyle: { color: text },
    },
  };
}

echarts.registerTheme('nixos-light', makeTheme('light'));
echarts.registerTheme('nixos-dark', makeTheme('dark'));

// Both heatmap gradients use the same persian-orange → white → afghani-blue
// 3-color palette. They're split so the two can diverge later if the percent
// vs. lift charts ever want different palettes. The semantic difference is in
// the visualMap range — see callers below:
//   - seqGradient: applied to percent heatmaps (visualMap min=0, max=100;
//     white sits at 50%, an arbitrary mid-range neutral)
//   - liftGradient: applied to lift heatmaps (visualMap min=0, max=2; white
//     sits at 1.0×, the meaningful "no difference from baseline" midpoint)
const seqGradient = () => [
  resolveColor(colors['accent-persian-orange'][55]),
  resolveColor(colors['primary-white'].DEFAULT),
  resolveColor(colors['secondary-afghani-blue'].DEFAULT),
];
const liftGradient = () => [
  resolveColor(colors['accent-persian-orange'][55]),
  resolveColor(colors['primary-white'].DEFAULT),
  resolveColor(colors['secondary-afghani-blue'].DEFAULT),
];


const currentTheme = () =>
  document.documentElement.classList.contains('dark') ? 'nixos-dark' : 'nixos-light';

// ECharts' theme merging replaces a chart's `visualMap` object as a whole when
// the chart provides one, so the theme's `inRange.color` never reaches the
// heatmap. Inject the colors per chart here based on the visualMap's range.
// Also fade out-of-range cells so the visualMap's hover-highlight reads clearly.
function injectVisualMapColors(option: Record<string, unknown>): void {
  const vm = option.visualMap as {
    min?: number;
    max?: number;
    inRange?: { color?: unknown[] };
    outOfRange?: { opacity?: number };
  } | undefined;
  if (!vm) return;
  if (vm.inRange?.color && vm.inRange.color.length > 0) return;
  const isLift = vm.min === 0 && vm.max === 2;
  vm.inRange = { color: isLift ? liftGradient() : seqGradient() };
  vm.outOfRange = { opacity: 0.15 };
}

// Heatmap tooltips need to look up axis labels by index — that can't be
// expressed as an ECharts string template, so inject a JS formatter here.
// Skip if the option already specifies a tooltip (e.g., from Python).
type HeatmapTooltipParams = { value: [number, number, number] };
function injectHeatmapTooltip(option: Record<string, unknown>): void {
  if (option.tooltip) return;
  const series = option.series as Array<{ type?: string }> | undefined;
  if (!series || series[0]?.type !== 'heatmap') return;
  const xAxis = option.xAxis as { data?: string[] } | undefined;
  const yAxis = option.yAxis as { data?: string[] } | undefined;
  const xLabels = xAxis?.data ?? [];
  const yLabels = yAxis?.data ?? [];
  const vm = option.visualMap as { min?: number; max?: number } | undefined;
  const isLift = vm?.min === 0 && vm?.max === 2;
  const unit = isLift ? '\u00d7' : '%';
  option.tooltip = {
    trigger: 'item',
    formatter: (params: HeatmapTooltipParams) => {
      const [xi, yi, value] = params.value;
      const xLabel = xLabels[xi] ?? '?';
      const yLabel = yLabels[yi] ?? '?';
      const formatted = typeof value === 'number' ? value.toFixed(1) : String(value);
      return `${xLabel} \u00d7 ${yLabel}<br/>${formatted}${unit}`;
    },
  };
}

// Sankey tooltips need toFixed(1) formatting — can't be expressed as a string
// template, so inject a JS formatter here.
type SankeyTooltipParams = { dataType: 'edge' | 'node'; name: string; value: number; data: { source: string; target: string } };
function injectSankeyTooltip(option: Record<string, unknown>): void {
  if ((option.series as any[])?.[0]?.type !== 'sankey') return;
  option.tooltip = {
    trigger: 'item',
    formatter: (p: SankeyTooltipParams) => {
      const v = Number(p.value).toFixed(1) + '%';
      if (p.dataType === 'edge') return `${p.data.source} → ${p.data.target}: ${v}`;
      return `${p.name}: ${v}`;
    },
  };
}

// Result cards use overflow:hidden (for rounded corners), so a long ECharts
// tooltip — rendered as an HTML div inside the chart — gets clipped at the card
// edge. Append it to <body> to escape the clip, and cap its width so very long
// content wraps into a tidy box instead of stretching across the screen.
// Array-safe: getOption() (the dark-mode re-init path) returns tooltip as an array.
function fixTooltipOverflow(option: Record<string, unknown>): void {
  const tt = option.tooltip;
  const tips = Array.isArray(tt) ? tt : tt ? [tt] : [];
  for (const t of tips) {
    if (t && typeof t === 'object') {
      const o = t as Record<string, unknown>;
      o.appendToBody = true;
      o.extraCssText = 'max-width: 320px; white-space: normal;';
    }
  }
}

// Shared observer: reflow each chart when its container's size changes (e.g.,
// browser window resize changes the grid column width). Fires only when the
// observed element's box actually changes, so no debouncing needed.
// Batch resize calls into a single requestAnimationFrame so a drag-resize
// generating many observer events per frame only triggers one resize per
// chart per frame, not one resize per event. The first observation event
// for each chart is skipped: the chart was just initialized at exactly
// that size, and calling resize() then would interrupt the entry animation.
const seenResizeTargets = new WeakSet<Element>();
const pendingResizeTargets = new Set<HTMLElement>();
let scheduledFrame: number | null = null;
const resizeObserver = new ResizeObserver(entries => {
  for (const entry of entries) {
    if (!seenResizeTargets.has(entry.target)) {
      seenResizeTargets.add(entry.target);
      continue;
    }
    pendingResizeTargets.add(entry.target as HTMLElement);
  }
  if (pendingResizeTargets.size === 0 || scheduledFrame !== null) return;
  scheduledFrame = requestAnimationFrame(() => {
    for (const target of pendingResizeTargets) {
      const inst = echarts.getInstanceByDom(target);
      if (inst) inst.resize();
    }
    pendingResizeTargets.clear();
    scheduledFrame = null;
  });
});

function initChart(card: Element): void {
  const optionScript = card.querySelector('script[type="application/json"]');
  const div = card.querySelector('.echarts-chart');
  if (!optionScript || !div) return;
  const option = JSON.parse(optionScript.textContent ?? '{}');
  injectVisualMapColors(option);
  injectHeatmapTooltip(option);
  injectSankeyTooltip(option);
  fixTooltipOverflow(option);
  echarts.init(div as HTMLElement, currentTheme(), { renderer: 'svg' }).setOption(option);
  resizeObserver.observe(div as HTMLElement);
}

export function initCharts(): void {
  const observer = new IntersectionObserver((entries, obs) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      initChart(entry.target);
      obs.unobserve(entry.target);
    }
  }, { rootMargin: '200px' });

  document.querySelectorAll('[data-echarts-option]').forEach(el => observer.observe(el));

  new MutationObserver(() => {
    // Re-theme already-initialized charts when the dark class flips: re-run
    // initChart from the original embedded JSON rather than replaying
    // getOption(), which bakes the prior theme's resolved colors in as explicit
    // values that would override the new theme. Not-yet-initialized charts are
    // skipped — they pick up the current theme when they lazily init.
    document.querySelectorAll<HTMLElement>('.echarts-chart').forEach(div => {
      const inst = echarts.getInstanceByDom(div);
      if (!inst) return;
      inst.dispose();
      const card = div.closest('[data-echarts-option]');
      if (card) initChart(card);
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
}
