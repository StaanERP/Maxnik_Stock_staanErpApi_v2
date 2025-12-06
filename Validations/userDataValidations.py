from django.core.validators import RegexValidator

aadhaar_validator = RegexValidator(
    regex=r'^\d{12}$',  # Aadhaar number is exactly 12 digits
    message="Aadhaar number must be exactly 12 digits."
)
pan_validator = RegexValidator(
    regex=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$',
    message="PAN number must be in the format: XXXXX9999X (uppercase)."
)

phone_Validator =  RegexValidator(
                regex=r'^\+?1?\d{9,15}$',  # Basic validation for phone numbers (allowing international format)
                message="Enter a valid mobile number with up to 15 digits, including country code."
            )

bank_account_no_Validator =  RegexValidator(
                regex=r'^\d{9,18}$',  # Example for bank account numbers (numeric and between 9 to 18 digits)
                message="Bank account number should contain only digits and be between 9 to 18 digits."
            )

IFSC_Validator = RegexValidator(
                regex=r'^[A-Za-z]{4}\d{7}$',  # IFSC code format: 4 letters followed by 7 digits
                message="Enter a valid IFSC code (4 letters followed by 7 digits)."
            )
esi_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Enter a valid 10-digit ESI number."
)