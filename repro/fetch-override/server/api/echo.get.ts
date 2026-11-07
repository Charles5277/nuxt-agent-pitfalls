export default defineEventHandler((e) => ({ auth: getRequestHeader(e, 'authorization') ?? null }))
