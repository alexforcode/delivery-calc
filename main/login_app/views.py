from django.contrib import messages
from django.contrib.auth.views import LogoutView


class CustomLogoutView(LogoutView):
    def get_next_page(self):
        next_page = super().get_next_page()
        messages.add_message(self.request, messages.SUCCESS, 'Вы успешно вышли!')

        return next_page
