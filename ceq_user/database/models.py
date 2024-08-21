from datetime import datetime
import uuid
from mongoengine import Document, EmailField, StringField, IntField, \
    DateTimeField, ReferenceField, EmbeddedDocument, \
    EmbeddedDocumentField, EmbeddedDocumentListField, ListField, BooleanField, fields 
 
"""
ALL our models are declared here
 
"""

class User(Document):
 
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    ROLE_CHOICES = (
        ('supervisor', 'SuperVisor'),
        ('auditor', 'Auditor'),
        ('admin', 'Admin'),
    )
    PERMISSION_CHOICE = (
        ('business', 'Business'),
        ('consumer', 'consumer'),
        ('all', 'All')
    )
    status = StringField(choices=STATUS_CHOICES)
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    phone_number = StringField(required=False, min_length=9)
    role = StringField(choices=ROLE_CHOICES)
    name = StringField()
    permission = StringField(choices=PERMISSION_CHOICE, required=False)
    supervisor = ReferenceField('User')
    login_count = IntField(default=0)
    last_login = DateTimeField()
    otp_code = StringField()
    otp_expiry = DateTimeField()


    def check_user_status(username):
        user = User.objects(username=username, status='active').first()
        if user is not None:
            return True
        else:
            return False



class Technicians(Document):
    emp_no = StringField(required=False)
    email_user_id = StringField(required=False)
    tech_pt = StringField(required=False)
    section = StringField(required=False)
    region = StringField(required=False)
    group = StringField(required=False)
    mobile_no = StringField(required=False)
    designation = StringField(required=False)
    technician_name = StringField(required=False)
    field_supervisor_pt = StringField(required=False)
    field_supervisor = StringField(required=False)
    

 
class ErrorCode(EmbeddedDocument):
    code = StringField(required=True)
    description = StringField(required=True)
 
 
 
class Category(Document):
    name = StringField(required=True, unique=True)
    error_codes = EmbeddedDocumentListField(ErrorCode)
   
   
   
class Violations(EmbeddedDocument):  
    category_code = StringField()
    violation_code = StringField()
    description = StringField()
    violation_type = BooleanField()
    remarks = StringField()
    image = StringField()
    severity = StringField()



class AuditData(Document):
    auditor_name = StringField()
    supervisor_contact = StringField()
    tech_pt = StringField()
    vehicle_number = StringField()
    tech_skills = StringField()
    sr_manager = StringField()
    tech_fullname = StringField()
    region = StringField()
    vendor = StringField()
    director = StringField()
    auditor_id = IntField()
    sr_number = StringField()
    tech_ein = StringField()
    team = StringField()
    duty_manager = StringField()
    supervisor = StringField()
    shortdescription = StringField()
    tech_contact = StringField()
    controller = StringField()
    group_head = StringField()
    user_action = StringField()
    status = StringField()
    lastmodified = DateTimeField(default=None)#this should be handled in the update API
    expiryDate = DateTimeField()
    auditDate = StringField()
    permission = StringField()
    createdDate = DateTimeField()
    ceqvs = ListField(EmbeddedDocumentField(Violations))
    audit_signature = StringField()
    signature_date = DateTimeField()
    audited_staff_signature = StringField()
    auditedDateTime = StringField()
    name = StringField()
    supervisor_id = StringField()
    superviser_comment = StringField(default="")
    # Define the index for the createdDate field
    meta = {
        'indexes': [
            {'fields': ['auditDate']}
        ]
    }


class BusinessAudit(Document):
    sn = IntField(default=0)
    date_of_visit = DateTimeField(default=None)
    date_and_time = DateTimeField(default=None)
    sr_dkt_no = StringField(default="")
    region = StringField(default="")
    sub_region = StringField(default="")
    product_group = StringField(default="")
    sr_type = StringField(default="")
    product_type = StringField(default="")
    contact_number = StringField(default="")
    ont_type = StringField(default="")
    ont_sn = StringField(default="")
    olt_code = StringField(default="")
    exch_code = StringField(default="")
    eid = StringField(default="")
    fdh_no = StringField(default="")
    account_no = StringField(default="")
    customer_name = StringField(default="")
    account_category = StringField(default="")
    sr_group = StringField(default="")
    cbcm_close_date = DateTimeField(default=None)
    latitude = StringField(default="")
    longitude = StringField(default="")
    wfm_emp_id = StringField(default="")
    tech_name = StringField(default="")
    party_id = StringField(default="")
    wfm_task_id = StringField(default="")
    wfm_wo_number = IntField(default=0)
    team_desc = StringField(default="")
    ceq_auditor_name = StringField(default="")
    observations_in_fhd_side = StringField(default="")
    violation_remarks = StringField(default="")
    violation = StringField(default="")
    photo1 = StringField(default="")
    photo2 = StringField(default="")
    photo3 = StringField(default="")
    photo4 = StringField(default="")
    photo5 = StringField(default="")
    photo6 = StringField(default="")
    ceqv01_sub_cable_inst = StringField(default="")
    ceqvo2_sub_inst_ont = StringField(default="")
    ceqv03_sub_inst_wastes_left_uncleaned = StringField(default="")
    ceqv04_existing_sub_inst_not_rectified = StringField(default="")
    ceqv05_sub_inst_cpe = StringField(default="")
    ceqv06_sub_labelling = StringField(default="")
    sub_cable_inst = IntField(default=0)
    sub_inst_ont = StringField(default="")
    sub_inst_wastes_left_uncleaned = IntField(default=0)
    existing_sub_inst_not_rectified = IntField(default=0)
    sub_inst_cpe = StringField(default="")
    sub_labelling = StringField(default="")
    total = IntField(default=0)
    compliance = StringField(default="")
    status = StringField(default="pending")
    superviser_comment = StringField(default="")
    signature = StringField(default="")
    
    def saves(self, *args, **kwargs):
        # Ensure default values are assigned if there's a ValueError
        for field_name, field in self._fields.items():
            try:
                value = getattr(self, field_name)
                # You might have an expected type for each field
                expected_type = field.expected_type  # Assume this attribute exists
                if not isinstance(value, expected_type):
                    value = expected_type(value)
                setattr(self, field_name, value)
            except ValueError:
                default = field.default
                if callable(default):
                    default = default()
                setattr(self, field_name, default)
        super(BusinessAudit, self).saves(*args, **kwargs)
    
    
class Companies(Document):
    company_name = StringField(default="")
    image_url = StringField(default="")
    

class FdhViolations(EmbeddedDocument):
    category_code = fields.StringField(default='')
    violation_code = fields.StringField(default='')
    violation_type = fields.BooleanField(default=False)
    severity = fields.StringField(default='')
    description = StringField(default='')
    remarks = fields.StringField(default='')
 
class Visit(EmbeddedDocument):
    visited_id = StringField(default='')
    visiter_name = fields.StringField(default='')
    visit_time = fields.DateTimeField(default=datetime.utcnow)
    violations = fields.ListField(fields.EmbeddedDocumentField(FdhViolations), default=[])
    images = fields.ListField(fields.StringField(), default=[])
 
class NewFdh(Document):
    fdh_health = fields.StringField(default='')
    fdh_number = fields.IntField(default=0)
    eid = fields.StringField(default='')
    olt = fields.StringField(default='')
    last_uplifted_date = fields.StringField(default='')
    uplifting_frequency = fields.IntField(default=0)
    region = fields.StringField(default='')
    latitude = fields.StringField(default='')
    longitude = fields.StringField(default='')
    sub_type = fields.StringField(default='')
    severity = fields.StringField(default='')
    action_proposed = fields.StringField(default='')
    expansion_required = fields.StringField(default='')
    datetime = fields.DateTimeField(default="")
    network_details = fields.StringField(default='')    
    size_score = fields.IntField(default=0)
    inspection_date = fields.StringField(default='')
    visit_required = fields.StringField(default='')
    size = fields.IntField(default=0)
    utilization = fields.StringField(default='')
    network_health_index = fields.IntField(default=0)
    health_index_slab = fields.StringField(default='')
    faults = fields.StringField(default='')
    health_index = fields.IntField(default=0)
    main_type = fields.StringField(default='')
    physical_health_index = fields.StringField(default='')
    utilization_score = fields.IntField(default=0)
    utilization_slab = fields.StringField(default='')
    faults_slab = fields.StringField(default='')
    name = fields.StringField(default='')
    uplift_required = fields.StringField(default='')
    fdh_id = fields.StringField(default='')
    comment = fields.StringField(default='')
    violations = fields.ListField(fields.EmbeddedDocumentField(FdhViolations), default=[])
    visits = fields.ListField(fields.EmbeddedDocumentField(Visit), default=[])
 
    def save(self, *args, **kwargs):
        for field_name, field in self._fields.items():
            if getattr(self, field_name) is None:
                default = field.default
                if callable(default):
                    default = default()
                setattr(self, field_name, default)
        super(NewFdh, self).save(*args, **kwargs)