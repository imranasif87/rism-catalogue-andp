# RISM Catalogue Site Setup Documentation

## Level 1: High-Level Overview

Setting up and adapting a RISM catalogue site involves three primary phases. Because the theme relies on custom plugins not supported by default GitHub Pages, the environment requires a specific build configuration before content can be adapted.

* **Phase 1: Environment & Build Setup:** Forking the base repository and configuring a custom GitHub Actions workflow to successfully build the Jekyll site with required Ruby gems and theme dependencies.
* **Phase 2: Composer Adaptation:** Modifying the central configuration file to update site metadata and point the data pipeline to a new composer's API endpoint.
* **Phase 3: Advanced Customization (Optional):** Overriding specific theme files locally to extend the site's default functionality, such as adding new search facets to the browsing interface.

---

## Level 2: Detailed Instruction Set

Follow these steps chronologically to fork, configure, and customize the catalogue site. 

### Phase A: Environment Setup & Troubleshooting

1.  **Fork the repository:** Start by forking the base catalogue repository (e.g., the [Pollini example](https://github.com/rism-digital/rism-catalog-andp)).
2.  **Configure GitHub Pages:** Navigate to your repository settings and enable GitHub Pages, ensuring it is set to deploy via GitHub Actions.
3.  **Create a custom workflow:** Create the file `.github/workflows/jekyll.yml` to handle Ruby installation, gem installation, Jekyll building, and deployment.
4.  **Fix theme loading:** Open `_config.yml` and change the theme declaration from `remote_theme: rism-digital/rism-catalog-theme` to simply `theme: rism-catalog-theme`.
5.  **Correct the workflow matrix:** In your `.github/workflows/jekyll.yml` file, ensure the matrix specifically targets your exact repository name (e.g., `username/repository-name`).
6.  **Hardcode repository metadata:** Add `repository: username/repository-name` directly into your `_config.yml` to prevent metadata-related build failures.

### Phase B: Adapting the Site for a New Composer

7.  **Update site titles:** In `_config.yml`, modify the `title:` and `title_mobile:` fields to reflect the new composer across all supported languages.
8.  **Change the data source:** In `_config.yml`, update the `rism_catalog:` value (e.g., `"publications/123"`) to point to the desired dataset in the RISM API.
9.  **Fetch the new data:** Run `bundle exec jekyll load-data` locally to index the new composer's works and update the site's content.

### Phase C: Adding Custom Search Facets

*Note: Because the theme functions as a Ruby gem, you must override its internal files by recreating them at the exact same directory paths within your own repository.*

10. **Override the search panel HTML:** Copy `_includes/sidepanels/search.html` from the theme gem into your repository.
11. **Inject the new facet UI:** Inside your copied `search.html`, add a locale assignment variable at the top, and insert the new facet container `<div>` inside the form.
12. **Override the search JavaScript:** Copy `assets/js/search.js` from the theme gem into your repository.
13. **Update the JavaScript configuration:** Inside your copied `search.js`, add a DOM query for your new facet container, and add a new object for the facet inside the `facetConfigs` array.
14. **Add translation labels:** Open `_data/locales.yml` and add a new entry with the appropriate language translations for your newly created facet.
