from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal


class MonthlyKPI(models.Model):
    MONTH_CHOICES = [
        ('1', 'Январь'),
        ('2', 'Февраль'),
        ('3', 'Март'),
        ('4', 'Апрель'),
        ('5', 'Май'),
        ('6', 'Июнь'),
        ('7', 'Июль'),
        ('8', 'Август'),
        ('9', 'Сентябрь'),
        ('10', 'Октябрь'),
        ('11', 'Ноябрь'),
        ('12', 'Декабрь'),
    ]
    # Поля для фильтрации по месяцу и году
    month = models.CharField(
        max_length=2,
        choices=MONTH_CHOICES,
        verbose_name='Месяц'
    )
    employee = models.ForeignKey(
        'Employee',
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        related_name="monthly_kpis"
    )
    completion_date = models.DateField(
        verbose_name='Дата выполнения',
        null=True,
        blank=True
    )
    completed = models.BooleanField(
        verbose_name='Выполнено',
        default=False
    )
    # Связи с конкретными объектами (одно из трех)
    bonus = models.ForeignKey(
        'Bonus',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Бонус'
    )
    prize = models.ForeignKey(
        'Prize',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Премия'
    )
    penalty = models.ForeignKey(
        'Penalty',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name='Штраф'
    )

    is_approved = models.BooleanField(
        verbose_name='Подтверждено',
        default=False
    )

    class Meta:
        verbose_name = 'Ежемесячный KPI'
        verbose_name_plural = 'Ежемесячные KPI'



class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name="employee_profile"
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Отдел',
        related_name="employees"
    )
    position = models.ForeignKey(
        'EmployeePosition',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Должность'
    )
    hire_date = models.DateField(verbose_name='Дата приема на работу', auto_now_add=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.position})"



class Department(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID отдела')
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название отдела')
    Description = models.TextField(verbose_name='Описание отдела', blank=True)
    Guide = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="departments_guided",
        verbose_name="Руководитель",
    )
    Staff = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="departments_worked",
        verbose_name="Сотрудники",
        blank=True
    )
    Chart = models.TextField(blank=True, null=True, verbose_name='График работы')

    class Meta:
        verbose_name = 'Отдел'
        verbose_name_plural = 'Отделы'
        ordering = ['Name']

    def __str__(self):
        return self.Name


class Expenses(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID расхода')
    User = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Пользователь",
        related_name="expenses_created"
    )
    Department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name='Отдел',
        related_name="department_expenses"
    )
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название расхода')
    Description = models.TextField(verbose_name='Описание', blank=True)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма'
    )
    date = models.DateField(verbose_name='Дата')

    class Meta:
        verbose_name = 'Расход'
        verbose_name_plural = 'Расходы'

    def __str__(self):
        return f"{self.Name} - {self.amount}"


class Change(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID смены')
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название смены')
    Schedule = models.CharField(max_length=255, db_index=True, verbose_name='График')

    class Meta:
        verbose_name = 'Смена'
        verbose_name_plural = 'Смены'
        ordering = ['Name']

    def __str__(self):
        return f"{self.Name} ({self.Schedule})"

class EmployeePosition(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID позиции')
    Name = models.CharField(max_length=255, unique=True, verbose_name='Название должности')
    Description = models.TextField(verbose_name='Описание', blank=True)
    Salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Оклад'
    )
    Change = models.ForeignKey(
        Change,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Смена',
        related_name="employees"
    )
    Bonuses = models.ManyToManyField(
        'Bonus',
        related_name='employee_positions',
        verbose_name='Бонусы',
        blank=True
    )
    Prizes = models.ManyToManyField(
        'Prize',
        related_name='employee_positions',
        verbose_name='Премии',
        blank=True
    )
    Penalties = models.ManyToManyField(
        'Penalty',
        related_name='employee_positions',
        verbose_name='Штрафы',
        blank=True
    )

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должность'



class Bonus(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID бонуса')
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма'
    )
    reason = models.TextField(verbose_name='Причина')

    class Meta:
        verbose_name = 'Бонус'
        verbose_name_plural = 'Бонусы'

    def __str__(self):
        return f"{self.Name} - {self.amount}"

class Prize(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID бонуса')
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма'
    )
    reason = models.TextField(verbose_name='Причина')

    class Meta:
        verbose_name = 'Премия'
        verbose_name_plural = 'Премии'

    def __str__(self):
        return f"{self.Name} - {self.amount}"



class Penalty(models.Model):
    CustomerID = models.AutoField(primary_key=True, verbose_name='ID штрафа')
    Name = models.CharField(max_length=255, db_index=True, verbose_name='Название')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Сумма'
    )
    reason = models.TextField(verbose_name='Причина')

    class Meta:
        verbose_name = 'Штраф'
        verbose_name_plural = 'Штрафы'

    def __str__(self):
        return f"{self.Name} - {self.amount}"