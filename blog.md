---
layout: page
title: Blog
description: "Tutorials, guides, and deep dives on Digital IC Design topics."
permalink: /blog/
---

<!-- Search + Filter bar -->
<div class="blog-controls">
  <div class="blog-search-wrap">
    <span class="search-icon">&#128269;</span>
    <input type="text" id="blog-search" placeholder="Search articles…" autocomplete="off">
    <button id="blog-search-clear" aria-label="Clear search" style="display:none;">&#x2715;</button>
  </div>
  <div class="filter-bar" id="filter-bar">
    <button class="filter-btn active" data-filter="all">All</button>
    {% assign cats = site.posts | map: "category" | uniq | sort %}
    {% for cat in cats %}{% if cat %}
    <button class="filter-btn" data-filter="{{ cat }}">{{ cat }}</button>
    {% endif %}{% endfor %}
  </div>
</div>

<!-- Results count -->
<p class="blog-count" id="blog-count"></p>

<div class="blog-layout">
  <div class="blog-main">
    <div class="post-grid" id="post-grid">
      {% for post in site.posts %}
      <article class="post-card"
               data-category="{{ post.category }}"
               data-tags="{{ post.tags | join: ' ' }}"
               data-title="{{ post.title | downcase }}"
               data-desc="{{ post.description | downcase }}">
        <div class="post-card-meta">
          <span class="post-card-tag cat-{{ post.category | slugify }}">{{ post.category | default: "Guide" }}</span>
          <span class="post-card-date">{{ post.date | date: "%b %d, %Y" }}</span>
        </div>
        <h4><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h4>
        <p>{{ post.description | truncate: 120 }}</p>
        <div class="post-card-tags">
          {% for tag in post.tags limit:4 %}
          <button class="tag tag-filter" data-tag="{{ tag }}">{{ tag }}</button>
          {% endfor %}
        </div>
      </article>
      {% endfor %}
    </div>
    <p class="no-results" id="no-results" style="display:none;">
      No articles match that search. Try a different keyword or category.
    </p>
  </div>

  <aside class="blog-sidebar">
    <div class="sidebar-widget">
      <h4>Categories</h4>
      <ul class="sidebar-cat-list">
        {% assign cats = site.posts | map: "category" | uniq | sort %}
        {% for cat in cats %}{% if cat %}
        {% assign count = site.posts | where: "category", cat | size %}
        <li>
          <button class="sidebar-cat-btn" data-filter="{{ cat }}">
            {{ cat }} <span class="cat-count">{{ count }}</span>
          </button>
        </li>
        {% endif %}{% endfor %}
      </ul>
    </div>

    <div class="sidebar-widget">
      <h4>&#128506; Learning Path</h4>
      <p style="font-size:0.85rem;color:var(--text-muted);margin-bottom:0.75rem;">New here? Follow our guided roadmap.</p>
      <a href="{{ '/learning-path' | relative_url }}" class="btn btn-primary" style="display:block;text-align:center;font-size:0.85rem;padding:0.5rem 1rem;">View Roadmap &rarr;</a>
    </div>

    <div class="sidebar-widget">
      <h4>&#128293; Popular Articles</h4>
      <ul style="padding-left:0;list-style:none;">
        <li style="margin-bottom:0.6rem;font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-17-verilog-interview-questions %}">50 Interview Questions</a></li>
        <li style="margin-bottom:0.6rem;font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-17-setup-hold-time-sta %}">Setup & Hold Time (STA)</a></li>
        <li style="margin-bottom:0.6rem;font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-17-fsm-design-verilog %}">FSM Design in Verilog</a></li>
        <li style="margin-bottom:0.6rem;font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-17-clock-domain-crossing %}">Clock Domain Crossing</a></li>
        <li style="margin-bottom:0.6rem;font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-12-riscv-single-cycle-verilog %}">RISC-V CPU in Verilog</a></li>
        <li style="font-size:0.85rem;"><a href="{{ site.baseurl }}{% post_url 2026-05-17-synopsys-design-compiler %}">Design Compiler Guide</a></li>
      </ul>
    </div>

    <div class="sidebar-widget">
      <h4>Quick Links</h4>
      <ul style="padding-left:0;">
        <li style="margin-bottom:0.5rem;"><a href="{{ '/courses' | relative_url }}">&#127891; Recommended Courses</a></li>
        <li style="margin-bottom:0.5rem;"><a href="{{ '/resources' | relative_url }}">&#128196; Free Resources</a></li>
        <li style="margin-bottom:0.5rem;"><a href="{{ '/shop' | relative_url }}">&#128218; PDF Guides</a></li>
      </ul>
    </div>

    {% if site.adsense_client %}
    <div class="sidebar-widget" style="padding:0.5rem;">
      <ins class="adsbygoogle"
           style="display:block"
           data-ad-client="{{ site.adsense_client }}"
           data-ad-slot="{{ site.adsense_slot }}"
           data-ad-format="auto"
           data-full-width-responsive="true"></ins>
      <script>(adsbygoogle = window.adsbygoogle || []).push({});</script>
    </div>
    {% endif %}
  </aside>
</div>

<script>
(function () {
  const grid      = document.getElementById('post-grid');
  const cards     = Array.from(grid.querySelectorAll('.post-card'));
  const searchIn  = document.getElementById('blog-search');
  const clearBtn  = document.getElementById('blog-search-clear');
  const countEl   = document.getElementById('blog-count');
  const noResults = document.getElementById('no-results');
  let activeFilter = 'all';

  function updateCount(n) {
    countEl.textContent = n === cards.length ? '' : n + ' of ' + cards.length + ' articles';
  }

  function applyFilters() {
    const q = searchIn.value.trim().toLowerCase();
    clearBtn.style.display = q ? 'inline' : 'none';
    let visible = 0;
    cards.forEach(function (c) {
      const catMatch  = activeFilter === 'all' || c.dataset.category === activeFilter;
      const textMatch = !q || c.dataset.title.includes(q) || c.dataset.desc.includes(q) || c.dataset.tags.includes(q);
      const show = catMatch && textMatch;
      c.style.display = show ? '' : 'none';
      if (show) visible++;
    });
    noResults.style.display = visible === 0 ? '' : 'none';
    updateCount(visible);
  }

  // Category filter buttons (top bar + sidebar)
  function setFilter(val) {
    activeFilter = val;
    document.querySelectorAll('.filter-btn, .sidebar-cat-btn').forEach(function (b) {
      b.classList.toggle('active', b.dataset.filter === val || (val === 'all' && b.dataset.filter === 'all'));
    });
    applyFilters();
  }

  document.getElementById('filter-bar').addEventListener('click', function (e) {
    if (e.target.classList.contains('filter-btn')) setFilter(e.target.dataset.filter);
  });
  document.querySelectorAll('.sidebar-cat-btn').forEach(function (b) {
    b.addEventListener('click', function () { setFilter(b.dataset.filter); });
  });

  // Tag pills inside post cards
  grid.addEventListener('click', function (e) {
    if (e.target.classList.contains('tag-filter')) {
      searchIn.value = e.target.dataset.tag;
      setFilter('all');
      applyFilters();
    }
  });

  // Search
  searchIn.addEventListener('input', applyFilters);
  clearBtn.addEventListener('click', function () { searchIn.value = ''; applyFilters(); searchIn.focus(); });

  // Support ?filter=RTL+Design in the URL (from homepage topic cards)
  const params = new URLSearchParams(window.location.search);
  const urlFilter = params.get('filter') || params.get('tag');
  if (urlFilter) setFilter(urlFilter);
  else updateCount(cards.length);
})();
</script>
