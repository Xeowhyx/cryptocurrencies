from django.contrib import admin

# Register your models here.



from .models import Profile #User


class UserAdmin(admin.ModelAdmin):

    #list_display=('pseudo','wallet','email','date')
    #list_filtre=('email','pseudo','wallet')
    list_display=('username','email','date')
    list_filtre=('email','pseudo')
    date_hierarchy='date'
    ordering=('date',)
    search_fields=('email','pseudo')
    #prepopulated_fields={"slug": ("pseudo",)}
    #remplissage de slug auto via les params"pseudo"



#admin.site.register(User, UserAdmin)

admin.site.register(Profile, UserAdmin)



#admin.site.register(Wallet)

