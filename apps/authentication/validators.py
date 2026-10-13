import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

# Indian NITI Aayog NGO Darpan Unique ID regex validator
# Standard format: 2 uppercase letters (state code) / 4 digit year / 7 digit registration number
# Example: DL/2019/0123456 or MH/2021/0089765
DARPAN_REGEX = r'^[A-Z]{2}/\d{4}/\d{7}$'

darpan_validator = RegexValidator(
    regex=DARPAN_REGEX,
    message="NGO Darpan ID must follow the standard format: 'STATE_CODE/YYYY/REGISTRATION_NO' (e.g. DL/2019/0123456)."
)

def validate_ngo_darpan_id(darpan_id: str) -> dict:
    """
    Validates and mocks official verification with the NITI Aayog NGO Darpan registry.
    Returns dict with verification status and metadata.
    """
    if not darpan_id:
        return {
            'valid': False,
            'status': 'REJECTED',
            'message': 'Darpan ID is required.'
        }
    
    cleaned_id = darpan_id.strip().upper()
    if not re.match(DARPAN_REGEX, cleaned_id):
        return {
            'valid': False,
            'status': 'REJECTED',
            'message': "Invalid Darpan ID format. Expected format: 'XX/YYYY/XXXXXXX' (e.g. DL/2020/0012345)."
        }
    
    # Mocking external NITI Aayog portal verification checks:
    # Any ID ending in 0000000 is simulated as invalid/blacklisted
    if cleaned_id.endswith("0000000"):
        return {
            'valid': False,
            'status': 'REJECTED',
            'message': 'The provided NGO Darpan ID has been deactivated or flagged by NITI Aayog.'
        }
    
    state_code = cleaned_id.split('/')[0]
    registration_year = cleaned_id.split('/')[1]
    
    return {
        'valid': True,
        'status': 'VERIFIED',
        'darpan_id': cleaned_id,
        'state_code': state_code,
        'registration_year': registration_year,
        'message': f'Darpan ID successfully verified with NITI Aayog registry ({state_code} State Chapter).'
    }
