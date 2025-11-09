# AI Chat Interface - Frontend

React-based frontend for AI chat web interface with LLM integration.

## Prerequisites

- Node.js 18+
- npm or yarn

## Installation

```bash
npm install
```

## Available Scripts

### Development

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build
npm run lint         # Run ESLint
```

### Testing

```bash
npm test             # Run tests in watch mode
npm run test:ui      # Run tests with Vitest UI
npm run test:coverage # Generate coverage report
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # React components
│   │   └── __tests__/   # Component tests
│   ├── utils/           # Utility functions
│   │   └── __tests__/   # Utility tests
│   ├── services/        # API client (future)
│   ├── types/           # TypeScript types
│   ├── test/            # Test setup
│   ├── App.tsx          # Main app component
│   ├── App.test.tsx     # App tests
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── index.html           # HTML entry point
└── vite.config.ts       # Vite + Vitest config
```

## Tech Stack

- **React 18+**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **Vitest**: Testing framework
- **React Testing Library**: Component testing
- **CSS Modules**: Scoped styling

## Testing Approach

- **Unit tests**: 100% coverage target for all components
- **React Testing Library**: Component behavior testing
- **Vitest**: Fast test execution with Vite integration

## Development Workflow

1. Start dev server: `npm run dev`
2. Open browser: http://localhost:5173
3. Make changes - hot module reload updates automatically
4. Run tests: `npm test`
5. Check coverage: `npm run test:coverage`

## Future Development

- **Sprint 2**: Chat components (ChatMessage, MessageInput, ChatContainer)
- **Sprint 3**: API integration with backend
- **Sprint 4**: Documentation and polish

## Quality Gates

- All tests pass
- 100% test coverage
- No linting errors
- TypeScript compilation succeeds

---

**Status**: Scaffold complete, ready for Sprint 2 component development
**Version**: 0.0.0
**Last Updated**: 2025-11-09
