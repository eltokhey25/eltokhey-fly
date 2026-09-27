"""
dashboard/models.py
Models owned by the dashboard app.
Content models (Trip, Booking, Review, SiteSettings) live in core because the
public site reads them too; only the media library is dashboard-specific.
"""
import os

from django.db import models


class MediaFile(models.Model):
    """One image in the reusable media library."""

    title = models.CharField('عنوان الملف', max_length=255, blank=True)
    file = models.ImageField('الملف', upload_to='dashboard/%Y/%m/')
    alt = models.CharField('النص البديل', max_length=255, blank=True)
    uploaded_at = models.DateTimeField('تاريخ الرفع', auto_now_add=True)

    class Meta:
        """List the newest upload first in the media library."""
        ordering = ['-uploaded_at']
        verbose_name = 'ملف وسائط'
        verbose_name_plural = 'مكتبة الوسائط'

    def __str__(self):
        """Return the title, falling back to the uploaded filename."""
        return self.title or os.path.basename(self.file.name)

    @property
    def size_display(self):
        """Return the file size as a human-readable Arabic string.

        Returns:
            str: e.g. '248 ك.ب'; em dash when no file is attached.
        """
        if not self.file:
            return '—'
        size = self.file.size or 0
        for unit in ('بايت', 'ك.ب', 'م.ب', 'ج.ب'):
            if size < 1024:
                return f'{size:.0f} {unit}'
            size /= 1024
        return f'{size:.1f} م.ب'

    @property
    def kind(self):
        """Classify the upload so the library can badge it.

        Returns:
            str: 'صورة' for a known image extension, otherwise 'ملف'.
        """
        name = (self.file.name or '').lower()
        if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            return 'صورة'
        return 'ملف'