import logging
from lib.db_connection import mongo_connect

async def store_likes_dislikes(nugget_id, user_id, user_id_value):
    try:
        db = await mongo_connect()
        collection = db["likes_dislikes"]
        query = {"nugget_id": nugget_id}
        collection_with_nugget_id = collection.find_one(query)
        if collection_with_nugget_id:
            collection.update_one(query, {"$set": {user_id: user_id_value}})
            print(
                f"Like and Dislike updated successfully for {nugget_id} & {user_id} --> {user_id_value}")
        else:
            collection.insert_one({"nugget_id": nugget_id, user_id: user_id_value})
            print(
                f"Like and Dislike added successfully for {nugget_id} & {user_id} --> {user_id_value}")
    except Exception as err:
        print(f"Error in store likes and dislikes function --> {err}")
        raise RuntimeError


async def delete_likes_dislikes(nugget_id, user_id):
    try:
        db = await mongo_connect()
        collection = db["likes_dislikes"]
        query = {"nugget_id": nugget_id}
        collection_with_nugget_id = collection.find_one(query)
        if collection_with_nugget_id:
            collection.update_many(query, {"$unset": {user_id: 1}})
            print(
                f"Like and Dislike deleted successfully for {nugget_id} & {user_id}")
    except Exception as err:
        print(f"Error in delete likes and dislikes function --> {err}")
        raise RuntimeError


# store_likes_dislikes(nugget_id, user_id, user_id_value)

# delete_likes_dislikes(nugget_id, user_id)

async def fetch_like_dislikes(nugget_id):
    try:
        db = await mongo_connect()
        collection = db["likes_dislikes"]
        query = {"nugget_id": nugget_id}
        collection_with_nugget_id = collection.find_one(query)
        if collection_with_nugget_id:
            print(f"collection_with_nugget_id ---> {collection_with_nugget_id}")
            collection = dict(collection_with_nugget_id)
            del collection["_id"]
            del collection["nugget_id"]
            # print(collection)
            return collection
        else:
            return ''
    except Exception as err:
        print(f"Error in fetch likes and dislikes function --> {err}")
        raise RuntimeError


async def remove_fields(nugget_data):
    try:
        fields_to_remove = ["dynamic_tags",
                            "system_demo_str",
                            "collection_str",
                            "knowledge_source_str",
                            "technology_str",
                            "development_scope_str",
                            "lob_str",
                            "artifact_tag_str",
                            "features_enabled_str"
                            ]
        for key in fields_to_remove:
            nugget_data.pop(key)
        return nugget_data
    except Exception as err:
        print(f"Error in remove fields function --> {err}")
        raise RuntimeError
