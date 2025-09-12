import { uniq } from 'lodash'

/*-------------------- To Siebel SearchSpec ----------------------*/
/*----------------------------------------------------------------*/

function parseClauseToString({ field, options, op = '=', concatenator }) {
  if (op === 'IS NULL' || op === 'IS NOT NULL') {
    return `[${field}] ${op}`
  }

  if (!concatenator) concatenator = op === '<>' ? 'AND' : 'OR'

  let fieldSpec = ''
  if (Array.isArray(options) && options.length > 0) {
    let queryItems = options.filter((item) => typeof item === 'string')
    fieldSpec = queryItems.map((val) => `[${field}] ${op} '${val}'`).join(` ${concatenator} `)
  }
  return fieldSpec
}

function parseExprToString(obj) {
  let op = obj?.op ?? 'AND'
  let expList = obj?.exp

  if (expList && typeof expList === 'object') {
    if (!Array.isArray(expList)) expList = [expList]

    const parsedItems = expList
      .map((item) => {
        let parsedItem = parseItemToString(item)
        return expList.length > 1 ? `(${parsedItem})` : parsedItem
      })
      .filter((item) => ![undefined, null, '', '()'].includes(item))

    return uniq(parsedItems).join(` ${op} `)
  } else {
    console.error('[filter: parse query]: missing expression', obj)
    return ''
  }
}

function parseItemToString(item) {
  // check if item is clause or expression
  if (item.field) return parseClauseToString(item)
  else if (item.exp) return parseExprToString(item)
  else {
    console.error('[filter: parse query]: wrong input', item)
    return ''
  }
}

export function objToSearchExpr(obj) {
  return parseItemToString(obj, '')
}

/*------------------- To JS filter functio -----------------------*/
/*----------------------------------------------------------------*/

const operatorMap = {
  '=': '===',
  '<>': '!==',
}

const concatenatorMap = {
  AND: '&&',
  OR: '||',
}

function parseClause({ field, options, op = '=', concatenator }) {
  if (op === 'IS NULL') return `[undefined, null, ''].includes(item[${field}])`

  if (op === 'IS NOT NULL') return `![undefined, null, ''].includes(item[${field}])`

  if (!Array.isArray(options) || options.length === 0) {
    return ''
  }

  concatenator = (concatenator ?? op === '<>') ? 'AND' : 'OR'

  var jsConcatenator = concatenatorMap[concatenator] ?? concatenator
  var jsop = operatorMap[op] ?? op
  let fieldSpec = ''

  if (op === 'LIKE') {
    fieldSpec = options
      .filter((item) => typeof item === 'string')
      .map((val) => `/^${val.replaceAll('*', '.*')}$/i.test(item['${field}'])`)
      // .map(val => `new RegExp('^${val.replaceAll('%', '.*')}$', 'i').test(item['${field}'])`)
      .join(` ${jsConcatenator} `)
  } else if (options.length === 1) {
    fieldSpec = `item['${field}'] ${jsop} '${options[0]}'`
  } else {
    if (['===', '=='].includes(jsop)) fieldSpec = `['${options.join("','")}'].includes(item['${field}'])`
    else if (['!=='].includes(jsop)) {
      fieldSpec = `!['${options.join("','")}'].includes(item['${field}'])`
    } else {
      fieldSpec = options
        .filter((item) => typeof item === 'string')
        .map((val) => `item.['${field}'] ${jsop} '${val}'`)
        .join(` ${jsConcatenator} `)
    }
  }

  return fieldSpec
}

function parseExpr(obj) {
  let op = obj?.op ?? 'AND'
  let expList = obj?.exp

  if (expList && typeof expList === 'object') {
    if (!Array.isArray(expList)) expList = [expList]

    const parsedItems = expList
      .map((item) => {
        let parsedItem = parseItem(item)
        return expList.length > 1 ? `(${parsedItem})` : parsedItem
      })
      .filter((item) => ![undefined, null, '', '()'].includes(item))

    return uniq(parsedItems).join(` ${op} `)
  } else {
    console.error('[filter: parse query]: missing expression', obj)
    return ''
  }
}

function parseItem(item) {
  // check if item is clause or expression
  if (item.field) return parseClause(item)
  else if (item.exp) return parseExpr(item)
  else {
    console.error('[filter: parse query]: wrong input', item)
    return ''
  }
}

export function objToJsFilter(obj) {
  const func = parseItem(obj)
  return func
}
