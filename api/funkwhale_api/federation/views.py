from django import forms
from django.core import paginator
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import exceptions, mixins, response, viewsets
from rest_framework.decorators import detail_route, list_route

from funkwhale_api.common import preferences
from funkwhale_api.music import models as music_models

from . import activity, authentication, models, renderers, serializers, utils, webfinger


class FederationMixin(object):
    def dispatch(self, request, *args, **kwargs):
        if not preferences.get("federation__enabled"):
            return HttpResponse(status=405)
        return super().dispatch(request, *args, **kwargs)


class SharedViewSet(FederationMixin, viewsets.GenericViewSet):
    permission_classes = []
    authentication_classes = [authentication.SignatureAuthentication]
    renderer_classes = [renderers.ActivityPubRenderer]

    @list_route(methods=["post"])
    def inbox(self, request, *args, **kwargs):
        if request.method.lower() == "post" and request.actor is None:
            raise exceptions.AuthenticationFailed(
                "You need a valid signature to send an activity"
            )
        if request.method.lower() == "post":
            activity.receive(activity=request.data, on_behalf_of=request.actor)
        return response.Response({}, status=200)


class ActorViewSet(FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    lookup_field = "preferred_username"
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    queryset = models.Actor.objects.local().select_related("user")
    serializer_class = serializers.ActorSerializer

    @detail_route(methods=["get", "post"])
    def inbox(self, request, *args, **kwargs):
        if request.method.lower() == "post" and request.actor is None:
            raise exceptions.AuthenticationFailed(
                "You need a valid signature to send an activity"
            )
        if request.method.lower() == "post":
            activity.receive(activity=request.data, on_behalf_of=request.actor)
        return response.Response({}, status=200)

    @detail_route(methods=["get", "post"])
    def outbox(self, request, *args, **kwargs):
        return response.Response({}, status=200)

    @detail_route(methods=["get"])
    def followers(self, request, *args, **kwargs):
        self.get_object()
        # XXX to implement
        return response.Response({})

    @detail_route(methods=["get"])
    def following(self, request, *args, **kwargs):
        self.get_object()
        # XXX to implement
        return response.Response({})


class WellKnownViewSet(viewsets.GenericViewSet):
    authentication_classes = []
    permission_classes = []
    renderer_classes = [renderers.JSONRenderer, renderers.WebfingerRenderer]

    @list_route(methods=["get"])
    def nodeinfo(self, request, *args, **kwargs):
        if not preferences.get("instance__nodeinfo_enabled"):
            return HttpResponse(status=404)
        data = {
            "links": [
                {
                    "rel": "http://nodeinfo.diaspora.software/ns/schema/2.0",
                    "href": utils.full_url(reverse("api:v1:instance:nodeinfo-2.0")),
                }
            ]
        }
        return response.Response(data)

    @list_route(methods=["get"])
    def webfinger(self, request, *args, **kwargs):
        if not preferences.get("federation__enabled"):
            return HttpResponse(status=405)
        try:
            resource_type, resource = webfinger.clean_resource(request.GET["resource"])
            cleaner = getattr(webfinger, "clean_{}".format(resource_type))
            result = cleaner(resource)
            handler = getattr(self, "handler_{}".format(resource_type))
            data = handler(result)
        except forms.ValidationError as e:
            return response.Response({"errors": {"resource": e.message}}, status=400)
        except KeyError:
            return response.Response(
                {"errors": {"resource": "This field is required"}}, status=400
            )

        return response.Response(data)

    def handler_acct(self, clean_result):
        username, hostname = clean_result

        try:
            actor = models.Actor.objects.local().get(preferred_username=username)
        except models.Actor.DoesNotExist:
            raise forms.ValidationError("Invalid username")

        return serializers.ActorWebfingerSerializer(actor).data


def has_library_access(request, library):
    if library.privacy_level == "everyone":
        return True
    if request.user.is_authenticated and request.user.is_superuser:
        return True

    try:
        actor = request.actor
    except AttributeError:
        return False

    return library.received_follows.filter(actor=actor, approved=True).exists()


class MusicLibraryViewSet(
    FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    serializer_class = serializers.LibrarySerializer
    queryset = music_models.Library.objects.all().select_related("actor")
    lookup_field = "uuid"

    def retrieve(self, request, *args, **kwargs):
        lb = self.get_object()

        conf = {
            "id": lb.get_federation_id(),
            "actor": lb.actor,
            "name": lb.name,
            "summary": lb.description,
            "items": lb.uploads.for_federation().order_by("-creation_date"),
            "item_serializer": serializers.UploadSerializer,
        }
        page = request.GET.get("page")
        if page is None:
            serializer = serializers.LibrarySerializer(lb)
            data = serializer.data
        else:
            # if actor is requesting a specific page, we ensure library is public
            # or readable by the actor
            if not has_library_access(request, lb):
                raise exceptions.AuthenticationFailed(
                    "You do not have access to this library"
                )
            try:
                page_number = int(page)
            except Exception:
                return response.Response({"page": ["Invalid page number"]}, status=400)
            conf["page_size"] = preferences.get("federation__collection_page_size")
            p = paginator.Paginator(conf["items"], conf["page_size"])
            try:
                page = p.page(page_number)
                conf["page"] = page
                serializer = serializers.CollectionPageSerializer(conf)
                data = serializer.data
            except paginator.EmptyPage:
                return response.Response(status=404)

        return response.Response(data)

    @detail_route(methods=["get"])
    def followers(self, request, *args, **kwargs):
        self.get_object()
        # XXX Implement this
        return response.Response({})


class MusicUploadViewSet(
    FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    queryset = music_models.Upload.objects.none()
    lookup_field = "uuid"


class MusicArtistViewSet(
    FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    queryset = music_models.Artist.objects.none()
    lookup_field = "uuid"


class MusicAlbumViewSet(
    FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    queryset = music_models.Album.objects.none()
    lookup_field = "uuid"


class MusicTrackViewSet(
    FederationMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = [authentication.SignatureAuthentication]
    permission_classes = []
    renderer_classes = [renderers.ActivityPubRenderer]
    queryset = music_models.Track.objects.none()
    lookup_field = "uuid"
