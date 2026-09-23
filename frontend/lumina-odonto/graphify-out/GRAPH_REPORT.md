# Graph Report - lumina-odonto  (2026-09-23)

## Corpus Check
- Corpus is ~17,980 words - fits in a single context window. You may not need a graph.

## Summary
- 590 nodes · 849 edges · 40 communities (19 shown, 21 thin omitted)
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.85)
- Token cost: 48,662 input · 0 output

## Community Hubs (Navigation)
- Sheet & Sidebar Layout
- Accordion Breadcrumb Carousel
- OTP Resizable & ESLint
- Dropdown Menu
- Login Screen & Forms
- Combobox
- shadcn Config
- Command Palette & Dialog
- Button Group & Items
- TypeScript Config
- Runtime Dependencies
- Drawer
- Charts (Recharts)
- Toast Notifications
- Attachments
- Badge & Toggle Variants
- Base UI Primitives
- cn Utility & Small Inputs
- Button & Calendar
- Navigation Menu
- Agent Rules & Project Docs
- Root Layout & Next Config
- Pagination
- Empty State
- Message Scroller
- Chat Bubble
- Alert
- Tabs
- Marker
- PostCSS Config

## God Nodes (most connected - your core abstractions)
1. `cn` - 61 edges
2. `react` - 40 edges
3. `@base-ui/react` - 39 edges
4. `lucide-react` - 23 edges
5. `class-variance-authority` - 17 edges
6. `Button()` - 16 edges
7. `compilerOptions` - 16 edges
8. `buttonVariants` - 9 edges
9. `tailwind` - 6 edges
10. `aliases` - 6 edges

## Surprising Connections (you probably didn't know these)
- `Next.js Agent Rules (This is NOT the Next.js you know)` --conceptually_related_to--> `Next.js Project (create-next-app bootstrap)`  [INFERRED]
  AGENTS.md → README.md
- `generate-agent-files.js (next dev agent-file generator)` --conceptually_related_to--> `Development Server (npm/yarn/pnpm/bun dev, localhost:3000)`  [INFERRED]
  AGENTS.md → README.md
- `SidebarProvider()` --calls--> `useIsMobile()`  [EXTRACTED]
  components/ui/sidebar.tsx → hooks/use-mobile.ts
- `CLAUDE.md @AGENTS.md import` --references--> `Next.js Agent Rules (This is NOT the Next.js you know)`  [EXTRACTED]
  CLAUDE.md → AGENTS.md
- `Calendar()` --calls--> `buttonVariants`  [EXTRACTED]
  components/ui/calendar.tsx → components/ui/button.tsx

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Agent instruction chain for Next.js breaking changes** — claude_agents_import, agents_nextjs_agent_rules, agents_next_bundled_docs, agents_generate_agent_files [EXTRACTED 1.00]

## Communities (40 total, 21 thin omitted)

### Community 0 - "Sheet & Sidebar Layout"
Cohesion: 0.06
Nodes (19): Sheet(), SheetContent(), SheetDescription(), SheetHeader(), SheetTitle(), Sidebar(), SidebarContext, SidebarContextProps (+11 more)

### Community 1 - "Accordion Breadcrumb Carousel"
Cohesion: 0.05
Nodes (15): CarouselApi, CarouselContent(), CarouselContext, CarouselContextProps, CarouselItem(), CarouselNext(), CarouselOptions, CarouselPlugin (+7 more)

### Community 2 - "OTP Resizable & ESLint"
Cohesion: 0.05
Nodes (33): eslintConfig, devDependencies, eslint, eslint-config-next, tailwindcss, @tailwindcss/postcss, @types/node, @types/react (+25 more)

### Community 3 - "Dropdown Menu"
Cohesion: 0.09
Nodes (13): DropdownMenu(), DropdownMenuContent(), DropdownMenuGroup(), DropdownMenuItem(), DropdownMenuLabel(), DropdownMenuPortal(), DropdownMenuRadioGroup(), DropdownMenuSeparator() (+5 more)

### Community 4 - "Login Screen & Forms"
Cohesion: 0.10
Nodes (14): LoginCard(), Login(), Card(), CardContent(), CardDescription(), CardHeader(), CardTitle(), Field() (+6 more)

### Community 5 - "Combobox"
Cohesion: 0.09
Nodes (7): InputGroup(), InputGroupAddon(), inputGroupAddonVariants, InputGroupButton(), inputGroupButtonVariants, InputGroupInput(), Textarea()

### Community 6 - "shadcn Config"
Cohesion: 0.09
Nodes (21): aliases, components, hooks, lib, ui, utils, iconLibrary, menuAccent (+13 more)

### Community 7 - "Command Palette & Dialog"
Cohesion: 0.11
Nodes (6): Dialog(), DialogContent(), DialogDescription(), DialogHeader(), DialogTitle(), cmdk

### Community 8 - "Button Group & Items"
Cohesion: 0.13
Nodes (7): ButtonGroup(), buttonGroupVariants, Item(), ItemMedia(), itemMediaVariants, itemVariants, Separator()

### Community 9 - "TypeScript Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 10 - "Runtime Dependencies"
Cohesion: 0.11
Nodes (18): dependencies, @base-ui/react, class-variance-authority, cmdk, cn, date-fns, embla-carousel-react, input-otp (+10 more)

### Community 12 - "Drawer"
Cohesion: 0.14
Nodes (4): DrawerContent(), DrawerContext, DrawerContextProps, useDrawer()

### Community 13 - "Charts (Recharts)"
Cohesion: 0.19
Nodes (11): ChartConfig, ChartContext, ChartContextProps, ChartLegendContent(), ChartTooltipContent(), getPayloadConfigFromPayload(), INITIAL_DIMENSION, THEMES (+3 more)

### Community 16 - "Attachments"
Cohesion: 0.20
Nodes (4): Attachment(), AttachmentMedia(), attachmentMediaVariants, attachmentVariants

### Community 18 - "Badge & Toggle Variants"
Cohesion: 0.27
Nodes (7): Badge(), badgeVariants, ToggleGroupContext, ToggleGroupItem(), Toggle(), toggleVariants, class-variance-authority

### Community 21 - "Button & Calendar"
Cohesion: 0.29
Nodes (7): Button(), buttonVariants, Calendar(), QuestionnaireNext(), QuestionnairePrevious(), QuestionnaireSkip(), QuestionnaireSubmit()

### Community 23 - "Agent Rules & Project Docs"
Cohesion: 0.25
Nodes (9): generate-agent-files.js (next dev agent-file generator), node_modules/next/dist/docs/ (bundled Next.js guides), Next.js Agent Rules (This is NOT the Next.js you know), CLAUDE.md @AGENTS.md import, app/page.tsx (entry page), Development Server (npm/yarn/pnpm/bun dev, localhost:3000), next/font with Geist font, Next.js Project (create-next-app bootstrap) (+1 more)

### Community 24 - "Root Layout & Next Config"
Cohesion: 0.22
Nodes (6): app_globals, geistMono, geistSans, metadata, nextConfig, next

### Community 30 - "Chat Bubble"
Cohesion: 0.38
Nodes (4): Bubble(), BubbleReactions(), bubbleReactionsVariants, bubbleVariants

## Knowledge Gaps
- **110 isolated node(s):** `geistSans`, `geistMono`, `metadata`, `$schema`, `style` (+105 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 392 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `cn` connect `cn Utility & Small Inputs` to `Sheet & Sidebar Layout`, `Accordion Breadcrumb Carousel`, `OTP Resizable & ESLint`, `Dropdown Menu`, `Login Screen & Forms`, `Combobox`, `Command Palette & Dialog`, `Button Group & Items`, `Context Menu`, `Drawer`, `Charts (Recharts)`, `Alert Dialog`, `Toast Notifications`, `Attachments`, `Questionnaire`, `Badge & Toggle Variants`, `Base UI Primitives`, `Button & Calendar`, `Navigation Menu`, `Pagination`, `Table`, `Empty State`, `Message Scroller`, `Avatar`, `Chat Bubble`, `Message`, `Popover`, `Alert`, `Progress`, `Tabs`, `Marker`, `Hover Card`?**
  _High betweenness centrality (0.324) - this node is a cross-community bridge._
- **Why does `react` connect `Login Screen & Forms` to `Sheet & Sidebar Layout`, `Accordion Breadcrumb Carousel`, `OTP Resizable & ESLint`, `Dropdown Menu`, `Combobox`, `Command Palette & Dialog`, `Button Group & Items`, `Context Menu`, `Drawer`, `Charts (Recharts)`, `Alert Dialog`, `Toast Notifications`, `Attachments`, `Questionnaire`, `Badge & Toggle Variants`, `Base UI Primitives`, `Button & Calendar`, `Pagination`, `Table`, `Message Scroller`, `Avatar`, `Chat Bubble`, `Message`, `Popover`, `Alert`, `Marker`?**
  _High betweenness centrality (0.184) - this node is a cross-community bridge._
- **Why does `@base-ui/react` connect `Base UI Primitives` to `Sheet & Sidebar Layout`, `Accordion Breadcrumb Carousel`, `OTP Resizable & ESLint`, `Dropdown Menu`, `Login Screen & Forms`, `Combobox`, `Command Palette & Dialog`, `Button Group & Items`, `Context Menu`, `Drawer`, `Alert Dialog`, `Toast Notifications`, `Attachments`, `Badge & Toggle Variants`, `cn Utility & Small Inputs`, `Button & Calendar`, `Navigation Menu`, `Avatar`, `Chat Bubble`, `Popover`, `Progress`, `Tabs`, `Marker`, `Collapsible`, `Hover Card`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **What connects `geistSans`, `geistMono`, `metadata` to the rest of the system?**
  _110 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Sheet & Sidebar Layout` be split into smaller, more focused modules?**
  _Cohesion score 0.05585106382978723 - nodes in this community are weakly interconnected._
- **Should `Accordion Breadcrumb Carousel` be split into smaller, more focused modules?**
  _Cohesion score 0.04734299516908213 - nodes in this community are weakly interconnected._
- **Should `OTP Resizable & ESLint` be split into smaller, more focused modules?**
  _Cohesion score 0.046511627906976744 - nodes in this community are weakly interconnected._