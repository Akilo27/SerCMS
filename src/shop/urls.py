from django.urls import path
from . import views

app_name = "shop"


urlpatterns = [
    # Товары
    path(
        "products-list/", views.ManufacturerProductsListView.as_view(), name="products"
    ),
    path(
        "product/create_and_edit/",
        views.ManufacturerProductCreateAndEditView.as_view(),
        name="product_create_and_edit",
    ),
    path(
        "product/<uuid:pk>/edit/",
        views.ManufacturerProductUpdateView.as_view(),
        name="product_edit",
    ),
    path(
        "product/<uuid:pk>/variants-edit/",
        views.ManufacturerProductUpdateVariateView.as_view(),
        name="product_variants_update",
    ),
    path(
        "product/delete/",
        views.ManufacturerProductDeleteView.as_view(),
        name="product_delete",
    ),
    path(
        "manufacturers/<slug:slug>/edit/",
        views.ManufacturerEditView.as_view(),
        name="manufacturer_edit",
    ),
    path("products/by-ids/", views.ProductsByIdsView.as_view(), name="products_by_ids"),

    path("catalog/", views.ProductsListView.as_view(), name="catalogs"),
    path("menu/", views.ProductsListMenuView.as_view(), name="menu"),
    path(
        "catalog/action/",
        views.ProductsActionListView.as_view(),
        name="catalogs_action",
    ),
    path(
        "manufacturerreviews/",
        views.ManufacturerReviewsListView.as_view(),
        name="manufacturerreviews",
    ),
    path(
        "manufacturerorder/",
        views.ManufacturerOrderListView.as_view(),
        name="manufacturerorder",
    ),
    path("catalog/<slug:slug>/", views.ProductsDetailView.as_view(), name="products"),
    path("order/<slug:pk>/", views.OrderDetailView.as_view(), name="orderdetail"),
    path(
        "order/<slug:ticket_id>/add_comment/",
        views.ProductCommentCreateView.as_view(),
        name="add_comment_product",
    ),
    path(
        "order/<int:pk>/update/", views.OrderUpdateView.as_view(), name="order_update"
    ),
    path(
        "catalog/<slug:slug>/<slug:variation_slug>",
        views.ProductsVariableDetailView.as_view(),
        name="products_variable",
    ),
    path('profile-subscribe/', views.ProfileSubscriptionView.as_view(), name='profile-subscribe'),

    path('toggle-price-reduction/', views.TogglePriceReductionView.as_view(), name='toggle_price_reduction'),
    path('product/<uuid:product_id>/load-reviews/', views.ReviewListView.as_view(), name='load_reviews'),
    path("product/<uuid:product_id>/load-faqs/", views.FaqsListView.as_view(), name="load_faqs"),

    path("categories/<slug:slug>/", views.CategoriesView.as_view(), name="categories"),
    path(
        "manufacturers/<slug:slug>/",
        views.ManufacturersView.as_view(),
        name="manufacturers",
    ),
    path(
        "manufacturers-blog/<slug:slug>/",
        views.ManufacturersBlogView.as_view(),
        name="manufacturers_blog",
    ),
    # path("submit-review/", views.SubmitReviewView.as_view(), name="submit_review"),
    path("addcart/", views.AddToCartView.as_view(), name="add_to_cart"),
    path("cart-item-count/", views.CartItemCountView.as_view(), name="cart_item_count"),
    path("cart-items/", views.CartItemsView.as_view(), name="cart_items"),
    path(
        "create-application/",
        views.ApplicationCreateView.as_view(),
        name="create-application",
    ),
    path("bookmark/add/", views.BookmarkAddView.as_view(), name="bookmark-add"),
    path(
        "bookmark/delete/", views.BookmarkDeleteView.as_view(), name="bookmark-delete"
    ),
    path('purchased-products/', views.PurchasedProductListView.as_view(), name='purchased_products_list'),

    path("add-faq/", views.AddFaqView.as_view(), name="add_faq"),
    path("myorder/", views.MyOrderView.as_view(), name="my_order"),
    path("bookmarks/", views.BookmarkListView.as_view(), name="bookmark_list"),
    path(
        "mycart/delete-selected-product/",
        views.DeleteSelectedProductView.as_view(),
        name="delete_selected_product",
    ),

    path("compare/", views.CompareView.as_view(), name="compare_page"),
    path("compare/add/<uuid:product_id>/", views.add_compare_view, name="compare_add"),
    path("compare/remove/<uuid:product_id>/", views.remove_compare_view, name="compare_aremove"),
    path("compare/clear/", views.clear_compare_view, name="compare_aclear"),

    path(
        "cart/update_quantity/<slug:product_id>/",
        views.UpdateProductQuantityView.as_view(),
        name="update_quantity",
    ),
    path("mycart/", views.MyCartView.as_view(), name="my_cart"),
    path(
        "update-cart-currency/",
        views.UpdateCartCurrencyView.as_view(),
        name="update_cart_currency",
    ),
    path(
        "load-category-content/<int:category_id>/",
        views.load_category_content,
        name="load_category_content",
    ),
    path(
        "cart/remove/<slug:product_slug>/",
        views.RemoveFromCartView.as_view(),
        name="remove_from_cart",
    ),
    path("order-lookup/", views.OrderLookupView.as_view(), name="order_lookup"),  # ← СНАЧАЛА

    path(
        "cart/update/<slug:product_slug>/",
        views.UpdateCartItemView.as_view(),
        name="update_cart_item",
    ),
    path("shop_edit/", views.UserUploadCSVView.as_view(), name="shop_edit"),
]
