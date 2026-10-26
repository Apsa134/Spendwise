
import calendar
from datetime import date
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from budgets.models import Budget
from transactions.models import Transaction
from core.management.commands.send_monthly_summary import Command


@login_required
def home(request):
    today = timezone.localdate()
    # Monthly report dropdown data
    month_choices = [
        (month, calendar.month_name[month])
        for month in range(1, 13)
    ]
    report_month = today.month
    report_year = today.year
    report_years = range(2024, today.year + 1)

    # All transactions belonging to the logged-in user
    user_transactions = Transaction.objects.filter(
        user=request.user
    )
    # Separate completed and planned transactions
    completed_transactions = user_transactions.filter(
        status='completed'
    )
    planned_transactions = user_transactions.filter(
        status='planned'
    ).order_by('date', 'created_at')

    # Planned transactions that need reminders
    due_today_transactions = planned_transactions.filter(
        date=today
    )
    overdue_transactions = planned_transactions.filter(
        date__lt=today
    )
    upcoming_transactions = planned_transactions.filter(
        date__gt=today
    )

    # All-time totals: completed transactions only
    total_income = (
        completed_transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    total_expenses = (
        completed_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    balance = total_income - total_expenses
    # All-time planned income
    planned_income = (
        planned_transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    # All-time planned expenses
    planned_expenses = (
        planned_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    # Projected balance after all planned transactions
    projected_balance = (
        balance + planned_income - planned_expenses
    )
    # Current month's completed transactions
    monthly_transactions = completed_transactions.filter(
        date__year=today.year,
        date__month=today.month,
    )

    monthly_income = (
        monthly_transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    monthly_expenses = (
        monthly_transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total']
        or Decimal('0.00')
    )

    monthly_savings = monthly_income - monthly_expenses

    # Current month's completed expenses by category
    category_summary = (
        monthly_transactions.filter(
            transaction_type='expense'
        )
        .values('category')
        .annotate(total=Sum('amount'))
        .order_by('category')
    )

    category_labels = dict(Transaction.CATEGORY_CHOICES)

    category_chart_labels = [
        category_labels.get(
            item['category'],
            item['category']
        )
        for item in category_summary
    ]

    category_chart_values = [
        float(item['total'])
        for item in category_summary
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

        month_transactions = completed_transactions.filter(
            date__year=year,
            date__month=month_number,
        )

        income = (
            month_transactions.filter(
                transaction_type='income'
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        expenses = (
            month_transactions.filter(
                transaction_type='expense'
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        monthly_chart_labels.append(
            date(year, month_number, 1).strftime('%b %Y')
        )

        monthly_income_values.append(float(income))
        monthly_expense_values.append(float(expenses))

    # Latest five completed transactions
    recent_transactions = completed_transactions.order_by(
        '-date', '-created_at'
    )[:5]

    # Budget alerts for the current month
    current_budgets = Budget.objects.filter(
        user=request.user,
        month=today.month,
        year=today.year,
    )

    # Only completed expenses count toward budgets
    current_expenses = completed_transactions.filter(
        transaction_type='expense',
        date__year=today.year,
        date__month=today.month,
    )

    budget_alerts = []

    for budget in current_budgets:
        spent = (
            current_expenses.filter(
                category=budget.category
            ).aggregate(total=Sum('amount'))['total']
            or Decimal('0.00')
        )

        if budget.amount <= 0:
            continue

        percentage = (spent / budget.amount) * 100

        # Show alerts when spending reaches 80%
        if percentage >= 80:
            status = (
                'exceeded'
                if percentage >= 100
                else 'warning'
            )

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

    # Most urgent budget alerts first
    budget_alerts.sort(
        key=lambda alert: alert['percentage'],
        reverse=True,
    )

    # Dashboard context
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'balance': balance,

        'planned_income': planned_income,
        'planned_expenses': planned_expenses,
        'projected_balance': projected_balance,
        
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_savings': monthly_savings,

        'recent_transactions': recent_transactions,
        'planned_transactions': planned_transactions,

        'category_chart_labels': category_chart_labels,
        'category_chart_values': category_chart_values,

        'monthly_chart_labels': monthly_chart_labels,
        'monthly_income_values': monthly_income_values,
        'monthly_expense_values': monthly_expense_values,

        'budget_alerts': budget_alerts,

        # Monthly report dropdowns
        'month_choices': month_choices,
        'report_month': report_month,
        'report_year': report_year,
        'report_years': report_years,

        'due_today_transactions': due_today_transactions,
        'overdue_transactions': overdue_transactions,
        'upcoming_transactions': upcoming_transactions,
    }

    return render(request, 'home.html', context)


@login_required
def send_monthly_report(request):
    if request.method != 'POST':
        return redirect('home')

    try:
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        if not 1 <= month <= 12:
            raise ValueError

        today = timezone.localdate()

        if year < 2024 or year > today.year:
            raise ValueError

        if year == today.year and month > today.month:
            raise ValueError

        month_name = calendar.month_name[month]

        if not request.user.email:
            messages.error(
                request,
                'Please add your email address to your profile first.'
            )
            return redirect('home')

        # Send the selected month's report to this user
        Command().build_and_send_email(
            request.user,
            month,
            year,
            month_name,
        )

        messages.success(
            request,
            f'Your {month_name} {year} report has been '
            f'sent to {request.user.email}.'
        )

    except ValueError:
        messages.error(
            request,
            'Please select a valid month and year.'
        )

    except Exception:
        messages.error(
            request,
            'Unable to send your report right now. Please try again later.'
        )

    return redirect('home')
