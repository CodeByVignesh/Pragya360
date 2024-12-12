
from collections import Counter
from lib.db_connection import initialize_elastic
from lib.document_content_extraction import remove_stopwords
from lib.feedback import fetch_like_dislikes
import spacy
from autocorrect import Speller
from nltk.corpus import stopwords
import logging
import os
from urllib.error import ContentTooShortError
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from string import punctuation

index = os.getenv("INDEX_NAME")
nlp = spacy.load("en_core_web_sm")
stopwords = stopwords.words('english')


async def autocorrect_text(text):
    try:
        # Create an instance of the autocorrect spell checker
        spell = Speller(lang='en')
        corrected_text = ''
        words = text.split()
        for word in words:
            corrected_word = spell(word)  # Autocorrect the word
            corrected_text += corrected_word + ' '
        return corrected_text.strip()
    except Exception as err:
        print(f"Exception in autocorrect text function --> {err}")
        raise RuntimeError


async def clean_string(text):
    try:
        text = ''.join([word for word in text if word not in punctuation])
        text = text.lower()
        text = " ".join([word for word in text.split()
                        if word not in stopwords])
        print(f"cleaned text\n\n{text}")
        return text
    except Exception as err:
        print(f"Exception in clean string function --> {err}")
        raise RuntimeError


async def clean_nuggets(nugget_data):
    try:
        key_list = ['collection',
                    'card_title',
                    'knowledge_source',
                    'technology',
                    'development_scope',
                    'context_background',
                    'lob',
                    'functionality_in_scope',
                    'functionality_out_of_scope',
                    'artifact_tag',
                    'system_demo',
                    'features_enabled']
        joined_string = ''
        for key, value in nugget_data.items():
            if (type(value) == list and key in key_list):
                list_str = ", ".join(value)
                joined_string += list_str + " "
            elif (type(value) == str and key in key_list):
                joined_string += value + " "
        print(joined_string)

        cleaned = await clean_string(joined_string)

        return {
            "str_value": cleaned
        }
    except Exception as err:
        print(f"Exception in clean nuggets function --> {err}")
        raise RuntimeError


async def find_duplicate_nugget(all_string, current_string):
    try:
        all_string.append(current_string)
        vectorizer = CountVectorizer().fit_transform(all_string)
        vectors = vectorizer.toarray()
        print(vectors)
        cos_sim = cosine_similarity(vectors)
        print(cos_sim)
        match_result = list(cos_sim[-1])
        # pop out the exact match result
        match_result.pop()
        print(match_result)
        sorted_match_result = sorted(match_result)[::-1]
        top_results = []
        top_results_index = []
        for result in sorted_match_result:
            if (result >= 0.8 and len(top_results) <= 5):
                top_results.append((match_result.index(result), result))
        if (top_results):
            print(f"top results ---> {top_results}")
            return [True, top_results]
        else:
            print("No duplicate nuggets found")
            return [False, top_results]
    except Exception as err:
        print(f"Exception in find_duplicate_nugget function --> {err}")
        raise RuntimeError


async def get_nugget_id(documents, duplicate_ids):
    try:
        all_duplicates = duplicate_ids[1]
        # print(f"final mongo docs\n\n\n{documents}")
        print(f"All Duplicates -->{all_duplicates}")
        return_data = []
        for result in all_duplicates:
            dict_data = dict()
            # print(result[0], result[1])
            dict_data["score"] = result[1]
            _nugget_id = documents[result[0]]["nugget_id"]
            print(
                f"Matching Score --> {dict_data['score']}\n Nugget ID --> {_nugget_id}")
            try:
                # initializing elastic
                es = await initialize_elastic()
            except Exception as err:
                raise ContentTooShortError

            query = {
                "query": {
                    "term": {
                        "_id": {
                            "value": _nugget_id
                        }
                    }
                }
            }

            resp = es.search(index=index, body=query)
            print("Nugget search is done")
            print(resp)
            if(resp['hits']['hits']):
                #es_result = resp['hits']['hits'][0]["_source"]
                es_result = dict()
                
                # dict_data["matching_data"] = es_result
                es_result["score"] = result[1]
                es_result["id"] = resp['hits']['hits'][0]["_id"]
                es_result["frontend_id"] = resp['hits']['hits'][0]["_source"]["frontend_id"]
                es_result["collection"] = resp['hits']['hits'][0]["_source"]["collection"]
                es_result["title"] = resp['hits']['hits'][0]["_source"]["card_title"]
                es_result["knowledge_source"] = resp['hits']['hits'][0]["_source"]["knowledge_source"]
                es_result["summary"] = resp['hits']['hits'][0]["_source"]["context_background"]
                
                print(es_result)
                
                return_data.append(es_result)
            else:
                print(f"No Nugget found for Nugget ID ----> {_nugget_id}")
        print(f"Duplicate Nuggets ---> \n {return_data}")
        return return_data
    except Exception as err:
        print(f"Exception in get nugget id function --> {err}")
        raise RuntimeError


async def get_dynamic_tags(nugget_data):
    try:
        print(nugget_data)
        key_list = ['card_title', 'knowledge_source',
                    'context_background', 'functionality_in_scope']
        dynamic_tags = []
        pos_tag = ['PROPN', 'NOUN']
        for key, value in nugget_data.items():
            if (type(value) == str and key in key_list):
                doc = nlp(value.lower())
                for token in doc:
                    if (token.text in nlp.Defaults.stop_words or token.text in punctuation):
                        continue
                    if (token.pos_ in pos_tag):
                        dynamic_tags.append(token.text.capitalize())
        output = Counter(dynamic_tags).most_common(20)
        output = [word[0] for word in output if len(word[0])>2]
        output = sorted(list(set(output)))
        print(output)
        return output
    except Exception as err:
        print(f"Exception in get dynamic tags function --> {err}")
        raise RuntimeError


async def text_highlighting(search_string, nugget_data):
    try:
        nugget_fields = [
            "frontend_id",
            "card_title",
            "context_background",
            "functionality_in_scope",
            "system_demo_str",
            'collection_str',
            'knowledge_source_str',
            'technology_str',
            'development_scope_str',
            'lob_str',
            'artifact_tag_str',
            'features_enabled_str'
        ]
        print(
            f"search string inside text highlighting --> {search_string}")
        #search_string = await remove_stopwords(search_string)
        search_str_split = search_string.split()
        print(search_str_split)

        summary_list = []

        for str in search_str_split:
            for field in nugget_fields:
                # print(f"str ---> {str}\n\nfield --> {field}")
                if (str in nugget_data[field].lower()):
                    print(
                        f"str ---> {str}\n\nnugget --> {nugget_data[field]}")
                    field_split = nugget_data[field].split(".")
                    for sentence in field_split:
                        if (str in sentence.lower()):
                            sentence = sentence.lower().replace(
                                str, f"<em>{str}</em>")
                            summary_list.append(sentence)

        # print(summary_list)
        print(". ".join(summary_list))
        return ". ".join(summary_list)
    except Exception as err:
        print(f"Exception in text highlighting function --> {err}")
        raise RuntimeError


async def text_highlighting_docupedia(search_string, nugget_data):
    try:
        nugget_fields = [
            "demo_presentation_document_content",
            "functional_specification_document_content",
            "requirement_document_content",
            "technical_specification_document_content"
        ]
        print(
            f"search string inside docupedia highlighting --> {search_string}")
        search_string = await remove_stopwords(search_string)

        search_str_split = search_string.split()
        # print(search_str_split)

        final_summary_list = []

        for field in nugget_fields:
            summary_list = []
            for str in search_str_split:
                # print(f"str ---> {str}\n\nfield --> {field}")
                if (nugget_data[field] and str in nugget_data[field].lower()):
                    print(
                        f"str ---> {str}\n\nnugget --> {nugget_data[field]}")
                    field_split = nugget_data[field].split(".")
                    for sentence in field_split:
                        if (str in sentence.lower()):
                            sentence = sentence.lower().replace(
                                str, f"<em>{str}</em>")
                            summary_list.append(sentence)
            if (len(summary_list) != 0):
                field_name = " ".join(field.split("_")[:-1]).capitalize()
                summary_list.insert(0, f"<b>{field_name}</b>")
                final_summary_list.append(" ".join(summary_list))

        # print(final_summary_list)
        print(" ".join(final_summary_list))
        return " ".join(final_summary_list)
    except Exception as err:
        print(
            f"Exception in text_highlighting_docupedia function --> {err}")
        raise RuntimeError


async def update_parent_nugget(index, nugget_id):
    try:
        # initializing elastic
        es = await initialize_elastic()
    except Exception as err:
        raise RuntimeError

    try:
        update_query = {
            "doc": {
                "available_for_search": "false"
            }
        }
        resp = es.update(index=index, id=nugget_id, body=update_query)
        print(
            f"---Nugget Updated  --- available for search is set to false for {nugget_id}")
        print(resp)
    except Exception as err:
        print(f"Error in updating parent nugget --> {err}")
        raise RuntimeError


async def process_search_result(search_string, item):
    try:
        print(item)
        _result = dict()
        print(f"item id -------------------{item['_id']}")
        _result["id"] = item["_id"]
        _result["likes_dislikes"] = await fetch_like_dislikes(item["_id"])
        _result["score"] = item["_score"]
        _result["title"] = item["_source"]["card_title"]
        _result["frontend_id"] = item["_source"]["frontend_id"]
        _result["views"] = item["_source"]["views"]
        _result["likes"] = item["_source"]["likes"]
        _result["dislikes"] = item["_source"]["dislikes"]
        _result["created_date"] = item["_source"]["created_date"]
        _result["approved_or_rejected_on"] = item["_source"]["approved_or_rejected_on"]
        _summary_list = []
        # for key, value in item["highlight"].items():
        #     _summary_list.extend(value)
        # _result["summary"] = ". ".join(_summary_list)
        nugget_match = await text_highlighting(search_string, item["_source"])
        docupedia_match = await text_highlighting_docupedia(search_string, item["_source"])
        _result["summary"] = nugget_match + " " + docupedia_match
        # _result["nugget_data"] = await remove_fields(item["_source"])
        return _result
    except Exception as err:
        print(f"Error in process search result function --> {err}")
