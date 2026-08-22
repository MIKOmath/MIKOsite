import datetime

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render

User = get_user_model()


@login_required
def profile(request):
    ctx = {
        "region_choices": User._meta.get_field('region').choices,
    }

    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        region = request.POST.get("region")
        dob_str = request.POST.get("date_of_birth")
        uploaded = request.FILES.get("profile_image")

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

        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.region = region

        try:
            request.user.full_clean()
        except ValidationError as e:
            ctx["custom_message"] = "\n".join(msg for msgs in e.message_dict.values() for msg in msgs)
            return render(request, "profile.html", ctx)

        request.user.save(
            update_fields=['first_name', 'last_name', 'region', 'date_of_birth', 'profile_image']
        )
        ctx["custom_message"] = "Profil został zaktualizowany."

    return render(request, "profile.html", ctx)


@login_required
def signout(request):
    logout(request)
    return redirect("/")
