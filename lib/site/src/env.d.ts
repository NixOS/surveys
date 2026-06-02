/// <reference path="../.astro/types.d.ts" />

type ColorScale = { DEFAULT: string } & Record<number, string>;
type BrandingColors = Record<string, ColorScale>;

declare module '@nixos/branding/colors/tailwind.js' {
  const colors: BrandingColors;
  export default colors;
}