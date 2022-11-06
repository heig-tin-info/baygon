import { defineUserConfig } from 'vuepress'
import { defaultTheme } from '@vuepress/theme-default'

import { backToTopPlugin } from '@vuepress/plugin-back-to-top'
import { mediumZoomPlugin } from '@vuepress/plugin-medium-zoom'
// import { docsearchPlugin } from '@vuepress/plugin-docsearch'

export default defineUserConfig({
  base: '/baygon/',
  lang: 'en-US',
  title: 'Baygon',
  description: "Minimalistic functional test framework",
  markdown: {
    code: {
        lineNumbers: false
    }
  },
  theme: defaultTheme({
    repo: 'heig-tin-info/baygon',
    repoLabel: 'Contribute!',
    editLinks: false,
    docsDir: 'docs',
    editLinkText: '',
    lastUpdated: false,
    smoothScroll: true,
    navbar: [
        {
          text: 'Guide',
          link: '/guide/',
        },
        {
          text: 'Baygon',
          link: 'https://pypi.org/project/baygon/'
        }
      ],
      // sidebar: {
      //   '/guide/': [
      //     {
      //       title: 'Guide',
      //       collapsable: true,
      //       children: [
      //         '',
      //         'Syntax',
      //         'Advanced',
      //       ]
      //     }
      //   ],
      // },
  }),
  plugins: [
    // backToTopPlugin(),
    // mediumZoomPlugin(),
    // docsearchPlugin({

    // })

  ]
})
