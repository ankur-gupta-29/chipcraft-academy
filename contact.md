---
layout: page
title: Contact
description: "Get in touch with ChipCraft Academy — questions, topic requests, or feedback."
permalink: /contact/
---

<div class="contact-page">

<div class="contact-intro">
  <p>
    Have a question, a topic you'd like covered, a course suggestion, or found an error in one of the tutorials?
    I'd love to hear from you.
  </p>
</div>

## Ways to Reach Me

<div class="contact-cards">

  <div class="contact-card">
    <div class="contact-card-icon">&#9993;</div>
    <h3>Email</h3>
    <p>For questions, feedback, or collaboration enquiries.</p>
    <a href="mailto:{{ site.author.email }}" class="btn btn-primary">Send an Email</a>
  </div>

  <div class="contact-card">
    <div class="contact-card-icon">&#128218;</div>
    <h3>PDF Guides</h3>
    <p>Questions about a purchased guide? Contact via Gumroad.</p>
    <a href="{{ site.gumroad_url }}" target="_blank" rel="noopener" class="btn btn-secondary">Gumroad Store</a>
  </div>

  <div class="contact-card">
    <div class="contact-card-icon">&#128214;</div>
    <h3>Request a Topic</h3>
    <p>Want a tutorial on a specific IC design topic? Let me know.</p>
    <a href="mailto:{{ site.author.email }}?subject=Topic%20Request%20for%20ChipCraft%20Academy" class="btn btn-secondary">Request a Topic</a>
  </div>

</div>

---

## Frequently Asked Questions

**Can I use code from the tutorials in my projects?**  
Yes — all code examples on this site are free to use for personal and educational projects. Please credit ChipCraft Academy if you share them publicly.

**Do you accept guest posts?**  
Not at this time, but reach out if you have something interesting to share.

**I found a bug in the Verilog code. What should I do?**  
Email with the post title and the specific issue — I take correctness seriously and will fix it quickly.

**Can I request a topic for a future post?**  
Absolutely. Email or use the "Request a Topic" button above with as much detail as you like.

**Do you offer tutoring or consulting?**  
Not currently, but feel free to ask.

---

*Response time is usually within 48 hours on weekdays.*

</div>

<style>
.contact-page { max-width: 760px; margin: 0 auto; }
.contact-intro { font-size: 1.1rem; color: var(--text-muted); margin-bottom: 2rem; padding: 1.25rem; background: var(--bg-card); border-radius: var(--radius-lg); border-left: 3px solid var(--accent); }
.contact-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.25rem; margin: 1.5rem 0 2rem; }
.contact-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 1.5rem; text-align: center; display: flex; flex-direction: column; gap: 0.6rem; align-items: center; }
.contact-card-icon { font-size: 2rem; }
.contact-card h3 { font-size: 1rem; margin: 0; }
.contact-card p { color: var(--text-muted); font-size: 0.88rem; flex: 1; }
</style>
