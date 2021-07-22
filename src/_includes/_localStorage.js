// On page load or when changing themes, best to add inline in `head` to avoid FOUC
if (
  localStorage.theme === 'light' ||
  (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: light)').matches)
) {
  document.querySelector('html').classList.remove('dark')
  localStorage.theme = 'light'
} else {
  document.querySelector('html').classList.add('dark')
  localStorage.theme = 'dark'
}
