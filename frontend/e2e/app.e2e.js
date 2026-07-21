const {expect, test} = require('@playwright/test')
const {createMockState, installMockBackend} = require('./support/mockBackend')

async function loginAndOpenValue(page) {
  await page.goto('/')
  await page.getByPlaceholder('username').fill('user')
  await page.getByPlaceholder('password').fill('password')
  await page.getByRole('button', {name: 'Login'}).click()

  const valueCard = page.locator('.value').filter({hasText: 'Health'})
  await expect(valueCard).toBeVisible()
  await valueCard.click()

  await expect(page).toHaveURL(/\/value\/1\/active$/)
  await expect(page.getByRole('heading', {name: 'Health'})).toBeVisible()
}

test('logs in and completes an idea CRUD journey', async ({page}) => {
  const state = await installMockBackend(page)
  await loginAndOpenValue(page)

  await page.getByRole('tab', {name: 'Ideas'}).click()
  await expect(page).toHaveURL(/\/value\/1\/ideas$/)

  const defaultList = page.locator('.subvalueList').first()
  await defaultList.locator('.addIdeaButton').click()

  const createDialog = page.locator('.v-overlay--active').last()
  await createDialog.getByLabel('Name').fill('Plan weekend walk')
  await createDialog.getByLabel('Description').fill('Pick a quiet trail nearby.')
  await createDialog.getByRole('button', {name: 'Add', exact: true}).click()

  const createdIdea = defaultList.locator('.idea').filter({hasText: 'Plan weekend walk'})
  await expect(createdIdea).toContainText('Pick a quiet trail nearby.')

  await createdIdea.click()
  const editor = defaultList.locator('.ideaEditor')
  await expect(editor.getByLabel('Name')).toBeFocused()
  await editor.getByLabel('Name').fill('Plan a Sunday walk')
  await editor.getByLabel('Description').fill('Choose a quiet trail and invite a friend.')
  await editor.getByLabel('Name').press('Enter')

  const updatedIdea = defaultList.locator('.idea').filter({hasText: 'Plan a Sunday walk'})
  await expect(updatedIdea).toContainText('Choose a quiet trail and invite a friend.')

  await updatedIdea.hover()
  await updatedIdea.locator('.deleteIdea').click()
  const deleteDialog = page.locator('.v-overlay--active').last()
  await expect(deleteDialog).toContainText('Delete Idea?')
  await deleteDialog.getByRole('button', {name: 'Confirm'}).click()
  await expect(defaultList.getByText('Plan a Sunday walk')).toHaveCount(0)

  expect(state.requests).toEqual(expect.arrayContaining([
    expect.objectContaining({method: 'POST', path: '/authenticate'}),
    expect.objectContaining({method: 'GET', path: '/values'}),
    expect.objectContaining({method: 'GET', path: '/value/1'}),
    expect.objectContaining({method: 'POST', path: '/value/1/subvalue/0/idea'}),
    expect.objectContaining({method: 'PUT'}),
    expect.objectContaining({method: 'DELETE'}),
  ]))
})

test.describe('mobile layout', () => {
  test.use({viewport: {width: 390, height: 600}, hasTouch: true, isMobile: true})

  test('keeps carousels responsive and dialog controls fixed while content scrolls', async ({page}) => {
    const state = createMockState()
    state.value.objectives[1].key_results = Array.from({length: 15}, (_, index) => ({
      id: 101 + index,
      name: `Active Key Result ${index + 1}`,
      state: 'active',
      date_created: '2026-07-01',
      date_reviewed: '2026-07-31',
      resolved_tasks_count: index % 3,
      all_tasks_count: 3,
    }))
    state.subvalues[0].ideas = Array.from({length: 15}, (_, index) => ({
      id: `idea-${index + 1}`,
      name: `Health idea ${index + 1}`,
      description: 'A practical idea with enough detail to occupy some vertical space.',
    }))
    await installMockBackend(page, state)
    await loginAndOpenValue(page)

    const valueView = page.locator('.valueView')
    const appbar = page.locator('.appbar')
    const objectiveCarousel = page.locator('.activeObjectives')
    const objectiveCards = objectiveCarousel.locator('.obj')
    const objectivePager = page.locator('.activeObjectivesCarousel > .carouselPager')
    const keyResultsList = objectiveCards.first().locator('.keyResultsList')
    const initialAppbarY = (await appbar.boundingBox()).y

    await expect(valueView).toHaveClass(/containedView/)
    await expect(valueView).toHaveCSS('height', '600px')
    await expect(valueView).toHaveCSS('overflow', 'hidden')
    expect(await page.evaluate(() => globalThis.document.scrollingElement.scrollHeight)).toBeLessThanOrEqual(600)
    await expect(objectiveCarousel).toHaveCSS('scroll-snap-type', /x mandatory/)
    await expect(keyResultsList).toHaveCSS('overscroll-behavior-y', 'contain')
    expect(await keyResultsList.evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true)
    await keyResultsList.evaluate((element) => element.scrollTo({top: element.scrollHeight}))
    expect(await keyResultsList.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
    expect(await page.evaluate(() => globalThis.scrollY)).toBe(0)
    expect((await appbar.boundingBox()).y).toBe(initialAppbarY)
    await expect(objectivePager).toBeVisible()
    await expect(objectiveCards).toHaveCount(2)

    const carouselBox = await objectiveCarousel.boundingBox()
    const firstCardBox = await objectiveCards.first().boundingBox()
    expect(Math.abs(firstCardBox.width - carouselBox.width)).toBeLessThanOrEqual(1)

    await objectiveCarousel.evaluate((element) => element.scrollTo({left: element.clientWidth}))
    await expect(objectivePager.locator('.carouselPagerDot').nth(1)).toHaveClass(/active/)

    await objectiveCards.nth(1).locator('.v-card-actions button').click()
    const keyResultDialog = page.locator('.v-overlay--active .createKeyResultDialog')
    const title = keyResultDialog.getByText('Create Key Result')
    const content = keyResultDialog.locator('.dialogContent')
    const addButton = keyResultDialog.getByRole('button', {name: 'Add', exact: true})

    await expect(title).toBeVisible()
    await expect(addButton).toBeVisible()
    expect(await content.evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true)

    await content.evaluate((element) => element.scrollTo({top: element.scrollHeight}))
    expect(await content.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
    await expect(title).toBeVisible()
    await expect(addButton).toBeVisible()

    await page.keyboard.press('Escape')
    await page.getByRole('tab', {name: 'Ideas'}).click()

    const ideaCarousel = page.locator('.ideaLists')
    const ideaPager = page.locator('.ideaCarousel > .carouselPager')
    const ideasList = page.locator('.subvalueIdeas').first()
    await expect(valueView).toHaveClass(/containedView/)
    await expect(page.locator('.ideasView')).toHaveCSS('overflow', 'hidden')
    await expect(ideasList).toHaveCSS('overscroll-behavior-y', 'contain')
    expect(await ideasList.evaluate((element) => element.scrollHeight > element.clientHeight)).toBe(true)
    await ideasList.evaluate((element) => element.scrollTo({top: element.scrollHeight}))
    expect(await ideasList.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
    expect(await page.evaluate(() => globalThis.document.scrollingElement.scrollHeight)).toBeLessThanOrEqual(600)
    expect(await page.evaluate(() => globalThis.scrollY)).toBe(0)
    expect((await appbar.boundingBox()).y).toBe(initialAppbarY)
    await expect(ideaCarousel).toHaveCSS('scroll-snap-type', /x mandatory/)
    await expect(ideaPager).toBeVisible()
    await expect(page.locator('.subvalueIdeasWrapper').first()).toHaveCSS('margin-bottom', '40px')
  })
})
