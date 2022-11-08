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
    docsDir: 'docs',
    editLinkText: '',
    lastUpdated: false,
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
        { text: 'Getting Started', link: '/guide/README.md' },
        { text: 'Syntax', link: '/guide/syntax.md' },
        { text: 'Scripting', link: '/guide/scripting.md' },
        { text: 'Advanced', link: '/guide/advanced.md' },
      ]
    }]
  }),
  plugins: [
  ]
})
