from django.core.management.base import BaseCommand
from django.conf import settings

import xml.etree.ElementTree as et
import requests, json

from oai.models import *

class Command(BaseCommand):
    """Gets a collection from calisphere and adds it to the OAI output"""
    help = "Gets a collection from calisphere and adds it to the OAI output"

    def add_arguments(self, parser):
        parser.add_argument("collection_id", help="`collection_id` of collection in Calisphere", type=int)
        parser.add_argument("repo_id", help="`repo_id` of collection in Calisphere", type=int)

    def handle(self, *args, **options):
        collection_id = options.get("collection_id")
        repo_id = options.get("repo_id")

        solr_url = settings.SOLR_URL + "/query"
        solr_auth = {"X-Authentication-Token": settings.SOLR_API_KEY}

        collection_url = "https://registry.cdlib.org/api/v1/collection/{}/".format(collection_id)
        collection_query = "collection_url:{}".format(collection_url)

        base_query = {
            "q": "{}".format(collection_query),
            # "fields": "id, collection_url, title, creator, date",  # fl = field list
            "rows": 1000,
            "sort": "score desc,id desc",
            "mm": "100%",
            "pf3": "title",
            "pf": "text,title",
            "qs": 12,
            "ps": 12,
        }

        repo_name, collection_name = get_collection_name(collection_url, repo_id)

        results = get_solr_iter(solr_url, solr_auth, base_query)

        if OAIRepository.objects.filter(repo_id=repo_id).exists():
            repo = OAIRepository.objects.get(repo_id=repo_id)
        else:
            repo = OAIRepository.objects.create(repo_id=repo_id, name=repo_name)

        set, created = OAISet.objects.get_or_create(repository=repo, set_id=collection_id, name=collection_name)
        record_ids = []

        for item in results:
            map_solr_to_oai(item, set, record_ids)

        for r in set.oairecord_set.exclude(pk__in=record_ids):
            r.sets.remove(set)
            if r.sets.count() == 0:
                r.delete()

def get_collection_name(url, repo_id):
    res = requests.get(url)
    data = json.loads(res.content)
    collection_name = data["name"]
    for r in data["repository"]:
        if r["id"] == repo_id:
            repo_name = r["name"]
            if "campus" in r and len(r["campus"]) > 0:
                repo_name = "{}, {}".format(r["campus"][0]["name"], repo_name)
            break    
    return (repo_name, collection_name)

def map_solr_to_oai(json_item, set, record_ids):
    this_id = json_item["id"]
    this_collection = json_item["collection_url"][0]
    identifier = f"oai:calipshere:{this_collection}:{this_id}"

    if OAIRecord.objects.filter(identifier=identifier).exists():
        record = OAIRecord.objects.get(identifier=identifier)
        record.datestamp = json_item["timestamp"]
        record.save()
        record.oaifield_set.all().delete()
    else:
        record = OAIRecord.objects.create(identifier=identifier, datestamp=json_item["timestamp"])
        record.sets.add(set)
        record.save()

    record_ids.append(record.pk)
    fields = ["title", "creator", "subject", "description", "publisher", "contributor", "date",
            "type", "format", "identifier", "source", "language", "relation", "coverage", "rights"]
    
    for f in fields:
        for value in json_item.get(f, []):
            OAIField.objects.get_or_create(record=record, name=f, value=str(value))

    # add thumbnail image MM@UCLA says fields accepted:
    # dc:description, dc:identifier.thumbnail, dc:identifier, or dc:identifier.* (*=wildcard)
    turl = "https://calisphere.org/crop/210x210/{}".format(json_item['reference_image_md5'])
    OAIField.objects.get_or_create(record=record, name="identifier", value=turl)

def get_solr_page(url, headers, params, cursor="*"):
    params.update({"cursorMark": cursor})
    res = requests.get(url, headers=headers, params=params, verify=False)
    res.raise_for_status()
    return json.loads(res.content)

def get_solr_iter(url, headers, params):
    nextCursorMark = "*"
    while True:
        results_dict = get_solr_page(url, headers, params, nextCursorMark)
        if len(results_dict["response"]["docs"]) == 0:
            break
        for document in results_dict["response"]["docs"]:
            yield document
        nextCursorMark = results_dict.get("nextCursorMark", False)
