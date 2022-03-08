from django.core.management.base import BaseCommand
from django.conf import settings

import requests, json, os, datetime, pytz

from lxml import etree

from pprint import pprint as pp

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

        solr_url = settings.SOLR_URL
        solr_auth = {"X-Authentication-Token": settings.SOLR_API_KEY}

        collection_query = "collection_url:https://registry.cdlib.org/api/v1/collection/{}/".format(collection_id)

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

        results = get_solr_iter(solr_url, solr_auth, base_query)

        xml_file = os.path.join(settings.OAI_ROOT, str(collection_id) + ".xml")
        repo_name, collection_name = create_output_xml(xml_file, results)

        if OAIInstitution.objects.filter(inst_id=repo_id).exists():
            inst = OAIInstitution.objects.get(inst_id=repo_id)
            #inst.update({"name": repo_name, "first_date": datetime.date.today()})
            #inst.save()
        else:
            inst = OAIInstitution.objects.create(inst_id=repo_id, name=repo_name, first_date=datetime.date.today())

        set, created = OAISet.objects.get_or_create(institution=inst, set_id=collection_id, name=collection_name)
        print(set)
        print(created)

NSMAP = {
    None: "http://www.openarchives.org/OAI/2.0/",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
    "oai_dc": "http://www.openarchives.org/OAI/2.0/oai_dc/",
    "dc": "http://purl.org/dc/elements/1.1/",
}
SCHEMALOCATION = "http://www.openarchives.org/OAI/2.0/ http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd "
SCHEMALOCATION += "http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd"

def create_output_xml(xmlfile, results):
    """ format a single XML result for the whole collection """
    # https://stackoverflow.com/a/4470035/1763984
    page = etree.Element(
        "OAI-PMH",
        {"{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": SCHEMALOCATION},
        nsmap=NSMAP,
    )
    doc = etree.ElementTree(page)
    responseDate = etree.SubElement(page, "responseDate")
    responseDate.text = datetime.datetime.now(pytz.utc).isoformat()
    request = etree.SubElement(page, "request")
    records = etree.SubElement(page, "ListRecords")

    for item in results:
        repo_name = "{}, {}".format(item["campus_name"][0], item["repository_name"][0])
        collection_name = item["collection_name"][0]
        map_solr_to_oai(item, records)

    return (repo_name, collection_name)

    #  TODO: validate the XML before saving

    doc.write(xmlfile, pretty_print=True)

def map_solr_to_oai(json_item, records):
    """ takes in solr json adds subelements to the `records` """
    #pp(json_item.keys())
    # start a new record
    record = etree.SubElement(records, "record")

    # set up the header
    header = etree.SubElement(record, "header")

    # oai identifier for the header
    identifier = etree.SubElement(header, "identifier")
    this_id = json_item["id"]
    this_collection = json_item["collection_url"][0]
    identifier.text = f"oai:calipshere:{this_collection}:{this_id}"

    # datastamp for the header
    datestamp = etree.SubElement(header, "datestamp")
    datestamp.text = json_item["timestamp"]

    # start the metadata section
    metadata = etree.SubElement(record, "metadata")
    oaidc = etree.SubElement(
        metadata, "{http://www.openarchives.org/OAI/2.0/oai_dc/}dc"
    )
    DC = "{http://purl.org/dc/elements/1.1/}"

    # main section of the mapping
    json_element_to_xml_element("title", f"{DC}title", json_item, oaidc)
    json_element_to_xml_element("creator", f"{DC}creator", json_item, oaidc)
    json_element_to_xml_element("subject", f"{DC}subject", json_item, oaidc)
    json_element_to_xml_element("description", f"{DC}description", json_item, oaidc)
    json_element_to_xml_element("publisher", f"{DC}publisher", json_item, oaidc)
    json_element_to_xml_element("contributor", f"{DC}contributor", json_item, oaidc)
    json_element_to_xml_element("date", f"{DC}date", json_item, oaidc)
    json_element_to_xml_element("type", f"{DC}type", json_item, oaidc)
    json_element_to_xml_element("format", f"{DC}format", json_item, oaidc)
    json_element_to_xml_element("identifier", f"{DC}identifier", json_item, oaidc)
    json_element_to_xml_element("source", f"{DC}source", json_item, oaidc)
    json_element_to_xml_element("language", f"{DC}language", json_item, oaidc)
    json_element_to_xml_element("relation", f"{DC}relation", json_item, oaidc)
    json_element_to_xml_element("coverage", f"{DC}coverage", json_item, oaidc)
    json_element_to_xml_element("rights", f"{DC}rights", json_item, oaidc)

def json_element_to_xml_element(json_name, xml_name, json_in, xml_out):
    """ perform a simple mapping from json to XML """
    for element_value in json_in.get(json_name, []):
        element_xml = etree.SubElement(xml_out, xml_name)
        element_xml.text = str(element_value)

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
