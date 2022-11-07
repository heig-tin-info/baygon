import{_ as n,o as s,c as a,e as t}from"./app.348ed178.js";const p={},o=t(`<h1 id="scripting" tabindex="-1"><a class="header-anchor" href="#scripting" aria-hidden="true">#</a> Scripting</h1><p>You can use Baygon as a library to write your own test runner. This is useful if you want to write your own test runner or if you want to use Baygon in a CI/CD pipeline.</p><p>Here is an example of a test runner using Baygon:</p><div class="language-python" data-ext="py"><pre class="language-python"><code><span class="token keyword">from</span> pathlib <span class="token keyword">import</span> Path
<span class="token keyword">import</span> baygon

ts <span class="token operator">=</span> baygon<span class="token punctuation">.</span>TestSuite<span class="token punctuation">(</span><span class="token punctuation">{</span>
        <span class="token string">&#39;filters&#39;</span><span class="token punctuation">:</span> <span class="token punctuation">{</span><span class="token string">&#39;uppercase&#39;</span><span class="token punctuation">:</span> <span class="token boolean">True</span><span class="token punctuation">}</span><span class="token punctuation">,</span>
        <span class="token string">&#39;tests&#39;</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span>
            <span class="token string">&#39;args&#39;</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token string">&#39;--version&#39;</span><span class="token punctuation">]</span><span class="token punctuation">,</span>
            <span class="token string">&#39;stderr&#39;</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span><span class="token string">&#39;contains&#39;</span><span class="token punctuation">:</span> <span class="token string">&#39;VERSION&#39;</span><span class="token punctuation">}</span><span class="token punctuation">]</span>
        <span class="token punctuation">}</span><span class="token punctuation">]</span>
    <span class="token punctuation">}</span><span class="token punctuation">,</span> executable<span class="token operator">=</span>Path<span class="token punctuation">(</span><span class="token string">&#39;myapp&#39;</span><span class="token punctuation">)</span><span class="token punctuation">)</span>
t <span class="token operator">=</span> ts<span class="token punctuation">.</span>run<span class="token punctuation">(</span><span class="token punctuation">)</span>

<span class="token keyword">assert</span><span class="token punctuation">(</span>t<span class="token punctuation">,</span> <span class="token punctuation">[</span><span class="token punctuation">[</span><span class="token punctuation">]</span><span class="token punctuation">]</span><span class="token punctuation">)</span>
</code></pre></div><h2 id="validation" tabindex="-1"><a class="header-anchor" href="#validation" aria-hidden="true">#</a> Validation</h2><p>You can validate a Baygon configuration file with the <code>baygon.Schema</code> function:</p><div class="language-python" data-ext="py"><pre class="language-python"><code><span class="token keyword">import</span> baygon

data <span class="token operator">=</span> baygon<span class="token punctuation">.</span>Schema<span class="token punctuation">(</span><span class="token punctuation">{</span>
    <span class="token string">&#39;version&#39;</span><span class="token punctuation">:</span> <span class="token number">1</span><span class="token punctuation">,</span>
    <span class="token string">&#39;tests&#39;</span><span class="token punctuation">:</span> <span class="token punctuation">[</span><span class="token punctuation">{</span>
        <span class="token string">&#39;name&#39;</span><span class="token punctuation">:</span> <span class="token string">&#39;Test&#39;</span><span class="token punctuation">,</span>
        <span class="token string">&#39;exit&#39;</span><span class="token punctuation">:</span> <span class="token number">0</span>
    <span class="token punctuation">}</span><span class="token punctuation">]</span>
<span class="token punctuation">}</span><span class="token punctuation">)</span>

<span class="token keyword">assert</span><span class="token punctuation">(</span>data<span class="token punctuation">[</span><span class="token string">&#39;version&#39;</span><span class="token punctuation">]</span><span class="token punctuation">,</span> <span class="token number">1</span><span class="token punctuation">)</span>
</code></pre></div>`,7),e=[o];function c(u,i){return s(),a("div",null,e)}const k=n(p,[["render",c],["__file","scripting.html.vue"]]);export{k as default};
