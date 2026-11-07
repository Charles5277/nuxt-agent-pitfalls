export default defineNuxtPlugin(() => {
  globalThis.$fetch = $fetch.create({ onRequest({ options }) { const h = new Headers(options.headers as HeadersInit); h.set('Authorization', 'Bearer TEST'); options.headers = h } }) as typeof globalThis.$fetch
})
