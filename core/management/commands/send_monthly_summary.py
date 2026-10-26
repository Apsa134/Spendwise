
import calendar
from datetime import date
from decimal import Decimal
from html import escape

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from budgets.models import Budget
from transactions.models import Transaction
from core.models import MonthlySummaryEmail
from core.email_utils import send_email


class Command(BaseCommand):
    help = 'Send monthly financial summary emails to users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=int,
            help='Month to report (1-12). Defaults to the previous month.',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Year to report. Defaults to the previous month.',
        )

    def handle(self, *args, **options):
        month = options['month']
        year = options['year']

        if (month is None) != (year is None):
            raise CommandError(
                'Provide both --month and --year, or neither.'
            )

        if month is None:
            today = timezone.localdate()

            if today.month == 1:
                month, year = 12, today.year - 1
            else:
                month, year = today.month - 1, today.year

        if not 1 <= month <= 12:
            raise CommandError('Month must be between 1 and 12.')

        month_name = calendar.month_name[month]
        User = get_user_model()

        users = User.objects.exclude(email='')

        sent_count = 0
        skipped_count = 0
        failed_count = 0

        for user in users.iterator():
            try:
                sent = self.send_user_summary(
                    user, month, year, month_name
                )

                if sent:
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Sent {month_name} {year} summary '
                            f'to {user.email}'
                        )
                    )
                else:
                    skipped_count += 1
                    self.stdout.write(
                        f'Skipped {user.email}: '
                        'summary already sent.'
                    )

            except Exception as exc:
                failed_count += 1
                self.stderr.write(
                    self.style.ERROR(
                        f'Failed for {user.email}: {exc}'
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Finished. Sent: {sent_count}, '
                f'Skipped: {skipped_count}, '
                f'Failed: {failed_count}.'
            )
        )

    def send_user_summary(self, user, month, year, month_name):
        with db_transaction.atomic():
            _, created = MonthlySummaryEmail.objects.get_or_create(
                user=user,
                month=month,
                year=year,
            )

            if not created:
                return False

        try:
            self.build_and_send_email(
                user, month, year, month_name
            )
        except Exception:
            # Permit a retry if sending fails.
            MonthlySummaryEmail.objects.filter(
                user=user,
                month=month,
                year=year,
            ).delete()
            raise

        return True

    def build_and_send_email(self, user, month, year, month_name):
        transactions = Transaction.objects.filter(
            user=user,
            date__month=month,
            date__year=year,
            status='completed',
        )

        income = transactions.filter(
            transaction_type='income'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        expenses = transactions.filter(
            transaction_type='expense'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        savings = income - expenses

        category_totals = (
            transactions.filter(transaction_type='expense')
            .values('category')
            .annotate(total=Sum('amount'))
            .order_by('-total')
        )

        category_rows = []

        for item in category_totals:
            category_label = Transaction._meta.get_field(
                'category'
            ).choices

            labels = dict(category_label)
            category_name = labels.get(
                item['category'], item['category']
            )

            category_rows.append(
                '<tr>'
                f'<td>{escape(str(category_name))}</td>'
                f'<td>₹{item["total"]:,.2f}</td>'
                '</tr>'
            )

        if not category_rows:
            category_rows.append(
                '<tr><td colspan="2">No expenses recorded.</td></tr>'
            )

        budgets = Budget.objects.filter(
            user=user,
            month=month,
            year=year,
        ).order_by('category')

        budget_rows = []

        for budget in budgets:
            spent = (
                transactions.filter(
                    transaction_type='expense',
                    category=budget.category,
                ).aggregate(total=Sum('amount'))['total']
                or Decimal('0')
            )

            remaining = budget.amount - spent

            if spent > budget.amount:
                status = f'Exceeded by ₹{abs(remaining):,.2f}'
            else:
                status = f'₹{remaining:,.2f} remaining'

            budget_rows.append(
                '<tr>'
                f'<td>{escape(str(budget.category))}</td>'
                f'<td>₹{budget.amount:,.2f}</td>'
                f'<td>₹{spent:,.2f}</td>'
                f'<td>{status}</td>'
                '</tr>'
            )

        if not budget_rows:
            budget_rows.append(
                '<tr><td colspan="4">No budgets set for this month.</td></tr>'
            )

        username = escape(user.get_username())

        html_content = f"""
        <div style="font-family: Arial, sans-serif;
                    max-width: 700px; margin: auto; color: #152b25;
                    line-height: 1.6;">
            <h1 style="color: #087f5b;">SpendWise Monthly Summary</h1>
            <p>Hello {username},</p>
            <p>Here is your financial summary for
               <strong>{month_name} {year}</strong>.</p>

            <table style="width: 100%; border-collapse: collapse;"
                   border="1" cellpadding="10">
                <tr><th>Income</th><th>Expenses</th><th>Savings</th></tr>
                <tr>
                    <td>₹{income:,.2f}</td>
                    <td>₹{expenses:,.2f}</td>
                    <td>₹{savings:,.2f}</td>
                </tr>
            </table>

            <h2 style="color: #087f5b;">Category-wise Spending</h2>
            <table style="width: 100%; border-collapse: collapse;"
                   border="1" cellpadding="10">
                <tr><th>Category</th><th>Spent</th></tr>
                {''.join(category_rows)}
            </table>

            <h2 style="color: #087f5b;">Budget Overview</h2>
            <table style="width: 100%; border-collapse: collapse;"
                   border="1" cellpadding="10">
                <tr>
                    <th>Category</th>
                    <th>Budget</th>
                    <th>Spent</th>
                    <th>Status</th>
                </tr>
                {''.join(budget_rows)}
            </table>

            <p>Keep tracking your spending and working toward
               your financial goals!</p>
            <p><strong>The SpendWise Team</strong></p>
        </div>
        """

        send_email(
            to_email=user.email,
            subject=f'Your SpendWise Summary - {month_name} {year}',
            html_content=html_content,
        )
