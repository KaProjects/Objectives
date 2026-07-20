const {expect, test} = require('@playwright/test')
const {installMockBackend} = require('./support/mockBackend')

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
  test.use({viewport: {width: 390, height: 600}})

  test('keeps carousels responsive and dialog controls fixed while content scrolls', async ({page}) => {
    await installMockBackend(page)
    await loginAndOpenValue(page)

    const objectiveCarousel = page.locator('.activeObjectives')
    const objectiveCards = objectiveCarousel.locator('.obj')
    const objectivePager = page.locator('.activeObjectivesCarousel > .carouselPager')

    await expect(objectiveCarousel).toHaveCSS('scroll-snap-type', /x mandatory/)
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
    await expect(ideaCarousel).toHaveCSS('scroll-snap-type', /x mandatory/)
    await expect(ideaPager).toBeVisible()
    await expect(page.locator('.subvalueIdeasWrapper').first()).toHaveCSS('margin-bottom', '40px')
  })
})
