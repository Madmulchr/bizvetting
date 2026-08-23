-- Region-mislabeling fix, single row, 2026-08-20 (cont'd 5)
-- South Central (TX) -> Midwest (MI): source listing is in Oakland County, Michigan
-- ("Heating/Cooling Business / Price Reduction!"), not Texas.

UPDATE public.deals SET region = 'Midwest (MI)', slug = 'midwest-mi-hvac-grade-a-1-6x-sde-a2a67565' WHERE slug = 'south-central-tx-hvac-grade-a-1-6x-sde-a2a67565';
