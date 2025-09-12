```json
{
  "_id": {
    "$oid": "66d5c90e6cffa21d4471fb0d"
  },
  "name": "Translate to the target language",
  "description": "Take in the text, understand the language and translate it to the target language",
  "_metadata": {
    "created_at": {
      "$date": "2024-09-02T14:17:50.788Z"
    },
    "modified_at": {
      "$date": "2024-09-03T17:13:24.806Z"
    }
  },
  "system_name": "TRANSLATE_TO_TARGET_LANGUAGE",
  "active_variant": "variant_1",
  "variants": [
    {
      "variant": "variant_1",
      "topP": 1,
      "temperature": 1,
      "category": "Other",
      "model": "cohere-command-r-plus",
      "retrieve": {
        "collection_system_names": []
      },
      "id": "66d5c90e6cffa21d4471fb0d",
      "text": "User will provide you with two inputs: \"\"target language\"\" and \"\"text to translate\"\".\n\nDetermine the \"\"original language\"\" of \"\"text to translate\"\" and translate it to \"\"target language\"\". \n\nOutput two parameters below in JSON format:\n\n* \"\"original language\"\": \"\"\"\"original language\"\"\"\"\n* \"\"translation\"\": \"\"\"\"Translation of \"\"text to translate\"\" from  \"\"original language\"\" to \"\"target language\"\"\"\"\n\nDon't note use markdown format in output\n",
      "sample_text": "\"target language\": \"'Spanish\"\ntext to translate\":\"The customer is inquiring about subscription options as they are moving abroad for six months. They want to know how their current subscription can be managed during their time away, with specific interest in keeping, canceling, or changing their subscription plan to suit their new circumstances.\""
    }
  ],
  "category": "generic"
}
```