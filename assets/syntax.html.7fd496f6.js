import{_ as a,o as n,c as s,e}from"./app.730162da.js";const t={},o=e(`<h1 id="config-file-syntax" tabindex="-1"><a class="header-anchor" href="#config-file-syntax" aria-hidden="true">#</a> Config File Syntax</h1><h2 id="base" tabindex="-1"><a class="header-anchor" href="#base" aria-hidden="true">#</a> Base</h2><p>Each config file should start with the version of the syntax which is <code>1</code>. Then the mandatory <code>tests</code> dictionary must exist. The following is a minimal example composed of 1 test which tests if the output is 3 when the binary is run with two arguments <code>1</code> and <code>2</code>:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span>
    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span>
</code></pre></div><h2 id="filters" tabindex="-1"><a class="header-anchor" href="#filters" aria-hidden="true">#</a> Filters</h2><p>Global filters can be applied to all outputs of every tests. The outputs are <code>stdout</code> and <code>stderr</code>. Baygon features the following filters:</p><ul><li><code>uppercase</code>: All outputs are transformed into uppercase.</li><li><code>lowercase</code>: All outputs are transformed into lowercase.</li><li><code>trim</code>: All outputs are trimmed (spaces are removed from both ends, on each line</li><li><code>ignore-spaces</code>: All spaces are removed from all outputs.</li><li><code>regex</code>: A remplacement is made using regular expressions.</li><li><code>replace</code>: A remplacement is made using a string.</li></ul><p>If more than one filter is applied, they are applied in the order they are written.</p><p>In the following, both standard output and standard error will be in lowercase and every occurrences of <code>foo</code> or <code>foobar</code> will be replaced by <code>bar</code>:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">filters</span><span class="token punctuation">:</span>
  <span class="token key atrule">lowercase</span><span class="token punctuation">:</span> <span class="token boolean important">true</span>
  <span class="token key atrule">regex</span><span class="token punctuation">:</span> <span class="token punctuation">[</span>foo(bar)<span class="token punctuation">?</span><span class="token punctuation">,</span> bar<span class="token punctuation">]</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span>
    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span>
</code></pre></div><h2 id="naming" tabindex="-1"><a class="header-anchor" href="#naming" aria-hidden="true">#</a> Naming</h2><p>All tests can be optionally named:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test functionality of the additionner
    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">-</span><span class="token punctuation">-</span>add<span class="token punctuation">,</span> <span class="token number">40</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span>
    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">42</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test error if less than two arguments
    <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">]</span>
    <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">2</span>
</code></pre></div><h2 id="groups-and-subgroups" tabindex="-1"><a class="header-anchor" href="#groups-and-subgroups" aria-hidden="true">#</a> Groups and subgroups</h2><p>Tests can be grouped into sub sections, by nesting each test into categories:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Category 1
    <span class="token key atrule">tests</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span>
        <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Category 2
    <span class="token key atrule">tests</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Subcategory 1
        <span class="token key atrule">tests</span><span class="token punctuation">:</span>
          <span class="token punctuation">-</span> <span class="token key atrule">args</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token number">1</span><span class="token punctuation">,</span> <span class="token number">2</span><span class="token punctuation">]</span>
            <span class="token key atrule">stdout</span><span class="token punctuation">:</span> <span class="token number">3</span>
</code></pre></div><h2 id="exit-status" tabindex="-1"><a class="header-anchor" href="#exit-status" aria-hidden="true">#</a> Exit status</h2><p>The exit status can be checked with the <code>exit</code> key followed with an integer. The following checks if the program returns 0</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span>
</code></pre></div><h2 id="standard-outputs" tabindex="-1"><a class="header-anchor" href="#standard-outputs" aria-hidden="true">#</a> Standard outputs</h2><p>Both <code>stdout</code> and <code>stderr</code> can be tested against multiple conditions:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span>
      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span>
    <span class="token key atrule">stderr</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar <span class="token comment"># Must be exactly equal to foobar</span>
</code></pre></div><h2 id="executable" tabindex="-1"><a class="header-anchor" href="#executable" aria-hidden="true">#</a> Executable</h2><p>In the case you want to specify a different executable name for a different test:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./foo
    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foo
    <span class="token key atrule">stdout</span><span class="token punctuation">:</span> I am Foo
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./bar
    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./bar
    <span class="token key atrule">stderr</span><span class="token punctuation">:</span> I am bar
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Group
    <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./baz
    <span class="token key atrule">tests</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test 1
        <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span>
</code></pre></div><p>The executable is propagated through the test tree. But you cannot override an existing executable. The following is invalid:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foo
    <span class="token key atrule">tests</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">executable</span><span class="token punctuation">:</span> ./bar
</code></pre></div><p>One approach is name the executable at the top level:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">version</span><span class="token punctuation">:</span> <span class="token number">1</span>
<span class="token key atrule">executable</span><span class="token punctuation">:</span> ./foobar
<span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">name</span><span class="token punctuation">:</span> Test ./foobar
    <span class="token key atrule">exit</span><span class="token punctuation">:</span> <span class="token number">0</span>
</code></pre></div><p>Or even from the shell:</p><div class="language-console" data-ext="console"><pre class="language-console"><code>baygon ./foobar
</code></pre></div><p>Note that the working directory is the directory of the config file, except if you specify the executable from the shell. In this case the working directory is the current directory.</p><h2 id="configuration-file" tabindex="-1"><a class="header-anchor" href="#configuration-file" aria-hidden="true">#</a> Configuration file</h2><p>By default Baygon will look for a file named <code>baygon.yml</code> in the current directory. You can specify a different file with the <code>-c</code> or <code>--config</code> option:</p><div class="language-console" data-ext="console"><pre class="language-console"><code>baygon --config other.yaml
</code></pre></div><p>Other names such as <code>t</code>, <code>test</code> or <code>tests</code> can be used, but the extension must be <code>.json</code>, <code>.yml</code> or <code>.yaml</code>. Here some valid configuration names:</p><div class="language-text" data-ext="text"><pre class="language-text"><code>baygon.yml
baygon.yaml
baygon.json
tests.yml
t.json
...
</code></pre></div><h2 id="tests-of-strings" tabindex="-1"><a class="header-anchor" href="#tests-of-strings" aria-hidden="true">#</a> Tests of strings</h2><p>Baygon currently features three type of tests :</p><ul><li><code>contains</code>: A string contained into the corresponding output.</li><li><code>regex</code>: A Python regular expression</li><li><code>equals</code>: An exact match</li></ul><p>You can combine any of the three tests together:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span>
      <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span>
      <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span>
      <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar
</code></pre></div><p>You can also add a negation with the <code>not</code> keyword:</p><div class="language-yaml" data-ext="yml"><pre class="language-yaml"><code><span class="token key atrule">tests</span><span class="token punctuation">:</span>
  <span class="token punctuation">-</span> <span class="token key atrule">stdout</span><span class="token punctuation">:</span>
      <span class="token key atrule">not</span><span class="token punctuation">:</span>
        <span class="token punctuation">-</span> <span class="token key atrule">contains</span><span class="token punctuation">:</span> foo <span class="token comment"># Must contain the word foo</span>
        <span class="token punctuation">-</span> <span class="token key atrule">regex</span><span class="token punctuation">:</span> f(oo<span class="token punctuation">|</span>aa<span class="token punctuation">|</span>uu) <span class="token comment"># Must match</span>
        <span class="token punctuation">-</span> <span class="token key atrule">equals</span><span class="token punctuation">:</span> foobar
</code></pre></div>`,44),p=[o];function c(l,u){return n(),s("div",null,p)}const r=a(t,[["render",c],["__file","syntax.html.vue"]]);export{r as default};
