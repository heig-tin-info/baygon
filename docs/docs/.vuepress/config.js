const { description } = require('../../package')

module.exports = {
  base: '/baygon/',
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#title
   */
  title: 'Baygon',
  /**
   * Ref：https://v1.vuepress.vuejs.org/config/#description
   */
  description: "Minimalistic functional test framework",

  /**
   * Extra tags to be injected to the page HTML `<head>`
   *
   * ref：https://v1.vuepress.vuejs.org/config/#head
   */
  head: [
    ['meta', { name: 'theme-color', content: '#5B3433' }],
    ['meta', { name: 'apple-mobile-web-app-capable', content: 'yes' }],
    ['meta', { name: 'apple-mobile-web-app-status-bar-style', content: 'black' }]
  ],

  /**
   * Theme configuration, here is the default theme configuration for VuePress.
   *
   * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
   */
  themeConfig: {
    repo: 'heig-tin-info/baygon',
    repoLabel: 'Contribute!',
    editLinks: false,
    docsDir: 'docs',
    editLinkText: '',
    lastUpdated: false,
    smoothScroll: true,
    nav: [
      {
        text: 'Guide',
        link: '/guide/',
      },
      {
        text: 'Baygon',
        link: 'https://pypi.org/project/baygon/'
      }
    ],
    sidebar: {
      '/guide/': [
        {
          title: 'Guide',
          collapsable: false,
          children: [
            '',
            'Syntax',
            'Advanced',
          ]
        }
      ],
    }
  },

  /**
   * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
   */
  plugins: [
    '@vuepress/plugin-back-to-top',
    '@vuepress/plugin-medium-zoom',
  ]
}
