from django.contrib import admin
from .models import (
    Department,
    Expenses,
    Change,
    EmployeePosition,
    Bonus,
    Prize,
    Penalty
)


class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'Guide', 'get_staff_count')
    search_fields = ('Name', 'Description')
    list_filter = ('Guide',)
    filter_horizontal = ('Staff',)

    def get_staff_count(self, obj):
        return obj.Staff.count()

    get_staff_count.short_description = 'Кол-во сотрудников'


class ExpensesAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'amount', 'date', 'Department', 'User')
    search_fields = ('Name', 'Description', 'amount')
    list_filter = ('date', 'Department')
    date_hierarchy = 'date'


class ChangeAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'Schedule')
    search_fields = ('Name', 'Schedule')


class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'Salary', 'Change')
    search_fields = ('Name', 'Description')
    list_filter = ('Change',)
    filter_horizontal = ('Bonuses', 'Prizes', 'Penalties')


class BonusAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'amount')
    search_fields = ('Name', 'reason')
    list_filter = ('amount',)


class PrizeAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'amount')
    search_fields = ('Name', 'reason')
    list_filter = ('amount',)


class PenaltyAdmin(admin.ModelAdmin):
    list_display = ('CustomerID', 'Name', 'amount')
    search_fields = ('Name', 'reason')
    list_filter = ('amount',)


admin.site.register(Department, DepartmentAdmin)
admin.site.register(Expenses, ExpensesAdmin)
admin.site.register(Change, ChangeAdmin)
admin.site.register(EmployeePosition, EmployeePositionAdmin)
admin.site.register(Bonus, BonusAdmin)
admin.site.register(Prize, PrizeAdmin)
admin.site.register(Penalty, PenaltyAdmin)