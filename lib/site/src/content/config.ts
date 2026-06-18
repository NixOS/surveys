// lib/site/src/content/config.ts
import { defineCollection, z } from 'astro:content';

const ChartSpec = z.object({
  option: z.record(z.any()),
  height: z.number().int().positive().optional(),
  caption: z.string().optional(),
});

const Row = z.object({
  id: z.string(),
  title: z.string(),
  question: z.string(),
  commentary: z.string(),
  charts: z.array(ChartSpec),
  wide: z.boolean().default(false),
});

const Section = z.object({
  id: z.string(),
  heading: z.string(),
  note: z.string().nullable().optional(),
  rows: z.array(Row),
});

const Results = z.object({
  schema_version: z.literal(1),
  series: z.string().default('community'),
  year: z.number().int(),
  title: z.string(),
  intro_meta: z.string().nullable().optional(),
  intro_paragraphs: z.array(z.string()).nullable().optional(),
  sections: z.array(Section),
});

export const collections = {
  results: defineCollection({
    type: 'data',
    schema: Results,
  }),
};
