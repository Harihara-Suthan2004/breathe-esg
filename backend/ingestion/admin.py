from django.contrib import admin

from .models import Organization, EmissionRecord  

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  
    search_fields = ('name',)

@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'organization', 'category_label', 'original_quantity', 'status')
    list_filter = ('status', 'ghg_scope', 'organization')