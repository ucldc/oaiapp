from django.contrib import admin

from .models import *

class OAIRepositoryAdmin(admin.ModelAdmin):
    pass

class OAISetAdmin(admin.ModelAdmin):
    pass

class OAIRecordAdmin(admin.ModelAdmin):
    pass

class OAIFieldAdmin(admin.ModelAdmin):
    pass

class ResumptionTokenAdmin(admin.ModelAdmin):
    pass

admin.site.register(OAIRepository, OAIRepositoryAdmin)
admin.site.register(OAISet, OAISetAdmin)
admin.site.register(OAIRecord, OAIRecordAdmin)
admin.site.register(OAIField, OAIFieldAdmin)
admin.site.register(ResumptionToken, ResumptionTokenAdmin)

