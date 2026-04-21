import ssl

from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.utils.functional import cached_property


class UnverifiedSSLContextEmailBackend(SMTPEmailBackend):
    """
    A custom SMTP email backend that uses an unverified SSL context.
    WARNING: This is insecure and should only be used for local development.
    """

    @cached_property
    def ssl_context(self):
        # Create an SSL context that does not verify certificates.
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context