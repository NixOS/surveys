// lib/site/src/echarts-init.ts
import * as echarts from 'echarts';
import colors from '@nixos/branding/colors/tailwind.js';

const PALETTE = [
  colors['secondary-afghani-blue'].DEFAULT,
  colors['accent-zambian-green'][55],
  colors['accent-italian-violet'][55],
  colors['accent-persian-orange'][55],
  colors['accent-norwegian-pink'][55],
  colors['accent-chinese-magenta'][55],
  colors['accent-indian-gold'][55],
];

function makeTheme(mode: 'light' | 'dark') {
  const text = mode === 'light' ? colors['primary-black'][15] : colors['primary-white'][85];
  const axis = mode === 'light' ? colors['primary-black'][75] : colors['primary-black'][35];
  const grid = mode === 'light' ? colors['primary-black'][85] : colors['primary-black'][25];
  const bg = mode === 'light' ? colors['primary-white'].DEFAULT : colors['primary-black'][15];
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
      inRange: { color: [colors['secondary-afghani-blue'][95], colors['secondary-afghani-blue'].DEFAULT] },
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
