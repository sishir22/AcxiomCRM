from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Customer(models.Model):

    STATUS_CHOICES = [
        ('LEAD', 'Lead'),
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    ]

    customer_code = models.CharField(
        max_length=20,
        unique=True
    )

    customer_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    phone = models.CharField(
        max_length=15,
        unique=True
    )

    company_name = models.CharField(
        max_length=150,
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    state = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='customers'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_customers'
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    modified_date = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.customer_name


class Lead(models.Model):

    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('QUALIFIED', 'Qualified'),
        ('UNQUALIFIED', 'Unqualified'),
        ('CONVERTED', 'Converted'),
        ('LOST', 'Lost'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    lead_code = models.CharField(
        max_length=20,
        unique=True
    )

    lead_name = models.CharField(
        max_length=100
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=15
    )

    company_name = models.CharField(
        max_length=150,
        blank=True
    )

    source = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )

    expected_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.lead_name


class Opportunity(models.Model):

    STAGE_CHOICES = [
        ('QUALIFICATION', 'Qualification'),
        ('PROPOSAL', 'Proposal'),
        ('NEGOTIATION', 'Negotiation'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('WON', 'Won'),
        ('LOST', 'Lost'),
    ]

    opportunity_name = models.CharField(
        max_length=150
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='opportunities'
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    stage = models.CharField(
        max_length=30,
        choices=STAGE_CHOICES,
        default='QUALIFICATION'
    )

    probability = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )

    expected_close_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPEN'
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='opportunities'
    )

    notes = models.TextField(
        blank=True
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    @property
    def weighted_value(self):
        return float(self.amount) * self.probability / 100

    def __str__(self):
        return self.opportunity_name


class FollowUp(models.Model):

    TYPE_CHOICES = [
        ('CALL', 'Call'),
        ('MEETING', 'Meeting'),
        ('EMAIL', 'Email'),
        ('TASK', 'Task'),
    ]

    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('COMPLETED', 'Completed'),
        ('MISSED', 'Missed'),
        ('CANCELLED', 'Cancelled'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followups'
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followups'
    )

    follow_up_date = models.DateField()

    follow_up_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='CALL'
    )

    subject = models.CharField(
        max_length=200
    )

    remarks = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED'
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='followups'
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.subject


class Activity(models.Model):

    ACTIVITY_TYPES = [
        ('CALL', 'Call'),
        ('MEETING', 'Meeting'),
        ('EMAIL', 'Email'),
        ('TASK', 'Task'),
    ]

    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES
    )

    subject = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    activity_date = models.DateTimeField()

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )

    lead = models.ForeignKey(
        Lead,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='activities'
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities'
    )

    status = models.CharField(
        max_length=30,
        default='OPEN'
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.subject


class AuditLog(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(
        max_length=50
    )

    entity_name = models.CharField(
        max_length=100
    )

    record_id = models.IntegerField(
        null=True,
        blank=True
    )

    old_value = models.TextField(
        blank=True
    )

    new_value = models.TextField(
        blank=True
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.action} - {self.entity_name}"