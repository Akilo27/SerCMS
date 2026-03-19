from django.contrib import sitemaps
from django.contrib.sites.models import Site
from webmain.models import (
    Pages,
    Blogs,
    CategorysBlogs,
    TagsBlogs,
    ContactPage,
    AboutPage,
)


class BaseSitemap(sitemaps.Sitemap):
    changefreq = "daily"
    priority = 0.6

    def items(self):
        raise NotImplementedError("Subclasses must implement items() method.")

    def location(self, obj):
        return obj.get_absolute_url()


class DynamicSiteSitemap(BaseSitemap):
    def __init__(self, model):
        self.model = model

    def items(self):
        current_site = Site.objects.get_current()
        return self.model.objects.filter(site=current_site)


class PagesSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(Pages)


class BlogsSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(Blogs)

    def lastmod(self, obj):
        return obj.create


class CategorysBlogsSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(CategorysBlogs)


class TagsBlogsSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(TagsBlogs)


class ContactPageSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(ContactPage)


class AboutPageSitemap(DynamicSiteSitemap):
    def __init__(self):
        super().__init__(AboutPage)


def get_site_sitemaps():
    current_site = Site.objects.get_current()
    sitemaps_dict = {
        "pages": PagesSitemap(current_site),
        "blogs": BlogsSitemap(current_site),
        "categorys": CategorysBlogsSitemap(current_site),
        "tags": TagsBlogsSitemap(current_site),
        "contact_page": ContactPageSitemap(current_site),
        "about_page": AboutPageSitemap(current_site),
    }
    return sitemaps_dict
