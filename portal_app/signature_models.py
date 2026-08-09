from django.db import models
from django.contrib.auth import get_user_model

class Signature(models.Model):
    ROLE_CHOICES = (
        ('gram_sevak', 'Gram Sevak'),
        ('sarpanch', 'Sarpanch'),
    )
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, limit_choices_to={'role__in': ['staff', 'admin']})
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    image = models.ImageField(upload_to='signatures/', blank=False, null=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('role', 'user')
        verbose_name = 'Digital Signature'
        verbose_name_plural = 'Digital Signatures'

    def __str__(self):
        return f"{self.get_role_display()} - {self.user.get_full_name()}"
