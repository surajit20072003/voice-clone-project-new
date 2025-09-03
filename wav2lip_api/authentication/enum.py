from django.db import models
from django.utils.translation import gettext_lazy as _


class RolesEnum(models.TextChoices):
    UNIVERSITY = 'university', 'University'
    EMPLOYER = 'employer', 'Employer'
    ALUMNI = 'alumni', 'Alumni'
    ADMIN = 'admin', 'Admin'
    STUDENT = 'student', 'Student'


class GenderEnum(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'


class OccupationChoices(models.TextChoices):
    JOB = 'job', 'Job'
    BUSINESS = 'business', 'Business'
    STUDENT = 'student', 'Student'
    OTHER = 'other', 'Other'


class CollegeChoices(models.TextChoices):
    NORTH_STATE_UNIVERSITY = 'north_state_university', 'North State University'
    PACIFIC_TECHNICAL_INSTITUTE = 'pacific_technical_institute', 'Pacific Technical Institute'
    EASTERN_COLLEGE_OF_ARTS = 'eastern_college_of_arts', 'Eastern College of Arts'
    SOUTHERN_ENGINEERING_UNIVERSITY = 'southern_engineering_university', 'Southern Engineering University'
    CENTRAL_BUSINESS_SCHOOL = 'central_business_school', 'Central Business School'
    NORTHWEST_MEDICAL_COLLEGE = 'northwest_medical_college', 'Northwest Medical College'
    MIDWESTERN_TECHNOLOGY_INSTITUTE = 'midwestern_institute_of_technology', 'Midwestern Institute of Technology'
    ATLANTIC_SCIENCES_UNIVERSITY = 'atlantic_sciences_university', 'Atlantic Sciences University'


class DepartmentChoices(models.TextChoices):
    COMPUTER_SCIENCE = 'computer_science', 'Computer Science'
    BUSINESS_ADMINISTRATION = 'business_administration', 'Business Administration'
    MECHANICAL_ENGINEERING = 'mechanical_engineering', 'Mechanical Engineering'
    ELECTRICAL_ENGINEERING = 'electrical_engineering', 'Electrical Engineering'
    LIBERAL_ARTS = 'liberal_arts', 'Liberal Arts'
    MEDICINE = 'medicine', 'Medicine'
    PSYCHOLOGY = 'psychology', 'Psychology'
    BIOLOGY = 'biology', 'Biology'


class GenderChoices(models.TextChoices):
    MALE = 'male', 'Male'
    FEMALE = 'female', 'Female'
    OTHER = 'other', 'Other'
    PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'


class IndustryChoices(models.TextChoices):
    TECHNOLOGY = 'technology', 'Technology'
    HEALTHCARE = 'healthcare', 'Healthcare'
    FINANCE = 'finance', 'Finance'
    EDUCATION = 'education', 'Education'
    MANUFACTURING = 'manufacturing', 'Manufacturing'
    RETAIL = 'retail', 'Retail'
    CONSTRUCTION = 'construction', 'Construction'
    ENTERTAINMENT = 'entertainment', 'Entertainment'
    AGRICULTURE = 'agriculture', 'Agriculture'
    ENERGY = 'energy', 'Energy'
    TRANSPORTATION = 'transportation', 'Transportation'


class EmploymentTypesEnum(models.TextChoices):
    FULL_TIME = 'full_time', 'Full Time'
    PART_TIME = 'part_time', 'Part Time'
    INTERNSHIP = 'internship', 'Internship'
    CONTRACT = 'contract', 'Contract'


class StatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROCESS = 'in_process', 'In Process'
    RUNNING = 'running', 'Running'
    COMPLETED = 'completed', 'Completed'
    ACCEPTED = 'accepted', 'Accepted'
    REJECTED = 'rejected', 'Rejected'
    APPROVED = 'approved', 'Approved'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'


class VisibilityEnum(models.TextChoices):
    PUBLIC = 'public', 'Public'
    PRIVATE = 'private', 'Private'
    FRIENDS = 'friends', 'Friends'
    ONLY_ME = 'only_me', 'Only Me'



class JobApplicationStatusEnum(models.TextChoices):
    PENDING = 'pending', 'Pending'
    SHORTLISTED = 'shortlisted', 'Shortlisted'
    INTERVIEW = 'interview', 'Interview'
    OFFERED = 'offered', 'Offered'
    REJECTED = 'rejected', 'Rejected'

class CourseStatusEnum(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ARCHIVED = 'archived', 'Archived'

class CourseLevelEnum(models.TextChoices):
    BEGINNER = 'beginner', 'Beginner'
    INTERMEDIATE = 'intermediate', 'Intermediate'
    ADVANCED = 'advanced', 'Advanced'
    EXPERT = 'expert', 'Expert'

class EnrollmentStatusEnum(models.TextChoices):
    ENROLLED = 'enrolled', 'Enrolled'
    IN_PROGRESS = 'in_progress', 'In_progress'
    COMPLETED = 'completed', 'Completed'

class DurationTypeEnum(models.TextChoices):
    WEEK = 'week', 'Week'
    MONTH = 'month', 'Month'
    DAY = 'day', 'Day'
    HOUR = 'hour', 'Hour'
    YEAR = 'year', 'Year'
    MINUTE = "minute", "Minute"

class AudienceTypeEnum(models.TextChoices):
    STUDENT = 'Student', 'student'
    ALUMNI = 'Alumni', 'alumni'
    BOTH = 'Both', 'both'

class QuestionTypeEnum(models.TextChoices):
    MULTIPLE_CJHOICE = 'Multiple-Choice', 'mulyiple-choice'
    MULTI_SELECT = 'Multi-Select', 'multi-select'

class JobFairStatus(models.TextChoices):
    UPCOMING = 'Upcoming', 'Upcoming'
    ONGOING = 'Ongoing', 'Ongoing'
    COMPLETED = 'Completed', 'Completed'

class RegistrationStatus(models.IntegerChoices):
    CLOSED = 0, 'Closed'
    OPEN = 1, 'Open'

class ContactMethodChoices(models.TextChoices):
    EMAIL = "Email", "Email"
    SMS = "SMS", "SMS"
    PHONE_CALL = "Phone Call", "Phone Call"
    WHATSAPP = "WhatsApp", "WhatsApp"

class InterestChoices(models.TextChoices):
    ALUMNI_EVENTS = "Alumni Events", "Alumni Events"
    JOB_POSTINGS = "Job Postings", "Job Postings"
    WORKSHOPS = "Workshops & Training", "Workshops & Training"
    NETWORKING = "Networking Opportunities", "Networking Opportunities"
    NEWSLETTER = "Newsletter", "Newsletter"

class MentorshipChoices(models.TextChoices):
    MENTOR = "mentor", "I'd like to be a mentor"
    FIND_MENTOR = "find_mentor", "I'd like to find a mentor"
    BOTH = "both", "Both"
    NOT_INTERESTED = "not_interested", "Not_interested"
USER_TYPE_CHOICES = [
            ('alumni', 'Alumni'),
            ('current', 'Current Student')]
class GraduationTypeChoices(models.TextChoices):
    UNDERGRADUATE = "undergraduate", "Undergraduate"
    GRADUATE = "graduate", "Graduate"
    POSTGRADUATE = "postgraduate", "Postgraduate"
    PHD = "phd", "PhD"


class ProgramChoices(models.TextChoices):
    BSC = "B.Sc", "B.Sc"
    BCOM = "B.Com", "B.Com"
    BA = "B.A", "B.A"
    BTECH = "B.Tech", "B.Tech"
    BBA = "BBA", "BBA"
    BCA = "BCA", "BCA"

    MSC = "M.Sc", "M.Sc"
    MCOM = "M.Com", "M.Com"
    MA = "M.A", "M.A"
    MTECH = "M.Tech", "M.Tech"
    MBA = "MBA", "MBA"
    MCA = "MCA", "MCA"

    PG_DIPLOMA = "PG Diploma", "PG Diploma"
    ADV_CERT = "Advanced Certificate", "Advanced Certificate"

    PHD_SCI = "Ph.D Science", "Ph.D Science"
    PHD_COM = "Ph.D Commerce", "Ph.D Commerce"
    PHD_ARTS = "Ph.D Arts", "Ph.D Arts"
    PHD_ENGG = "Ph.D Engineering", "Ph.D Engineering"


class JobFairTypeEnum(models.TextChoices):
    PHYSICAL = 'physical', 'Physical'
    VIRTUAL = 'virtual', 'Virtual'

class ParticipantRoleEnum(models.TextChoices):
    STUDENT = 'student', 'Student'
    ALUMNI = 'alumni', 'Alumni'
    STAFF = 'staff', 'Staff'


# --- NEW: Employer Status Choices ---
class EmployerStatusChoices(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'

# NEW: Enum for Associated Course Types
class AssociatedCourseTypeEnum(models.TextChoices):
    LEADERSHIP_SKILLS = "leadership_skills", "Leadership Skills"
    PROJECT_MANAGEMENT = "project_management", "Project Management"
    DIGITAL_MARKETING = "digital_marketing", "Digital Marketing"
    DATA_ANALYTICS = "data_analytics", "Data Analytics" 
    # Add any other specific choices your frontend requires


# NEW: Update the CourseTypeEnum with the new choices and make it optional
class CourseTypeEnum(models.TextChoices):
    REGULAR = 'regular', 'Regular Course'
    IRE = 'ire', 'IRE Session'
    LIVE = 'live', 'Live'

class LiveSessionTypeEnum(models.TextChoices):
    # Database Value (key)   Human-Readable Label
    LIVE_SESSION = "live_session", "Live Session"
    RECORDED_SESSION = "recorded_session", "Recorded Session"
    WORKSHOP = "workshop", "Workshop"
    WEBINAR = "webinar", "Webinar"


# --- Enums for Donation Campaigns and Transactions ---
class DonationCampaignStatusChoices(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    ACTIVE = 'active', _('Active')
    COMPLETED = 'completed', _('Completed')
    SUSPENDED = 'suspended', _('Suspended')


class DonationTransactionStatusChoices(models.TextChoices):
    COMPLETED = 'completed', _('Completed')
    PENDING = 'pending', _('Pending')
    FAILED = 'failed', _('Failed')

# Choices for the status of a scholarship.
# This list is based on the "Status" dropdown from the screenshot.
SCHOLARSHIP_STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('active', 'Active'),
    ('closed', 'Closed'),
    ('under_review', 'Under Review'),
)

# Choices for the department.
# This list is based on the "Department" dropdown from the screenshot.
DEPARTMENT_CHOICES = (
    ('all_departments', 'All Departments'),
    ('engineering', 'Engineering'),
    ('business', 'Business'),
    ('arts_and_sciences', 'Arts & Sciences'),
    ('medicine', 'Medicine'),
    ('law', 'Law'),
)

# Choices for the year of study.
# This list has been updated to include 'Graduate' and 'Post Graduate'.
YEAR_OF_STUDY_CHOICES = (
    ('any_year', 'Any Year'),
    ('1st_year', '1st Year'),
    ('2nd_year', '2nd Year'),
    ('3rd_year', '3rd Year'),
    ('4th_year', '4th Year'),
    ('graduate', 'Graduate'),
    ('post_graduate', 'Post Graduate'),
)

# New enum for scholarship categories.
# This is an example, you can adjust the categories as needed.
CATEGORY_CHOICES = (
    ('merit_based', 'Merit-based'),
    ('need_based', 'Need-based'),
    ('sports', 'Sports'),
    ('arts_and_culture', 'Arts & Culture'),
    ('research', 'Research'),
    ('minority', 'Minority'),
    ('international_students', 'International Students'),
)

class CompanySizeChoices(models.TextChoices):
    """
    Size categories for a company, based on employee count.
    """
    RANGE_1_10 = '1-10', '1-10 employees'
    RANGE_11_50 = '11-50', '11-50 employees'
    RANGE_51_200 = '51-200', '51-200 employees'
    RANGE_201_500 = '201-500', '201-500 employees'
    RANGE_501_1000 = '501-1000', '501-1000 employees'
    RANGE_1000_PLUS = '1000+', '1000+ employees'