
from django.conf import settings
from django.db import models


class BudgetEmailAlert(models.Model):
    STATUS_CHOICES = [
        ('warning', 'Budget Warning'),
        ('exceeded', 'Budget Exceeded'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    category = models.CharField(max_length=100)
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
    )
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year', 'status'],
                name='unique_budget_email_alert',
            ),
        ]

    def __str__(self):
        return (
            f'{self.user} - {self.category} - '
            f'{self.month}/{self.year} - {self.status}'
        )

class MonthlySummaryEmail(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    month = models.PositiveSmallIntegerField()
    year = models.PositiveSmallIntegerField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'month', 'year'],
                name='unique_monthly_summary_email',
            ),
        ]
        ordering = ['-year', '-month']

    def __str__(self):
        return (
            f'{self.user} - Monthly Summary - '
            f'{self.month}/{self.year}'
        )
