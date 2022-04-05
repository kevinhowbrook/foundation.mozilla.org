from django import test
from django.core import exceptions
from wagtail.core import models as wagtail_models
from wagtail_localize import synctree

from networkapi.wagtailpages.factory import research_hub as research_factory
from networkapi.wagtailpages.factory import homepage as home_factory
from networkapi.wagtailpages import models as pagemodels


class ResearchHubTestCase(test.TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._setup_homepage()
        cls._setup_research_hub_structure(homepage=cls.homepage)
        cls._setup_locales()

    @classmethod
    def _setup_homepage(cls):
        root = wagtail_models.Page.get_first_root_node()
        if not root:
            raise ValueError('A root page should exist. Something is off.')
        cls.homepage = home_factory.WagtailHomepageFactory(parent=root)

        sites = wagtail_models.Site.objects.all()
        if sites.count() != 1:
            raise ValueError('There should be exactly one site. Something is off.')
        cls.site = sites.first()

        cls.site.root_page = cls.homepage
        cls.site.clean()
        cls.site.save()

    @classmethod
    def _setup_research_hub_structure(cls, homepage):
        cls.landing_page = research_factory.ResearchLandingPageFactory(
            parent=homepage,
        )
        cls.library_page = research_factory.ResearchLibraryPageFactory(
            parent=cls.landing_page,
        )
        cls.author_index = research_factory.ResearchAuthorsIndexPageFactory(
            parent=cls.landing_page,
            title="Authors",
        )

    @classmethod
    def _setup_locales(cls):
        cls.default_locale = wagtail_models.Locale.get_default()
        cls.fr_locale, _ = wagtail_models.Locale.objects.get_or_create(
            language_code='fr'
        )
        assert cls.fr_locale != cls.default_locale

    def setUp(self):
        self.synchronize_tree()

    def synchronize_tree(self):
        synctree.synchronize_tree(
            source_locale=self.default_locale,
            target_locale=self.fr_locale
        )


class TestResearchLibraryPage(ResearchHubTestCase):
    def test_get_context_detail_pages_in_context(self):
        detail_page_1 = research_factory.ResearchDetailPageFactory(
            parent=self.library_page,
        )
        detail_page_2 = research_factory.ResearchDetailPageFactory(
            parent=self.library_page,
        )

        context = self.library_page.get_context(request=None)

        self.assertEqual(len(context['research_detail_pages']), 2)
        self.assertIn(detail_page_1, context['research_detail_pages'])
        self.assertIn(detail_page_2, context['research_detail_pages'])

    def test_get_context_translation_aliases_not_in_context(self):
        detail_page_1 = research_factory.ResearchDetailPageFactory(
            parent=self.library_page,
        )
        detail_page_2 = research_factory.ResearchDetailPageFactory(
            parent=self.library_page,
        )
        self.synchronize_tree()
        fr_detail_page_1 = detail_page_1.get_translation(self.fr_locale)
        fr_detail_page_2 = detail_page_2.get_translation(self.fr_locale)

        context = self.library_page.get_context(request=None)

        self.assertEqual(len(context['research_detail_pages']), 2)
        self.assertIn(detail_page_1, context['research_detail_pages'])
        self.assertIn(detail_page_2, context['research_detail_pages'])
        self.assertNotIn(fr_detail_page_1, context['research_detail_pages'])
        self.assertNotIn(fr_detail_page_2, context['research_detail_pages'])


class TestResearchDetailLink(test.TestCase):
    def test_clean_with_url(self):
        link = research_factory.ResearchDetailLinkFactory.build(with_url=True)

        link.clean()

        self.assertTrue(link.url)
        self.assertFalse(link.document)

    def test_clean_with_doc(self):
        link = research_factory.ResearchDetailLinkFactory.build(with_document=True)

        link.clean()

        self.assertTrue(link.document)
        self.assertFalse(link.url)

    def test_clean_with_url_and_doc(self):
        link = research_factory.ResearchDetailLinkFactory.build(
            with_url=True,
            with_document=True,
        )

        with self.assertRaises(exceptions.ValidationError):
            link.clean()

    def test_clean_with_neither_url_nor_doc(self):
        link = research_factory.ResearchDetailLinkFactory.build()

        with self.assertRaises(exceptions.ValidationError):
            link.clean()
