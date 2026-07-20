function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function createObjective(id, name) {
  return {
    id,
    value_id: 1,
    state: 'active',
    name,
    description: `${name} description`,
    date_created: '2026-07-01',
    date_finished: '',
    ideas_count: 0,
    key_results: [],
  }
}

function createMockState() {
  return {
    requests: [],
    values: [
      {
        id: 1,
        name: 'Health',
        description: 'Build sustainable health habits.',
        active_count: 2,
        achievements_count: 1,
      },
    ],
    value: {
      id: 1,
      name: 'Health',
      description: 'Build sustainable health habits.',
      objectives: [
        createObjective(11, 'Improve sleep'),
        createObjective(12, 'Exercise consistently'),
      ],
    },
    subvalues: [
      {
        id: '0',
        name: 'default',
        ideas: [
          {id: 'idea-1', name: 'Morning walk', description: 'Start with twenty minutes.'},
        ],
      },
      {
        id: '1',
        name: 'Exercise',
        ideas: [
          {id: 'idea-2', name: 'Try swimming', description: 'Visit the pool on Saturday.'},
        ],
      },
    ],
  }
}

async function fulfillJson(route, body, status = 200) {
  await route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  })
}

async function installMockBackend(page, state = createMockState()) {
  await page.route('**/api/**', async (route) => {
    const request = route.request()
    const method = request.method()
    const path = new URL(request.url()).pathname.replace(/^\/api/, '')
    const data = request.postData() ? request.postDataJSON() : undefined

    state.requests.push({method, path, data})

    if (method === 'POST' && path === '/authenticate') {
      await route.fulfill({status: 201, contentType: 'text/plain', body: 'signed-test-token'})
      return
    }

    if (method === 'GET' && path === '/values') {
      await fulfillJson(route, clone(state.values))
      return
    }

    if (method === 'GET' && path === '/value/1') {
      await fulfillJson(route, clone(state.value))
      return
    }

    if (method === 'GET' && path === '/value/1/subvalue') {
      await fulfillJson(route, clone(state.subvalues))
      return
    }

    const ideaMatch = path.match(/^\/value\/1\/subvalue\/(\d+)\/idea(?:\/([^/]+))?$/)
    if (ideaMatch) {
      const [, subvalueId, ideaId] = ideaMatch
      const subvalue = state.subvalues.find((item) => item.id === subvalueId)

      if (method === 'POST' && !ideaId) {
        const idea = {id: `idea-${Date.now()}`, ...data}
        subvalue.ideas.push(idea)
        await fulfillJson(route, clone(idea), 201)
        return
      }

      const index = subvalue.ideas.findIndex((idea) => idea.id === ideaId)
      if (method === 'PUT' && index !== -1) {
        state.subvalues[state.subvalues.indexOf(subvalue)].ideas[index] = {id: ideaId, ...data}
        await fulfillJson(route, clone(state.subvalues[state.subvalues.indexOf(subvalue)].ideas[index]))
        return
      }

      if (method === 'DELETE' && index !== -1) {
        subvalue.ideas.splice(index, 1)
        await route.fulfill({status: 204})
        return
      }
    }

    await fulfillJson(route, {
      error: {code: 'unhandled_mock', message: `${method} ${path} is not mocked`},
    }, 501)
  })

  return state
}

module.exports = {
  createMockState,
  installMockBackend,
}
