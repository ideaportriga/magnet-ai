import { DateTime } from 'luxon'

function fieldmapToVue(controls, item) {
  const result = item.reduce((res, record) => {
    // Map fields
    const mappedRecord = Object.keys(record).reduce((map, field) => {
      const control = controls[field]
      let fieldValue = record[field]
      if (control) {
        const type = control.uiType

        // DATE

        if (['JDateTimeZonePick', 'JDatePick', 'JDateTimePick'].includes(type)) {
          // parse from nexus - JS data format
          fieldValue = DateTime.fromJSDate(fieldValue)
          // if (!fieldValue.c) {
          //   // parse from string - mock
          //   fieldValue = DateTime.fromISO(fieldValue)
          // }
          // if (!fieldValue?.isValid)
          // fieldValue = {}
        }
      }
      map[field] = fieldValue
      return map
    }, {})
    res[record.Id] = mappedRecord
    return res
  }, {})

  return result
}

// maps date fields from string to luxon date
function fieldmapToVueMock(controls, item) {
  const result = item.reduce((res, record) => {
    // Map fields
    const mappedRecord = Object.keys(record).reduce((map, field) => {
      const control = controls[field]
      let fieldValue = record[field]
      if (control) {
        const type = control.uiType

        // DATE
        if (['JDateTimeZonePick', 'JDatePick', 'JDateTimePick'].includes(type) && fieldValue) {
          // parse from nexus - JS data format
          fieldValue = DateTime.fromISO(fieldValue)
        }
      }
      map[field] = fieldValue
      return map
    }, {})
    res[record.Id] = mappedRecord
    return res
  }, {})

  return result
}

// function gotoView(viewName, appletName, id) {
//   // id = typeof id === 'undefined' ? (this.getCurrentRecord(true) || {}).Id : id
//   if (appletName && id) {
//     let SWECmd = `GotoView&SWEView=${viewName}&SWEApplet0=${appletName}`
//     SWECmd += `&SWEBU=1&SWEKeepContext=FALSE&SWERowId0=${id}`
//     SWECmd = encodeURI(SWECmd)
//     return window.SiebelApp.S_App.GotoView(viewName, '', SWECmd, '')
//   } else {
//     return window.SiebelApp.S_App.GotoView(viewName)
//   }
// };

// FUNCTIONS TO simplify PropSet <=> JS Object coversion
function convertPropSetToJS(propSet, omitPropTypes = []) {
  if (propSet instanceof window.JSSPropertySet && !omitPropTypes.includes(propSet.GetType() ?? '')) {
    let res = {}

    // map type, value
    const propType = propSet.GetType(),
      propValue = propSet.GetValue()

    if (propType) {
      res.propType = propType
    }
    if (propValue) {
      res.propType = propValue
    }

    // map props
    if (Object.prototype.hasOwnProperty.call(propSet, 'propArray')) {
      for (let [key, value] of Object.entries(propSet.propArray)) {
        res[key] = value
      }
    }

    // map children
    if (Array.isArray(propSet.childArray) && propSet.childArray.length) {
      res.propChildren = []
      propSet.childArray.forEach((item) => {
        let child = convertPropSetToJS(item, omitPropTypes)
        if (child) res.propChildren.push(child)
      })
    }

    return res
  } else {
    return undefined
  }
}

function convertJSToPropSet(obj) {
  if (typeof obj === 'object') {
    let res = window.SiebelApp.S_App.NewPropertySet()

    const { propType, propValue, propChildren, ...props } = obj
    // const props = {}

    res.SetType(propType ?? '')
    res.SetValue(propValue ?? '')

    // map props
    if (typeof props === 'object') {
      for (let [key, value] of Object.entries(props)) {
        if (value !== undefined) res.SetProperty(key, value)
      }
    }

    // map children
    if (Array.isArray(propChildren)) {
      propChildren.forEach((item) => {
        let child = convertJSToPropSet(item)
        if (child) res.AddChild(child)
      })
    }

    return res
  } else {
    return undefined
  }
}

const convertTypes = (items, metadata) => {
  return (
    items?.map((item) => {
      Object.entries(item).forEach(([field, val]) => {
        if (field in metadata) {
          if (metadata[field] === 'Boolean') item[field] = val === 'Y'
          else if (metadata[field] === 'Date') {
            item[field] = DateTime.fromFormat(val, 'LL/dd/yyyy')
          }
        }
      })
      return item
    }) ?? items
  )
}
export { fieldmapToVue, fieldmapToVueMock, convertPropSetToJS, convertJSToPropSet, convertTypes }
