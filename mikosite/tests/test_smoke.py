from django.test import TestCase


class WebsiteTest(TestCase):

    def test_home_page_response(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')

    def test_about_response(self):
        response = self.client.get('/about/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'about.html')

    def test_kolomat_response(self):
        response = self.client.get('/kolo/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'informacje.html')
