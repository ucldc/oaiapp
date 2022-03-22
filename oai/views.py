from django.shortcuts import render, get_object_or_404
from django.conf import settings

from oai.models import *

import datetime

def list_repositories(request):
    return render(request, template_name="oai/list_repositories.html", 
                  context={"repositories": OAIRepository.objects.all()})

def oai(request, repo_id):
    verb = request.GET.get("verb")
    repo = get_object_or_404(OAIRepository, repo_id=repo_id)
    context = {"repo": repo, 
               "base_url": "{}://{}{}".format(request.scheme, request.get_host(), request.path)}
    if verb == "Identify":
        template_name = "oai/identify.html"
    elif verb == "ListMetadataFormats":
        template_name = "oai/metadata_formats.html"
    elif verb == "ListSets":
        template_name = "oai/list_sets.html"
    elif verb == "ListRecords" or verb == "ListIdentifiers":
        query_args = {"verb": verb}
        if verb == "ListRecords":
            template_name = "oai/list_records.html"
        else:
            template_name = "oai/list_identifiers.html"

        if "resumptionToken" in request.GET:
            exp = datetime.datetime.now() - datetime.timedelta(days=2)
            ResumptionToken.objects.filter(date_created__lt=exp).delete()
            tkey = request.GET.get("resumptionToken")
            if ResumptionToken.objects.filter(key=tkey).exists():
                token = ResumptionToken.objects.get(key=tkey)
                cursor = token.cursor + settings.OAI_RESULTS_LIMIT
            else:
                context.update({"error": "badResumptionToken"})
                token = None
                cursor = 0
        else:
            token = None
            cursor = 0

        set_id = token.set.set_id if token and token.set else request.GET.get("set", False)
        if set_id:
            if OAISet.objects.filter(set_id=set_id).exists():
                set = OAISet.objects.get(set_id=set_id)
                records = set.oairecord_set.all().order_by('pk')
                context.update({"set_id": set_id})
                query_args.update({"set": set})
            else:
                context.update({"error": "noRecordsMatch"})
                records = None
        else:
            records = repo.get_all_records()
        if records:
            fro = token.fro if token and token.fro else request.GET.get("from", False)
            if fro:
                records = records.filter(datestamp__gt=fro)
                query_args.update({"fro": fro})
            until = token.until if token and token.until else request.GET.get("until", False)
            if until:
                records = records.filter(datestamp__lt=until)
                query_args.update({"until": until})

            total_records = records.count()
            records = records[cursor:]
            
            if len(records) > settings.OAI_RESULTS_LIMIT:
                first = records[0]
                query_args.update({"cursor": cursor, "first_timestamp": first.datestamp})
                token = ResumptionToken.objects.create(**query_args)
                token.genkey()
                context.update({"resumptionToken": token, "total_records": total_records})

            context.update({"records": records[:settings.OAI_RESULTS_LIMIT]})
    elif verb == "GetRecord":
        template_name = "oai/get_record.html"
        record_id = request.GET.get("identifier")
        if OAIRecord.objects.filter(identifier=record_id).exists():
            record = OAIRecord.objects.get(identifier=record_id)
            context.update({"record": record})
        else:
            context.update({"error": "idDoesNotExist"})
    else:
        template_name = "oai/bad_verb.html"

    return render(request, template_name=template_name, context=context, content_type='text/xml')