const { src, dest, watch, parallel } = require('gulp')
const postcss = require('gulp-postcss')
const inlinesource = require('gulp-inline-source')
const htmlmin = require('gulp-htmlmin')

function css(done) {
  src('./src/postcss/*.css').pipe(postcss()).pipe(dest('./src/styles'))
  done()
}

function cssWatch() {
  watch('./src/postcss/*.css', css)
}

function inline() {
  return src('./dist/*.html')
    .pipe(htmlmin({ collapseWhitespace: true }))
    .pipe(inlinesource())
    .pipe(dest('./dist'))
}

exports.build = inline
exports.css = css
exports.cssWatch = parallel(css, cssWatch)
