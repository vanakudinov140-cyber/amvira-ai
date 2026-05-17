# Файлы standalone frontend-репозитория

Корень репозитория = корень Amvera-сборки (без monorepo).

```
retention-admin-frontend/
├── amvera.yml
├── Dockerfile
├── nginx.conf
├── .dockerignore
├── .gitignore
├── .env.example
├── .env.production
├── package.json
├── package-lock.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.node.json
├── tailwind.config.js
├── postcss.config.js
├── public/
│   └── .gitkeep
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── constants.ts
│   ├── vite-env.d.ts
│   ├── api/
│   ├── components/
│   ├── hooks/
│   ├── i18n/
│   ├── layout/
│   ├── lib/
│   ├── pages/
│   └── types/
├── README.md
├── DEPLOY_AMVERA.md
└── REPO_FILES.md
```

Не коммитить: `node_modules/`, `dist/`, `.env`
