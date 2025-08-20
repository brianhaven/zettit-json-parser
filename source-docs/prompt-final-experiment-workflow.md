Based on all this new knowledge and discussion between us, and the feedback I've given you, do you think you could build a new experiment script from scratch that could handle most of this? Or is it too complex for a script and requires an AI? Please give me an honest answer. Keep in mind, I know the region detection can be a little tricky, so I will likely work with you to add sPacy and GLiNER to the repo to assist, but I want to know how well we can get the experiment scripts working. Also, I'm wondering if we should work through the library building step by step. For example:

1. Get all the collections set up using the mongodb mcp server.

2. Get the "market_terms" set now since there are only two and we'll need them to proceed with the following steps.

3. Modify the script to analyze the titles and identify the date range patterns and output the results for me to review and enhance with you until we land on a solid list for the library. Also, when the date/date range is extracted, let's use the field name "extracted_forecast_date_range".

4. Then we move on to report types and have the script isolate and deduplicate all the report type scenarios and we refine that until we land on a solid list to use for the library. When we insert the extracted report type, let's use the field name "extracted_report_type".

5. Then we engage in a more significant effort to set up the region detection and use our existing library plus run sveral tests with sPacy and GLiNER to pares through the documents and try to extract and match as many as possible in the mongodb collection, and hopefully add some that we may not have in our current list. When we insert the extracted regions, let's use the field name "extracted_regions" and use an array. Within the Array, let's retain the order of multiple regions as they appear in the source title, not alphabetical for now.

6. Then we can run some end-to-end tests to evaluate the outputs and the identified topic/topicName and refine untile we can get close. When we insert the extracted topic and topicName, let's use the field names "topic" and "topicName", respectively.

7. Ensure there is some mechanism for the script to identify when it might be confused and create a list of titles that you and I can evaluate and try to help set up more rules.

The core question here is: can a script be designed to do this, or is it really the task for an AI. If a script is possible, then what we build in this experiement can give us all the learnings we need to develop the offical script. Also, you'll need to recommend if this is one larger script that does it all, or if it should be broken up into smaller scripts in a pipeline. Please share your thoughts on all of this.

Do not implement anything yet, await my response and instructions