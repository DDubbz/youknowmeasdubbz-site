import { defineCollection, z } from 'astro:content';

const pages = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    url: z.string(),
    published: z.boolean().default(true),
    order: z.number().default(0),
    seoTitle: z.string().optional(),
    seoDescription: z.string().optional(),
    seoKeywords: z.array(z.string()).optional(),
    ogImage: z.string().optional(),
    heroImage: z.string().optional(),
    heroVideo: z.string().optional(),
    showHeader: z.boolean().default(true),
    showFooter: z.boolean().default(true),
  }),
});

const mixes = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.date().optional(),
    genre: z.array(z.string()),
    duration: z.string().optional(), // e.g. "1:23:45"
    bpmRange: z.string().optional(), // e.g. "69-136"
    trackCount: z.number().optional(),
    youtubeUrl: z.string().optional(),
    spotifyUrl: z.string().optional(),
    soundcloudUrl: z.string().optional(),
    mixcloudUrl: z.string().optional(),
    coverImage: z.string(),
    audioFile: z.string().optional(),
    downloadable: z.boolean().default(false),
    featured: z.boolean().default(false),
    tags: z.array(z.string()).optional(),
  }),
});

const gigs = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    venue: z.string(),
    address: z.string().optional(),
    date: z.date(),
    startTime: z.string(), // e.g. "20:00"
    endTime: z.string().optional(), // e.g. "23:00"
    status: z.enum(['booked', 'actual', 'expected', 'pipeline']),
    fee: z.number().optional(),
    feeType: z.enum(['cash', 'check', 'venmo', 'invoice']).optional(),
    contactName: z.string().optional(),
    contactPhone: z.string().optional(),
    contactEmail: z.string().optional(),
    notes: z.string().optional(),
    recordingUrl: z.string().optional(),
    debriefUrl: z.string().optional(),
    isRecurring: z.boolean().default(false),
    recurringPattern: z.string().optional(), // e.g. "weekly-friday"
    featured: z.boolean().default(false),
  }),
});

const press = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    outlet: z.string(),
    date: z.date(),
    url: z.string().optional(),
    type: z.enum(['article', 'review', 'interview', 'feature', 'mention']),
    excerpt: z.string().optional(),
    image: z.string().optional(),
    featured: z.boolean().default(false),
  }),
});

export const collections = { pages, mixes, gigs, press };