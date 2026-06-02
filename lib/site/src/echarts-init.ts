// lib/site/src/echarts-init.ts
import * as echarts from 'echarts';
import colors from '@nixos/branding/colors/tailwind.js';

// ECharts' internal color interpolation (visualMap heatmap gradients) does not
// handle oklch() strings, so we resolve every theme color to #rrggbb before
// handing it to ECharts. Canvas 2D's fillStyle always normalizes to a hex (or
// rgba) string regardless of browser (whereas getComputedStyle now preserves
// oklch() in modern Firefox per the CSS Color 4 spec).
const _colorCache = new Map<string, string>();
let _canvasCtx: CanvasRenderingContext2D | null = null;
function resolveColor(input: string): string {
  const cached = _colorCache.get(input);
  if (cached) return cached;
  if (!_canvasCtx) {
    _canvasCtx = document.createElement('canvas').getContext('2d');
  }
  if (!_canvasCtx) {
    _colorCache.set(input, input);
    return input;
  }
  // Reset to a known value before assigning. Canvas fillStyle silently keeps
  // its previous value if the assigned string is unparseable.
  _canvasCtx.fillStyle = '#000000';
  _canvasCtx.fillStyle = input;
  const out = String(_canvasCtx.fillStyle);
  _colorCache.set(input, out);
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
  const bg = resolveColor(mode === 'light' ? colors['primary-white'].DEFAULT : colors['primary-black'][15]);
  return {
    color: PALETTE,
    backgroundColor: 'transparent',
    textStyle: { color: text },
    axisLine: { lineStyle: { color: axis } },
    splitLine: { lineStyle: { color: grid } },
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

// Sequential gradient (rate / composition heatmaps, percent 0-100).
const seqGradient = () => [
  resolveColor(colors['secondary-afghani-blue'][95]),
  resolveColor(colors['secondary-afghani-blue'].DEFAULT),
];
// Diverging gradient (lift heatmaps, centered at 1.0 with min=0 max=2).
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

function initChart(card: Element): void {
  const optionScript = card.querySelector('script[type="application/json"]');
  const div = card.querySelector('.echarts-chart');
  if (!optionScript || !div) return;
  const option = JSON.parse(optionScript.textContent ?? '{}');
  injectVisualMapColors(option);
  injectHeatmapTooltip(option);
  echarts.init(div as HTMLElement, currentTheme(), { renderer: 'svg' }).setOption(option);
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
    document.querySelectorAll<HTMLElement>('.echarts-chart').forEach(div => {
      const inst = echarts.getInstanceByDom(div);
      if (!inst) return;
      const opt = inst.getOption() as Record<string, unknown>;
      inst.dispose();
      injectVisualMapColors(opt);
      injectHeatmapTooltip(opt);
      echarts.init(div, currentTheme(), { renderer: 'svg' }).setOption(opt);
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
}
