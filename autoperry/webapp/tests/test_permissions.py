
from django.test import TestCase
from django.utils import timezone

public_urls = ['/',
               '/privacy',
               '/help/about',
               '/help/organisers',
               '/help/helpers',
               '/account/create',
               #'/account/confirm/XXX/XXX',
               '/accounts/password_reset/',
               '/accounts/password_reset/done/',
               '/accounts/reset/XXX/XXX/',
               '/accounts/reset/done/',
              ]

logout_url = '/accounts/logout/'

limbo_urls  = ['/account',
               '/account/resend',
               '/account/edit',
               '/account/cancel',
               '/accounts/password_change/',
               '/accounts/password_change/done/',
               ]

core_urls   = ['/events',
               '/event/create',
               '/event/1/cancel',
               '/event/1/edit',
               '/event/1/clone',
               '/event/1/volunteer',
               '/event/1/unvolunteer',
               '/event/1/decline/1',
               ]

admin_urls  = ['/admin/send-emails',
               '/admin/account-list',
               '/admin/account-approve/1',
               '/admin/account-toggle/suspend/1',
               ]



class DecoratorTestCase(TestCase):

	def setUpTestData(cls):
		user_model = get_user_model()
		cls.valivated = user_model.objects.create_user(
			'validated@autoperry.com',
			password='Password',
			first_name='Albert',
			last_name='Validated',
			tower='Little Shelford',
			email_validated=timezone.now())


    def test_anonymous(self):
        for url in public_urls:
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200, url)

        for url in limbo_urls + core_urls + admin_urls:
            response = self.client.get(url)
            self.assertRedirects(response, '/?next=' + url, msg_prefix=url)

        response = self.client.get(logout_url)
        self.assertRedirects(response, '/', msg_prefix=logout_url)


    def test_validated_only(self):

        self.client.login('validated@autoperry.com', 'password')

        for url in public_urls + lombo_urls:
            response = self.client.get(url)
            self.assertEquals(response.status_code, 200, url)

        for url in core_urls + admin_urls:
            response = self.client.get(url)
            self.assertRedirects(response, '/?next=' + url, msg_prefix=url)

        response = self.client.get(logout_url)
        self.assertRedirects(response, '/', msg_prefix=logout_url)

