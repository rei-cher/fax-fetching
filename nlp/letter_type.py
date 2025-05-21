import re

# ==== Patterns for different types of letter for determination ====

approval_patterns = [
    r"has been approved",
    r"Type of coverage approved: Prior Authorization",
    r"Type of coverage approved: Non-Formulary",
    r"pproved for",
    r"This drug has been approved",
    r"This request has been reviewed and approved for the following time period",
    r"Approved for",
    r"approved the requast as follows",
    r"the request is approved for the following time period",
    r"writing to let you know that we have approved",
    r"APPROVAL NOTICE",
    r"Prior Authorization Status: Approved",
    r"no prior authorization required",
    r"We've approved your request for coverage",
    r"the request was APPROVED",
    r"has approved a request from you or your doctor for"
    r"We approved coverage under the member's prescription drug benefits for"
    r"Prior authorization is not required at this time"
]
 
denial_patterns = [
    r"Reason for Denial:",
    r"__X__ Denying your request for",
    r"__X___Denying your request for",
    r"__X__Denying your request for",
    r"__x__ Denying your request for",
    r"__X%__Denying your request for",
    r"__X%___Denying your request for",
    r"__x%__Denying your request for",
    r"_xX__Denying your request for",
    r"__xX__Denying your request for",
    r"X_ Denying your request for",
    r"X_Denying your request for",
    r"x_ Denying your request for",
    r"x_Denying your request for",
    r"X__ Denying your request for",
    r"RE: Denial of request for coverage",
    r"denied the request for the following reason",
    r"We are unable to approve your request for this drug",
    r"denied the prior authorization",
    r"After reviewing the information sent with your request, it was determined that this request does not meet the criteria for medical necessity",

]

request_patterns = [
    r'RE: Prior Authorization Request',
    r'is waiting for their medication',
    r'A Prior Authorization has been started for',
    r'the PA started for your patient',
    r'has been rejected and requires prior authorization',
    r'ALTERNATIVE REQUESTED :NOT COVERED',
    r'Prior Authorization has already been created',
    r'A Prior Authorization has been started  for',
    r'RESPONSE REQUESTED:  Please send a new prescription',
    r'PRIOR AUTHORIZATION REQUEST',
    r'Your request for prior authorization has been denied. Complete and fax this appeal to the plan today so your patient can receive their medication'
]

received_request_patterns = [
    r'Request Status: Received'
]

trash_pattern = [
    r"Duplicate request. An approved prior authorization is already in the system"
]

# TODO: find and determine patterns for clinical requests without breaking the other determinations
clinical_pattern = [
    
]

def determine_letter_type(text) -> str:
    """
    Deternines letter type based on the patterns
    Return one of the following: 'Approval', 'Denial', 'PA-Request', 'Received-Request', 'Trash'
    """
    for pattern in approval_patterns:
        if re.search(pattern, text):
            return "Approval"
    for pattern in denial_patterns:
        if re.search(pattern, text):
            return "Denial"
    for pattern in request_patterns:
        if re.search(pattern, text):
            return "PA-Request"
    for pattern in received_request_patterns:
        if re.search(pattern, text):
            return "Received-Request"
    for pattern in trash_pattern:
        if re.search(pattern, text):
            return "Trash"
    # for pattern in clinical_pattern:
    #     if re.search(pattern, text):
    #         return "Clinical"