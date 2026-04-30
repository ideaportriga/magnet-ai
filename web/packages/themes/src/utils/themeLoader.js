const load = async (themeName) => {
  await Promise.all([import('../base/app.css'), import(`../themes/${themeName}/theme.css`), import(`../themes/${themeName}/init.js`)])
}

export default load
