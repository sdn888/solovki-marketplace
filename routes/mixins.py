from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect


class ManagerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_manager()

    def handle_no_permission(self):
        return redirect('login')


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin()

    def handle_no_permission(self):
        return redirect('login')
