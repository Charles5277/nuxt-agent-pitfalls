export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  modules: ['@nuxthub/core'],
  hub: { db: { dialect: 'sqlite', ...(process.env.NODE_ENV === 'production' ? { driver: 'd1' as const, connection: { databaseId: '0f1e2d3c-aaaa-bbbb-cccc-123456789abc' } } : {}) } },
})
