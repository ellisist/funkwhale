from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from django.db.models import Prefetch

from funkwhale_api.activity import record
from funkwhale_api.common import fields, permissions
from funkwhale_api.music.models import Track
from funkwhale_api.music import utils as music_utils
from . import models, serializers


class ListeningViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):

    serializer_class = serializers.ListeningSerializer
    queryset = models.Listening.objects.all().select_related("user")
    permission_classes = [
        permissions.ConditionalAuthentication,
        permissions.OwnerPermission,
        IsAuthenticatedOrReadOnly,
    ]
    owner_checks = ["write"]

    def get_serializer_class(self):
        if self.request.method.lower() in ["head", "get", "options"]:
            return serializers.ListeningSerializer
        return serializers.ListeningWriteSerializer

    def perform_create(self, serializer):
        r = super().perform_create(serializer)
        record.send(serializer.instance)
        return r

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(
            fields.privacy_level_query(self.request.user, "user__privacy_level")
        )
        tracks = Track.objects.annotate_playable_by_actor(
            music_utils.get_actor_from_request(self.request)
        ).select_related("artist", "album__artist")
        return queryset.prefetch_related(Prefetch("track", queryset=tracks))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["user"] = self.request.user
        return context
