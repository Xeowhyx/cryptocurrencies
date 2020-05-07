from django.conf.urls import url
from django.urls import path
from django.contrib.auth.views import LogoutView, PasswordResetView ,PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

from .views import(
    activate,
    activation_sent_view,
    portefeuille_view,
    signup,
    signin,
    changepwd,
    preference_view,
    mail_exist,
)


urlpatterns = [
    url(r'^sent/', activation_sent_view, name="activation_sent"),
    url(r'^sent/$', activation_sent_view),

    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        activate, name='activate'),
    #redirection vers la page du portefeuille d'actif
    url( r'^portefeuille/$', portefeuille_view,name="portefeuille"),
    url(r'^logout/$',LogoutView.as_view(template_name="compte/login.html"),{'next_page': '/'},  name="logout"),

    path('signup',signup, name='signup'),
    path('signin',signin, name='signin'),
    path('changepwd',changepwd, name='changepwd'),
    path('password-reset',PasswordResetView.as_view(template_name="password_reset.html"), name='password_reset'),
    path('password-reset/done/',PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',PasswordResetConfirmView.as_view(template_name="compte/password_reset_confirm.html"), name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name="compte/password_reset_complete.html"), name='password_reset_complete'),
    path('preference',preference_view,name='preference'),
    path('mail_exist',mail_exist,name='mail_exist'),

]
