const load = async (themeName) => {
  await Promise.all([import('../base/app.styl'), import(`../themes/${themeName}/theme.styl`), import(`../themes/${themeName}/init.js`)])
}

export default load
