import typesense
import yaml


# ==== Configuration ==========================================================

# Configuration file:
with open("config.yml", "r", encoding="utf-8") as config:

    # Load config file:
    config_file = yaml.safe_load(config)

# ==== Variables ==============================================================

api_key = config_file["typesense_api_key"]
collection = config_file["collection_name"]
background_css = config_file["background_css"]
colour_background = config_file["colour_background"]
colour_background_accent = config_file["colour_background_accent"]
colour_background_accent_light = config_file["colour_background_accent_light"]
colour_background_accent_lighter = config_file["colour_background_accent_lighter"]
colour_primary_accent = config_file["colour_primary_accent"]
colour_results_list_divider = config_file["colour_results_list_divider"]
colour_text = config_file["colour_text"]
custom_image_filename = config_file["custom_image_filename"]
custom_image_height = config_file["custom_image_height"]
typesense_host = config_file["typesense_host"]
typesense_port = config_file["typesense_port"]

# ++++ HTML Template ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

html = f"""
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Start</title>
        <link rel="stylesheet" href="assets/css/stylesheet.css">
        <link rel="stylesheet" href="assets/css/line-awesome.css">
        <link rel="shortcut icon" href="assets/images/favicon.png" type="image/x-icon">
        <style>
           :root {{
              --colour_primary_accent: {colour_primary_accent};
              --background_css: {background_css};
              --colour_background: {colour_background};
              --colour_background_accent: {colour_background_accent};
              --colour_background_accent_lighter: {colour_background_accent_lighter};
              --colour_background_accent_light: {colour_background_accent_light};
              --colour_text: {colour_text};
              --colour_results_list_divider: {colour_results_list_divider};
              --custom_image_height: {custom_image_height};
            }}
        </style>
    </head>

    <body>
        <div id="wrapper">
            <header>
                <div id="start">
                    <h1 class="title">Start</h1>
                </div>
                <div id="symbol">
                    <img src="assets/images/{custom_image_filename}">
                </div>
            </header>

            <div id="searchbox"></div>
            <div id="refinement-list"></div>

            <ul id="results">
            </ul>

            <script src="https://cdn.jsdelivr.net/npm/instantsearch.js@4.43.0/dist/instantsearch.production.min.js"></script>
            <script src="https://cdn.jsdelivr.net/npm/typesense-instantsearch-adapter@2.4.2-1/dist/typesense-instantsearch-adapter.min.js"></script>
            <script src="./src/typesense_adaptor.js"></script>
            <script src="./src/instantsearch.js"></script>
        </div>
    </body>

</html>

"""
# ==== Initiate Typesense Client ==============================================

# Typesense client:
client = typesense.Client(
    {
        "api_key": f"{api_key}",
        "nodes": [
            {
                "host": f"{typesense_host}",
                "port": f"{typesense_port}",
                "protocol": "https",
            }
        ],
    }
)

# ==== Search API =============================================================

# search-only api key (can be public):
key_list = client.keys.retrieve()

# Delete any existing search-only api keys:
for key in key_list["keys"]:

    key_id = key["id"]

    client.keys[key_id].delete()

    print(f'Existing search-only key "{key_id}" deleted\n')

search_only_api_key = client.keys.create(
    {
        "description": "Search-only key",
        "actions": ["documents:search"],
        "collections": [collection],
    }
)

search_only_api_key_id = search_only_api_key["id"]
print(f'New search-only key "{search_only_api_key_id}" created\n')

search_only_api_key_value = search_only_api_key["value"]


typesense_instant_search = f"""
const typesenseInstantsearchAdapter = new TypesenseInstantSearchAdapter({{
  server: {{
    apiKey: '{search_only_api_key_value}', // Be sure to use an API key that only allows searches, in production
    nodes: [
      {{
        host: '{typesense_host}',
        protocol: 'https',
      }},
    ],
  }},
  // The following parameters are directly passed to Typesense's search API endpoint.
  //  So you can pass any parameters supported by the search endpoint below.
  //  queryBy is required.
  //  filterBy is managed and overridden by InstantSearch.js. To set it, you want to use one of the filter widgets like refinementList or use the `configure` widget.
  additionalSearchParameters: {{
    query_by: 'title,tags,url',
    sort_by: "title:asc",
    highlight_affix_num_tokens: 20,
    highlight_full_fields: 'title',
    snippet_threshold: 100,
  }},
}});
const searchClient = typesenseInstantsearchAdapter.searchClient;

const search = instantsearch({{
  searchClient,
  indexName: '{collection}',
  routing: true,
}});
"""


def load():

    """
    Load list of links to a Typesense collection
    """

    # Drop existing collection:
    try:
        client.collections[collection].delete()
        print(f'"{collection}" collection deleted!\n')
    except:
        print(f'"{collection}" collection doesn\'t exist, skipping...\n')

    # Create collection:
    client.collections.create(
        {
            "name": f"{collection}",
            "fields": [
                {"name": "title", "type": "string", "sort": True},
                {"name": "url", "type": "string"},
                {"name": "category", "type": "string", "facet": True},
                {"name": "tags", "type": "string[]"},
            ],
            "default_sorting_field": "title",
        }
    )
    print(f'"{collection}" created!\n')

    # Import links:
    with open(config_file["yaml_link_file"], "r", encoding="utf-8") as start_yaml:
        yaml_content = yaml.safe_load(start_yaml)

        client.collections[collection].documents.import_(
            yaml_content, {"action": "create"}
        )
        print(f'Links loaded to "{collection}" collection.\n')

    # Create typesense_adaptor.js file from template:
    with open(
        "public/src/typesense_adaptor.js", "w", encoding="utf-8"
    ) as typesense_adaptor:

        typesense_adaptor.write(typesense_instant_search)

    # Create index.html from template:
    with open("public/index.html", "w", encoding="utf-8") as html_index:

        html_index.write(html)


load()
