To further the development of the first script or scripts, the first goal is to analyze the "report_title_short" values for each document in the collections "markets_raw". These titles nseed to be used to identify topics, and when present, regions, and insert them back into the document as separate items.

For example, for the "topic" and "topicName" definition:
- You might see a title like this in the key "report_title_short": "Automotive Steel Wheels Market Size & Share Report, 2030"
	- The objective is to find: "Automotive Steel Wheels"
	- And exclude: "Market Size & Share Report, 2030"
	- So the final "topic" value would be (normalized): "automotive-steel-wheels"
	- And the final "topicName" would be: "Automotive Steel Wheels"
	- You might want to consider using "report_slug" as a hint, but there may be missing information in the slug as well as information that must be excluded, so be careful using this.

Additionally, for the "regions" definition:
- - You might see a title like this in the key "report_title_short": "APAC & Middle East Personal Protective Equipment Market Report, 2030"
	- The objective is to find: "APAC & Middle East"
	- And exclude: "Personal Protective Equipment" and "Market Report, 2030"
	- So the final "regions" value would be a JSON array of the countries or regions identified: "APAC" and "Middle East"
	- You might want to consider using "report_slug" as a hint, but there may be missing information in the slug as well as information that must be excluded, so be careful using this.

The two examples above are extremely simple -- there are much more complex scenarios in the collection. I've previously tried to develop tools to do this that I can share as a reference.
- Please analyze the @/resources/json-transformer directory.
- The README.md file explains much of the intent behind the scripts and how to handle some of the more complex scenarios.
- The /config directory includes some of the attempts to isolate the sccenarios.
- As you analyze the scripts in the main directory, you'see some of the config files used to try and navigate the complexity.
- The region_mappings.json file in the config directory was a backstop to try and help the script handle edge cases, abbreviations, abbreviations with and without punctuation, etc. Even with the sPacy "en_core_web_md" model, we still needed the region_mappings.json to help out. **IMPORTANT: I need to avoid this aproach.**
- As you can see, it was very difficult. **DO NOT** use any of this code, just analyze it to see what some of the scenarios were that present challenges and learn about the overall objective.

More complex examples include ("report_title_short" values):
- "Global Grilling Tools and Accessories Aftermarket Market in Outdoor Camping Gear Market, Trends, and Analysis 2025"
	- This one is more complex. This would be the breakdown:
		- "topic": "global-grilling-tools-and-accessories-aftermarket"
		- "topicName": "Global Grilling Tools and Accessories Aftermarket"
		- Excluded: "Market in Outdoor Camping Gear Market, Trends, and Analysis 2025"
	- Note the "Market in" portion of this title. As you'll see in the example code I've provided as a resource, there are a couple of market terms that we had to define in the @/resources/json-transformer/config/market_terms.json file to try and identiy, isolate, and exclude such as "Market in" and "Market for".
	Also note that "Global" in this case is considered a region.
- "Ammonium Sulfate Market for Mining and Construction, Study and Trends 2021-2031"
	- "topic": "ammonium-sulfate-for-mining-and-construction"
	- "topicName": "Ammonium Sulfate for Mining and Construction"
	- Excluded: ", Study and Trends 2021-2031" and "Market " from the "Market for" phrase.
	- Note that in this case, the market_term "Market for" is in the middle of the text needed to be assembled for the topic and topicName and the "for" needs to be retained as the separator.
- "Germany, Belgium and Netherlands Laboratory Consumables Market"
	- "topic": "laboratory-consumables"
	- "topicName": "Laboratory Consumables"
	- "regions":  [Germany, Belgium, Netherlands]
	- Excluded: "Market"
	- Note that there is an "and" separator in the midding of the regions being extracted. Additionally, there is no comma after "Belgium" and the final region "and Netherlands". These types of separator workds need to be handled.
- "Europe Roller Shades or Blinds Market"
	- "topic": "roller-shades-or-blinds"
	- "topicName": "Roller Shades or Blinds"
	- "regions":  [Europe]
	- Excluded: "Market"
	- Note that "Europe" is a region. Other might include "APAC", "ASEAN", "MEA", "EMEA", etc. In the example files you'll see @/resources/json-transformer/config/region_mappings.json which has some of our initial attempts to handle all the region names and normalize to a canonical name. **IMPORTANT: I need our new script to try and avoid storing lists like this becuase new titles will come with new terms. So, we need to find a way to hanlde this more dynamically, or find a way to dynamically maintain a list like this that can be referenced for easy fust analysis of r "report_title_short" value but not rely on it exclusively. There needs to be anoter layer of analysis that can identify new region names that may not be in the list, extract them for the "regions" array, and update the source list. This needs to be a more dynamic approach. we can use a database to maintain these as needed, but the detection needs to be dynamic to find new region names.**
- "U.S. Liposomal Vitamins and Minerals Market"
	- "topic": "liposomal-vitamins-and-minerals"
	- "topicName": "Liposomal Vitamins and Minerals"
	- "regions":  [UUnited States]
	- Excluded: "Market"
	- Note the "U.S." abbreviation that needs to be detected and then normalized to a canonical region name "United States".
- "Floating Liquefied Natural Gas (FLNG) Terminals Market, Trends, and Analysis 2023"
	- "topic": "floating-liquefied-natural-gas-flng-terminals"
	- "topicName": "Floating Liquefied Natural Gas (FLNG) Terminals"
	- Excluded: "Market, Trends, and Analysis 2023"
	- Note the acronym "(FLNG)" which needs to remain as it appears in the "report_title_short" value with the parentheses and all capitalized version for "topicName", but also included normalized in "topic" in lower case without the parentheses.

Pay close attention in the complex examples above that elements like spaces, ending punctuation following a region ("U.S. "), and separator words ("and") between regions add additional complexity for handling. 

Additionally, we need to create a base set of countires and regions as the canonical names. For example, the script might find "US", "U.S.", "U.S" (a typo missing the closing punctuation), "United States", "USA", "U.S.A.", "United States of America", "United States Of America", etc. which all need to be normalized in the "regions" to something like "United States".

Here are some approaches and requirements that need to be addressed in the solution:
- For regions, we can't just keep a big list of countries or regions. That won't be flexible enough unless it is highly dynamic and updateable, we need more intelligent analysis. 
- One approach I've found reasonably successful in the past is to use an entity extraction model, such as sPacy (https://spacy.io/models/en). I've found "en_core_web_md" to be fairly good at helping identify geographical regions and locations through NER identification. It's possible that the "en_core_web_lg" or "en_core_web_trf" models will do even better. However, "en_core_web_md" did struggle at times with variations of abbreivations that may appear and I had to do a lot of experimentation on normalizing or not normalizing the source text in "report_title_short" before NER analysis to get it to work. So, this could be an entry point, but we probably need something more sophisticated that is more accurate and does not require storing a list of all the possible counties, regions, GPE areas, etc. unless the list is highly dynamic. Otherwise, a static, manual list is just unmanagable.
- As you'll see in the example script I provided from my past attempt, there were a lot of complex scenarios to get the topic, topciName, and regions properly extracted from the "report_title_short".
- There are also other considerations where the "report_title_short" also includes an abbreivation of the topic like "(FLNG)" for "Floating Liquefied Natural Gas" in the above example. We want to include that in the topic and topicName.

We need to build a far superior version to the example script I provided in the @/resources directory. I need you to find way to build a script that can do this more dynamically. I'd prefer to not have to use paid LLMs to process this text, but if it's necessary I'll consider it. Even better might be a small local model that doesn't need to be from a separate hosted provider and can run in my AWS EC2 instance locally that is good enough to do this. 

You'll need to research options to accomplish this, such as:
1. Running sPAcy locally to assist with region detection.
2. Running another superior NER type model locally to assist with region detection.
3. Accessing a low cost NER model or LLM, but find a way to find the cheapest version that can reliably assist with region detection.
4. Some other strategy that will reliably accomplish this task.
5. We probably need multiple options available.

The goal is to extract the topic, topicName, and regions array (if present in the source "report_title_short" value) and insert these back into the document in the database.

Please ultrathink about the best approach to accomplish this. use any mcp servers or tools available to you in your research. Create a PRD explaining your solution for my review before developing and scripts.