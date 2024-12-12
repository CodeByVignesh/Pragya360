from datetime import datetime
import logging
from textblob import TextBlob
from lib.document_content_extraction import remove_stopwords

# This function is used to remove the stopwords, correct spellings and lemmatize the search string given


async def update_search_string(text):
    try:
        text = text.lower()
        string_list = []
        string_list.append(text)

        blobWord = TextBlob(text)

        _spell_check = blobWord.correct()
        string_list.append(str(_spell_check))

        # _plural = _spell_check.words.pluralize()
        # string_list.append(" ".join(list(_plural)))

        # _singular = _spell_check.words.singularize()
        # string_list.append(" ".join(list(_singular)))

        # lemmatized_sentence = ' '.join(
        #     [Word(word).lemmatize() for word in blobWord.words])
        # string_list.append(lemmatized_sentence)
        print(string_list)
        full_string = " ".join(string_list)
        # full_string = " ".join(list(set(full_string.split())))
        return full_string
    except Exception as err:
        print(f"Error in update_search_string function --> {err}")
        raise RuntimeError

# This function is used to create the Search Query


async def create_search_query(body):
    try:
        body["query"] = await update_search_string(body["query"])
        body_search_string = body["query"]
        body["query"] = await remove_stopwords(body["query"])
        if (("put" in body_search_string and "away" in body_search_string) or "putaway" in body_search_string):
            body["query"] += " put away putaway "
        print(f"Updated Search Body ---> \n\n {body}")
        document_to = datetime.now().strftime('%Y-%m-%d')
        print("Base Query with No filters")
        data = {
            "size": 10000,
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": body[
                                    "query"
                                ],
                                "fields": [
                                    "frontend_id",
                                    "card_title",
                                    "card_title._2gram",
                                    "card_title._3gram",
                                    "context_background",
                                    "context_background._2gram",
                                    "context_background._3gram",
                                    "functionality_in_scope",
                                    "functionality_in_scope._2gram",
                                    "functionality_in_scope._3gram",
                                    "system_demo",
                                    "system_demo_str",
                                    "collection_str",
                                    "knowledge_source_str",
                                    "technology_str",
                                    "development_scope_str",
                                    "lob_str",
                                    "artifact_tag_str",
                                    "features_enabled_str",
                                    "demo_presentation_document_content",
                                    "functional_specification_document_content",
                                    "requirement_document_content",
                                    "technical_specification_document_content"
                                ],
                                "type": "bool_prefix"
                            }
                        },
                        {
                            "range": {
                                "created_date": {
                                    "gte": body["document_from"],
                                    "lte": document_to
                                }
                            }
                        }
                    ],
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "available_for_search": "true"
                                    }
                                }
                            ]
                        }
                    }
                }
            }
        }
        if (body["artifact_tag"] and body["artifact_tag"][0] != ""):
            print("Artifacts tags added to search query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "terms": {
                    "artifact_tag.keyword": body[
                        "artifact_tag"
                    ]
                }
            })

        if (body["collection"] and body["collection"][0] != ""):
            print("Collection filter added to query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "terms": {
                    "collection.keyword": body["collection"]
                }
            })
        
        if (body["features_enabled"] and body["features_enabled"][0] != ""):
            print("Features Enabled filter added to query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "terms": {
                    "features_enabled.keyword": body["features_enabled"]
                }
            })
        if (body["development_scope"] and body["development_scope"] != "" and body["development_scope"].upper() == "YES"):
            print("Development Scope 'YES' filter added to query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "term": {
                    "development_scope.keyword": "Enhancement"
                }
            })

        if (body["development_scope"] and body["development_scope"] != "" and body["development_scope"].upper() == "NO"):
            print("Development Scope 'NO' filter added to query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "term": {
                    "development_scope.keyword": "No"
                }
            })

        if (body["system_demo"] and body["system_demo"] != "" and body["system_demo"].upper() == "YES"):
            print("System Demo 'YES' filter added to query")
            data["query"]["bool"]["must_not"] = [
                {
                    "match": {
                        "system_demo": "No"
                    }
                }
            ]
        if (body["system_demo"] and body["system_demo"] != "" and body["system_demo"].upper() == "NO"):
            print("System Demo 'NO' filter added to query")
            data["query"]["bool"]["filter"]["bool"]["must"].append({
                "term": {
                    "system_demo.keyword": "No"
                }
            })

        print(f"full search string----->{body['query']}")
        print(f"search query----->{data}")
        return [body["query"], data]
    except Exception as err:
        print(f"Error in create search query function --> {err}")
        raise RuntimeError

# This function is used to create the Update Query


async def create_update_query(body):
    try:
        data = body.copy()
        del data["id"]

        # later used to form a big query
        return_data = {
            "doc": data
        }

        return return_data
    except Exception as err:
        print(f"Error in create update query function --> {err}")
        raise RuntimeError
