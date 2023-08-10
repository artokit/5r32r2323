import os
from django.shortcuts import redirect
from django.views.generic import TemplateView, FormView
from .forms import SendForm
from kaif.settings import MEDIA_ROOT
from .utils import send_all
from threading import Thread
from django.contrib import messages


class Index(TemplateView):
    template_name = 'admin_controller/index.html'

    def get(self, request, *args, **kwargs):
        if self.request.user.is_staff:
            return super().get(request, *args, **kwargs)
        return redirect('admin/')


class Sender(FormView):
    template_name = 'admin_controller/sender.html'
    form_class = SendForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def post(self, request, *args, **kwargs):
        text = request.POST.get('text')

        photo = self.request.FILES.get('photo')

        if photo:
            with open(os.path.join(MEDIA_ROOT, photo.name), 'wb') as f:
                f.write(photo.read())

        messages.success(self.request, 'Рассылка началась')

        th = Thread(target=send_all, args=(text, photo))
        th.start()

        return redirect('index')
