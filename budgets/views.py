
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect, get_object_or_404
from .forms import BudgetForm
from .models import Budget
from datetime import date
from decimal import Decimal
from django.db.models import Sum
from transactions.models import Transaction

@login_required
def budget_list(request):
    today = date.today()
    # Selected month and year; default to the current month
    try:
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
        if not 1 <= month <= 12 or not 2000 <= year <= 2100:
            raise ValueError
    except (TypeError, ValueError):
        month = today.month
        year = today.year
    # Get this user's expenses for the selected month
    expenses = Transaction.objects.filter(
        user=request.user,
        transaction_type='expense',
        status='completed',
        date__month=month,
        date__year=year,
    )
    # Total expenses grouped by category for the pie chart
    expense_summary = list(
        expenses.values('category')
        .annotate(total=Sum('amount'))
        .order_by('category')
    )

    # Add readable category names and prepare chart data
    category_labels = dict(Transaction.CATEGORY_CHOICES)

    chart_labels = [
        category_labels.get(item['category'], item['category'])
        for item in expense_summary
    ]

    chart_values = [
        float(item['total'] or 0)
        for item in expense_summary
    ]

    # Get this user's budgets for the selected month
    budgets = Budget.objects.filter(
        user=request.user,
        month=month,
        year=year,
    )

    budget_details = []

    for budget in budgets:
        spent = expenses.filter(
            category=budget.category
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        remaining = budget.amount - spent
        percentage = (spent / budget.amount) * 100

        budget_details.append({
            'budget': budget,
            'spent': spent,
            'remaining': remaining,
            'percentage': min(float(percentage), 100),
            'actual_percentage': float(percentage),
            'exceeded': spent > budget.amount,
        })

    context = {
        'budgets': budgets,
        'budget_details': budget_details,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'selected_month': month,
        'selected_year': year,
        'month_name': date(year, month, 1).strftime('%B'),
        'month_choices': Budget.MONTH_CHOICES,

    }

    return render(request, 'budgets/budget_list.html', context)


@login_required
def add_budget(request):
    if request.method == 'POST':
        form = BudgetForm(request.POST)

        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user

            try:
                with transaction.atomic():
                    budget.save()

                messages.success(
                    request,
                    'Monthly budget added successfully.'
                )
                return redirect('budget_list')

            except IntegrityError:
                form.add_error(
                    None,
                    'A budget for this category and month already exists.'
                )
    else:
        form = BudgetForm()

    return render(
        request,
        'budgets/add_budget.html',
        {'form': form}
    )


@login_required
def edit_budget(request, pk):
    budget = get_object_or_404(Budget, pk=pk, user=request.user)

    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(request, 'Budget updated successfully.')
                return redirect('budget_list')

            except IntegrityError:
                form.add_error(
                    None,
                    'A budget for this category and month already exists.'
                )
    else:
        form = BudgetForm(instance=budget)

    return render(
        request,
        'budgets/edit_budget.html',
        {'form': form, 'budget': budget}
    )

@login_required
def delete_budget(request, pk):
    budget = get_object_or_404(
        Budget,
        pk=pk,
        user=request.user
    )
    if request.method == 'POST':
        budget.delete()
        messages.success(request, 'Budget deleted successfully.')
        return redirect('budget_list')

    return render(
        request,
        'budgets/delete_budget.html',
        {'budget': budget}
    )
