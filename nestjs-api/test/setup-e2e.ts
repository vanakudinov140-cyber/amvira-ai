process.env.NODE_ENV ??= 'test';
process.env.PORT ??= '3000';
process.env.DATABASE_URL ??=
  'postgresql://app:app@127.0.0.1:5432/app?schema=public';
process.env.REDIS_HOST ??= '127.0.0.1';
process.env.REDIS_PORT ??= '6379';
