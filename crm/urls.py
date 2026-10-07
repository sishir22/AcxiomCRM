from django.urls import path

from .views import (
    dashboard,

    # Customers
    customer_list,
    customer_create,
    customer_edit,
    customer_delete,

    # Leads
    lead_list,
    lead_create,
    lead_edit,
    lead_convert,

    # Opportunities
    opportunity_list,
    opportunity_create,
    opportunity_edit,

    # Follow-ups
    followup_list,
    followup_create,
    followup_complete,
)


urlpatterns = [

    # ============================================================
    # DASHBOARD
    # ============================================================

    path(
        '',
        dashboard,
        name='dashboard'
    ),


    # ============================================================
    # CUSTOMERS
    # ============================================================

    path(
        'customers/',
        customer_list,
        name='customer_list'
    ),

    path(
        'customers/add/',
        customer_create,
        name='customer_create'
    ),

    path(
        'customers/<int:customer_id>/edit/',
        customer_edit,
        name='customer_edit'
    ),

    path(
        'customers/<int:customer_id>/delete/',
        customer_delete,
        name='customer_delete'
    ),


    # ============================================================
    # LEADS
    # ============================================================

    path(
        'leads/',
        lead_list,
        name='lead_list'
    ),

    path(
        'leads/add/',
        lead_create,
        name='lead_create'
    ),

    path(
        'leads/<int:lead_id>/edit/',
        lead_edit,
        name='lead_edit'
    ),

    path(
        'leads/<int:lead_id>/convert/',
        lead_convert,
        name='lead_convert'
    ),


    # ============================================================
    # OPPORTUNITIES
    # ============================================================

    path(
        'opportunities/',
        opportunity_list,
        name='opportunity_list'
    ),

    path(
        'opportunities/add/',
        opportunity_create,
        name='opportunity_create'
    ),

    path(
        'opportunities/<int:opportunity_id>/edit/',
        opportunity_edit,
        name='opportunity_edit'
    ),


    # ============================================================
    # FOLLOW-UPS
    # ============================================================

    path(
        'followups/',
        followup_list,
        name='followup_list'
    ),

    path(
        'followups/add/',
        followup_create,
        name='followup_create'
    ),

    path(
        'followups/<int:followup_id>/complete/',
        followup_complete,
        name='followup_complete'
    ),
]