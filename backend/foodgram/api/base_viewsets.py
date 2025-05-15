from rest_framework import mixins, viewsets


class ListRetrieveViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    """Base viewset only for list/retrieve operations."""

    pass


class ListViewSet(
    mixins.ListModelMixin,
    viewsets.GenericViewSet
):
    """Base viewset only for list operations."""

    pass
