-- Region-mislabeling fix, batch of 12, 2026-08-20
-- Run each statement; each targets exactly one row by old slug.

UPDATE public.deals SET region = 'Mid-Atlantic (VA)', slug = 'mid-atlantic-va-hvac-grade-c-3-84x-sde-c6f0b5cc' WHERE slug = 'southeast-fl-hvac-grade-c-3-84x-sde-c6f0b5cc';
UPDATE public.deals SET region = 'Mid-Atlantic (VA)', slug = 'mid-atlantic-va-hvac-grade-c-3-84x-sde-7320c7b3' WHERE slug = 'southeast-fl-hvac-grade-c-3-84x-sde-7320c7b3';
UPDATE public.deals SET region = 'Pacific (CA)', slug = 'pacific-ca-hvac-grade-b-3-11x-sde-f8fc2d75' WHERE slug = 'midwest-mo-hvac-grade-b-3-11x-sde-f8fc2d75';
UPDATE public.deals SET region = 'Southeast (TN)', slug = 'southeast-tn-hvac-grade-c-3-68x-sde-9e8b065a' WHERE slug = 'new-england-ma-hvac-grade-c-3-68x-sde-9e8b065a';
UPDATE public.deals SET region = 'New England (NH)', slug = 'new-england-nh-hvac-grade-b-3-08x-sde-6ee0deee' WHERE slug = 'southwest-az-hvac-grade-b-3-08x-sde-6ee0deee';
UPDATE public.deals SET region = 'New England (NH)', slug = 'new-england-nh-hvac-grade-b-2-64x-sde-8dde3176' WHERE slug = 'region-withheld-hvac-grade-b-2-64x-sde-8dde3176';
UPDATE public.deals SET region = 'Mountain West (MT)', slug = 'mountain-west-mt-hvac-grade-b-3-01x-sde-1e875026' WHERE slug = 'region-withheld-hvac-grade-b-3-01x-sde-1e875026';
UPDATE public.deals SET region = 'Southeast (NC)', slug = 'southeast-nc-hvac-grade-b-2-78x-sde-08038b3b' WHERE slug = 'region-withheld-hvac-grade-b-2-78x-sde-08038b3b';
UPDATE public.deals SET region = 'Midwest (MN)', slug = 'midwest-mn-hvac-grade-a-2-18x-sde-35dc67c4' WHERE slug = 'region-withheld-hvac-grade-a-2-18x-sde-35dc67c4';
UPDATE public.deals SET region = 'New England (ME)', slug = 'new-england-me-hvac-grade-b-3-4x-sde-50100a13' WHERE slug = 'region-withheld-hvac-grade-b-3-4x-sde-50100a13';
UPDATE public.deals SET region = 'New England (RI)', slug = 'new-england-ri-hvac-grade-c-4-66x-sde-56ab247e' WHERE slug = 'region-withheld-hvac-grade-c-4-66x-sde-56ab247e';
UPDATE public.deals SET region = 'Southwest (UT)', slug = 'southwest-ut-hvac-grade-c-3-63x-sde-fd940681' WHERE slug = 'region-withheld-hvac-grade-c-3-63x-sde-fd940681';
