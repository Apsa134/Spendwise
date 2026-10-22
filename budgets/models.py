
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator

class Budget(models.Model):
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('shopping', 'Shopping'),
        ('bills', 'Bills & Utilities'),
        ('health', 'Health'),
        ('education', 'Education'),
        ('entertainment', 'Entertainment'),
        ('grocery','Grocery'),
        ('other', 'Other'),
    ]
    MONTH_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='budgets'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    month = models.PositiveSmallIntegerField(
        choices=MONTH_CHOICES
    )
    year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year'],
                name='unique_user_category_month_year_budget'
            )
        ]
        ordering = ['-year', '-month', 'category']
    def __str__(self):
        return (
            f"{self.user.username} - {self.get_category_display()} "
            f"- {self.month}/{self.year}"
        )
