
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from budgets.models import Budget
from transactions.models import Transaction
from .models import BudgetEmailAlert
from .email_utils import send_email



def check_budget_email(user, category, month, year):
    """
    Check a user's monthly category budget and send an email
    when spending reaches 80% or exceeds the budget.
    """

    if not user.email:
        return

    budget = Budget.objects.filter(
        user=user,
        category=category,
        month=month,
        year=year,
    ).first()

    if not budget or budget.amount <= 0:
        return

    spent = Transaction.objects.filter(
        user=user,
        category=category,
        transaction_type='expense',
        date__year=year,
        date__month=month,
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

    percentage = (spent / budget.amount) * 100

    if percentage >= 100:
        status = 'exceeded'
        subject = f'{category} budget exceeded - SpendWise'
        overspent = spent - budget.amount

        message = (
            f'You have exceeded your {category} budget for '
            f'{month}/{year} by ₹{overspent:.2f}. '
            f'Budget: ₹{budget.amount:.2f}; '
            f'Spent: ₹{spent:.2f}.'
        )

    elif percentage >= 80:
        status = 'warning'
        subject = f'{category} budget warning - SpendWise'
        remaining = budget.amount - spent

        message = (
            f'You have used {percentage:.1f}% of your {category} '
            f'budget for {month}/{year}. '
            f'Budget: ₹{budget.amount:.2f}; '
            f'Spent: ₹{spent:.2f}; '
            f'Remaining: ₹{remaining:.2f}.'
        )

    else:
        return

    # Avoid sending the same alert more than once per month.
    with db_transaction.atomic():
        alert, created = BudgetEmailAlert.objects.get_or_create(
            user=user,
            category=category,
            month=month,
            year=year,
            status=status,
        )

        if not created:
            return

        try:
            send_email(
                to_email=user.email,
                subject=subject,
                html_content=f"""
                    <div style="font-family: Arial, sans-serif;
                                max-width: 600px; margin: auto;
                                padding: 24px;">
                        <h2 style="color: #087f5b;">
                            SpendWise Budget Alert
                        </h2>
                        <p>Hello {user.username},</p>
                        <p>{message}</p>
                        <p>
                            Open SpendWise to review your transactions
                            and manage your budget.
                        </p>
                        <p>The SpendWise Team</p>
                    </div>
                """,
            )
        except Exception:
            # Allow a later retry if the email service fails.
            alert.delete()
            raise
