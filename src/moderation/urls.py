from django.urls import path
from . import views

app_name = "moderation"
from .views import subscribe


urlpatterns = [
    path("",views.ModerationHome.as_view(),name='home'),

    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("subscribe/", subscribe, name="subscribe"),
    path("dashbord/", views.DashbordView.as_view(), name="dashbord"),
    path("languages/", views.LanguageListView.as_view(), name="language_list"),
    path(
        "languages/edit/<str:code>/",
        views.LanguageEditView.as_view(),
        name="language_edit",
    ),
    path("indevelopment/", views.IndevelopmentView.as_view(), name="indevelopment"),
    path("edit_profile/", views.EditMyProfileView.as_view(), name="edit_profile"),
    path("groups/", views.GroupListView.as_view(), name="groups_list"),
    path("groups/create/", views.GroupCreateView.as_view(), name="groups_create"),
    path('settings/', views.SettingsModerationEditView.as_view(), name='settings_edit'),
    path("shifts/<uuid:user_id>/", views.UserShiftListView.as_view(), name="user_shift_list"),
    path('work_shift_update/', views.WorkShiftUpdateView.as_view(), name='work_shift_update'),
    path('products/copy/', views.ProductCopyView.as_view(), name='product_copy'),
    path('update-product-positions/', views.update_product_positions, name='update_product_positions'),
    path('check/', views.ProductsCheckView.as_view(), name='check'),
    path('ajax/update-media-positions/', views.ajax_update_media_positions, name='ajax_update_media_positions'),
    path('ajax/get-tags/', views.ajax_get_tags, name='ajax_get_tags'),
    path('ajax/get-tags-list/', views.ajax_get_tags_list, name='ajax_get_tags_list'),
    path('ajax/create-tag/', views.ajax_create_tag, name='ajax_create_tag'),
    path('ajax/edit-tag/', views.ajax_edit_tag, name='ajax_edit_tag'),
    path('ajax/toggle-tag/', views.ajax_toggle_tag, name='ajax_toggle_tag'),


    path('product_expense_position_list', views.ProductExpensePositionList.as_view(), name='product_expense_position'),
    path('expenses/create/', views.ProductExpensePositionCreateView.as_view(), name='expenses_create'),
    path('expenses/update/<int:pk>/', views.ProductExpensePositionUpdateView.as_view(), name='expenses_update'),
    path('expenses/delete/', views.expenses_delete, name='expenses_delete'),

    path('product_expense_purchase_list', views.ProductExpensePurchaseList.as_view(), name='product_purchase_list'),
    path('purchase/expenses/create/', views.ProductExpensePurchaseCreateView.as_view(), name='purchase_expenses_create'),
    path('purchase/expenses/update/<int:pk>/', views.ProductExpensePurchaseUpdateView.as_view(), name='purchase_expenses_update'),
    path('purchase/expenses/delete/', views.purchase_expenses_delete, name='purchase_expenses_delete'),
    path('create-order/', views.create_order, name='create_order'),
    path('check-payment-status/', views.CheckPaymentStatusView.as_view(), name='check_payment_status'),


    path(
        "groups/<uuid:pk>/update/",
        views.GroupUpdateView.as_view(),
        name="groups_update",
    ),
    path(
        "groups/<uuid:pk>/ajax-delete/",
        views.GroupAjaxDeleteView.as_view(),
        name="ajax_group_delete",
    ),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("workerslist/", views.WorkerListView.as_view(), name="worker_list"),
    path("clientslist/", views.ClientListView.as_view(), name="clients_list"),
    path("user/<slug:pk>/delete/", views.UserDeleteView.as_view(), name="user_delete"),
    path(
        "worker/<slug:pk>/delete/",
        views.WorkerDeleteView.as_view(),
        name="worker_delete",
    ),
    path("profile/block/<uuid:pk>/", views.BlockUserView.as_view(), name="block_user"),
    path(
        "profile/unblock/<uuid:pk>/",
        views.UnblockUserView.as_view(),
        name="unblock_user",
    ),
    path(
        "profile/restore/<uuid:pk>/",
        views.RestoreUserView.as_view(),
        name="restore_user",
    ),
    path(
        "profile/deleteuser/<uuid:pk>/",
        views.DeleteUserView.as_view(),
        name="delete_user",
    ),
    path(
        "profile/edit/<slug:pk>/", views.EditProfileView.as_view(), name="edit_profiles"
    ),
    path(
        "profile/editclient/<slug:pk>/",
        views.EditProfileClientView.as_view(),
        name="edit_profile_client",
    ),
    path(
        "user-detail/<uuid:user_id>/",
        views.UserDetailView.as_view(),
        name="user_detail",
    ),
    path(
        "profileworker/edit/<uuid:user_id>/",
        views.EditWorkerProfileView.as_view(),
        name="edit_worker_profiles",
    ),
    path("create_worker/", views.SignUpWorkerView.as_view(), name="create_worker"),
    path("create_user/", views.SignUpView.as_view(), name="create_user"),
    path("create_client/", views.SignClientUpView.as_view(), name="create_client"),
    # Выплаты
    path("withdraw_moderation/", views.WithdrawPage.as_view(), name="withdraw"),
    path("withdraw_all/", views.WithdrawAllPage.as_view(), name="withdraw_all"),
    path(
        "withdraw_moderation/create/",
        views.WithdrawCreateView.as_view(),
        name="withdraw_create",
    ),
    # Карта
    path("cards/create/", views.CardsCreateView.as_view(), name="cards_create"),
    path(
        "cards/update/<int:pk>/", views.CardsUpdateView.as_view(), name="cards_update"
    ),
    path("tickets/", views.TicketsView.as_view(), name="tickets"),
    path("tickets/delete/", views.TicketDeleteView.as_view(), name="ticket_delete"),
    path(
        "tickets/<uuid:ticket_id>/add_comment/",
        views.TicketCommentCreateView.as_view(),
        name="add_comment",
    ),
    path(
        "tickets/<slug:pk>/", views.TicketMessageView.as_view(), name="ticket_message"
    ),
    # Документация
    path("documentation/", views.Documentation.as_view(), name="documentation"),
    path(
        "documentation/create/",
        views.DocumentationCreateView.as_view(),
        name="docs_create",
    ),
    path(
        "documentation/update/<int:pk>/",
        views.DocumentationUpdateView.as_view(),
        name="docs_update",
    ),
    path(
        "documentation/delete/",
        views.DocumentationDeleteView.as_view(),
        name="docs_delete",
    ),
    path(
        "documentation/add_files/<int:documentation_id>/",
        views.UploadFileView.as_view(),
        name="add_files",
    ),
    path(
        "documentation/delete_file/<int:file_id>/",
        views.DeleteFileView.as_view(),
        name="delete_file",
    ),
    # База знаний
    path("knowledge_base_moderation/", views.KnowledgePage.as_view(), name="knowledge"),
    path(
        "site/notifications/",
        views.NotificationSettings.as_view(),
        name="notifications_settings",
    ),
    path(
        "site/notifications/create/",
        views.NotificationCreateView.as_view(),
        name="notifications_create",
    ),
    path(
        "notification/delete_multiple/",
        views.NotificationDeleteMultipleView.as_view(),
        name="notification_delete_multiple",
    ),
    path(
        "site/settings/<int:pk>/",
        views.SettingGlobalUpdateView.as_view(),
        name="settings_global",
    ),
    path(
        "homepagesettings/<int:pk>/",
        views.HomepageUpdateView.as_view(),
        name="homepage_update",
    ),
    path(
        "aboutsettings/<int:pk>/", views.AboutUpdateView.as_view(), name="about_update"
    ),
    path(
        "contactsettings/<int:pk>/",
        views.ContactUpdateView.as_view(),
        name="contact_update",
    ),
    path(
        "contact/<int:contact_page_id>/add/",
        views.ContactPageInformationCreateView.as_view(),
        name="add_contact",
    ),
    path(
        "contact/<int:contact_info_id>/update/",
        views.ContactPageInformationUpdateView.as_view(),
        name="update_contact",
    ),
    path(
        "contact/<int:contact_info_id>/delete/",
        views.ContactPageInformationDeleteView.as_view(),
        name="delete_contact",
    ),
    path(
        "schedule/<uuid:user_id>/", views.ScheduleList.as_view(), name="schedule-list"
    ),
    path(
        "schedule/create/", views.ScheduleCreateView.as_view(), name="schedule_create"
    ),
    path(
        "schedule/update/<int:schedule_id>/",
        views.ScheduleUpdateView.as_view(),
        name="schedule_update",
    ),
    path(
        "schedule/delete/<int:schedule_id>/",
        views.ScheduleDeleteView.as_view(),
        name="schedule_delete",
    ),
    # Товары
    path("category/", views.create_category_advertisement, name="category_create"),
    path("category_list/", views.advertisement_category_list, name="category_list"),
    path(
        "site/category-product/",
        views.CategoryProducts.as_view(),
        name="categorys_product_settings",
    ),
    path(
        "site/category-product/create/",
        views.CategoriesCreateView.as_view(),
        name="categorys_product_create",
    ),
    path(
        "site/category-product/<int:pk>/update/",
        views.CategoriesUpdateView.as_view(),
        name="categorys_product_cupdate",
    ),
    path(
        "categorys/product/delete/",
        views.CategoriesDeleteView.as_view(),
        name="categorys_product_delete",
    ),
    path(
        "save-categories/<slug:slug>/",
        views.save_advertisement_categories,
        name="save_product_categories",
    ),
    path("complaint/", views.Complaints.as_view(), name="complaints"),
    path(
        "complaint/<uuid:pk>/update/",
        views.ComplaintsUpdateView.as_view(),
        name="complaint_update",
    ),
    path("reviews/", views.ReviewListView.as_view(), name="reviews"),
    path("reviews/delete/", views.ReviewsDeleteView.as_view(), name="reviews_delete"),
    path(
        "collaborations/",
        views.CollaborationsList.as_view(),
        name="collaborations_list",
    ),
    path(
        "collaborations/<int:pk>/edit/",
        views.CollaborationsUpdateView.as_view(),
        name="collaborations_edit",
    ),
    path(
        "collaborations/delete/",
        views.CollaborationsDeleteView.as_view(),
        name="collaborations_delete",
    ),
    # SEO
    path("site/seo/", views.SeoSettings.as_view(), name="seo_settings"),
    path("site/seo/create/", views.SeoCreateView.as_view(), name="seo_create"),
    path("site/seo/<int:pk>/update/", views.SeoUpdateView.as_view(), name="seo_update"),
    path("seo/delete/", views.SeoDeleteMultipleView.as_view(), name="seo_delete"),
    # Pages
    path("site/pages/", views.PagesSettings.as_view(), name="pages_settings"),
    path("site/pages/create/", views.PagesCreateView.as_view(), name="pages_create"),
    path(
        "site/pages/<slug:slug>/update/",
        views.PagesUpdateView.as_view(),
        name="pages_update",
    ),
    path("pages/delete/", views.PagesDeleteView.as_view(), name="pages_delete"),
    # vacance
    path("payments/", views.StatusPaymentListView.as_view(), name="statuspayment_list"),
    path(
        "payments/delete/",
        views.StatusPaymentDeleteView.as_view(),
        name="statuspayment_delete",
    ),
    path(
        "ajax/statuspayment/create/",
        views.AjaxStatusPaymentCreateView.as_view(),
        name="ajax_statuspayment_create",
    ),
    path('payment_settings/',views.PaymentSettings.as_view(),name='payment_settings'),
    # vacance
    path("site/vacance/", views.Vacances.as_view(), name="vacances"),
    path(
        "site/vacances-aplication/",
        views.VacancyResponse.as_view(),
        name="vacances_aplication",
    ),
    path(
        "site/vacance/create/",
        views.VacancesCreateView.as_view(),
        name="vacances_create",
    ),
    path(
        "site/vacance/<slug:slug>/update/",
        views.VacancesUpdateView.as_view(),
        name="vacances_update",
    ),
    path("vacances/delete/", views.VacancesDeleteView.as_view(), name="vacance_delete"),
    # Товары
    path("products/", views.ProductsListView.as_view(), name="products"),
    path(
        "product/create_and_edit/",
        views.ProductCreateRedirectView.as_view(),
        name="product_create_and_edit",
    ),
    path("HRChangeLog/<uuid:user_id>/", views.HRChangeLogListView.as_view(), name="hr_change_log"),
    path("lessons/", views.LessonListView.as_view(), name="lesson_list"),
    path('lesson/<uuid:pk>/', views.LessonDetailView.as_view(), name='lesson_detail'),

    path("lessons-delete/", views.LessonDeleteView.as_view(), name="lesson_delete"),
    path("lesson/create/", views.LessonInitCreateRedirectView.as_view(), name="lesson_create"),
    path("lesson/<uuid:pk>/edit/", views.LessonEditView.as_view(), name="lesson_edit"),
    path("upload-chunk/", views.ChunkUploadView.as_view(), name="lesson_chunk_upload"),
    path('delete-material/<uuid:material_id>/', views.DeleteMaterialView.as_view(), name='delete_material'),

    path(
        "product/<uuid:pk>/edit/",
        views.ProductUpdateView.as_view(),
        name="product_edit",
    ),
    path(
        "product/<uuid:pk>/variants-edit/",
        views.ProductUpdateVariateView.as_view(),
        name="product_variants_update",
    ),
    path(
        "ajax/create-stock/",
        views.CreateStockAvailabilityView.as_view(),
        name="ajax_create_stock",
    ),
    path("ajax/load-atributes/", views.load_atributes, name="ajax_load_atributes"),
    path("ajax-load-atributes/", views.ajax_load_atributes, name="load_atributes"),
    path(
        "moderation/ajax/create-variants/<uuid:pk>/",
        views.create_product_variants,
        name="create_product_variants",
    ),
    path("product/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    # Воспросы
    path("faq-product/", views.FaqsProductsList.as_view(), name="faq_product"),
    path(
        "faq-product/create/",
        views.FaqsProductsCreateView.as_view(),
        name="faq_product_create",
    ),
    path(
        "faq-product/<int:pk>/update/",
        views.FaqsProductsUpdateView.as_view(),
        name="faq_product_update",
    ),
    path(
        "faq-product/delete/",
        views.FaqsProductsDeleteView.as_view(),
        name="faq_product_delete",
    ),
    # Валюты
    path("valute/", views.ValuteList.as_view(), name="valute"),
    path("valute/create/", views.ValuteCreateView.as_view(), name="valute_create"),
    path(
        "valute/<int:pk>/update/",
        views.ValuteUpdateView.as_view(),
        name="valute_update",
    ),
    path("valute/delete/", views.ValuteDeleteView.as_view(), name="valute_delete"),
    # Вариация
    path("variable/", views.VariableList.as_view(), name="variable"),
    path(
        "variable/create/", views.VariableCreateView.as_view(), name="variable_create"
    ),
    path(
        "variable/<int:pk>/update/",
        views.VariableUpdateView.as_view(),
        name="variable_update",
    ),
    path(
        "variable/delete/", views.VariableDeleteView.as_view(), name="variable_delete"
    ),
    path(
        "ajax/atributes/<int:variable_id>/",
        views.load_attributes,
        name="load_attributes",
    ),
    path(
        "ajax/atributes/save/<int:variable_id>/",
        views.save_atribute,
        name="save_atribute",
    ),
    path(
        "ajax/atributes/save/<int:variable_id>/<int:atribute_id>/",
        views.save_atribute,
        name="update_atribute",
    ),
    path(
        "ajax/atributes/delete/<int:atribute_id>/",
        views.delete_atribute,
        name="delete_atribute",
    ),
    # ЗАявки
    path(
        "applicationsproducts/",
        views.ApplicationsProductsList.as_view(),
        name="applicationsproducts",
    ),
    path(
        "applicationsproducts/create/",
        views.ApplicationsProductsCreateView.as_view(),
        name="applicationsproducts_create",
    ),
    path(
        "applicationsproducts/<uuid:pk>/update/",
        views.ApplicationsProductsUpdateView.as_view(),
        name="applicationsproducts_update",
    ),
    path(
        "applicationsproducts/delete/",
        views.ApplicationsProductsDeleteView.as_view(),
        name="applicationsproducts_delete",
    ),
    # ЗАявки
    path("storages/", views.StorageList.as_view(), name="storages"),
    path("storages/create/", views.StorageCreateView.as_view(), name="storages_create"),
    path(
        "storages/<int:pk>/update/",
        views.StorageUpdateView.as_view(),
        name="storages_update",
    ),
    path("storages/delete/", views.StorageDeleteView.as_view(), name="storages_delete"),
    # ЗАявки

    path("manufacturers/", views.ManufacturersList.as_view(), name="manufacturers"),
    path("mymanufacturers/", views.MyManufacturerListView.as_view(), name="mymanufacturers"),
    path('manufacturers-dashboard/<int:id>/', views.ManufacturersDashboardView.as_view(), name='manufacturers_dashboard'),

    path(
        "manufacturers/create/",
        views.ManufacturersCreateView.as_view(),
        name="manufacturers_create",
    ),
    path(
        "manufacturers/<int:pk>/update/",
        views.ManufacturersUpdateView.as_view(),
        name="manufacturers_update",
    ),
    path(
        "manufacturers/delete/",
        views.ManufacturersDeleteView.as_view(),
        name="manufacturers_delete",
    ),
    path('export/xml/<str:xml_link>/', views.ProductsXMLExportView.as_view(), name='export_products_xml'),
    path('export/csv/<str:xml_link>/', views.ProductsCSVExportView.as_view(), name='export_products_csv'),
    path('export/xls/<str:xml_link>/', views.ProductsXLSXExportView.as_view(), name='export_products_xls'),
    path('import/', views.ImportHistoryCreateView.as_view(), name='import_history_create'),
    path('import/history/', views.ImportHistoryListView.as_view(), name='import_history_list'),
    path('import_download_file/', views.import_download_file, name='import_download_file'),
    path('api/products/import/', views.ProductImportView.as_view(), name='product_import'),

    # Воспросы
    path(
        "productcomments/", views.ProductCommentList.as_view(), name="productcomments"
    ),
    path(
        "productcomments/create/",
        views.ProductCommentCreateView.as_view(),
        name="productcomments_create",
    ),
    path(
        "productcomments/<int:pk>/update/",
        views.ProductCommentUpdateView.as_view(),
        name="productcomments_update",
    ),
    path(
        "productcomments/delete/",
        views.ProductCommentDeleteView.as_view(),
        name="productcomments_delete",
    ),
    # Комментарии
    path("faq/", views.FaqSettings.as_view(), name="faq_settings"),
    path("faq/create/", views.FaqCreateView.as_view(), name="faq_create"),
    path("faq/<int:pk>/update/", views.FaqUpdateView.as_view(), name="faq_update"),
    path("faq/delete/", views.FaqDeleteView.as_view(), name="faq_delete"),
    # Имущество
    path("assets/", views.AssetListView.as_view(), name="asset_list"),
    path("asset/<uuid:pk>/edit/", views.AssetUpdateView.as_view(), name="asset_edit"),
    path(
        "asset/create/", views.AssetCreateAndRedirectView.as_view(), name="asset_create"
    ),
    path("asset/<uuid:pk>/edit/", views.AssetUpdateView.as_view(), name="asset_edit"),
    path(
        "assets/<uuid:asset_id>/usage/", views.asset_usage_list, name="asset_usage_list"
    ),
    path(
        "assets/<uuid:asset_id>/usage/create/",
        views.asset_usage_create,
        name="asset_usage_create",
    ),
    path(
        "assets/usage/<int:usage_id>/delete/",
        views.asset_usage_delete,
        name="asset_usage_delete",
    ),
    path(
        "usage/<int:usage_id>/toggle-active/",
        views.toggle_usage_active,
        name="toggle_usage_active",
    ),
    path(
        "assets/<uuid:asset_id>/maintenance/",
        views.asset_maintenance_list,
        name="asset_maintenance_list",
    ),
    path(
        "assets/<uuid:asset_id>/maintenance/create/",
        views.asset_maintenance_create,
        name="asset_maintenance_create",
    ),
    path(
        "assets/maintenance/<int:maintenance_id>/delete/",
        views.asset_maintenance_delete,
        name="asset_maintenance_delete",
    ),
    path("users/json/", views.user_list_json, name="user_list_json"),
    # Order
    path("orders/", views.OrdersView.as_view(), name="orders"),
    path("orders/create/", views.OrderCreateView.as_view(), name="order_create"),
    path("orders/<int:pk>/", views.OrderUpdateView.as_view(), name="order_edit"),
    path("orders/delete/", views.OrderDeleteView.as_view(), name="orders_delete"),
    path(
        "add-selected-product/", views.add_selected_product, name="add_selected_product"
    ),
    # Blog
    path("site/blog/", views.BlogsSettings.as_view(), name="blog_settings"),
    path("site/blog/create/", views.BlogCreateView.as_view(), name="blog_create"),
    path(
        "site/blog/<slug:slug>/update/",
        views.BlogUpdateView.as_view(),
        name="blog_update",
    ),
    path("blogs/delete/", views.BlogDeleteView.as_view(), name="blogs_delete"),
    path("create-category/", views.create_category, name="category_create"),
    path("category_list/", views.category_list, name="category_list"),
    path(
        "site/category/",
        views.CategorysBlogsSettings.as_view(),
        name="categorys_settings",
    ),
    path(
        "site/category/create/",
        views.CategorysBlogsCreateView.as_view(),
        name="categorys_create",
    ),
    path(
        "site/category/<int:pk>/update/",
        views.CategorysBlogsUpdateView.as_view(),
        name="categorys_update",
    ),
    path(
        "categorys/delete/",
        views.CategorysBlogsDeleteView.as_view(),
        name="categorys_delete",
    ),
    path("save_categories/<slug:slug>/", views.save_categories, name="save_categories"),
    path("create-tags/", views.create_tag, name="tag_create"),
    path("tags_list/", views.tag_list, name="tags_list"),
    path("site/tags/", views.TagsBlogsSettings.as_view(), name="tags_settings"),
    path("site/tags/create/", views.TagsBlogsCreateView.as_view(), name="tags_create"),
    path(
        "site/tags/<int:pk>/update/",
        views.TagsBlogsUpdateView.as_view(),
        name="tags_update",
    ),
    path("tags/delete/", views.TagsBlogsDeleteView.as_view(), name="tags_delete"),
    path("save_tags/<slug:slug>/", views.save_tags, name="save_tags"),
    # Faq
    path("site/faq/", views.FaqSettings.as_view(), name="faq_settings"),
    path("site/faq/create/", views.FaqCreateView.as_view(), name="faq_create"),
    path("site/faq/<int:pk>/update/", views.FaqUpdateView.as_view(), name="faq_update"),
    path("faq/delete/", views.FaqDeleteView.as_view(), name="faq_delete"),
    path(
        "site/sponsorship/",
        views.SponsorshipSettings.as_view(),
        name="sponsorship_settings",
    ),
    path(
        "site/sponsorship/create/",
        views.SponsorshipsCreateView.as_view(),
        name="sponsorshipcreate",
    ),
    path(
        "site/sponsorship/<int:pk>/update/",
        views.SponsorshipUpdateView.as_view(),
        name="sponsorship_update",
    ),
    path(
        "sponsorships/delete/",
        views.SponsorshipDeleteView.as_view(),
        name="sponsorships_delete",
    ),
    path("domains/", views.ExtendedSiteListView.as_view(), name="extended_site_list"),
    path("domains/delete/", views.ExtendedSiteDeleteView.as_view(), name="site_delete"),
    path(
        "domains/create/",
        views.ExtendedSiteCreateView.as_view(),
        name="extended_site_create",
    ),
    path(
        "domains/<int:pk>/update/",
        views.ExtendedSiteUpdateView.as_view(),
        name="extended_site_update",
    ),
    # Gallery
    path("site/gallery/", views.GallerySettings.as_view(), name="gallery_settings"),
    path(
        "site/gallery/create/", views.GalleryCreateView.as_view(), name="gallery_create"
    ),
    path(
        "site/gallery/<slug:slug>/update/",
        views.GalleryUpdateView.as_view(),
        name="gallery_update",
    ),
    path("gallery/delete/", views.GalleryDeleteView.as_view(), name="gallery_delete"),
    # Services
    path("site/services/", views.ServicesSettings.as_view(), name="service_settings"),
    path(
        "site/services/create/",
        views.ServicesCreateView.as_view(),
        name="service_create",
    ),
    path(
        "site/services/<slug:slug>/update/",
        views.ServicesUpdateView.as_view(),
        name="service_update",
    ),
    path("services/delete/", views.ServicesDeleteView.as_view(), name="service_delete"),
    # Prices
    path("site/prices/", views.PricesSettings.as_view(), name="price_settings"),
    path("site/prices/create/", views.PricesCreateView.as_view(), name="price_create"),
    path(
        "site/prices/<slug:slug>/update/",
        views.PricesUpdateView.as_view(),
        name="price_update",
    ),
    path("prices/delete/", views.PricesDeleteView.as_view(), name="price_delete"),
]
