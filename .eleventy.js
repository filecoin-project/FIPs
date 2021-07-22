module.exports = (eleventyConfig) => {
  eleventyConfig.setBrowserSyncConfig({
    open: 'local', // launches localhost in browser on npm start
    ghostMode: false,
  })

  eleventyConfig.setUseGitIgnore(false)

  // copy static assets
  eleventyConfig.addPassthroughCopy('./src/assets')
  eleventyConfig.addPassthroughCopy('./src/styles')
  eleventyConfig.addPassthroughCopy('./src/scripts')

  return {
    dir: {
      input: 'src',
      output: 'dist',
    },
  }
}
