"""Controllers related to viewing lists of bookmarks"""
import logging

from datetime import datetime
from pyramid.view import view_config
from StringIO import StringIO

from bookie.lib.access import Authorize
from bookie.lib.readable import ReadContent

from bookie.models import Bmark
from bookie.models import BmarkMgr
from bookie.models import DBSession
from bookie.models import NoResultFound
from bookie.models import Readable
from bookie.models import TagMgr

from bookie.models.fulltext import get_fulltext_handler

LOG = logging.getLogger(__name__)
RESULTS_MAX = 10


@view_config(route_name="api_bmark_recent", renderer="morjson")
def bmark_recent(request):
    """Get a list of the bmarks for the api call"""
    rdict = request.matchdict
    params = request.params

    # check if we have a page count submitted
    page = int(params.get('page', '0'))
    count = int(params.get('count', RESULTS_MAX))

    # do we have any tags to filter upon
    tags = rdict.get('tags', None)

    if isinstance(tags, str):
        tags = [tags]

    # if we don't have tags, we might have them sent by a non-js browser as a
    # string in a query string
    if not tags and 'tag_filter' in params:
        tags = params.get('tag_filter').split()

    recent_list = BmarkMgr.find(limit=count,
                           order_by=Bmark.stored.desc(),
                           tags=tags,
                           page=page,
                           with_tags=True)

    result_set = []

    for res in recent_list:
        return_obj = dict(res)
        return_obj['tags'] = [dict(tag[1]) for tag in res.tags.items()]
        result_set.append(return_obj)

    ret = {
        'success': True,
        'message': "",
        'payload': {
             'bmarks': result_set,
             'max_count': RESULTS_MAX,
             'count': len(recent_list),
             'page': page,
             'tags': tags,
        }

    }

    return ret


@view_config(route_name="api_bmark_popular", renderer="morjson")
def bmark_popular(request):
    """Get a list of the bmarks for the api call"""
    rdict = request.matchdict
    params = request.params

    # check if we have a page count submitted
    page = int(params.get('page', '0'))
    count = int(params.get('count', RESULTS_MAX))

    # do we have any tags to filter upon
    tags = rdict.get('tags', None)

    if isinstance(tags, str):
        tags = [tags]

    # if we don't have tags, we might have them sent by a non-js browser as a
    # string in a query string
    if not tags and 'tag_filter' in params:
        tags = params.get('tag_filter').split()

    popular_list = BmarkMgr.find(limit=count,
                           order_by=Bmark.clicks.desc(),
                           tags=tags,
                           page=page)
    result_set = []

    for res in popular_list:
        return_obj = dict(res)
        return_obj['tags'] = [dict(tag[1]) for tag in res.tags.items()]
        result_set.append(return_obj)

    ret = {
        'success': True,
        'message': "",
        'payload': {
             'bmarks': result_set,
             'max_count': RESULTS_MAX,
             'count': len(popular_list),
             'page': page,
             'tags': tags,
        }

    }

    return ret


@view_config(route_name="api_bmark_sync", renderer="morjson")
def bmark_sync(request):
    """Return a list of the bookmarks we know of in the system

    For right now, send down a list of hash_ids

    """

    hash_list = BmarkMgr.hash_list()

    ret = {
        'success': True,
        'message': "",
        'payload': {
             'hash_list': [hash[0] for hash in hash_list]
        }
    }

    return ret


@view_config(route_name="api_bmark_hash", renderer="morjson")
def bmark_get(request):
    """Return a bookmark requested via hash_id

    We need to return a nested object with parts
        bmark
            - readable
    """
    rdict = request.matchdict

    hash_id = rdict.get('hash_id', None)

    if not hash_id:
        return {
            'success': False,
            'message': "Could not find bookmark for hash " + hash_id,
            'payload': {}
        }

    bookmark = BmarkMgr.get_by_hash(hash_id)
    if not bookmark:
        # then not found
        ret = {
            'success': False,
            'message': "Bookmark for hash id {0} not found".format(hash_id),
            'payload': {}
        }

    else:
        return_obj = dict(bookmark)
        if bookmark.hashed.readable:
            return_obj['readable'] = dict(bookmark.hashed.readable)

        return_obj['tags'] = [dict(tag[1]) for tag in bookmark.tags.items()]

        ret = {
            'success': True,
            'message': "",
            'payload': {
                 'bmark': return_obj
            }
        }

    return ret

@view_config(route_name="api_bmark_add", renderer="morjson")
def bmark_add(request):
    """Add a new bookmark to the system"""
    params = request.params

    with Authorize(request.registry.settings.get('api_key', ''),
                   params.get('api_key', None)):

        if 'url' in params and params['url']:
            # check if we already have this
            try:
                mark = BmarkMgr.get_by_url(params['url'])

                mark.description = params.get('description', mark.description)
                mark.extended = params.get('extended', mark.extended)

                new_tags = params.get('tags', None)
                if new_tags:
                    mark.update_tags(new_tags)

            except NoResultFound:
                # then let's store this thing
                # if we have a dt param then set the date to be that manual
                # date
                if 'dt' in request.params:
                    # date format by delapi specs:
                    # CCYY-MM-DDThh:mm:ssZ
                    fmt = "%Y-%m-%dT%H:%M:%SZ"
                    stored_time = datetime.strptime(request.params['dt'], fmt)
                else:
                    stored_time = None

                # we want to store fulltext info so send that along to the
                # import processor
                conn_str = request.registry.settings.get('sqlalchemy.url',
                                                         False)
                fulltext = get_fulltext_handler(conn_str)

                mark = BmarkMgr.store(params['url'],
                             params.get('description', ''),
                             params.get('extended', ''),
                             params.get('tags', ''),
                             dt=stored_time,
                             fulltext=fulltext,
                       )

            # if we have content, stick it on the object here
            if 'content' in request.params:
                content = StringIO(request.params['content'])
                content.seek(0)
                parsed = ReadContent.parse(content, content_type="text/html")

                mark.hashed.readable = Readable()
                mark.hashed.readable.content = parsed.content
                mark.hashed.readable.content_type = parsed.content_type
                mark.hashed.readable.status_code = parsed.status
                mark.hashed.readable.status_message = parsed.status_message

            return {
                        'success': True,
                        'message': "done",
                        'payload': {
                            'bmark': dict(mark)
                        }
                    }
        else:
            return { 'success': False,
                     'message': 'Bad Request: missing url',
                     'payload': dict(params)
                 }


@view_config(route_name="api_bmark_remove", renderer="morjson")
def bmark_remove(request):
    """Remove this bookmark from the system"""
    params = request.params

    with Authorize(request.registry.settings.get('api_key', ''),
                   params.get('api_key', None)):
        if 'url' in params and params['url']:
            try:
                bmark = BmarkMgr.get_by_url(params['url'])

                session = DBSession()
                session.delete(bmark)

                return {
                        'success': True,
                        'message': "done",
                        'payload': {}
                }

            except NoResultFound:
                # if it's not found, then there's not a bookmark to delete
                return {
                    'success': False,
                    'message': "Bad Request: bookmark not found",
                    'payload': {}

                }


@view_config(route_name="api_tag_complete", renderer="morjson")
def tag_complete(request):
    """Complete a tag based on the given text

    :@param tag: GET string, tag=sqlalchemy
    :@param current: GET string of tags we already have python+database

    """
    params = request.GET

    if 'current' in params and params['current'] != "":
        current_tags = params['current'].split()
    else:
        current_tags = None

    if 'tag' in params and params['tag']:
        tag = params['tag']
        tags = TagMgr.complete(tag, current=current_tags)
        # reset this for the payload join operation
        current_tags = []

    ret = {
        'success': True,
        'message': "",
        'payload': {
             'current': ",".join(current_tags),
             'tags': [tag.name for tag in tags]
        }
    }

    return ret