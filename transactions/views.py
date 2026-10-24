from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .forms import TransactionForm
from .models import Transaction
from django.db.models import Q
from django.core.paginator import Paginator

@login_required
def add_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
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

    # Read filters from the URL query parameters.
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
        transactions = transactions.filter(category=category)

    # Filter by date range.
    if start_date:
        transactions = transactions.filter(date__gte=start_date)

    if end_date:
        transactions = transactions.filter(date__lte=end_date)

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
        form = TransactionForm(request.POST, instance=transaction)

        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully.')
            return redirect('transaction_list')
    else:
        form = TransactionForm(instance=transaction)

    return render(
        request,
        'transactions/edit_transaction.html',
        {'form': form, 'transaction': transaction}
    )


@login_required
def delete_transaction(request, pk):
    transaction = get_object_or_404(
        Transaction,
        pk=pk,
        user=request.user
    )

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully.')
        return redirect('transaction_list')

    return render(
        request,
        'transactions/delete_transaction.html',
        {'transaction': transaction}
    )
