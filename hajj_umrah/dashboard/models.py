import os

from django.db import models


class MediaFile(models.Model):
    title = models.CharField('عنوان الملف', max_length=255, blank=True)
    file = models.ImageField('الملف', upload_to='dashboard/%Y/%m/')
    alt = models.CharField('النص البديل', max_length=255, blank=True)
    uploaded_at = models.DateTimeField('تاريخ الرفع', auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'ملف وسائط'
        verbose_name_plural = 'مكتبة الوسائط'

    def __str__(self):
        return self.title or os.path.basename(self.file.name)

    @property
    def size_display(self):
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
        name = (self.file.name or '').lower()
        if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg')):
            return 'صورة'
        return 'ملف'