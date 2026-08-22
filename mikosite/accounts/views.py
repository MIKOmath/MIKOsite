import datetime

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render, resolve_url
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

User = get_user_model()

# Named rather than imported: mainSite.models already imports this app.
EDIT_BIO_PERMISSION = 'mainSite.change_bio'


def admin_login(request):
    """Stands in front of the admin panel's own login form.

    The panel ships a login page of its own, which is neither styled like the
    rest of the site nor able to offer Google and Discord. Anonymous visitors
    go to the site's form instead, carrying where they were headed; someone
    signed in without the rights gets a page that says so, rather than the
    panel's form asking them to sign in again as somebody else.
    """
    destination = request.GET.get(REDIRECT_FIELD_NAME) or reverse('admin:index')
    if not url_has_allowed_host_and_scheme(destination, allowed_hosts={request.get_host()},
                                           require_https=request.is_secure()):
        destination = reverse('admin:index')

    if not request.user.is_authenticated:
        return redirect_to_login(destination, resolve_url(settings.LOGIN_URL))
    if admin.site.has_permission(request):
        return admin.site.login(request)
    return render(request, 'admin_no_access.html', status=403)


@login_required
def profile(request):
    # The about page reads a name off the account behind the card, so for
    # anybody on show, respelling it is editing the card.
    card = getattr(request.user, 'bio', None)
    name_is_editable = (
        card is None
        or not card.is_published
        or request.user.has_perm(EDIT_BIO_PERMISSION)
    )
    ctx = {
        "region_choices": User._meta.get_field('region').choices,
        "name_is_locked": not name_is_editable,
    }

    if request.method == "POST":
        region = request.POST.get("region")
        dob_str = request.POST.get("date_of_birth")
        uploaded = request.FILES.get("profile_image")
        saved_fields = ['region', 'date_of_birth', 'profile_image']

        if dob_str:
            try:
                date_of_birth = datetime.date.fromisoformat(dob_str)
            except ValueError:
                ctx["custom_message"] = "Niepoprawna data urodzenia."
                return render(request, "profile.html", ctx)
            else:
                request.user.date_of_birth = date_of_birth

        if uploaded:
            request.user.profile_image = uploaded

        if name_is_editable:
            request.user.first_name = request.POST.get("first_name")
            request.user.last_name = request.POST.get("last_name")
            saved_fields += ['first_name', 'last_name']

        request.user.region = region

        try:
            request.user.full_clean()
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(msg for msgs in e.message_dict.values() for msg in msgs)
            return render(request, "profile.html", ctx)

        request.user.save(update_fields=saved_fields)
        ctx["custom_message"] = "Profil został zaktualizowany."

    return render(request, "profile.html", ctx)


@login_required
def signout(request):
    logout(request)
    return redirect("/")
