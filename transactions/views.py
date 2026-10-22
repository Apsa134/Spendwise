from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from .forms import TransactionForm
from .models import Transaction

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
    transactions = Transaction.objects.filter(
        user=request.user
    )
    return render(
        request,
        'transactions/transaction_list.html',
        {'transactions': transactions}
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
