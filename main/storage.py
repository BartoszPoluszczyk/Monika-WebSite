from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateDocumentStorage(FileSystemStorage):
    """Storage without a public URL, served only by authorized Django views."""

    def __init__(self):
        super().__init__(
            location=settings.PRIVATE_DOCUMENT_ROOT,
            base_url=None,
        )
