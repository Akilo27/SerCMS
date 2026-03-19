from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from moderation.views import ProductImportView, ExpenseListView, AggregatedExpenseDailyView
from rest_framework_simplejwt import views as jwt_views

from shop.views import SubmitReviewView

urlpatterns = [
    # path("__debug__/", include("debug_toolbar.urls")),
    path("_nested_admin/", include("nested_admin.urls")),
    path("developer_management/", admin.site.urls),
    # path("silk/", include("silk.urls", namespace="silk")),
    path("api/", include("apirestframework.urls")),
    path("rosetta/", include("rosetta.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path('api/products/import/', ProductImportView.as_view(), name='product-import'),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path("submit-review/", SubmitReviewView.as_view(), name="submit_review"),
    path('api/expenses/', ExpenseListView.as_view(), name='expense-list'),
    path('api/aggregated-expenses/daily/', AggregatedExpenseDailyView.as_view(),
         name='aggregated-expenses-daily'),


]
urlpatterns += i18n_patterns(
    path("set_language/", include("django.conf.urls.i18n")),
    path("", include("webmain.urls", namespace="webmain")),
    path("profile/", include("useraccount.urls", namespace="useraccount")),
    path("moderation/", include("moderation.urls", namespace="moderation")),
    path("", include("hr.urls", namespace="hr")),
    path("", include("kpi.urls", namespace="kpi")),
    path("", include("shop.urls", namespace="shop")),
    path("", include("payment.urls", namespace="payment")),
    path("", include("delivery.urls", namespace="delivery")),
    path("chat/", include("chat.urls", namespace="chat")),
    path("crm/", include("crm.urls", namespace="crm")),
    path("", include("integration_import.urls", namespace="integration_import")),
    path("", include("documentation.urls")),
    # Другие ваши URL, которые должны поддерживать смену языка
)

if "rosetta" in settings.INSTALLED_APPS:
    urlpatterns += [re_path("rosetta/", include("rosetta.urls"))]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
