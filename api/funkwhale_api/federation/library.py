import json
import requests

from django.conf import settings

from funkwhale_api.common import session

from . import actors
from . import models
from . import serializers
from . import signing
from . import webfinger


def scan_from_account_name(account_name):
    """
    Given an account name such as library@test.library, will:

    1. Perform the webfinger lookup
    2. Perform the actor lookup
    3. Perform the library's collection lookup

    and return corresponding data in a dictionary.
    """
    data = {}
    try:
        username, domain = webfinger.clean_acct(
            account_name, ensure_local=False)
    except serializers.ValidationError:
        return {
            'webfinger': {
                'errors': ['Invalid account string']
            }
        }
    system_library = actors.SYSTEM_ACTORS['library'].get_actor_instance()
    library = models.Library.objects.filter(
        actor__domain=domain,
        actor__preferred_username=username
    ).select_related('actor').first()
    data['local'] = {
        'following': False,
        'awaiting_approval': False,
    }
    try:
        follow = models.Follow.objects.get(
            target__preferred_username=username,
            target__domain=username,
            actor=system_library,
        )
        data['local']['awaiting_approval'] = not bool(follow.approved)
        data['local']['following'] = True
    except models.Follow.DoesNotExist:
        pass

    try:
        data['webfinger'] = webfinger.get_resource(
            'acct:{}'.format(account_name))
    except requests.ConnectionError:
        return {
            'webfinger': {
                'errors': ['This webfinger resource is not reachable']
            }
        }
    except requests.HTTPError as e:
        return {
            'webfinger': {
                'errors': [
                    'Error {} during webfinger request'.format(
                        e.response.status_code)]
            }
        }
    except json.JSONDecodeError as e:
        return {
            'webfinger': {
                'errors': ['Could not process webfinger response']
            }
        }

    try:
        data['actor'] = actors.get_actor_data(data['webfinger']['actor_url'])
    except requests.ConnectionError:
        data['actor'] = {
            'errors': ['This actor is not reachable']
        }
        return data
    except requests.HTTPError as e:
        data['actor'] = {
            'errors': [
                'Error {} during actor request'.format(
                    e.response.status_code)]
        }
        return data

    serializer = serializers.LibraryActorSerializer(data=data['actor'])
    if not serializer.is_valid():
        data['actor'] = {
            'errors': ['Invalid ActivityPub actor']
        }
        return data
    data['library'] = get_library_data(
        serializer.validated_data['library_url'])

    return data


def get_library_data(library_url):
    actor = actors.SYSTEM_ACTORS['library'].get_actor_instance()
    auth = signing.get_auth(actor.private_key, actor.private_key_id)
    try:
        response = session.get_session().get(
            library_url,
            auth=auth,
            timeout=5,
            verify=settings.EXTERNAL_REQUESTS_VERIFY_SSL,
            headers={
                'Content-Type': 'application/activity+json'
            }
        )
    except requests.ConnectionError:
        return {
            'errors': ['This library is not reachable']
        }
    scode = response.status_code
    if scode == 401:
        return {
            'errors': ['This library requires authentication']
        }
    elif scode == 403:
        return {
            'errors': ['Permission denied while scanning library']
        }
    elif scode >= 400:
        return {
            'errors': ['Error {} while fetching the library'.format(scode)]
        }
    serializer = serializers.PaginatedCollectionSerializer(
        data=response.json(),
    )
    if not serializer.is_valid():
        return {
            'errors': [
                'Invalid ActivityPub response from remote library']
        }

    return serializer.validated_data


def get_library_page(library, page_url):
    actor = actors.SYSTEM_ACTORS['library'].get_actor_instance()
    auth = signing.get_auth(actor.private_key, actor.private_key_id)
    response = session.get_session().get(
        page_url,
        auth=auth,
        timeout=5,
        verify=settings.EXTERNAL_REQUESTS_VERIFY_SSL,
        headers={
            'Content-Type': 'application/activity+json'
        }
    )
    serializer = serializers.CollectionPageSerializer(
        data=response.json(),
        context={
            'library': library,
            'item_serializer': serializers.AudioSerializer})
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data