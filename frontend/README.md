# Pinata Code - Frontend (Next.js + React)

This directory contains the Next.js 14 React frontend for the Pinata Code SaaS platform.

## Overview

The frontend is a modern web application built with:
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: React Query (TanStack Query)
- **Visualizations**: React Flow, Plotly.js, Mermaid
- **Auth**: Clerk.dev

## Project Structure

```
frontend/
├── app/                    # Next.js 14 app router
│   ├── (auth)/             # Protected routes
│   │   ├── dashboard/      # Main dashboard
│   │   ├── repositories/   # Repository management
│   │   ├── scans/          # Scan results
│   │   └── settings/       # User/org settings
│   ├── (marketing)/        # Public routes
│   │   ├── page.tsx        # Homepage
│   │   ├── pricing/        # Pricing page
│   │   └── docs/           # Documentation
│   ├── api/                # API routes (BFF pattern)
│   ├── layout.tsx          # Root layout
│   └── globals.css         # Global styles
├── components/             # React components
│   ├── ui/                 # Shadcn/ui components
│   ├── scan-results/       # Visualization components
│   │   ├── WorkflowGraph.tsx
│   │   ├── DatabaseSchema.tsx
│   │   └── OperationsChart.tsx
│   └── dashboard/          # Dashboard components
├── lib/                    # Utilities
│   ├── api-client.ts       # Backend API client
│   ├── auth.ts             # Clerk integration
│   └── utils.ts            # Helper functions
├── hooks/                  # Custom React hooks
├── stores/                 # Zustand stores
├── types/                  # TypeScript types
├── public/                 # Static assets
├── Dockerfile
├── Dockerfile.dev
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm
- Docker (for local development)

### Installation

```bash
# Install dependencies
cd frontend
npm install

# Copy environment variables
cp ../.env.example ../.env
# Edit .env with your configuration

# Start development server
npm run dev
```

### With Docker

```bash
# From project root
cd infrastructure/docker
docker-compose up frontend
```

Visit http://localhost:3000

## Development

### Running the App

```bash
# Development mode (hot reload)
npm run dev

# Production build
npm run build
npm run start

# Lint
npm run lint

# Type check
npm run type-check
```

### Testing

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# E2E tests (Playwright)
npm run test:e2e
```

## Key Features

### 1. Authentication (Clerk.dev)

```tsx
// app/(auth)/dashboard/page.tsx
import { auth } from '@clerk/nextjs';

export default async function DashboardPage() {
  const { userId } = auth();

  if (!userId) {
    redirect('/sign-in');
  }

  return <Dashboard />;
}
```

### 2. API Client

```tsx
// lib/api-client.ts
import { apiClient } from '@/lib/api-client';

// Fetch scans
const scans = await apiClient.get('/api/v1/scans');

// Start scan
const scan = await apiClient.post('/api/v1/repositories/123/scans', {
  config: { file_extensions: ['.cs', '.ts'] }
});
```

### 3. React Query (Data Fetching)

```tsx
// hooks/useScans.ts
import { useQuery } from '@tanstack/react-query';

export function useScans(repositoryId: string) {
  return useQuery({
    queryKey: ['scans', repositoryId],
    queryFn: () => apiClient.get(`/api/v1/repositories/${repositoryId}/scans`),
  });
}
```

### 4. Visualization Components

```tsx
// components/scan-results/WorkflowGraph.tsx
import ReactFlow from 'reactflow';

export function WorkflowGraph({ nodes, edges }: Props) {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      fitView
    />
  );
}
```

### 5. Real-time Progress (WebSockets)

```tsx
// hooks/useScanProgress.ts
import { useEffect, useState } from 'react';

export function useScanProgress(scanId: string) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ws/scans/${scanId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgress(data.progress);
    };

    return () => ws.close();
  }, [scanId]);

  return progress;
}
```

## UI Components

We use [Shadcn/ui](https://ui.shadcn.com/) for components:

```bash
# Add new component
npx shadcn-ui@latest add button

# Add multiple components
npx shadcn-ui@latest add button input card dialog
```

## Styling

Tailwind CSS with custom theme:

```tsx
// Example component
export function ScanCard({ scan }: Props) {
  return (
    <div className="rounded-lg border bg-card p-6 shadow-sm">
      <h3 className="text-xl font-semibold">{scan.repository.name}</h3>
      <p className="text-muted-foreground">{scan.status}</p>
    </div>
  );
}
```

## State Management

Zustand for global state:

```tsx
// stores/scan-store.ts
import { create } from 'zustand';

interface ScanStore {
  currentScan: Scan | null;
  setCurrentScan: (scan: Scan) => void;
}

export const useScanStore = create<ScanStore>((set) => ({
  currentScan: null,
  setCurrentScan: (scan) => set({ currentScan: scan }),
}));
```

## Routes

### Public Routes (Marketing)
- `/` - Homepage
- `/pricing` - Pricing page
- `/docs` - Documentation
- `/sign-in` - Login
- `/sign-up` - Registration

### Protected Routes (App)
- `/dashboard` - Main dashboard
- `/repositories` - Repository list
- `/repositories/[id]` - Repository details
- `/scans/[id]` - Scan results
- `/settings` - User settings
- `/settings/organization` - Organization settings
- `/settings/billing` - Billing & subscription

## Environment Variables

See `../.env.example` for all configuration options.

Key frontend variables:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
```

## Code Style

```tsx
// Use TypeScript
interface ScanProps {
  scanId: string;
  onComplete?: () => void;
}

// Use arrow functions for components
export const ScanProgress = ({ scanId, onComplete }: ScanProps) => {
  // Component logic
};

// Use named exports
export { ScanProgress };
export type { ScanProps };
```

## Performance

### Optimization Techniques
- **Code Splitting**: Automatic with Next.js App Router
- **Image Optimization**: `next/image` component
- **Font Optimization**: `next/font`
- **Lazy Loading**: React.lazy() for heavy components
- **Memoization**: useMemo, useCallback, React.memo

```tsx
import dynamic from 'next/dynamic';

// Lazy load heavy visualization component
const WorkflowGraph = dynamic(
  () => import('@/components/scan-results/WorkflowGraph'),
  { ssr: false, loading: () => <Skeleton /> }
);
```

## Deployment

### Vercel (Recommended for Frontend)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Docker (Self-hosted)

```bash
# Build production image
docker build -f Dockerfile -t pinata-frontend .

# Run
docker run -p 3000:3000 pinata-frontend
```

## Branding

**Product Name**: Pinata Code
**Tagline**: "It's what's inside that counts"
**Icon**: 🪅 (Pinata emoji)

**Color Palette**:
- Primary: Tailwind default (customizable)
- Accent: Rainbow gradient for progress bars
- Dark mode: Fully supported

## Next Steps

1. ✅ Set up project structure
2. ⏳ Install dependencies (Next.js, Tailwind, Shadcn/ui)
3. ⏳ Set up Clerk authentication
4. ⏳ Create layout components
5. ⏳ Build dashboard pages
6. ⏳ Implement scan visualization
7. ⏳ Add billing pages

See `../../docs/IMPLEMENTATION_PLAN.md` for detailed roadmap.

## Resources

- [Next.js Docs](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Shadcn/ui](https://ui.shadcn.com/)
- [React Query](https://tanstack.com/query/latest)
- [Clerk Docs](https://clerk.com/docs)

## License

Part of Pinata Code - Proprietary Software
