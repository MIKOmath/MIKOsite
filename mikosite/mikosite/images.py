"""One way in for every image the site stores."""
import uuid
from io import BytesIO

from PIL import Image, ImageOps

from django.core.files.base import ContentFile

WEBP_QUALITY = 85


def to_webp(file, size, quality=WEBP_QUALITY) -> ContentFile:
    """Centre-crop to `size` and re-encode as WebP under a fresh name."""
    image = ImageOps.exif_transpose(Image.open(file))

    if image.mode != 'RGB':
        image = image.convert('RGB')

    image = ImageOps.fit(image, size, method=Image.LANCZOS)
    out = BytesIO()
    image.save(out, format='WEBP', quality=quality)
    out.seek(0)
    return ContentFile(out.read(), name=f"{uuid.uuid4().hex}.webp")


class ConvertedImageMixin:
    """Converts one image field on the way in and drops the file it replaces.

    Set `IMAGE_FIELD` and `IMAGE_SIZE`; list the mixin before the model base so
    its `save()` runs first.
    """

    IMAGE_FIELD = 'image'
    IMAGE_SIZE = None
    IMAGE_QUALITY = WEBP_QUALITY

    def save(self, *args, **kwargs):
        replaced = self._stored_image_name()
        incoming = getattr(self, self.IMAGE_FIELD)
        changed = getattr(incoming, 'name', None) != replaced

        if changed and incoming:
            setattr(
                self,
                self.IMAGE_FIELD,
                to_webp(incoming, self.IMAGE_SIZE, self.IMAGE_QUALITY),
            )

        super().save(*args, **kwargs)

        if changed and replaced:
            storage = getattr(self, self.IMAGE_FIELD).storage
            if storage.exists(replaced):
                storage.delete(replaced)

    def _stored_image_name(self):
        if not self.pk:
            return None
        try:
            stored = type(self).objects.only(self.IMAGE_FIELD).get(pk=self.pk)
        except type(self).DoesNotExist:
            return None
        image = getattr(stored, self.IMAGE_FIELD)
        return image.name if image else None
