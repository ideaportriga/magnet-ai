const unicodeRangeLatin =
  'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD'
const unicodeRangeLatinExt =
  'U+0100-02AF, U+0304, U+0308, U+0329, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20CF, U+2113, U+2C60-2C7F, U+A720-A7FF'
const unicodeRangeCyrillic = 'U+0301, U+0400-045F, U+0490-0491, U+04B0-04B1, U+2116'

const interProps = (weightRange, unicodeRange) => {
  return weightRange.map((weight) => ({
    weight,
    unicodeRange,
  }))
}

const config = {
  'Material Icons': {
    fonts: [
      {
        name: 'Material Icons',
        loadUrl: () => import('@quasar/extras/material-icons/web-font/flUhRq6tzZclQEJ-Vdg-IuiaDsNcIhQ8tQ.woff2'),
        props: {
          weight: '400',
        },
      },
      {
        name: 'Material Icons Outlined',
        loadUrl: () => import('@quasar/extras/material-icons-outlined/web-font/gok-H7zzDkdnRel8-DQ6KAXJ69wP1tGnf4ZGhUcel5euIg.woff2'),
        props: {
          weight: '400',
        },
      },
    ],
    styles: [() => import(`../base/assets/css/material-icons.css`)],
  },
  'Font Awesome 6': {
    fonts: [
      {
        name: 'Font Awesome 6 Brands',
        loadUrl: () => import(`../base/assets/fonts/fa/fa-brands-400.woff2`),
        props: {
          weight: '400',
        },
      },
      {
        name: 'Font Awesome 6 Free',
        loadUrl: () => import(`../base/assets/fonts/fa/fa-regular-400.woff2`),
        props: {
          weight: '400',
        },
      },
      {
        name: 'Font Awesome 6 Free',
        loadUrl: () => import(`../base/assets/fonts/fa/fa-solid-900.woff2`),
        props: {
          weight: '900',
        },
      },
    ],
    styles: [() => import(`../base/assets/css/fontawesome.css`)],
  },
  'Oracle Sans': {
    fonts: [
      {
        name: 'Oracle Sans',
        loadUrl: () => import(`../base/assets/fonts/oracle/OracleSans_W_Rg.woff2`),
        props: {
          weight: '400',
        },
      },
      {
        name: 'Oracle Sans',
        loadUrl: () => import(`../base/assets/fonts/oracle/OracleSans_W_SBd.woff2`),
        props: {
          weight: '600',
        },
      },
      {
        name: 'Oracle Sans',
        loadUrl: () => import(`../base/assets/fonts/oracle/OracleSans_W_Bd.woff2`),
        props: {
          weight: '700',
        },
      },
      {
        name: 'Oracle Sans',
        loadUrl: () => import(`../base/assets/fonts/oracle/OracleSans_XBd.woff2`),
        props: {
          weight: '800',
        },
      },
      {
        name: 'Oracle Sans Condensed',
        loadUrl: () => import(`../base/assets/fonts/oracle/OracleSansCd_W_Bd.woff2`),
        props: {
          weight: '700',
        },
      },
    ],
  },
  Inter: {
    fonts: [
      {
        name: 'Inter',
        loadUrl: () => import(`../base/assets/fonts/inter/Inter-latin.woff2`),
        props: interProps(['300', '400', '500', '600', '700'], unicodeRangeLatin),
      },
      {
        name: 'Inter',
        loadUrl: () => import(`../base/assets/fonts/inter/Inter-cyr.woff2`),
        props: interProps(['300', '400', '500', '600', '700'], unicodeRangeCyrillic),
      },
      {
        name: 'Inter',
        loadUrl: () => import(`../base/assets/fonts/inter/Inter-latin-ext.woff2`),
        props: interProps(['300', '400', '500', '600', '700'], unicodeRangeLatinExt),
      },
    ],
  },
}

export const addFont = (name, url, props = {}) => {
  const font = new FontFace(name, `url(${url})`, props)
  font
    .load()
    .then((item) => {
      document.fonts.add(item)
    })
    .catch((err) => {
      console.error('Error loading font', name, err)
    })
}

const loadFonts = (familyNames) => {
  console.log('familyNames', familyNames)
  familyNames.forEach((familyName) => {
    const fonts = config[familyName].fonts
    fonts.forEach(({ name, loadUrl, props }) => {
      loadUrl().then((url) => {
        if (Array.isArray(props)) {
          props.forEach((propSet) => addFont(name, url.default, propSet))
        } else {
          addFont(name, url.default, props)
        }
      })
    })
    const styles = config[familyName]?.styles || []
    styles.forEach((style) => {
      style().then((style) => {
        console.log('style', style)
      })
    })
  })
}

export default loadFonts
