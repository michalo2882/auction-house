from rest_framework import permissions, viewsets, mixins
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from app.models import *
from app.rest.serializers import *


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard(request):
    return Response({'user': request.user.username})


class ItemViewSet(mixins.RetrieveModelMixin,
                  mixins.ListModelMixin,
                  GenericViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
