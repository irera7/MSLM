# LM Studio Clone - Frontend

React + TypeScript + TailwindCSS frontend for LM Studio Clone.

## Features

- 🎨 Modern UI with Dark/Light theme
- 📱 Responsive design
- 🔄 Real-time model management
- 💬 Chat interface with streaming support
- 📊 Dashboard with statistics
- ⚙️ Settings page

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The app will be available at `http://localhost:3032`

## Build

```bash
npm run build
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable components
│   │   ├── Layout.tsx
│   │   ├── Sidebar.tsx
│   │   └── Header.tsx
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Models.tsx
│   │   ├── Chat.tsx
│   │   └── Settings.tsx
│   ├── services/       # API services
│   │   └── api.ts
│   ├── types/          # TypeScript types
│   │   └── index.ts
│   ├── lib/            # Utilities
│   │   └── utils.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## API Integration

The frontend connects to the FastAPI backend running on `http://localhost:8078`. All API calls are proxied through Vite's dev server.

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Technologies

- React 18
- TypeScript
- TailwindCSS
- React Router
- TanStack Query (React Query)
- Axios
- Lucide Icons
- Vite

