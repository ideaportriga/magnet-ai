export default function patchObject(obj, props) {
  // Check if the input is an object
  if (typeof obj !== 'object' || obj === null) {
    return obj
  }
  //create new objet
  const newObj = JSON.parse(JSON.stringify(obj))

  // Iterate over each key in the object
  for (let key in newObj) {
    if (Object.prototype.hasOwnProperty.call(newObj, key)) {
      newObj[key] = { ...props, ...obj[key] }
    }
  }
  return newObj
}
