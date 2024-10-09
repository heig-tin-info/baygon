import { defineUserConfig } from 'vuepress'
import { defaultTheme } from '@vuepress/theme-default'
import { viteBundler } from '@vuepress/bundler-vite'

export default defineUserConfig({
  base: '/',  // Ou '/baygon/' si tu déploies dans un sous-dossier
  lang: 'en-US',
  title: 'Baygon',
  description: "Minimalistic functional test framework",
  bundler: viteBundler({
    viteOptions: {},
    vuePluginOptions: {},
  }),
  theme: defaultTheme({
    repo: 'heig-tin-info/baygon',
    docsDir: 'docs',  // Assure-toi que cela correspond à ton répertoire source
    navbar: [
      { text: 'Guide', link: '/guide/' },
      { text: 'Baygon', link: 'https://pypi.org/project/baygon/' },
    ],
    sidebar: [
      {
        text: 'Guide',
        link: '/guide/',
        children: [
          { text: 'Getting Started', link: '/guide/' },
          { text: 'Syntax', link: '/guide/syntax.md' },
          { text: 'Scripting', link: '/guide/scripting.md' },
          { text: 'Advanced', link: '/guide/advanced.md' },
        ],
      },
    ],
  }),
})
