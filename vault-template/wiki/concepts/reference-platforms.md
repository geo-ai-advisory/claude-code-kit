---
type: concept
tags: [product, design, reference, dashboard, analytics]
related: ["[[wiki/projects/report]]", "[[wiki/projects/<your-advisory>]]"]
created: 2026-05-12
updated: 2026-05-12
recency: 2026-05-12
confidence: high
---

# Reference платформы по типам задач

Каталог для **product-architect** агента: какие реальные платформы изучать как референс перед началом UI/dashboard разработки.

Цель: НЕ изобретать колесо и НЕ городить «правки на коленке вокруг неинформативных метрик» (главная боль А/Б витрины). Сначала смотрим как делают лучшие, потом адаптируем под <your-workspace> design tokens.

## Analytics dashboards

| Платформа | URL для WebFetch | Что украсть |
|---|---|---|
| Mixpanel | mixpanel.com/product | KPI cards сверху, cohort/retention chart, funnel breakdown |
| Amplitude | amplitude.com/product/analytics | Pathfinder flows, retention curves, experiment views |
| PostHog | posthog.com/product-analytics | Heatmaps + session replay в одной UI, dashboard-builder |
| Vercel Analytics | vercel.com/analytics | Минималистичные KPI, conversion funnel, period compare |
| Plausible | plausible.io/feature-comparison | Single-page dashboard, всё на одном экране без drill-down |

## А/Б testing и эксперименты

| Платформа | URL | Что украсть |
|---|---|---|
| Optimizely | optimizely.com/products/experiment | Stats Engine confidence, variant cards, lift% indicator |
| VWO | vwo.com/platform | Heatmap overlay variant comparison, winner highlight |
| GrowthBook | growthbook.io | Bayesian stats, sequential analysis, variant winning probability |
| Statsig | statsig.com | Pulse view, exposure-result-impact tracking |
| LaunchDarkly | launchdarkly.com/experimentation | Feature flag + experiment в одной панели |

## Heatmaps / behavior

| Платформа | URL | Что украсть |
|---|---|---|
| Hotjar | hotjar.com/heatmaps | Click/scroll/move overlay, segment filtering |
| Microsoft Clarity | clarity.microsoft.com | Free heatmap + session replay, dead clicks, rage clicks |
| Smartlook | smartlook.com | Event funnels поверх heatmap |
| FullStory | fullstory.com | Frustration signals (rage clicks, dead clicks, error clicks) |

## Tables / grids / data views

| Платформа | URL | Что украсть |
|---|---|---|
| Linear | linear.app | Issue table с inline filters, sortable columns, density modes |
| Notion | notion.so/databases | Multiple views (table/board/gallery/list/timeline) одной коллекции |
| Airtable | airtable.com | Grouping, conditional formatting, linked records |
| Retool | retool.com/components | Dense data tables для admin UI |
| Attio | attio.com | CRM table с rich cell types (people, companies, deals) |

## Финансовые отчёты / dashboard денег

| Платформа | URL | Что украсть |
|---|---|---|
| Stripe Dashboard | stripe.com/dashboard | Payment timeline, dispute view, payout breakdown |
| Brex | brex.com/product/spend-management | Budget vs actual, spend by category |
| Mercury | mercury.com | Cash flow chart, account aggregation, investment view |
| QuickBooks | quickbooks.intuit.com/online | P&L statement, cash flow report layout |

## Conversion funnels

| Платформа | URL | Что украсть |
|---|---|---|
| Mixpanel Funnel | mixpanel.com/funnels | Step drop-off с percent, conversion windows |
| Amplitude Pathfinder | amplitude.com/blog/pathfinder | Sankey-style flow, branching paths |
| GA4 Funnel Exploration | analytics.google.com | Drop-off bars + step time |
| Heap | heap.io | Auto-tracked funnel events |

## Sales pipeline / CRM

| Платформа | URL | Что украсть |
|---|---|---|
| HubSpot | hubspot.com/products/crm | Deal kanban, contact timeline, email tracking |
| Pipedrive | pipedrive.com | Visual pipeline, deal aging colors |
| Attio | attio.com | Modern CRM с relationship graph |
| Folk | folk.app | Lightweight pipeline для small teams |

## Cohort retention

| Платформа | URL | Что украсть |
|---|---|---|
| Mixpanel Retention | mixpanel.com/retention | Cohort table с color-coded retention% |
| Amplitude Retention | amplitude.com/retention-analysis | N-day retention, custom event-based cohorts |
| Looker | looker.com | SQL-based cohort builder |

## Landing pages / конверсия

| Платформа | URL | Что украсть |
|---|---|---|
| Linear (landing) | linear.app | Hero animation, feature scroll, dark theme |
| Stripe (landing) | stripe.com | Anchored sections, smooth scroll, code samples |
| Vercel (landing) | vercel.com | Above-fold benefit, trust-pills logos |
| Anthropic claude.com | claude.com | Минимальный hero, контрастная CTA |

## Form / wizard / multi-step

| Платформа | URL | Что украсть |
|---|---|---|
| Stripe Checkout | stripe.com/payments/checkout | Progressive disclosure, smart defaults |
| Typeform | typeform.com | Single-question-per-screen, soft transitions |
| Tally | tally.so | Notion-style form editor |
| Calendly | calendly.com | Date+time picker UX |

## Status pages / monitoring

| Платформа | URL | Что украсть |
|---|---|---|
| Vercel Observability | vercel.com/docs/observability | Log streams + metrics + traces |
| Datadog | datadoghq.com | Service map, APM flame graphs |
| Grafana | grafana.com | Time-series dashboard panels |

## Reference design tokens (откуда копировать «премиум-уровень»)

| Аспект | Источник эталона |
|---|---|
| Type scale | Linear (14/16/20/24/32) или Stripe (1.125 modular) |
| Spacing | 4-base scale: Vercel, Linear |
| Цвет | Stripe (1 акцент + neutrals), Notion (whitespace) |
| Анимации | Linear (200-250ms ease-out), cubic-bezier(0.16, 1, 0.3, 1) |
| Тени | shadcn/ui scale: sm/md/lg |
| Радиусы | 4/8/12/16 — Linear/Vercel |

## Как использовать product-architect'у

1. Определить тип задачи (analytics / А/Б / heatmap / table / landing / form).
2. Взять 2-3 платформы из соответствующей секции.
3. `WebFetch` каждой URL — извлечь конкретные паттерны (layout, наверху что, какие фильтры, переходы).
4. В brief'е под секцией «Reference платформы» указать **что именно** украдено: «metric card layout как у Mixpanel», «funnel breakdown как у Amplitude».
5. Адаптировать под <your-workspace> design tokens из `wiki/concepts/html-report-design-system.md`.

## Связанные

- [[wiki/concepts/html-report-design-system.md]] — наши design tokens
- [[wiki/concepts/design-balance.md]] — золотая середина цвета
- [[wiki/concepts/ui-grid-discipline.md]] — ровная сетка
- [[wiki/concepts/showcase-anchor-position.md]] — якорная позиция в витрине (CR 9x)
