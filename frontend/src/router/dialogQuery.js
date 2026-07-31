export const DIALOG_QUERY_PARAM = Object.freeze({
  OBJECTIVE: 'objDialog',
  KEY_RESULT: 'krDialog',
})

const dialogQueryParams = Object.freeze(Object.values(DIALOG_QUERY_PARAM))

export function parseDialogId(value) {
  if (typeof value !== 'string' || !/^[1-9]\d*$/.test(value)) return null
  const id = Number(value)
  return Number.isSafeInteger(id) ? id : null
}

export function withDialogQuery(query, parameter, id) {
  const updatedQuery = {...query}
  for (const dialogParameter of dialogQueryParams) delete updatedQuery[dialogParameter]
  updatedQuery[parameter] = String(id)
  return updatedQuery
}

export function withoutDialogQuery(query, parameter) {
  const updatedQuery = {...query}
  delete updatedQuery[parameter]
  return updatedQuery
}
