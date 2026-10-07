from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User

from django.core.exceptions import ValidationError

from django.db import transaction

from django.db.models import Q

from django.shortcuts import get_object_or_404, redirect, render

from django.utils import timezone
from datetime import timedelta



from .models import Customer, Lead, Opportunity, FollowUp, AuditLog





@login_required

def dashboard(request):

    user = request.user

    profile = getattr(user, 'profile', None)

    role = profile.role if profile else 'SALES'



    if role in ['ADMIN', 'MANAGER']:

        customers = Customer.objects.all()

        leads = Lead.objects.all()

        opportunities = Opportunity.objects.all()

        followups = FollowUp.objects.all()

    else:

        customers = Customer.objects.filter(assigned_to=user)

        leads = Lead.objects.filter(assigned_to=user)

        opportunities = Opportunity.objects.filter(assigned_to=user)

        followups = FollowUp.objects.filter(assigned_to=user)



    context = {

        'total_customers': customers.count(),

        'total_leads': leads.count(),

        'open_leads': leads.exclude(

            status__in=['LOST', 'CONVERTED']

        ).count(),

        'total_opportunities': opportunities.count(),

        'open_opportunities': opportunities.filter(

            status='OPEN'

        ).count(),

        'won_opportunities': opportunities.filter(

            status='WON'

        ).count(),

        'lost_opportunities': opportunities.filter(

            status='LOST'

        ).count(),

        'pipeline_value': sum(

            opportunity.amount

            for opportunity in opportunities.filter(status='OPEN')

        ),

        'role': role,

    }



    return render(request, 'dashboard.html', context)





@login_required

def customer_list(request):

    user = request.user

    role = getattr(getattr(user, 'profile', None), 'role', 'SALES')



    if role in ['ADMIN', 'MANAGER']:

        customers = Customer.objects.all()

    else:

        customers = Customer.objects.filter(assigned_to=user)



    search = request.GET.get('search', '').strip()



    if search:

        customers = customers.filter(

            Q(customer_name__icontains=search) |

            Q(email__icontains=search) |

            Q(phone__icontains=search) |

            Q(company_name__icontains=search)

        )



    customers = customers.select_related(

        'assigned_to'

    ).order_by('-created_date')



    return render(

        request,

        'customers/list.html',

        {

            'customers': customers,

            'search': search,

            'role': role,

        }

    )





@login_required

def customer_create(request):



    if request.method == 'POST':



        name = request.POST.get('customer_name', '').strip()

        email = request.POST.get('email', '').strip()

        phone = request.POST.get('phone', '').strip()

        company = request.POST.get('company_name', '').strip()

        address = request.POST.get('address', '').strip()

        city = request.POST.get('city', '').strip()

        state = request.POST.get('state', '').strip()

        status = request.POST.get('status', 'ACTIVE')

        assigned_to_id = request.POST.get('assigned_to')



        errors = []



        if not name:

            errors.append('Customer name is required.')



        if not email:

            errors.append('Email is required.')



        if not phone:

            errors.append('Phone is required.')



        if Customer.objects.filter(email=email).exists():

            errors.append('A customer with this email already exists.')



        if Customer.objects.filter(phone=phone).exists():

            errors.append('A customer with this phone number already exists.')



        if errors:

            for error in errors:

                messages.error(request, error)



            return render(

                request,

                'customers/form.html',

                {

                    'customer': request.POST,

                    'users': User.objects.filter(is_active=True),

                    'page_title': 'Add Customer',

                }

            )



        assigned_to = None



        if assigned_to_id:

            assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        customer = Customer.objects.create(

            customer_code=f"CUST-{int(timezone.now().timestamp())}",

            customer_name=name,

            email=email,

            phone=phone,

            company_name=company,

            address=address,

            city=city,

            state=state,

            status=status,

            assigned_to=assigned_to or request.user,

            created_by=request.user,

        )



        messages.success(

            request,

            f'Customer "{customer.customer_name}" created successfully.'

        )



        return redirect('customer_list')



    return render(

        request,

        'customers/form.html',

        {

            'users': User.objects.filter(is_active=True),

            'page_title': 'Add Customer',

        }

    )





@login_required

def customer_edit(request, customer_id):



    customer = get_object_or_404(

        Customer,

        id=customer_id

    )



    role = getattr(

        getattr(request.user, 'profile', None),

        'role',

        'SALES'

    )



    if role == 'SALES' and customer.assigned_to != request.user:

        messages.error(

            request,

            'You are not authorized to edit this customer.'

        )

        return redirect('customer_list')



    if request.method == 'POST':



        name = request.POST.get('customer_name', '').strip()

        email = request.POST.get('email', '').strip()

        phone = request.POST.get('phone', '').strip()



        if not name or not email or not phone:

            messages.error(

                request,

                'Customer name, email and phone are required.'

            )

            return redirect('customer_edit', customer_id=customer.id)



        if Customer.objects.filter(

            email=email

        ).exclude(id=customer.id).exists():

            messages.error(

                request,

                'Another customer already uses this email.'

            )

            return redirect('customer_edit', customer_id=customer.id)



        if Customer.objects.filter(

            phone=phone

        ).exclude(id=customer.id).exists():

            messages.error(

                request,

                'Another customer already uses this phone.'

            )

            return redirect('customer_edit', customer_id=customer.id)



        customer.customer_name = name

        customer.email = email

        customer.phone = phone

        customer.company_name = request.POST.get(

            'company_name',

            ''

        ).strip()

        customer.address = request.POST.get(

            'address',

            ''

        ).strip()

        customer.city = request.POST.get(

            'city',

            ''

        ).strip()

        customer.state = request.POST.get(

            'state',

            ''

        ).strip()

        customer.status = request.POST.get(

            'status',

            customer.status

        )



        assigned_to_id = request.POST.get('assigned_to')



        if assigned_to_id and role in ['ADMIN', 'MANAGER']:

            customer.assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        customer.save()



        messages.success(

            request,

            'Customer updated successfully.'

        )



        return redirect('customer_list')



    return render(

        request,

        'customers/form.html',

        {

            'customer': customer,

            'users': User.objects.filter(is_active=True),

            'page_title': 'Edit Customer',

        }

    )





@login_required

def customer_delete(request, customer_id):



    customer = get_object_or_404(

        Customer,

        id=customer_id

    )



    role = getattr(

        getattr(request.user, 'profile', None),

        'role',

        'SALES'

    )



    if role not in ['ADMIN', 'MANAGER']:

        messages.error(

            request,

            'Only Admin or Manager can deactivate customers.'

        )

        return redirect('customer_list')



    if request.method == 'POST':



        customer.status = 'INACTIVE'

        customer.save()



        messages.success(

            request,

            'Customer deactivated successfully.'

        )



    return redirect('customer_list')

@login_required

def lead_list(request):



    user = request.user

    role = getattr(

        getattr(user, 'profile', None),

        'role',

        'SALES'

    )



    if role in ['ADMIN', 'MANAGER']:

        leads = Lead.objects.all()

    else:

        leads = Lead.objects.filter(

            assigned_to=user

        )



    search = request.GET.get(

        'search',

        ''

    ).strip()



    if search:



        leads = leads.filter(

            Q(lead_name__icontains=search) |

            Q(email__icontains=search) |

            Q(phone__icontains=search) |

            Q(company_name__icontains=search) |

            Q(status__icontains=search)

        )



    leads = leads.select_related(

        'assigned_to'

    ).order_by('-created_date')



    return render(

        request,

        'leads/list.html',

        {

            'leads': leads,

            'search': search,

            'role': role,

        }

    )





@login_required

def lead_create(request):



    if request.method == 'POST':



        name = request.POST.get(

            'lead_name',

            ''

        ).strip()



        email = request.POST.get(

            'email',

            ''

        ).strip()



        phone = request.POST.get(

            'phone',

            ''

        ).strip()



        company = request.POST.get(

            'company_name',

            ''

        ).strip()



        source = request.POST.get(

            'source',

            ''

        ).strip()



        status = request.POST.get(

            'status',

            'NEW'

        )



        priority = request.POST.get(

            'priority',

            'MEDIUM'

        )



        expected_value = request.POST.get(

            'expected_value',

            '0'

        )



        assigned_to_id = request.POST.get(

            'assigned_to'

        )



        errors = []



        if not name:

            errors.append(

                'Lead name is required.'

            )



        if not email:

            errors.append(

                'Email is required.'

            )



        if not phone:

            errors.append(

                'Phone is required.'

            )



        try:

            expected_value = float(

                expected_value

            )



            if expected_value < 0:

                errors.append(

                    'Expected value cannot be negative.'

                )



        except ValueError:

            errors.append(

                'Expected value must be numeric.'

            )



        if errors:



            for error in errors:

                messages.error(

                    request,

                    error

                )



            return render(

                request,

                'leads/form.html',

                {

                    'lead': request.POST,

                    'users': User.objects.filter(

                        is_active=True

                    ),

                    'page_title': 'Add Lead',

                }

            )



        assigned_to = None



        if assigned_to_id:



            assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        lead = Lead.objects.create(

            lead_code=f"LEAD-{int(timezone.now().timestamp())}",

            lead_name=name,

            email=email,

            phone=phone,

            company_name=company,

            source=source,

            status=status,

            priority=priority,

            expected_value=expected_value,

            assigned_to=assigned_to or request.user,

        )



        messages.success(

            request,

            f'Lead "{lead.lead_name}" created successfully.'

        )



        return redirect(

            'lead_list'

        )



    return render(

        request,

        'leads/form.html',

        {

            'users': User.objects.filter(

                is_active=True

            ),

            'page_title': 'Add Lead',

        }

    )





@login_required

def lead_edit(request, lead_id):



    lead = get_object_or_404(

        Lead,

        id=lead_id

    )



    role = getattr(

        getattr(request.user, 'profile', None),

        'role',

        'SALES'

    )



    if (

        role == 'SALES'

        and lead.assigned_to != request.user

    ):



        messages.error(

            request,

            'You are not authorized to edit this lead.'

        )



        return redirect(

            'lead_list'

        )



    if request.method == 'POST':



        lead.lead_name = request.POST.get(

            'lead_name',

            ''

        ).strip()



        lead.email = request.POST.get(

            'email',

            ''

        ).strip()



        lead.phone = request.POST.get(

            'phone',

            ''

        ).strip()



        lead.company_name = request.POST.get(

            'company_name',

            ''

        ).strip()



        lead.source = request.POST.get(

            'source',

            ''

        ).strip()



        lead.status = request.POST.get(

            'status',

            lead.status

        )



        lead.priority = request.POST.get(

            'priority',

            lead.priority

        )



        lead.expected_value = request.POST.get(

            'expected_value',

            lead.expected_value

        )



        assigned_to_id = request.POST.get(

            'assigned_to'

        )



        if (

            assigned_to_id

            and role in ['ADMIN', 'MANAGER']

        ):



            lead.assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        lead.save()



        messages.success(

            request,

            'Lead updated successfully.'

        )



        return redirect(

            'lead_list'

        )



    return render(

        request,

        'leads/form.html',

        {

            'lead': lead,

            'users': User.objects.filter(

                is_active=True

            ),

            'page_title': 'Edit Lead',

        }

    )

@login_required
def lead_convert(request, lead_id):
    """Convert a lead into a Customer and an Opportunity."""
    lead = get_object_or_404(Lead, id=lead_id)

    role = getattr(
        getattr(request.user, 'profile', None),
        'role',
        'SALES'
    )

    if role == 'SALES' and lead.assigned_to != request.user:
        messages.error(
            request,
            'You are not authorized to convert this lead.'
        )
        return redirect('lead_list')

    if lead.status == 'CONVERTED':
        messages.warning(
            request,
            'This lead has already been converted.'
        )
        return redirect('lead_list')

    if lead.status == 'LOST':
        messages.error(
            request,
            'A lost lead cannot be converted.'
        )
        return redirect('lead_list')

    if request.method != 'POST':
        messages.error(
            request,
            'Invalid conversion request.'
        )
        return redirect('lead_list')

    with transaction.atomic():
        customer = Customer.objects.filter(email=lead.email).first()

        if not customer:
            customer = Customer.objects.filter(phone=lead.phone).first()

        if not customer:
            customer = Customer.objects.create(
                customer_code=f"CUST-{int(timezone.now().timestamp())}",
                customer_name=lead.lead_name,
                email=lead.email,
                phone=lead.phone,
                company_name=lead.company_name,
                status='ACTIVE',
                assigned_to=lead.assigned_to or request.user,
                created_by=request.user
            )

        opportunity = Opportunity.objects.create(
            opportunity_name=(
                f"{lead.company_name or lead.lead_name} Opportunity"
            ),
            customer=customer,
            lead=lead,
            amount=(
                lead.expected_value
                if lead.expected_value > 0
                else 1
            ),
            stage='QUALIFICATION',
            probability=20,
            expected_close_date=(
                timezone.now().date() + timedelta(days=30)
            ),
            status='OPEN',
            assigned_to=lead.assigned_to or request.user,
            notes=f"Opportunity created from lead {lead.lead_code}."
        )

        old_status = lead.status
        lead.status = 'CONVERTED'
        lead.save()

        AuditLog.objects.create(
            user=request.user,
            action='CONVERT',
            entity_name='Lead',
            record_id=lead.id,
            old_value=old_status,
            new_value=(
                f'CONVERTED | Customer ID: {customer.id} | '
                f'Opportunity ID: {opportunity.id}'
            )
        )

    messages.success(
        request,
        (
            f'Lead "{lead.lead_name}" converted successfully. '
            f'Customer and Opportunity created.'
        )
    )

    return redirect('lead_list')

@login_required

def opportunity_list(request):



    user = request.user



    role = getattr(

        getattr(user, 'profile', None),

        'role',

        'SALES'

    )



    if role in ['ADMIN', 'MANAGER']:

        opportunities = Opportunity.objects.all()

    else:

        opportunities = Opportunity.objects.filter(

            assigned_to=user

        )



    search = request.GET.get(

        'search',

        ''

    ).strip()



    if search:

        opportunities = opportunities.filter(

            Q(opportunity_name__icontains=search) |

            Q(customer__customer_name__icontains=search) |

            Q(stage__icontains=search) |

            Q(status__icontains=search)

        )



    opportunities = opportunities.select_related(

        'customer',

        'lead',

        'assigned_to'

    ).order_by('-created_date')



    return render(

        request,

        'opportunities/list.html',

        {

            'opportunities': opportunities,

            'search': search,

            'role': role,

        }

    )





@login_required

def opportunity_create(request):



    if request.method == 'POST':



        opportunity_name = request.POST.get(

            'opportunity_name',

            ''

        ).strip()



        customer_id = request.POST.get(

            'customer'

        )



        lead_id = request.POST.get(

            'lead'

        )



        amount = request.POST.get(

            'amount',

            ''

        )



        stage = request.POST.get(

            'stage',

            'QUALIFICATION'

        )



        probability = request.POST.get(

            'probability',

            ''

        )



        expected_close_date = request.POST.get(

            'expected_close_date',

            ''

        )



        status = request.POST.get(

            'status',

            'OPEN'

        )



        notes = request.POST.get(

            'notes',

            ''

        ).strip()



        assigned_to_id = request.POST.get(

            'assigned_to'

        )



        errors = []



        if not opportunity_name:

            errors.append(

                'Opportunity name is required.'

            )



        if not customer_id:

            errors.append(

                'Customer is required.'

            )



        try:

            amount_value = float(amount)



            if amount_value <= 0:

                errors.append(

                    'Opportunity Amount must be greater than 0.'

                )



        except (ValueError, TypeError):

            amount_value = 0

            errors.append(

                'Opportunity Amount must be a valid number.'

            )



        try:

            probability_value = int(probability)



            if probability_value < 0 or probability_value > 100:

                errors.append(

                    'Probability must be between 0 and 100.'

                )



        except (ValueError, TypeError):

            probability_value = 0

            errors.append(

                'Probability must be between 0 and 100.'

            )



        if not expected_close_date:

            errors.append(

                'Expected Close Date is required.'

            )

        else:

            try:

                from datetime import date



                close_date = date.fromisoformat(

                    expected_close_date

                )



                if (

                    status == 'OPEN'

                    and close_date < date.today()

                ):

                    errors.append(

                        'Expected Close Date cannot be in the past.'

                    )



            except ValueError:

                errors.append(

                    'Enter a valid Expected Close Date.'

                )



        if errors:



            for error in errors:

                messages.error(

                    request,

                    error

                )



            return render(

                request,

                'opportunities/form.html',

                {

                    'opportunity': request.POST,

                    'customers': Customer.objects.all(),

                    'leads': Lead.objects.all(),

                    'users': User.objects.filter(

                        is_active=True

                    ),

                    'page_title': 'Add Opportunity',

                }

            )



        customer = get_object_or_404(

            Customer,

            id=customer_id

        )



        lead = None



        if lead_id:

            lead = get_object_or_404(

                Lead,

                id=lead_id

            )



        assigned_to = request.user



        if assigned_to_id:

            assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        opportunity = Opportunity.objects.create(

            opportunity_name=opportunity_name,

            customer=customer,

            lead=lead,

            amount=amount_value,

            stage=stage,

            probability=probability_value,

            expected_close_date=expected_close_date,

            status=status,

            assigned_to=assigned_to,

            notes=notes,

        )



        messages.success(

            request,

            f'Opportunity "{opportunity.opportunity_name}" created successfully.'

        )



        return redirect(

            'opportunity_list'

        )



    return render(

        request,

        'opportunities/form.html',

        {

            'customers': Customer.objects.all(),

            'leads': Lead.objects.all(),

            'users': User.objects.filter(

                is_active=True

            ),

            'page_title': 'Add Opportunity',

        }

    )





@login_required

def opportunity_edit(request, opportunity_id):



    opportunity = get_object_or_404(

        Opportunity,

        id=opportunity_id

    )



    role = getattr(

        getattr(request.user, 'profile', None),

        'role',

        'SALES'

    )



    if (

        role == 'SALES'

        and opportunity.assigned_to != request.user

    ):

        messages.error(

            request,

            'You are not authorized to edit this opportunity.'

        )



        return redirect(

            'opportunity_list'

        )



    if request.method == 'POST':



        opportunity.opportunity_name = request.POST.get(

            'opportunity_name',

            ''

        ).strip()



        opportunity.stage = request.POST.get(

            'stage',

            opportunity.stage

        )



        opportunity.status = request.POST.get(

            'status',

            opportunity.status

        )



        opportunity.notes = request.POST.get(

            'notes',

            ''

        ).strip()



        amount = request.POST.get(

            'amount',

            ''

        )



        probability = request.POST.get(

            'probability',

            ''

        )



        expected_close_date = request.POST.get(

            'expected_close_date',

            ''

        )



        try:

            amount_value = float(amount)



            if amount_value <= 0:

                messages.error(

                    request,

                    'Opportunity Amount must be greater than 0.'

                )

                return redirect(

                    'opportunity_edit',

                    opportunity_id=opportunity.id

                )



            opportunity.amount = amount_value



        except (ValueError, TypeError):



            messages.error(

                request,

                'Opportunity Amount must be a valid number.'

            )



            return redirect(

                'opportunity_edit',

                opportunity_id=opportunity.id

            )



        try:

            probability_value = int(probability)



            if probability_value < 0 or probability_value > 100:

                messages.error(

                    request,

                    'Probability must be between 0 and 100.'

                )



                return redirect(

                    'opportunity_edit',

                    opportunity_id=opportunity.id

                )



            opportunity.probability = probability_value



        except (ValueError, TypeError):



            messages.error(

                request,

                'Probability must be between 0 and 100.'

            )



            return redirect(

                'opportunity_edit',

                opportunity_id=opportunity.id

            )



        from datetime import date



        try:



            close_date = date.fromisoformat(

                expected_close_date

            )



            if (

                opportunity.status == 'OPEN'

                and close_date < date.today()

            ):



                messages.error(

                    request,

                    'Expected Close Date cannot be in the past.'

                )



                return redirect(

                    'opportunity_edit',

                    opportunity_id=opportunity.id

                )



            opportunity.expected_close_date = close_date



        except ValueError:



            messages.error(

                request,

                'Enter a valid Expected Close Date.'

            )



            return redirect(

                'opportunity_edit',

                opportunity_id=opportunity.id

            )



        if role in ['ADMIN', 'MANAGER']:



            assigned_to_id = request.POST.get(

                'assigned_to'

            )



            if assigned_to_id:



                opportunity.assigned_to = get_object_or_404(

                    User,

                    id=assigned_to_id,

                    is_active=True

                )



        opportunity.save()



        messages.success(

            request,

            'Opportunity updated successfully.'

        )



        return redirect(

            'opportunity_list'

        )



    return render(

        request,

        'opportunities/form.html',

        {

            'opportunity': opportunity,

            'customers': Customer.objects.all(),

            'leads': Lead.objects.all(),

            'users': User.objects.filter(

                is_active=True

            ),

            'page_title': 'Edit Opportunity',

        }

    )

# ============================================================

# FOLLOW-UP MANAGEMENT

# ============================================================



@login_required

def followup_list(request):



    user = request.user



    role = getattr(

        getattr(user, 'profile', None),

        'role',

        'SALES'

    )



    # Admin and Manager can see all follow-ups

    if role in ['ADMIN', 'MANAGER']:

        followups = FollowUp.objects.all()

    else:

        followups = FollowUp.objects.filter(

            assigned_to=user

        )



    search = request.GET.get(

        'search',

        ''

    ).strip()



    if search:



        followups = followups.filter(

            Q(subject__icontains=search) |

            Q(remarks__icontains=search) |

            Q(status__icontains=search) |

            Q(follow_up_type__icontains=search) |

            Q(customer__customer_name__icontains=search) |

            Q(lead__lead_name__icontains=search)

        )



    followups = followups.select_related(

        'customer',

        'lead',

        'assigned_to'

    ).order_by(

        'follow_up_date',

        'created_date'

    )



    return render(

        request,

        'followups/list.html',

        {

            'followups': followups,

            'search': search,

            'role': role,

            'today': timezone.now().date(),

        }

    )





@login_required

def followup_create(request):



    if request.method == 'POST':



        customer_id = request.POST.get(

            'customer'

        )



        lead_id = request.POST.get(

            'lead'

        )



        follow_up_date = request.POST.get(

            'follow_up_date'

        )



        follow_up_type = request.POST.get(

            'follow_up_type',

            'CALL'

        )



        subject = request.POST.get(

            'subject',

            ''

        ).strip()



        remarks = request.POST.get(

            'remarks',

            ''

        ).strip()



        status = request.POST.get(

            'status',

            'PLANNED'

        )



        assigned_to_id = request.POST.get(

            'assigned_to'

        )



        errors = []



        # -------------------------

        # Validation

        # -------------------------



        if not follow_up_date:

            errors.append(

                'Follow-up date is required.'

            )



        if not subject:

            errors.append(

                'Subject is required.'

            )



        # At least one entity

        if not customer_id and not lead_id:

            errors.append(

                'Select either a customer or a lead.'

            )



        # Date cannot be before today

        if follow_up_date:



            try:



                from datetime import date



                selected_date = date.fromisoformat(

                    follow_up_date

                )



                if selected_date < date.today():



                    errors.append(

                        'Follow-up date cannot be in the past.'

                    )



            except ValueError:



                errors.append(

                    'Enter a valid follow-up date.'

                )



        if errors:



            for error in errors:



                messages.error(

                    request,

                    error

                )



            return render(

                request,

                'followups/form.html',

                {

                    'followup': request.POST,

                    'customers': Customer.objects.all(),

                    'leads': Lead.objects.all(),

                    'users': User.objects.filter(

                        is_active=True

                    ),

                    'page_title': 'Add Follow-Up',

                }

            )



        # -------------------------

        # Related objects

        # -------------------------



        customer = None

        lead = None



        if customer_id:



            customer = get_object_or_404(

                Customer,

                id=customer_id

            )



        if lead_id:



            lead = get_object_or_404(

                Lead,

                id=lead_id

            )



        # -------------------------

        # Assigned user

        # -------------------------



        assigned_to = request.user



        if assigned_to_id:



            assigned_to = get_object_or_404(

                User,

                id=assigned_to_id,

                is_active=True

            )



        # -------------------------

        # Create Follow-Up

        # -------------------------



        followup = FollowUp.objects.create(

            customer=customer,

            lead=lead,

            follow_up_date=follow_up_date,

            follow_up_type=follow_up_type,

            subject=subject,

            remarks=remarks,

            status=status,

            assigned_to=assigned_to

        )



        messages.success(

            request,

            f'Follow-up "{followup.subject}" created successfully.'

        )



        return redirect(

            'followup_list'

        )



    # GET request



    return render(

        request,

        'followups/form.html',

        {

            'customers': Customer.objects.all(),

            'leads': Lead.objects.all(),

            'users': User.objects.filter(

                is_active=True

            ),

            'page_title': 'Add Follow-Up',

        }

    )





@login_required

def followup_complete(request, followup_id):



    followup = get_object_or_404(

        FollowUp,

        id=followup_id

    )



    role = getattr(

        getattr(request.user, 'profile', None),

        'role',

        'SALES'

    )



    # Sales users can only update their own follow-ups

    if (

        role == 'SALES'

        and followup.assigned_to != request.user

    ):



        messages.error(

            request,

            'You are not authorized to update this follow-up.'

        )



        return redirect(

            'followup_list'

        )



    followup.status = 'COMPLETED'



    followup.save()



    messages.success(

        request,

        'Follow-up marked as completed.'

    )



    return redirect(

        'followup_list'

    )
