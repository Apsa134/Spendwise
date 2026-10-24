import csv
import logging
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .forms import TransactionForm
from .models import Transaction
from core.budget_email import check_budget_email

logger = logging.getLogger(__name__)
def check_budget_email_safely(user, category, date):
    """
    Check the budget and send an alert email if required.
    Email failures should not interrupt transaction operations.
    """
    try:
        check_budget_email(
            user=user,
            category=category,
            month=date.month,
            year=date.year,
        )
    except Exception:
        logger.exception("Failed to send budget alert email.")


@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)

        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()

            # Check the budget after adding an expense.
            if transaction.transaction_type == 'expense':
                check_budget_email_safely(
                    request.user,
                    transaction.category,
                    transaction.date,
                )

            messages.success(
                request,
                'Transaction added successfully.'
            )
            return redirect('transaction_list')

    else:
        form = TransactionForm()

    return render(
        request,
        'transactions/add_transaction.html',
        {'form': form}
    )


@login_required
def transaction_list(request):
    # Only show the logged-in user's transactions.
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-date', '-created_at')

    # Read filters from URL query parameters.
    search_query = request.GET.get('q', '').strip()
    transaction_type = request.GET.get('type', '').strip()
    category = request.GET.get('category', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Search by transaction title or description.
    if search_query:
        transactions = transactions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Filter by income or expense.
    if transaction_type in ('income', 'expense'):
        transactions = transactions.filter(
            transaction_type=transaction_type
        )

    # Filter by category.
    valid_categories = {
        value for value, label
        in Transaction._meta.get_field('category').choices
    }

    if category in valid_categories:
        transactions = transactions.filter(
            category=category
        )

    # Filter by date range.
    if start_date:
        transactions = transactions.filter(
            date__gte=start_date
        )

    if end_date:
        transactions = transactions.filter(
            date__lte=end_date
        )

    paginator = Paginator(transactions, 5)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'transactions': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': search_query,
        'selected_type': transaction_type,
        'selected_category': category,
        'start_date': start_date,
        'end_date': end_date,
        'category_choices': Transaction._meta.get_field(
            'category'
        ).choices,
    }

    return render(
        request,
        'transactions/transaction_list.html',
        context
    )


@login_required
def edit_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        form = TransactionForm(
            request.POST,
            instance=transaction
        )

        if form.is_valid():
            # Preserve the old values before updating.
            old_category = transaction.category
            old_date = transaction.date
            old_type = transaction.transaction_type

            transaction = form.save()

            # Recheck the previous category/month.
            if old_type == 'expense':
                check_budget_email_safely(
                    request.user,
                    old_category,
                    old_date,
                )

            # Recheck the updated category/month.
            if transaction.transaction_type == 'expense':
                check_budget_email_safely(
                    request.user,
                    transaction.category,
                    transaction.date,
                )

            messages.success(
                request,
                'Transaction updated successfully.'
            )
            return redirect('transaction_list')

    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        'transactions/edit_transaction.html',
        {
            'form': form,
            'transaction': transaction,
        }
    )


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        # Preserve values before deleting the transaction.
        old_category = transaction.category
        old_date = transaction.date
        old_type = transaction.transaction_type

        transaction.delete()

        # Recheck spending for the affected budget.
        if old_type == 'expense':
            check_budget_email_safely(
                request.user,
                old_category,
                old_date,
            )

        messages.success(
            request,
            'Transaction deleted successfully.'
        )
        return redirect('transaction_list')

    return render(
        request,
        'transactions/delete_transaction.html',
        {'transaction': transaction}
    )


@login_required
def export_transactions_csv(request):
    # Get only the logged-in user's transactions.
    transactions = Transaction.objects.filter(
        user=request.user
    ).order_by('-date', '-created_at')

    # Read the same filters used on the Transactions page.
    search_query = request.GET.get('q', '').strip()
    transaction_type = request.GET.get('type', '').strip()
    category = request.GET.get('category', '').strip()
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()

    # Apply search.
    if search_query:
        transactions = transactions.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Apply transaction type filter.
    if transaction_type in ('income', 'expense'):
        transactions = transactions.filter(
            transaction_type=transaction_type
        )

    # Apply category filter.
    valid_categories = {
        value for value, label
        in Transaction._meta.get_field('category').choices
    }

    if category in valid_categories:
        transactions = transactions.filter(
            category=category
        )

    # Apply date filters.
    if start_date:
        transactions = transactions.filter(
            date__gte=start_date
        )

    if end_date:
        transactions = transactions.filter(
            date__lte=end_date
        )

    # Create the CSV response.
    response = HttpResponse(
        content_type='text/csv; charset=utf-8'
    )
    response['Content-Disposition'] = (
        'attachment; filename="spendwise_transactions.csv"'
    )

    # Write CSV header and transaction rows.
    writer = csv.writer(response)

    writer.writerow([
        'Title',
        'Description',
        'Category',
        'Date',
        'Type',
        'Amount',
    ])

    for transaction in transactions:
        writer.writerow([
            transaction.title,
            transaction.description,
            transaction.get_category_display(),
            transaction.date,
            transaction.get_transaction_type_display(),
            transaction.amount,
        ])

    return response
