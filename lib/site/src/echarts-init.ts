// lib/site/src/echarts-init.ts
import * as echarts from 'echarts';
import colors from '@nixos/branding/colors/tailwind.js';

// ECharts' internal color interpolation (visualMap heatmap gradients) does not
// handle oklch() strings, so we resolve every theme color to #rrggbb via the
// browser's CSS engine before handing it to ECharts.
const _colorCache = new Map<string, string>();
function resolveColor(input: string): string {
  const cached = _colorCache.get(input);
  if (cached) return cached;
  const probe = document.createElement('span');
  probe.style.color = input;
  probe.style.display = 'none';
  document.documentElement.appendChild(probe);
  const computed = getComputedStyle(probe).color;
  probe.remove();
  const m = computed.match(/rgba?\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)/);
  const out = m
    ? '#' + [m[1], m[2], m[3]].map(n => Math.round(parseFloat(n)).toString(16).padStart(2, '0')).join('')
    : input;
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
  const visMin = resolveColor(mode === 'light' ? colors['secondary-afghani-blue'][95] : colors['secondary-afghani-blue'][25]);
  const visMax = resolveColor(colors['secondary-afghani-blue'].DEFAULT);
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
    visualMap: {
      inRange: { color: [visMin, visMax] },
    },
  };
}

echarts.registerTheme('nixos-light', makeTheme('light'));
echarts.registerTheme('nixos-dark', makeTheme('dark'));

const currentTheme = () =>
  document.documentElement.classList.contains('dark') ? 'nixos-dark' : 'nixos-light';

function initChart(card: Element): void {
  const optionScript = card.querySelector('script[type="application/json"]');
  const div = card.querySelector('.echarts-chart');
  if (!optionScript || !div) return;
  const option = JSON.parse(optionScript.textContent ?? '{}');
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
      const opt = inst.getOption();
      inst.dispose();
      echarts.init(div, currentTheme(), { renderer: 'svg' }).setOption(opt);
    });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
}
