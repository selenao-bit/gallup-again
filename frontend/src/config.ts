import { apiPrefix } from '../config/api-prefix'

export const API_BASE_URL = apiPrefix(import.meta.env.VITE_API_BASE_URL)
export const HEALTH_TIMEOUT_MS = 5_000
