# ChipCraft Academy

A free Digital IC Design education website built with Jekyll and hosted on GitHub Pages.

**Live site:** https://yourusername.github.io/digital-IC-Course

## Topics Covered
- RTL Design (Verilog / SystemVerilog)
- ASIC Design Flow
- VLSI Fundamentals
- Static Timing Analysis (STA)
- Functional Verification & UVM

## Tech Stack
- **Framework:** Jekyll (GitHub Pages built-in)
- **Hosting:** GitHub Pages (free)
- **Payments:** Gumroad (10% fee on sales only)
- **Ads:** Google AdSense
- **Analytics:** Google Analytics 4
- **Email:** Mailchimp

## Local Development

```bash
# Install dependencies
gem install bundler
bundle install

# Run dev server
bundle exec jekyll serve --livereload

# Open http://localhost:4000
```

## Deployment

Push to the `main` branch. GitHub Pages builds and deploys automatically.

Go to **Settings → Pages → Source: Deploy from branch → main / (root)**.

## Configuration

Edit `_config.yml` and replace these placeholders before going live:

| Key | What to replace |
|-----|----------------|
| `url` | Your GitHub Pages URL |
| `baseurl` | Your repo name |
| `adsense_client` | Your AdSense publisher ID (`ca-pub-XXXX`) |
| `adsense_slot` | Your AdSense ad slot ID |
| `google_analytics` | Your GA4 measurement ID (`G-XXXX`) |
| `gumroad_url` | Your Gumroad store URL |
| `author.email` | Your contact email |

## Monetization Setup

### AdSense
1. Apply at [Google AdSense](https://adsense.google.com)
2. Add your site for review
3. Once approved, replace `ca-pub-XXXXXXXXXXXXXXXX` in `_config.yml`
4. Ads render automatically in the header, sidebar, and in-article slots

### Gumroad
1. Create account at [gumroad.com](https://gumroad.com)
2. Upload PDF products
3. Replace `PRODUCT_ID` placeholders in `shop.md` with real product IDs
4. Update `gumroad_url` in `_config.yml`

### Affiliate Links
- **Udemy:** Join [Udemy Affiliates](https://www.udemy.com/affiliate/) and replace `AFFILIATE_CODE` in `courses.md`
- **Coursera:** Join [Coursera for Partners](https://www.coursera.org/business/partners/)

### Mailchimp Newsletter
1. Create account at [mailchimp.com](https://mailchimp.com)
2. Create an audience + embedded form
3. Replace the `action` URL in `index.md` newsletter form

## File Structure

```
.
├── _config.yml          # Site configuration
├── _layouts/
│   ├── default.html     # Base layout (nav, footer, AdSense)
│   ├── home.html        # Homepage
│   ├── post.html        # Blog post (with in-article ad, Gumroad CTA)
│   └── page.html        # Static pages
├── _posts/              # Blog articles (5 included)
├── assets/
│   ├── css/main.css     # Dark theme stylesheet
│   └── js/main.js       # Nav toggle, lazy ads, smooth scroll
├── index.md             # Homepage
├── about.md             # About page
├── blog.md              # Blog listing
├── courses.md           # Curated courses + affiliate links
├── shop.md              # Gumroad PDF guide listings
└── resources.md         # Free tools and resources
```

## License

Content: All rights reserved.  
Code/template: MIT License.
