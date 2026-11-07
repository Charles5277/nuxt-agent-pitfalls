import { db, schema } from 'hub:db'
export default defineEventHandler(async () => ({ rows: await db.select().from(schema.projects) }))
