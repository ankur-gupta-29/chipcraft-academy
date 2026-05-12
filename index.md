---
layout: home
title: "ChipCraft Academy — Learn Digital IC Design"
description: "Free tutorials, curated courses, and PDF guides on RTL, ASIC, VLSI, STA, and Verification for beginners."
permalink: /
---

<!-- Hero -->
<section class="hero">
  <div class="hero-badge">&#x26A1; Free Digital IC Design Education</div>
  <h1>Master Digital IC Design — From RTL to Silicon</h1>
  <p class="hero-subtitle">
    Free tutorials, curated courses, and step-by-step guides for engineers learning
    RTL design, ASIC flows, VLSI, STA, and Verification.
  </p>
  <div class="hero-actions">
    <a href="/blog" class="btn btn-primary">Start Learning &rarr;</a>
    <a href="/courses" class="btn btn-secondary">Browse Courses</a>
  </div>
  <div class="hero-stats">
    <div class="stat"><span class="stat-number">5+</span><span class="stat-label">Topic Areas</span></div>
    <div class="stat"><span class="stat-number">20+</span><span class="stat-label">Free Articles</span></div>
    <div class="stat"><span class="stat-number">100%</span><span class="stat-label">Free to Access</span></div>
  </div>
</section>

<!-- Topics -->
<section class="section" style="background: var(--bg-card); border-bottom: 1px solid var(--border);">
  <div class="container">
    <h2 class="section-title">What You'll Learn</h2>
    <p class="section-subtitle">Core topics in Digital IC Design, explained from first principles.</p>
    <div class="topics-grid">
      <a href="{{ '/blog' | relative_url }}?filter=RTL+Design" class="topic-card">
        <div class="topic-icon">&#128187;</div>
        <h3>RTL Design</h3>
        <p>Verilog & SystemVerilog from scratch</p>
      </a>
      <a href="{{ '/blog' | relative_url }}?filter=ASIC+Flow" class="topic-card">
        <div class="topic-icon">&#9881;</div>
        <h3>ASIC Flow</h3>
        <p>Synthesis, place & route, sign-off</p>
      </a>
      <a href="{{ '/blog' | relative_url }}?filter=Beginner" class="topic-card">
        <div class="topic-icon">&#128268;</div>
        <h3>VLSI</h3>
        <p>CMOS fundamentals & physical design</p>
      </a>
      <a href="{{ '/blog' | relative_url }}?filter=STA" class="topic-card">
        <div class="topic-icon">&#9201;</div>
        <h3>STA</h3>
        <p>Static timing analysis & constraints</p>
      </a>
      <a href="{{ '/blog' | relative_url }}?filter=Beginner" class="topic-card">
        <div class="topic-icon">&#9989;</div>
        <h3>Verification</h3>
        <p>UVM, testbenches & coverage</p>
      </a>
      <a href="{{ '/blog' | relative_url }}?filter=Beginner" class="topic-card">
        <div class="topic-icon">&#128312;</div>
        <h3>FPGA</h3>
        <p>Prototyping & FPGA vs ASIC trade-offs</p>
      </a>
    </div>
  </div>
</section>

<!-- Featured articles -->
<section class="section">
  <div class="container">
    <h2 class="section-title">Featured Articles</h2>
    <p class="section-subtitle">Start with these beginner-friendly guides.</p>
    <div class="post-grid">
      {% for post in site.posts limit:6 %}
      <article class="post-card">
        <span class="post-card-tag">{{ post.category | default: "Guide" }}</span>
        <h4><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h4>
        <p>{{ post.description | truncate: 110 }}</p>
        <span class="post-card-date">{{ post.date | date: "%b %d, %Y" }}</span>
      </article>
      {% endfor %}
    </div>
    <div style="text-align:center; margin-top:2rem;">
      <a href="/blog" class="btn btn-secondary">View All Articles &rarr;</a>
    </div>
  </div>
</section>

<!-- Newsletter CTA -->
<section class="newsletter-section">
  <h2>Stay up to date</h2>
  <p>Get new tutorials, course reviews, and free PDF guides delivered to your inbox.</p>
  <!-- Replace with your Mailchimp embed URL -->
  <form class="newsletter-form" action="https://YOUR-MAILCHIMP-ACTION-URL" method="post" target="_blank">
    <input type="email" name="EMAIL" placeholder="your@email.com" required>
    <button type="submit" class="btn btn-primary">Subscribe</button>
  </form>
</section>

<!-- Shop teaser -->
<section class="section" style="background: var(--bg-card); border-top: 1px solid var(--border);">
  <div class="container" style="text-align:center;">
    <h2>PDF Guides &amp; Cheat Sheets</h2>
    <p style="color: var(--text-muted); max-width:500px; margin: 0.5rem auto 2rem;">
      Structured, printable PDF guides to accelerate your learning — from RTL basics to full ASIC flows.
    </p>
    <a href="/shop" class="btn btn-primary">&#128218; Browse the Shop &rarr;</a>
  </div>
</section>
