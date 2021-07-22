// -----------------------------------------------------------------------------
// Constants
// -----------------------------------------------------------------------------

// -----------------------------------------------------------------------------
// Functions
// -----------------------------------------------------------------------------
const toggleTheme = () => {
  const themeLabel = document.getElementById('label')
  const isDark = localStorage.theme === 'dark'

  if (isDark) {
    document.querySelector('html').classList.remove('dark')
    localStorage.theme = 'light'
    themeLabel.innerHTML = '☀️'
  } else {
    document.querySelector('html').classList.add('dark')
    localStorage.theme = 'dark'
    themeLabel.innerHTML = '🌙'
  }
}

const initToggle = () => {
  const isDark = localStorage.theme === 'dark'
  const themeLabel = document.getElementById('label')
  themeLabel.innerHTML = isDark ? '🌙' : '☀️'
}

// -----------------------------------------------------------------------------
// Init App
// -----------------------------------------------------------------------------
initToggle()

const themeButton = document.getElementById('theme')
themeButton.addEventListener('click', (event) => {
  toggleTheme()
})
