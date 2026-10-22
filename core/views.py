
from datetime import date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from budgets.models import Budget
from transactions.models import Transaction
@login_required
def home(request):
    today = timezone.localdate()

    user_transactions = Transaction.objects.filter(user=request.user)

    # All-time totals
    total_income = (
        user_transactions.filter(transaction_type='income')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    total_expenses = (
        user_transactions.filter(transaction_type='expense')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    balance = total_income - total_expenses

    # Current month's totals
    monthly_transactions = user_transactions.filter(
        date__year=today.year,
        date__month=today.month,
    )

    monthly_income = (
        monthly_transactions.filter(transaction_type='income')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    monthly_expenses = (
        monthly_transactions.filter(transaction_type='expense')
        .aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    monthly_savings = monthly_income - monthly_expenses

    # Current month's expenses grouped by category
    category_summary = (
        monthly_transactions.filter(transaction_type='expense')
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('category')
    )

    category_labels = dict(Transaction.CATEGORY_CHOICES)

    category_chart_labels = [
        category_labels.get(item['category'], item['category'])
        for item in category_summary
    ]

    category_chart_values = [
        float(item['total']) for item in category_summary
    ]

    # Income and expenses for the last six months
    monthly_chart_labels = []
    monthly_income_values = []
    monthly_expense_values = []

    for offset in range(5, -1, -1):
        month_number = today.month - offset
        year = today.year

        while month_number <= 0:
            month_number += 12
            year -= 1

        month_transactions = user_transactions.filter(
            date__year=year,
            date__month=month_number,
        )

        income = (
            month_transactions.filter(transaction_type='income')
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        expenses = (
            month_transactions.filter(transaction_type='expense')
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        monthly_chart_labels.append(
            date(year, month_number, 1).strftime('%b %Y')
        )
        monthly_income_values.append(float(income))
        monthly_expense_values.append(float(expenses))

    # Latest five transactions
    recent_transactions = user_transactions.order_by(
        '-date', '-created_at'
    )[:5]


    
    # Budget alerts for the current month
    current_budgets = Budget.objects.filter(
        user=request.user,
        month=today.month,
        year=today.year,
    )

    current_expenses = user_transactions.filter(
        transaction_type='expense',
        date__year=today.year,
        date__month=today.month,
    )

    budget_alerts = []

    for budget in current_budgets:
        spent = (
            current_expenses.filter(category=budget.category)
            .aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        # Avoid division by zero
        if budget.amount <= 0:
            continue

        percentage = (spent / budget.amount) * 100

        # Show alerts only when spending reaches 80%
        if percentage >= 80:
            if percentage > 100:
                status = 'exceeded'
            else:
                status = 'warning'

            budget_alerts.append({
                'category': budget.get_category_display(),
                'spent': spent,
                'budget_amount': budget.amount,
                'remaining': max(
                    Decimal('0.00'),
                    budget.amount - spent
                ),
                'overspent': max(
                    Decimal('0.00'),
                    spent - budget.amount
                ),
                'percentage': float(percentage),
                'status': status,
            })

    # Show the most urgent alerts first
    budget_alerts.sort(
        key=lambda alert: alert['percentage'],
        reverse=True,
    )
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,
        'recent_transactions': recent_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,
        'category_chart_labels': category_chart_labels,
        'category_chart_values': category_chart_values,
        'monthly_chart_labels': monthly_chart_labels,
        'monthly_income_values': monthly_income_values,
        'monthly_expense_values': monthly_expense_values,
        'budget_alerts': budget_alerts,
    }
    return render(request, 'home.html', context)
