from django.contrib import admin
from .models import Problem, ProblemHint, Review
# Register your models here.


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    list_display = ('problem_id', 'author', "get_tags")
    
    def get_tags(self, obj):
        return ",".join(o for o in obj.tags.names())
admin.site.register(ProblemHint)
admin.site.register(Review)
