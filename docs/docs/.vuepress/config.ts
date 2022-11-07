import { defineUserConfig } from 'vuepress'
import { defaultTheme } from '@vuepress/theme-default'

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
    sidebar: [{
      text: 'Guide',
      link: '/guide/',
      children: [
        {
          text: 'Getting Started',
          link: '/guide/README.md',
        },
        'Syntax',
        'Scripting',
        'Advanced',
      ]
    }]
  }),
  plugins: [
  ]
})
