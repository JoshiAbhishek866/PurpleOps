import { SitemapStream, streamToPromise } from "sitemap";
import { createWriteStream } from "fs";
import { resolve } from "path";

console.log("🗺️  Generating sitemap for PurpleOps...\n");

const sitemap = new SitemapStream({
  hostname: "https://PurpleOps.com",
});

// Define all your pages
const pages = [
  // Main pages
  {
    url: "/",
    changefreq: "daily",
    priority: 1.0,
    lastmod: new Date().toISOString(),
  },
  {
    url: "/about",
    changefreq: "monthly",
    priority: 0.8,
    lastmod: new Date().toISOString(),
  },
  {
    url: "/features",
    changefreq: "monthly",
    priority: 0.8,
    lastmod: new Date().toISOString(),
  },
  {
    url: "/pricing",
    changefreq: "weekly",
    priority: 0.9,
    lastmod: new Date().toISOString(),
  },

  // Blog
  {
    url: "/blog",
    changefreq: "daily",
    priority: 0.7,
    lastmod: new Date().toISOString(),
  },

  // Contact
  {
    url: "/contact",
    changefreq: "monthly",
    priority: 0.6,
    lastmod: new Date().toISOString(),
  },

  // Auth pages (if public)
  {
    url: "/auth/login",
    changefreq: "monthly",
    priority: 0.5,
    lastmod: new Date().toISOString(),
  },
  {
    url: "/auth/register",
    changefreq: "monthly",
    priority: 0.5,
    lastmod: new Date().toISOString(),
  },
];

// Write all pages to sitemap
pages.forEach((page) => {
  sitemap.write(page);
  console.log(`✓ Added: ${page.url}`);
});

sitemap.end();

// Generate and save sitemap
streamToPromise(sitemap)
  .then((data) => {
    const outputPath = resolve("./public/sitemap.xml");
    createWriteStream(outputPath).write(data);

    console.log("\n✅ Sitemap generated successfully!");
    console.log(`📄 Location: ${outputPath}`);
    console.log(`📊 Total URLs: ${pages.length}`);
    console.log("\n🚀 Next steps:");
    console.log("   1. Deploy your site");
    console.log("   2. Submit sitemap to Google Search Console");
    console.log("   3. URL: https://PurpleOps.com/sitemap.xml");
  })
  .catch((err) => {
    console.error("❌ Error generating sitemap:", err);
    process.exit(1);
  });
