import{_ as a,o as s,c as n,e}from"./app.348ed178.js";const t={},o=e(`<h1 id="advanced" tabindex="-1"><a class="header-anchor" href="#advanced" aria-hidden="true">#</a> Advanced</h1><h2 id="test-on-source-files" tabindex="-1"><a class="header-anchor" href="#test-on-source-files" aria-hidden="true">#</a> Test on source files</h2><p>You may want to execute tests on source files. This is possible by using <code>cat</code> as executable:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test function foo
    <span class="token key atrule">executable</span><span class="token punctuation">:</span> cat
    <span class="token key atrule">stdin</span><span class="token punctuation">:</span> foo.c
    <span class="token key atrule">stdout</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> void\\s+foo\\s<span class="token important">*\\(\\s*int\\s+\\w+\\)</span>
</code></pre></div>`,4),c=[o];function p(l,u){return s(),n("div",null,c)}const r=a(t,[["render",p],["__file","advanced.html.vue"]]);export{r as default};
