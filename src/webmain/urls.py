from django.urls import path
from . import views
from .sitemaps import *
from django.contrib.sitemaps.views import sitemap
from .sitemaps import get_site_sitemaps
from django.views.generic import TemplateView


app_name = "webmain"

urlpatterns = [

    path(
        "sitemap-pages.xml",
        sitemap,
        {"sitemaps": get_site_sitemaps},
        name="sitemap-pages",
    ),
    path(
        "sitemap-blogs.xml",
        sitemap,
        {"sitemaps": get_site_sitemaps},
        name="sitemap-blogs",
    ),
    path(
        "sitemap-categorys.xml",
        sitemap,
        {"sitemaps": get_site_sitemaps},
        name="sitemap-categorys",
    ),
    path(
        "sitemap-contact-page.xml",
        sitemap,
        {"sitemaps": get_site_sitemaps},
        name="sitemap-contact-page",
    ),
    path(
        "sitemap-about-page.xml",
        sitemap,
        {"sitemaps": get_site_sitemaps},
        name="sitemap-about-page",
    ),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path("development/", views.HomePageView.as_view(), name="development"),
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contacts/", views.ContactView.as_view(), name="contacts"),
    path("faqs/", views.FaqsView.as_view(), name="faqs"),
    path("blogs/", views.BlogView.as_view(), name="blogs"),
    path("blog/<slug:slug>/", views.BlogDetailView.as_view(), name="blogdetail"),
    path(
        "blog/<slug:slug>/comments/",
        views.BlogCommentsView.as_view(),
        name="blog_comments",
    ),
    path(
        "blog/<slug:slug>/add_comment/",
        views.AddCommentView.as_view(),
        name="add_comment",
    ),
    path("sponsorships/", views.SponsorshipView.as_view(), name="sponsorships"),
    path(
        "sponsorship/<slug:slug>/",
        views.SponsorshipDetailView.as_view(),
        name="sponsorship",
    ),
    path("galleries/", views.GalleryView.as_view(), name="galleries"),
    path("gallery/<slug:slug>/", views.GalleryDetailView.as_view(), name="gallery"),
    path("services/", views.ServiceView.as_view(), name="services"),
    path("service/<slug:slug>/", views.ServiceDetailView.as_view(), name="service"),
    path("prices/", views.PriceView.as_view(), name="prices"),
    path("page/<slug:slug>/", views.PageDetailView.as_view(), name="page"),
    path("subscribe/", views.subscribe, name="subscribe"),
    path("search/", views.MultiModelSearchView.as_view(), name="search"),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('search/log/', views.search_log, name='search_log'),
    path('search/history/clear/', views.search_history_clear, name='search_history_clear'),
    path('referrals/', views.ReferralListView.as_view(), name='referrals_list'),
    path('my-subscriber/', views.SubscriberlListView.as_view(), name='my_subscriber'),
    path('my-price-reduction/', views.PriceReductionListView.as_view(), name='my_price_reduction'),
    path('my-recomendets/', views.RecomendetsListView.as_view(), name='my_recomendets'),
    path('feed/', views.MyFeedView.as_view(), name='feed'),

    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.custom_logout, name="logout"),
    path(
        "password_reset/",
        views.CustomPasswordResetView.as_view(),
        name="password_reset",
    ),
    path("my-reviews/", views.MyReviewsView.as_view(), name="my_reviews"),
    path("my-faqs-product/", views.MyFaqsProductsView.as_view(), name="my_faqs_product"),

    path(
        "password_reset/done/",
        views.CustomPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.CustomPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        views.CustomPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
