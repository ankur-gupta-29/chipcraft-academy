---
layout: page
title: Blog
description: "Tutorials, guides, and deep dives on Digital IC Design topics."
permalink: /blog/
---

<div class="blog-layout">
  <div class="blog-main">
    <div class="post-grid">
      {% for post in site.posts %}
      <article class="post-card">
        <span class="post-card-tag">{{ post.category | default: "Guide" }}</span>
        <h4><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h4>
        <p>{{ post.description | truncate: 120 }}</p>
        <span class="post-card-date">{{ post.date | date: "%B %d, %Y" }}</span>
      </article>
      {% endfor %}
    </div>
  </div>

  <aside class="blog-sidebar">
    <div class="sidebar-widget">
      <h4>Topics</h4>
      <div class="tag-cloud">
        <a href="#" class="tag">RTL Design</a>
        <a href="#" class="tag">ASIC</a>
        <a href="#" class="tag">VLSI</a>
        <a href="#" class="tag">STA</a>
        <a href="#" class="tag">Verification</a>
        <a href="#" class="tag">FPGA</a>
        <a href="#" class="tag">Verilog</a>
        <a href="#" class="tag">SystemVerilog</a>
        <a href="#" class="tag">UVM</a>
        <a href="#" class="tag">Beginner</a>
      </div>
    </div>

    <div class="sidebar-widget">
      <h4>Quick Links</h4>
      <ul style="padding-left:0;">
        <li style="margin-bottom:0.5rem;"><a href="/courses">&#127891; Recommended Courses</a></li>
        <li style="margin-bottom:0.5rem;"><a href="/resources">&#128196; Free Resources</a></li>
        <li style="margin-bottom:0.5rem;"><a href="/shop">&#128218; PDF Guides</a></li>
      </ul>
    </div>

    <!-- Sidebar AdSense -->
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
