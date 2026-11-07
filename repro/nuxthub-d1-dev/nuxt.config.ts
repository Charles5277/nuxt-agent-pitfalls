export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  modules: ['@nuxthub/core'],
  hub: { db: { dialect: 'sqlite', driver: 'd1', connection: { databaseId: '0f1e2d3c-aaaa-bbbb-cccc-123456789abc' } } },
})
