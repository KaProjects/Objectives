import {backend} from '@/properties'
import {appState, setError} from '@/state/appState'

async function request(path, {method = 'GET', data, authenticated = true} = {}) {
    const headers = new Headers()

    if (data !== undefined) {
        headers.set('Content-Type', 'application/json')
    }

    if (authenticated && appState.token) {
        headers.set('Authorization', `Bearer ${appState.token}`)
    }

    try {
        const response = await fetch(`${backend}${path}`, {
            method,
            headers,
            body: data === undefined ? undefined : JSON.stringify(data),
        })
        const contentType = response.headers.get('content-type') ?? ''
        const body = contentType.includes('application/json')
            ? await response.json()
            : await response.text()

        if (!response.ok) {
            throw new Error(`[${response.status}] ${typeof body === 'string' ? body : JSON.stringify(body)}`)
        }

        return body
    } catch (error) {
        setError(error)
        throw error
    }
}

export const api = {
    get: (path) => request(path),
    delete: (path) => request(path, {method: 'DELETE'}),
    post: (path, data) => request(path, {method: 'POST', data}),
    put: (path, data) => request(path, {method: 'PUT', data}),
    login: (username, password) => request('/authenticate', {
        method: 'POST',
        data: {user: username, password},
        authenticated: false,
    }),
}
