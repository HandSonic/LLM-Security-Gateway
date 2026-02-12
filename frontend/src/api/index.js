import axios from 'axios'

const api = axios.create({
    baseURL: '/api', // Vite proxy will handle this
    timeout: 60000 // 60s timeout for LLM
})

export default api
