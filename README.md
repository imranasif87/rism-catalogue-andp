# Forking and Running the RISM Catalogue (Pollini) : A Troubleshooting Story

This repository documents the steps required to successfully fork and deploy a RISM catalogue site based on the Pollini example. The process was not straightforward — several build errors appeared, and each required investigation and fixes. This guide tells the story step-by-step so future users can avoid the same issues.

---

# Stage 1 — Forking the Repository

The task began by forking the Pollini repository and enabling GitHub Pages. The expectation was that the fork would behave exactly like the original site.

However, after enabling GitHub Pages, the site **failed to build**.

---

# First Error — Missing `static_href`

The initial build failed with a Liquid error similar to:

```
Liquid Exception: undefined tag 'static_href'
```

This happened because GitHub Pages' default Jekyll build **does not support custom plugins** used by the RISM theme.

### Fix

We switched from GitHub Pages default build to a **custom GitHub Actions workflow** that installs dependencies and builds using Bundler.

---

# Second Error — Missing workflow in parent repository

We expected the parent repository to contain a `.github/workflows` folder, but it did not exist. This meant we had to create our own workflow file.

A custom workflow (`.github/workflows/jekyll.yml`) was created to:

* install Ruby
* install gems
* build Jekyll
* deploy to GitHub Pages

This allowed plugin support.

---

# Third Error — Missing include file

After the workflow started working, the build failed again:

```
Liquid Exception: Could not locate the included file 'theme-info.md'
```

This indicated that the theme expected an include file that did not exist in the fork.

### Temporary Fix

We created:

```
_includes/theme-info.md
```

But shortly after, a better solution was discovered.

---

# Better Fix — Switching from `remote_theme` to `theme`

Instead of using:

```
remote_theme: rism-digital/rism-catalog-theme
```

we switched to:

```
theme: rism-catalog-theme
```

This allowed Bundler to load the theme, which resolved include path issues automatically.

After this change, the site built successfully.

---

# Advanced Workflow Setup

To support catalog builds similar to production, a more complex workflow was introduced. This workflow:

* builds catalogs dynamically
* loads API data
* assembles a multi-catalog site
* deploys to GitHub Pages

However, this introduced another error.

---

# Fourth Error — Repository Metadata Missing

The build failed with:

```
No repo name found. Specify using PAGES_REPO_NWO environment variables,
'repository' in your configuration, or set up an 'origin' git remote
```

This occurred because the workflow matrix referenced the wrong repository name.

The workflow contained:

```
repo: imranasif87/rism-catalogue-andp
```

But the actual repository was:

```
imranasif8/rism-catalogue-andp
```

### Fix

We updated the workflow matrix:

```
matrix:
  catalog:
    - repo: imranasif8/rism-catalogue-andp
      target: AndP
```

---

# Final Stability Fix

To ensure the theme always detects repository metadata, we added this to `_config.yml`:

```
repository: imranasif8/rism-catalogue-andp
```

This prevents metadata-related build failures.

---

# Final Working Setup

After all fixes:

* GitHub Actions builds successfully
* Jekyll loads plugins correctly
* Theme renders properly
* API data loads
* Works list and facets function
* Pages deploy automatically

---

# Steps to Follow When Forking

1. Fork the repository
2. Enable GitHub Actions for Pages
3. Ensure `.github/workflows/jekyll.yml` exists
4. Use `theme:` instead of `remote_theme`
5. Update workflow matrix repo name
6. Add repository entry in `_config.yml`
7. Push changes
8. Wait for GitHub Actions to deploy

---

# Result

The fork behaves identically to the original Pollini site:

* styling preserved
* landing page works
* works list loads
* search and facets work
* work detail pages display correctly

This completes Stage 1 of the RISM catalogue setup.

# Stage 2 — Adapting the Catalogue for a Different Composer

After successfully deploying the forked Pollini catalogue, the next step was to adapt the site for a different composer. The goal was to keep the structure and functionality intact while switching the data source and metadata.

For this example, the catalogue was adapted for **Henry Purcell**.

---

## Updating `_config.yml`

The adaptation was done entirely through the `_config.yml` file. The title and mobile title were updated to reflect the new composer:

```yaml
title: 
 en: Catalog of the Works of Henry Purcell (ZimP)
 it: Catalogo delle opere di Henry Purcell (ZimP)

title_mobile: 
  en: Works of Henry Purcell (ZimP)
  it: Opere di Henry Purcell (ZimP)
```

---

## Changing the Data Source

The most important change was updating the `rism_catalog` value. This parameter controls which dataset is loaded from the API.

```yaml
rism_catalog: "publications/123"
```

After this change, the indexing step:

```bash
bundle exec jekyll load-data
```

automatically fetched works for Henry Purcell instead of Pollini.

---

## Repository Metadata

To ensure correct GitHub metadata resolution during build, the repository field remained explicitly defined:

```yaml
repository: imranasif8/rism-catalogue-andp
```

This prevents the following build error from reappearing:

```
No repo name found. Specify using PAGES_REPO_NWO...
```

---

## Result

After committing and pushing the changes:

* The landing page title updated to Henry Purcell
* The works list loaded Purcell records
* Facets continued to work correctly
* Work detail pages opened normally
* GitHub Pages deployed without errors

This confirms that adapting the catalogue to a new composer only requires:

1. Updating titles
2. Changing `rism_catalog`
3. Keeping repository metadata intact

The catalogue is now fully configured for Henry Purcell.

# Stage 3 — Customising Faceted Browsing (Adding a Scoring Facet)

After successfully deploying the catalogue for a different composer, the next task was to extend the faceted browsing to include a new facet for **scoring summary** (the instruments playing in each work).

---

## The Problem: No Documentation for Adding Facets

The RISM Catalogue Theme README only documents how to **exclude** facets using `_data/search_config.yml`:

```yaml
exclude:
  - keyMode
  - relationship
  - subject
  - dateRange
```

There is no documented way to **add** a new facet. The theme is installed as a Ruby gem, which means its internal files are not directly visible or editable in the catalog repository.

This required investigating how the facet system actually works under the hood.

---

## Investigation

By reading the theme's TypeScript source file (`src/search.ts` on the theme's GitHub repository), it became clear that the entire facet system is driven by a single `facetConfigs` array in the compiled JavaScript:

```javascript
const facetConfigs = [
    { name: "keyMode",      field: "keyMode",      container: facetKeyMode },
    { name: "relationship", field: "relationship",  container: facetRelationship },
    { name: "subject",      field: "subject",       container: facetSubject }
];
```

Every part of the pipeline — filtering, URL parameter parsing, aggregating counts, and rendering checkboxes — loops over this array generically. This means adding a new facet only requires:

1. Adding a new entry to `facetConfigs` in the JS
2. Adding a corresponding DOM element in the search HTML
3. Adding a label in the locales file

Crucially, `scoringSummary` is **already indexed** by the `load-data` command — the README lists it as an indexed field. So no re-indexing was needed.

---

## The Approach: Override Theme Files

Because the theme is a gem, its files cannot be edited directly. However, Jekyll has a well-defined override mechanism: **any file placed in your repository at the same path as a theme file takes precedence**.

Two files were copied out of the gem and placed in the catalog repository with modifications.

---

## File 1 — `_includes/sidepanels/search.html`

This file controls the left-hand sidebar on the search page, including all the facet UI. The original file from the theme was copied into the repository at:

```
_includes/sidepanels/search.html
```

Two additions were made.

**Add the locale assignment** at the top alongside the existing ones:

```liquid
{% assign search_facet_scoring_summary = site.data.locales | where: "id", "search-facet-scoring-summary" | first %}
```

**Add the facet container div** in the form, right after the `keyMode` block:

```liquid
{% unless excluded_facets contains "scoringSummary" %}
<h2 class="mt-3">{{ search_facet_scoring_summary.name[site.active_lang] | default: "Scoring" }}</h2>
<div id="facet-scoring-summary" class="mt-2 scroll-facet"></div>
{% endunless %}
```

This follows exactly the same pattern as the existing facets — a locale-driven heading and a div whose `id` the JavaScript targets to populate checkboxes.

---

## File 2 — `assets/js/search.js`

The compiled JavaScript from the theme gem was copied into the repository at:

```
assets/js/search.js
```

Two additions were made.

**Add the DOM query** alongside the existing facet queries:

```javascript
let facetKeyMode = document.querySelector("#facet-key-mode");
let facetRelationship = document.querySelector("#facet-relationship");
let facetSubject = document.querySelector("#facet-subject");
let facetScoringSummary = document.querySelector("#facet-scoring-summary"); // ← ADDED
let facetDateFromInput = document.querySelector("#facet-date-from");
```

**Add the entry to `facetConfigs`**:

```javascript
const facetConfigs = [
    {
        name: "keyMode",
        field: "keyMode",
        container: facetKeyMode
    },
    {
        name: "scoringSummary",       // ← ADDED
        field: "scoringSummary",
        container: facetScoringSummary
    },
    {
        name: "relationship",
        field: "relationship",
        container: facetRelationship
    },
    {
        name: "subject",
        field: "subject",
        container: facetSubject
    }
];
```

Because all filtering, URL parameter handling, and rendering is already generic over `facetConfigs`, no further changes to the JavaScript were needed.

---

## File 3 — `_data/locales.yml`

A label entry was added for the new facet alongside the existing ones:

```yaml
- id: search-facet-scoring-summary
  name:
    en: Scoring
    it: Organico
```

---

## Result

After committing and pushing these changes:

* The works list sidebar displays a **Scoring** facet below the Key facet
* The scoring options shown are drawn directly from the data — only values that exist in the indexed works appear
* Selecting a scoring value filters the results list correctly
* The facet respects the `exclude` mechanism — adding `scoringSummary` to `search_config.yml` would hide it
* All existing facets and search behaviour remain unchanged

This completes Stage 3 of the RISM catalogue setup.
